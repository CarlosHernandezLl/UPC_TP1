# Documentación de Referencia — HVAC AI Engine (UPC TP1)

> Sistema de Soporte a la Decisión para optimización energética de sistemas HVAC en una planta farmacéutica (entorno GxP / 21 CFR Part 11). Combina un **Gemelo Digital** basado en XGBoost, un pipeline **MLOps** de reentrenamiento con explicabilidad (SHAP), auditoría y un panel web por roles.

Fecha de la actualización: 2026-11-04 · Rama: `master` · Cambios aún sin commitear (ver §8)

---

## 1. Visión general

El operador ingresa las condiciones de la sala limpia y de la UMA (unidad manejadora de aire). El backend usa un modelo XGBoost que predice la humedad absoluta de la sala (`room_w`, g/kg) y busca la **mínima potencia del deshumidificador/secador** (`dryer_power`) que mantiene la humedad dentro del objetivo con un margen de seguridad. Gemini redacta una justificación técnica. Toda decisión del operador (aplicar o sobrescribir la IA) queda registrada en BD y en la pista de auditoría.

```
┌────────────────┐   HTTP/JSON + Bearer JWT    ┌──────────────────────────┐   ┌────────────┐
│ Frontend       │ ─────────────────────────▶ │ Backend FastAPI          │──▶│ PostgreSQL │
│ Next.js 16     │                             │ routers → services →     │   │ hvac_db    │
│ :3000          │ ◀───────────────────────── │ repositories → models    │   └────────────┘
└────────────────┘                             │        │                 │
                                               │  ml_engine (XGBoost RAM) │──▶ saved_models/*.json (volumen)
                                               │  Gemini                  │
                                               └──────────────────────────┘
```

### Stack

| Capa | Tecnologías |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy, Alembic, Pydantic v2 / pydantic-settings, uvicorn |
| ML | XGBoost (incluye TreeSHAP vía `pred_contribs`), scikit-learn, pandas, numpy |
| Seguridad | JWT (`python-jose`) con `jti` revocable, bcrypt, OAuth2 Password Bearer |
| IA generativa | Google Gemini (`gemini-2.5-flash-lite`) vía `google-genai` |
| Reportes | reportlab (PDF), csv |
| Frontend | Next.js 16.1.6 (App Router), React 19, TypeScript 5, Tailwind CSS 4, Recharts 3, Heroicons |
| BD | PostgreSQL 17 (zona horaria `America/Lima`) |
| Despliegue | Docker Compose (db + backend + frontend). El frontend también estuvo publicado en Vercel (`https://upc-tp-1-sigma.vercel.app`) |

---

## 2. Estructura del repositorio

```
UPC_TP1/
├── .clinerules                  # Manifiesto de arquitectura y limpieza (reglas para IA/colaboradores)
├── docker-compose.yml           # db (postgres:17) + backend + frontend; volúmenes pgdata y models
├── docs/                        # ESTADO_IMPLEMENTACION.md, HU/CP (xlsx), datasets de entrenamiento (Mayo y Julio)
├── tests/e2e/                   # Suite de aceptación (Chrome + API) de los 59 CP; ver su README
├── HU_CP_para_VSCode.md         # Historias de usuario y casos de prueba
├── TP1_BACKEND/
│   ├── Dockerfile, .dockerignore, .env.example
│   ├── alembic.ini, migrations/versions/   # 0001 esquema inicial · 0002 feature_importance · 0003 revoked_tokens
│   ├── requirements.txt         # 19 dependencias, todas con versión fijada
│   └── app/
│       ├── main.py              # App FastAPI, CORS, lifespan (seed admin + carga del Champion), routers
│       ├── core/                # config.py, database.py, security.py
│       ├── api/deps.py          # Usuario actual (valida revocación), RBAC (check_role)
│       ├── api/routers/         # auth, users, data, gmp, audit, simulation, mlops, dashboard
│       ├── services/            # Lógica de negocio
│       ├── repositories/        # Acceso a datos (SQLAlchemy)
│       ├── models/              # Entidades ORM (8 tablas)
│       ├── schemas/             # Modelos Pydantic de entrada/salida
│       └── ml_engine/           # simulator_engine.py, ssd_filter.py, saved_models/
└── TP1_FRONTEND/
    ├── Dockerfile, next.config.ts   # next.config: cabeceras no-store (sin caché de páginas protegidas)
    ├── app/                     # Rutas App Router: (auth)/login, (dashboard)/*
    ├── components/ui/           # SideNav, justification-modal, toast
    ├── services/                # Clientes HTTP hacia la API
    ├── types/user.ts
    └── package.json
```

### Reglas de arquitectura (`.clinerules`)
1. Cero código zombie (comentado, deprecado, imports sin usar).
2. Ningún archivo > 250 líneas.
3. Tipado estricto: payloads de entrada/salida con Pydantic, sin `dict`/`Any`.
4. `logging` en lugar de `print`; errores con HTTP status explícito y JSON estructurado.
5. No añadir dependencias sin confirmación.

---

## 3. Backend

### 3.1 Arquitectura en capas

`Router` (HTTP + RBAC) → `Service` (reglas de negocio) → `Repository` (SQLAlchemy) → `Model` (tabla). Los proveedores de dependencias (`get_*_service`) ensamblan repositorios y servicios por request. El motor ML es un **singleton** (`simulator_engine_instance`) compartido vía `app.state.simulator_engine`.

### 3.2 Configuración (`app/core/config.py`, `.env`)

Plantilla en `TP1_BACKEND/.env.example` (el `.env` real no se versiona).

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | Cadena PostgreSQL (requerida) |
| `SECRET_KEY`, `ALGORITHM` (HS256), `ACCESS_TOKEN_EXPIRE_MINUTES` (60) | JWT |
| `GEMINI_API_KEY` | Opcional; sin ella se usan textos de contingencia |
| `FRONTEND_URL` | Origen CORS adicional (por defecto el de Vercel) |
| `FIRST_ADMIN_PASSWORD` | Si la BD no tiene usuarios, crea el admin inicial al arrancar |
| `FIRST_ADMIN_USERNAME` (`admin_hvac`), `FIRST_ADMIN_FULL_NAME` | Datos del admin inicial |

Frontend: `NEXT_PUBLIC_API_URL` (URL base de la API). Se **incrusta en el build**, por eso el Dockerfile la recibe como `build-arg`.

### 3.3 Arranque (`app/main.py`)
- El esquema lo gestiona **solo Alembic** (`alembic upgrade head` en el `CMD` del Dockerfile); ya no se usa `create_all`.
- `lifespan`: (1) si hay `FIRST_ADMIN_PASSWORD` y la BD está vacía, crea el admin y los límites GMP por defecto (40–55 %, setpoint 49); (2) consulta el modelo **Champion** en BD y lo carga en RAM; si no existe o su archivo no se encuentra, usa el modelo base `saved_models/xgboost_hvac_v1.json`.
- `_resolve_model_path` tolera rutas guardadas en otro sistema operativo o contenedor (busca el mismo archivo dentro de `saved_models/`).
- CORS: `localhost:3000`, `192.168.0.100:3000` y `FRONTEND_URL`.
- Logging a `logs/app.log` (nivel ERROR). Health check: `GET /`.

### 3.4 Modelo de datos (8 tablas)

| Tabla | Propósito | Campos clave |
|---|---|---|
| `users` | Usuarios y roles | `username` (único), `hashed_password`, `role` (ADMIN/SUPERVISOR/AUDITOR/GERENTE), `is_active` (soft delete) |
| `hvac_historical_data` | Telemetría minuto a minuto | `timestamp`, `batch_id` (UUID), `outdoor_temp/w`, `ahu_temp/w`, `injection_pressure`, `dryer_power`, `room_temp/rh/w`, `is_clean` |
| `data_ingestion_logs` | Linaje de cargas | `batch_id`, `data_range`, `record_count`, `status` (SINCRONIZADO / ERROR COLUMNAS / ERROR FORMATO) |
| `ml_model_versions` | Model Registry | `version_tag` (`v1.MMDD.HHMMSS`), `model_path`, `batch_id`, `r2_score`, `rmse`, **`feature_importance` (JSON, SHAP)**, `status` (ACTIVE=Champion / ARCHIVED) |
| `simulation_logs` | Decisiones del operador | entradas ambientales, `current_power`, `recommended_power`, `applied_power`, `action`, `justification`, `model_version_id` |
| `audit_trail` | Pista de auditoría GxP | `user_id`, `action`, `resource`, `detail`, `ip_address`, `created_at` |
| `gmp_parameters` | Límites regulatorios de HR | `min_hum_limit`, `max_hum_limit`, `default_setpoint`, `updated_by` |
| `revoked_tokens` | Tokens JWT cerrados | `jti` (PK), `expires_at` (se purgan al vencer) |

La tabla `energy_pricing` y su repositorio se eliminaron; la tarifa del kWh vive solo en el navegador (Dashboard).

### 3.5 Roles y permisos (RBAC)

`check_role([...])` en `deps.py`; **ADMIN siempre pasa**. Un acceso denegado genera `ACCESS_DENIED` en la auditoría con IP (dentro de `detail`) y responde 403.

| Rol | Acceso (backend) | Menú del frontend |
|---|---|---|
| ADMIN | Todo (usuarios, reentrenamiento, límites GMP) | Todo |
| SUPERVISOR | Dashboard, simulador, ingesta de datos, métricas/historial MLOps | Dashboard, Ingesta, Simulador |
| GERENTE | Dashboard | Dashboard |
| AUDITOR | Auditoría, métricas/historial MLOps | Auditoría |

El frontend solo oculta opciones del menú; la autorización real está en el backend.

### 3.6 Endpoints

| Método y ruta | Roles | Descripción |
|---|---|---|
| `POST /auth/login` | público | OAuth2 form (`username`,`password`) → `access_token` (con `jti`), `user_info` |
| `POST /auth/logout` | autenticado | **Revoca el token** (lo guarda en `revoked_tokens`) y audita `USER_LOGOUT` |
| `POST /auth/register-first-user` | público | Crea el admin inicial; solo funciona con la BD vacía y `FIRST_ADMIN_PASSWORD` definida (403 si ya hay usuarios) |
| `GET /users/` · `POST /users/` · `PUT /users/{id}` · `DELETE /users/{id}` | ADMIN | CRUD de usuarios; DELETE es inhabilitación (soft delete) |
| `POST /data/upload` | SUPERVISOR | Multipart: `file_plc`, `file_log`, `file_ext`, `start_date?`, `end_date?` |
| `GET /data/ingestion/history` | SUPERVISOR | Historial de ingestas |
| `GET /config/gmp/` | cualquier autenticado | Límites GMP vigentes |
| `PUT /config/gmp/` | ADMIN | Actualiza límites (audita `GMP_LIMITS_UPDATE`) |
| `POST /simulation/predict` | SUPERVISOR | Recomendación de potencia + explicación Gemini |
| `POST /simulation/log-action` | SUPERVISOR | Registra decisión (APPLIED / OVERRIDDEN) + auditoría |
| `GET /mlops/metrics` | SUPERVISOR, AUDITOR | Métricas del Champion, incluida la importancia SHAP |
| `GET /mlops/history` | SUPERVISOR, AUDITOR | Historial de versiones |
| `GET /mlops/training-log` | SUPERVISOR, AUDITOR | Entrenamientos exitosos, rechazados y fallidos con su motivo |
| `POST /mlops/retrain` | ADMIN | Ejecuta el pipeline de reentrenamiento |
| `GET /dashboard/metrics` | GERENTE, SUPERVISOR | KPIs de ahorro y series para gráficos |
| `GET /audit/` | AUDITOR | Últimos 500 eventos; filtros opcionales `desde` y `hasta` (AAAA-MM-DD, inclusivos; 400 si están invertidos) |
| `POST /audit/log` | autenticado | Registro manual de evento |
| `GET /audit/export-applied-csv` · `/export-applied-pdf` | AUDITOR | Exportación del Audit Trail (CSV con BOM para Excel, o PDF); aceptan los mismos `desde` / `hasta` |

### 3.7 Flujos principales

#### a) Ingesta de datos (`DataService.upload_and_sync`)
1. Recibe 3 archivos en `.csv` o `.xlsx` (el datalogger también `.xls`, tabulado o binario): **PLC** (col. `fecha`, `f20910p` presión, `f20911t/h` T/HR de la UMA, `f209potsecador`), **logger de sala** (CSV/TXT/XLS/XLSX con 20 filas de cabecera; col. `Fecha`, `Hora`, `Temperatura`, `Humedad`) y **externo** (col. `timestamp`, `temp_ext`, `hum_ext`).
2. **Valida la estructura** antes de procesar: si faltan columnas responde 400 con "Estructura inválida. <archivo>: falta(n) la(s) columna(s) …" y registra la carga como error. Valida que las fechas tengan el formato `DD/MM/AAAA HH:MM` (error de formato si más del 10 % de las filas con fecha no se interpretan). Si se informan ambas fechas de corte y la de fin no es mayor que la de inicio responde "La fecha de fin debe ser mayor a la fecha de inicio."; si solo se informa una, la otra se toma del rango común de los archivos.
3. Filtra ruido (HR 0–100 %, T −10…60 °C), recorta al rango común (o al indicado), fusiona por timestamp, remuestrea a **1 min** con interpolación lineal.
4. Calcula humedades absolutas (g/kg) con `SSDFilter.calculate_absolute_humidity`: `w_ext`, `w_sala`, `w_uma` (con presión dinámica de la UMA).
5. Guarda en `hvac_historical_data` con un `batch_id` UUID nuevo y registra el lote en `data_ingestion_logs`.

#### b) Recomendación (`SimulatorEngine.recomendar_potencia`)
1. Convierte HR a humedad absoluta (exterior, UMA con presión `1013.25 + Pinj/100`).
2. Objetivo: `w_límite = w(room_temp, setpoint) − safety_margin (0.37 g/kg)`.
3. Recorre potencias **de la actual hacia abajo (mín. 5 %)** y se queda con la menor cuya predicción `room_w` ≤ límite; se detiene en la primera que falla.
4. Verificación final: calcula la HR simulada resultante; `alerta_gmp = true` si queda fuera de [min, max] de `gmp_parameters`.
5. `SimulationService` calcula `ahorro_estimado_pct = (actual − ideal)/actual·100` y pide a `LlmService` una justificación de ≤ 2 líneas (con textos de contingencia si no hay API key o falla Gemini).

Features del modelo (6): `dryer_power, outdoor_temp, outdoor_w, ahu_temp, ahu_w, injection_pressure`.

**Validación de entrada** (`SimulationBase`): HR y setpoint 0–100 %, potencia 0–100 %, temperaturas 0–50 °C, **presión de inyección 0–1000 Pa** (la UI aplica los mismos rangos con mensajes de rango por campo). Al descartar una recomendación (`RECOMMENDATION_OVERRIDDEN`) la justificación debe tener ≥ 10 caracteres (422 si no). La recomendación devuelta es siempre un entero.

#### c) Reentrenamiento MLOps (`MLTrainingService.execute_retraining_pipeline`)
1. Toma el **último lote** ingerido con éxito (mín. 100 filas). Si no hay registro de carga válido, usa los últimos 5000 registros.
2. **Filtro SSD** (`SSDFilter.extract_stationary_minutes`): por cada escalón de potencia, detecta estado estacionario (variación suavizada de `room_w` bajo el percentil 95 durante ≥10 min consecutivos; grupos < 20 filas se descartan).
3. Validación **LOSO** (Leave-One-Step-Out) con métricas agrupadas: R² y RMSE fuera de muestra.
4. **Quality Gate**: si R² < 70 % → `ML_MODEL_REJECTED` (HTTP 400).
5. Si pasa: entrena con el 100 % de los datos, guarda `saved_models/xgboost_hvac_<tag>.json`, **calcula la importancia SHAP**, registra la versión como **ACTIVE** (archiva las previas), recarga el modelo en RAM sin reiniciar y audita `ML_MODEL_PROMOTED`.
- Hiperparámetros: `n_estimators=50, max_depth=3, lr=0.1, reg_lambda=1, reg_alpha=0.1, subsample=0.8, colsample_bytree=0.8`, restricciones monótonas `(-1, 0, 1, -1, 1, 0)`, `random_state=42`.

**Importancia SHAP**: se calcula con TreeSHAP exacto de XGBoost (`get_booster().predict(DMatrix, pred_contribs=True)`), sin la librería `shap`. Es el promedio del |SHAP| de cada variable sobre los datos estacionarios de entrenamiento, en g/kg de humedad de sala. Se guarda en `ml_model_versions.feature_importance` como lista `[{feature, shap}]` ordenada de mayor a menor. Resultado de referencia con los datos de desarrollo: `ahu_w` 0.45 ≫ `dryer_power` 0.14 > `injection_pressure` 0.09 > `ahu_temp` 0.05 ≫ `outdoor_w` 0.008 ≈ `outdoor_temp` 0.007. Los modelos anteriores a esta función no tienen análisis hasta que se reentrenan.

#### d) Decisión del operador
`POST /simulation/log-action` guarda en `simulation_logs` y genera auditoría `RECOMMENDATION_APPLIED` o `RECOMMENDATION_OVERRIDDEN` (con justificación) sobre el recurso `HVAC_SIMULATOR`.

#### e) Dashboard (`DashboardService`)
- Toma las últimas 24 recomendaciones **aplicadas** (`RECOMMENDATION_APPLIED`; los descartes no cuentan): serie *estimada vs. recomendada* (estimada = `current_power`, la potencia que ingresó el operador), `kpi_ahorro` = suma de excesos (actual − recomendada) y `kpi_diferencial` = ahorro × 1.5 (kWh estimados; el factor 1,5 es el definido en los CP). Sin recomendaciones aplicadas la gráfica queda vacía y los indicadores en 0.
- `r2_score` sale del Champion registrado en BD (se actualiza tras cada reentrenamiento).
- **Firma térmica** (humedad vs. potencia): recorre el histórico completo por `SSDFilter` (solo puntos estacionarios) y submuestrea a 25 puntos por nivel de potencia (≈450 puntos). Ejes: humedad de sala en g/kg y potencia en %.

#### f) Sesión y cierre de sesión
El token JWT lleva un `jti` único. `POST /auth/logout` lo registra en `revoked_tokens`; `get_current_user` rechaza con 401 cualquier token revocado, aunque no haya vencido. Los tokens emitidos antes de este cambio no tienen `jti` y valen hasta su vencimiento (máx. 60 min).

### 3.8 Eventos de auditoría
`ACCESS_DENIED`, `GMP_LIMITS_UPDATE`, `RECOMMENDATION_APPLIED`, `RECOMMENDATION_OVERRIDDEN`, `ML_RETRAIN_FAILED`, `ML_MODEL_REJECTED`, `ML_MODEL_PROMOTED`, `USER_LOGOUT`, `USER_CREATED`, `USER_UPDATED`, `USER_DELETED` y los registros manuales (`MANUAL_AUDIT`). La gestión de usuarios (alta, edición, baja) **aún no genera eventos** de auditoría.

### 3.9 Modelos ML guardados
`app/ml_engine/saved_models/` contiene el modelo base versionado (`xgboost_hvac_v1.json`, `xgboost_metadata.json`). Los modelos entrenados en runtime (`xgboost_hvac_v1.MMDD.HHMMSS.json`) **ya no se versionan en git** (`.gitignore`) y en Docker viven en el volumen `models`.

---

## 4. Frontend

### 4.1 Rutas (`app/`)

| Ruta | Archivo | Contenido |
|---|---|---|
| `/login` | `(auth)/login/page.tsx` | Autenticación |
| `/` | `(dashboard)/page.tsx` | Pantalla de bienvenida |
| `/dashboard` | `(dashboard)/dashboard/page.tsx` | KPIs de ahorro, costo kWh configurable (default 0.15), AreaChart real vs. recomendado, ScatterChart de firma térmica (estacionaria, ejes con unidades) |
| `/ingesta` | `(dashboard)/ingesta/page.tsx` | Carga de 3 archivos + rango de fechas + historial |
| `/ia-control` | `(dashboard)/ia-control/page.tsx` | Métricas del Champion, botón de entrenamiento, historial de entrenamientos (éxito, rechazo y fallo), **tarjeta "Validación del Modelo" con el gráfico de impacto SHAP**, edición de límites GMP |
| `/simulador` | `(dashboard)/simulador/page.tsx` | Formulario de variables con validación de rangos, resultado IA, aplicar/ignorar con modal de justificación |
| `/auditoria` | `(dashboard)/auditoria/page.tsx` | Pestañas: pista de auditoría (filtro Desde/Hasta, botones "Exportar" CSV y "PDF") y directorio de usuarios (CRUD) |

`(dashboard)/layout.tsx` es un Server Component que valida la cookie `scada_token` y redirige a `/login` si falta.

### 4.2 Componentes
- `ui/SideNav.tsx`: navegación lateral filtrada por rol, perfil y cierre de sesión. Incluye un **guardia de sesión** que revisa la cookie en `pageshow`, `popstate` y `focus` y manda al login si ya no existe.
- `ui/justification-modal.tsx`, `ui/toast.tsx` (`ToastProvider` en el layout raíz).
- Se eliminaron `RoleGuard`, `plc/PLCControl`, `plc/PLCTrend` y `_middleware.ts` (no se usaban).

### 4.3 Servicios (`services/`)
Un cliente `fetch` por dominio, con `Authorization: Bearer <cookie scada_token>` y base `NEXT_PUBLIC_API_URL`: `authService`, `userService`, `dataService`, `gmpService`, `simulationService`, `mlopsService`, `dashboardService`, `auditService`.

### 4.4 Sesión
- Login: `authService.login` guarda las cookies `scada_token` y `scada_email` (60 min, igual que el JWT) y en `localStorage` `scada_userName` y `scada_userRole`.
- Logout ("Finalizar Sesión"): avisa a `POST /auth/logout` (revoca el token), borra cookies y `localStorage`, y usa `location.replace('/login')` para que la página protegida no quede en el historial.
- `next.config.ts` envía `Cache-Control: no-store` en todas las rutas salvo los estáticos, para que el botón Atrás no muestre páginas protegidas desde caché.

### 4.5 Variables del simulador (UI → API)

| Campo UI | Campo API | Unidad | Rango |
|---|---|---|---|
| Temp. exterior | `outdoor_temp` | °C | validado en UI |
| Hum. exterior | `outdoor_rh` | % | 0–100 |
| Temp. UMA | `ahu_temp` | °C | validado en UI |
| Hum. UMA | `ahu_rh` | % | 0–100 |
| Potencia actual | `current_power` | % | 0–100 |
| Temp. sala | `room_temp` | °C | validado en UI |
| Hum. sala | `current_room_rh` | % | 0–100 |
| Presión de inyección | `injection_pressure` | Pa | 0–1000 |
| Setpoint | `target_setpoint` | % HR | 0–100 |

---

## 5. Puesta en marcha

### Con Docker (recomendado)
```bash
docker compose up --build        # levanta db, backend y frontend
```
- Frontend: http://localhost:3000 · API: http://localhost:8000 (docs en `/docs`).
- Admin inicial en una BD vacía: usuario `admin_hvac`, contraseña `Admin12345` (variable `FIRST_ADMIN_PASSWORD`; cámbiela fuera de desarrollo).
- Variables opcionales: `POSTGRES_PASSWORD`, `SECRET_KEY`, `GEMINI_API_KEY`, `FIRST_ADMIN_PASSWORD`.
- Tras cambiar código, repita con `--build`. `docker compose down -v` borra BD y modelos.
- Volúmenes: `pgdata` (BD) y `models` (modelos entrenados, que sobreviven a los reinicios).
- `NEXT_PUBLIC_API_URL` se fija en el build (`http://localhost:8000`).

### Local (hot reload)
```bash
# Backend (requiere un PostgreSQL accesible)
cd TP1_BACKEND
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env           # completar DATABASE_URL, SECRET_KEY, FIRST_ADMIN_PASSWORD
alembic upgrade head
uvicorn app.main:app --reload    # http://localhost:8000

# Frontend
cd TP1_FRONTEND
npm install
# .env.local → NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                      # http://localhost:3000
```
No ejecute a la vez `npm run dev` y el contenedor del frontend: ambos usan el puerto 3000.

---

## 6. Flujo operativo típico

1. **Supervisor** carga los 3 archivos en *Ingesta* → se crea un lote.
2. **Admin** pulsa *Disparar Entrenamiento* en *IA Control* → pipeline SSD + LOSO → nuevo Champion si R² ≥ 70 %. En *Validación del Modelo* se ve qué variables pesan más (SHAP).
3. **Supervisor** usa el *Simulador* → recibe potencia recomendada, ahorro %, alerta GMP y explicación → aplica o ignora (con justificación).
4. **Gerente / Supervisor** revisan el *Dashboard* de ahorro y la firma térmica; **Auditor** revisa la pista y exporta el reporte.

---

## 7. Dependencias externas

- **Google Gemini**: justificaciones; degradación elegante a texto fijo si no hay clave o falla la llamada.
- **PostgreSQL**: obligatoria.
- `WeatherService` (OpenWeather) se eliminó: nunca estuvo conectado a un router.

---

## 8. Estado actual del repositorio

- Todo el trabajo reciente está **sin commitear** (último commit: `d023488`). Incluye: Dockerfiles y `docker-compose.yml`, migraciones Alembic 0001–0003, `.env.example`, limpieza de código no usado y las funciones descritas en este documento.
- `TP1_BACKEND/.env` está marcado como borrado del índice de git, pero **sigue en el historial**: las claves que contiene deben considerarse comprometidas (ver §9).
- **Pruebas**: `tests/e2e` automatiza los casos de `docs/P20261007_CP.xlsx` contra la app en Docker (Chrome + API): **64 de 64 pasan**. No hay pruebas unitarias del backend ni del frontend.
- **Historias de usuario**: `docs/ESTADO_IMPLEMENTACION.md` re-evalúa los 59 criterios de `docs/P20261007_HU.xlsx`: **59 implementados**, con los conflictos de texto entre HU y CP y lo pendiente fuera de los Excel.

---

## 9. Hallazgos y deudas técnicas

**Resueltos desde el análisis anterior (2026-10-04)**
- Dockerfiles, `.dockerignore` y `docker-compose.yml` ya existen y funcionan; el esquema lo gestiona solo Alembic.
- `register-first-user` ya no falla (el método existe) y se limita a una BD sin usuarios; además hay seed por `FIRST_ADMIN_PASSWORD`.
- `_middleware.ts`, `RoleGuard`, componentes PLC, `weather_service`, `energy_pricing`, `test_conn.py` y `get_simulator_engine` se eliminaron.
- El Dashboard ya no crea su propio `SimulatorEngine`: el R² sale del Champion en BD.
- `LlmService` usa correctamente el SDK `google-genai`.
- `requirements.txt` se recortó a 19 dependencias con versión fija.
- Los modelos entrenados dejaron de versionarse; en Docker van a un volumen.
- El token JWT se invalida en el servidor al cerrar sesión.
- La firma térmica usa datos estacionarios y unidades correctas.
- Los 59 criterios de las HU están implementados y los 64 casos de la suite de aceptación pasan: ingesta con `.xlsx` y fechas parciales, dashboard solo con recomendaciones aplicadas, auditoría de usuarios, filtro de fechas y exportación CSV/PDF.

**Seguridad (pendiente)**
1. **Rotar secretos**: el `.env` anterior (con `SECRET_KEY='supersecretkey'`, contraseña de BD y claves de API) sigue en el historial de git. Rotar las claves y, si el repositorio se comparte, limpiar el historial.
2. La cookie `scada_token` no es `httponly` (el frontend la lee para el header Bearer); un XSS podría robarla.
3. `POST /audit/log` permite a cualquier usuario autenticado escribir eventos arbitrarios en la pista "inmutable".
4. `AuditTrail.ip_address` existe pero `record_action` nunca lo llena (la IP solo aparece dentro de `detail` en `ACCESS_DENIED`).
5. La contraseña por defecto del admin en `docker-compose.yml` (`Admin12345`) y la `SECRET_KEY` por defecto son solo para desarrollo.
6. `POST /auth/register-first-user` es público; hoy se autolimita, pero conviene quitarlo ahora que existe el seed por variable de entorno.

**Correctitud (pendiente)**
7. `GmpService.update_gmp_config` indexa `config_data['min_hum_limit']` y `['max_hum_limit']`: da `KeyError` si el PUT omite alguno.
8. `GET /config/gmp/` devuelve 404 si la tabla está vacía y no hubo seed; el modelo declara 40/70 como default y el seed usa 40/55.
9. `SimulationLog.model_version_id` nunca se asigna al registrar una decisión (se pierde el vínculo con la versión del modelo).
10. `kpi_diferencial` usa un factor fijo × 1.5 y el costo kWh vive en el estado del navegador.
11. `DataService._save_records` usa `iterrows` (lento en lotes grandes) y el fallback `get_latest(limit=5000)` puede mezclar lotes en el entrenamiento.
13. El indicador "ML Service: ONLINE" de *IA Control* es visual: no consulta el estado real del backend.
14. Los tokens emitidos antes de agregar `jti` no son revocables (valen hasta 60 min).

**Mantenibilidad (incumplimientos de `.clinerules`)**
15. `data_service.py` tiene 348 líneas (límite 250). `ml_training_service.py` (240) y `audit_service.py` (195) están cerca.
16. Uso de `current_user: any`, `dict` como payload interno y endpoints sin `response_model` (`/mlops/*`, `/dashboard/metrics`, `/data/*`, `/audit/log`).
17. `dashboard_repository.py` está vacío; `types/user.ts` conserva código comentado; el frontend tiene errores de lint (`any`, `setState` en efectos, variables sin usar) concentrados en `auditoria`, `ia-control`, `dashboard` y `simulador`.
18. Los comentarios y mensajes mezclan español/inglés y emojis; algunos docstrings mencionan "12 Variables" cuando el modelo usa 6.
19. Logging a nivel ERROR: los `logger.info` (p. ej. carga del Champion) nunca se escriben.
20. Sin pruebas unitarias (solo la suite de aceptación `tests/e2e`, que además deja datos de prueba en la BD).

---

## 10. Glosario

| Término | Significado |
|---|---|
| UMA / AHU | Unidad Manejadora de Aire |
| GxP / GMP | Buenas prácticas de manufactura/regulatorias farmacéuticas |
| 21 CFR Part 11 | Norma FDA sobre registros y firmas electrónicas |
| SSD | Steady-State Detection, filtro de estado estacionario |
| LOSO | Leave-One-Step-Out, validación cruzada por escalón de potencia |
| SHAP | Medida de cuánto aporta cada variable a una predicción; aquí, el promedio de su valor absoluto |
| Champion | Versión de modelo activa en producción (`status = ACTIVE`) |
| Gemelo Digital | Modelo predictivo que simula la respuesta higrométrica de la sala |
| jti | Identificador único de un token JWT, usado para revocarlo al cerrar sesión |
| g/kg | Humedad absoluta (gramos de vapor por kg de aire seco) |
