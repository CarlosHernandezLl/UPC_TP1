# Estado de implementación (re-evaluado 2026-11-04)

Fuentes: `docs/P20261007_HU.xlsx` (19 HU · 59 criterios) y `docs/P20261007_CP.xlsx` (59 casos de prueba).
Método: la app se levantó con `docker compose up --build` y se ejecutó una suite automatizada con Chrome (`tests/e2e`) que sigue los pasos de cada CP contra la UI y la API reales.

## Resultado

| | |
|---|---|
| Criterios de aceptación | **59 de 59 IMPLEMENTADOS** |
| Casos de prueba ejecutados | **64 de 64 pasan** (los 59 CP + variantes: CP001b, CP003b, CP010b, CP023b, CP041b) |
| Navegador probado | Chrome (sin ventana). Firefox, Edge y Safari no se probaron |

Antes de esta revisión (análisis del 2026-10-04) había 37 implementados, 16 parciales, 4 que difieren y 2 sin implementar.

## Detalle por criterio

| CA | CP | Estado | Prueba | Nota |
|---|---|---|---|---|
| HU0001-1 | CP001 | IMPLEMENTADO | CP001, CP001b | Los tres selectores admiten `.csv` y `.xlsx` (el datalogger también `.xls`). CP001b procesa PLC y Clima en `.xlsx` en el backend. |
| HU0001-2 | CP002 | IMPLEMENTADO | CP002 | Valida las columnas por archivo. El criterio cita nombres lógicos (`timestamp, temp_ext, …`); los archivos reales usan los del PLC (`fecha, f20911t, …, f209potsecador`) y esos son los que se exigen. Toast del CP + detalle del archivo/columna bajo el formulario. |
| HU0001-3 | CP003 | IMPLEMENTADO | CP003, CP003b | Sin encabezado → columnas faltantes; fechas fuera de `DD/MM/AAAA HH:MM` → error de formato (se toleran filas vacías al final). |
| HU0001-4 | CP004 | IMPLEMENTADO | CP004 | Con solo una fecha se acepta: la otra se toma del rango común de los archivos. |
| HU0001-5 | CP005 | IMPLEMENTADO | CP005 | Mensaje exacto de la HU, validado en front y backend; Fin = Inicio también se rechaza. |
| HU0001-6 | CP006 | IMPLEMENTADO | CP006 | Toast "Operación Exitosa / Sincronizado: …" y fila "Sincronizado" en el historial. |
| HU0002-1 | CP007 | IMPLEMENTADO | CP007 | Log "Entrenamiento exitoso" en el historial. |
| HU0002-2 | CP008 | IMPLEMENTADO | CP008 | Log "Entrenamiento fallido" con el motivo; el toast usa "Fallo crítico en el pipeline MLOps". |
| HU0002-3 | CP009 | IMPLEMENTADO | CP009 | Tarjetas R², RMSE y versión; el modelo nuevo pasa a ACTIVE y el anterior a ARCHIVED. Incluye el análisis SHAP. |
| HU0002-4 | CP010 | IMPLEMENTADO | CP010, CP010b | Cada carga nueva (probado con el dataset de Julio) habilita un nuevo entrenamiento. |
| HU0003-1 | CP011 | IMPLEMENTADO | CP011 | Menú: Dashboard, Ingesta, Entrenamiento IA, Simulador, Auditoría. |
| HU0003-2 | CP055 | IMPLEMENTADO | CP055 | Menú: Dashboard, Ingesta, Simulador. |
| HU0003-3 | CP056 | IMPLEMENTADO | CP056 | Menú: Dashboard. |
| HU0003-4 | CP057 | IMPLEMENTADO | CP057 | Menú: Auditoría. |
| HU0003-5 | CP012 | IMPLEMENTADO | CP012 | "Credenciales inválidas" y permanece en el login. |
| HU0003-6 | CP013 | IMPLEMENTADO | CP013 | Redirige a `/login`, borra cookies y `localStorage`, "Atrás" no restaura la sesión y el token queda revocado en el servidor (401). |
| HU0004-1 | CP014 | IMPLEMENTADO | CP014 | La UI no deja digitar negativos ni valores > 100; la API devuelve 422 fuera de 0–100. |
| HU0004-2 | CP015 | IMPLEMENTADO | CP015 | Mensaje exacto y sin persistir. |
| HU0004-3 | CP016 | IMPLEMENTADO | CP016 | Confirmación exacta y valores guardados en BD. |
| HU0004-4 | CP017 | IMPLEMENTADO | CP017, CP051 | `GMP_LIMITS_UPDATE` con administrador, fecha y `Min=…%, Max=…%`. |
| HU0005-1 | CP018 | IMPLEMENTADO | CP018 | Cards de usuarios activos; el Administrador entra en esa pestaña. |
| HU0005-2 | CP019 | IMPLEMENTADO | CP019 | Toast "Nueva identidad GxP dada de alta en el sistema" (ver conflicto HU/CP050). |
| HU0005-3 | CP020 | IMPLEMENTADO | CP020 | Rechazo por username duplicado con el texto de la HU. |
| HU0005-4 | CP021 | IMPLEMENTADO | CP021 | Los campos obligatorios usan la validación nativa ("Completar este campo"). |
| HU0005-5 | CP022 | IMPLEMENTADO | CP022 | Actualiza datos y clave (la anterior deja de valer). Toast "Identidad GxP actualizada con éxito." |
| HU0005-6 | CP023 | IMPLEMENTADO | CP023, CP023b | Confirmación, baja lógica, toast exacto; el revocado recibe "Credenciales inválidas". |
| HU0006-1 | CP024 | IMPLEMENTADO | CP024 | 0–50 °C y 0–100 % en UI; temperaturas con rango también en el backend. |
| HU0006-2 | CP025 | IMPLEMENTADO | CP025 | Mensaje de la HU (con "Humeda", tal cual); no se consulta al modelo. |
| HU0007-1 | CP026 | IMPLEMENTADO | CP026 | Temp. 0–50, Humedad 0–100, Presión 0–1000 Pa en UI y backend. |
| HU0007-2 | CP027 | IMPLEMENTADO | CP027 | Mensaje de la HU ("Humedad"; el CP escribe "Humeda"). |
| HU0008-1 | CP028 | IMPLEMENTADO | CP028 | 0–100 %, rechaza 150 y negativos. |
| HU0008-2 | CP029 | IMPLEMENTADO | CP029 | "Por favor, llene la variable de Potencia antes de consultar al Gemelo Digital". |
| HU0009-1 | CP030 | IMPLEMENTADO | CP030 | Temperatura de sala 0–50 °C y humedad 0–100 %. |
| HU0009-2 | CP031 | IMPLEMENTADO | CP031 | Mensaje general; la tarjeta de resultado previa se limpia. |
| HU0010-1 | CP032 | IMPLEMENTADO | CP032, CP034 | Objetivo 0–100 y recomendación mostrada. |
| HU0010-2 | CP033 | IMPLEMENTADO | CP033 | Mensaje general si falta el objetivo. |
| HU0011-1 | CP034 | IMPLEMENTADO | CP034 | La recomendación es un entero 0–100 (también con potencia de entrada decimal). |
| HU0011-2 | CP035 | IMPLEMENTADO | CP035 | Todo vacío → mensaje general y campos en rojo. |
| HU0011-3 | CP036 | IMPLEMENTADO | CP036 | Botón "Sí, aplicada"; toast "Recomendación Aplicada. Ajuste del N%. Transacción cifrada en Audit Trail." y log con el usuario. |
| HU0011-4 | CP037 | IMPLEMENTADO | CP037 | Modal de justificación; Cancelar no registra nada. |
| HU0012-1 | CP038 | IMPLEMENTADO | CP038 | Registra la decisión ("Operación Exitosa") y el Dashboard la refleja. |
| HU0012-2 | CP039 | IMPLEMENTADO | CP039 | "Descarte operativo registrado con éxito junto a su sustento técnico." y la justificación queda en auditoría. |
| HU0012-3 | CP058 | IMPLEMENTADO | CP058 | Bloqueo en la UI (alerta GxP) y también en el backend (422 con justificación vacía, "n/a" o < 10 caracteres). |
| HU0013-1 | CP040 | IMPLEMENTADO | CP040 | Gráfica de líneas con dos curvas: Estimada vs. Recomendada (últimas 24 aplicadas). |
| HU0013-2 | CP041 | IMPLEMENTADO | CP041, CP041b | Solo cuentan las recomendaciones aplicadas; un descarte no cambia gráfica ni indicadores. Sin aplicadas: gráfica vacía e indicadores en 0 (verificado contra el servicio). |
| HU0014-1 | CP042 | IMPLEMENTADO | CP042 | 80 % vs 60 % → +20 pp × 1,5 × $0.15 = +$4.50, verificado en pantalla. |
| HU0014-2 | CP043 | IMPLEMENTADO | CP043 | Aplicada ≤ recomendada → diferencial 0. |
| HU0014-3 | CP059 | IMPLEMENTADO | CP059 | Recalcula al instante al cambiar la tarifa (0.15 → 0.20). |
| HU0015-1 | CP044 | IMPLEMENTADO | CP044 | Ahorro = Diferencial × costo kWh. |
| HU0015-2 | CP045 | IMPLEMENTADO | CP045 | No se puede digitar "-"; tope de 5 USD/kWh. |
| HU0016-1 | CP046 | IMPLEMENTADO | CP046 | Dispersión humedad (g/kg) vs potencia (%) con puntos estacionarios históricos. |
| HU0017-1 | CP047 | IMPLEMENTADO | CP047 | "Alerta de Riesgo GMP" con el texto de la HU y el rótulo "Alerta de incumplimiento" del CP. |
| HU0017-2 | CP048 | IMPLEMENTADO | CP048 | Sin alerta dentro de los límites. |
| HU0018-1 | CP049 | IMPLEMENTADO | CP049 | `RECOMMENDATION_APPLIED` / `OVERRIDDEN` en el Audit Trail. |
| HU0018-2 | CP050 | IMPLEMENTADO | CP050 | `USER_CREATED`, `USER_UPDATED` y `USER_DELETED` con el detalle. |
| HU0018-3 | CP051 | IMPLEMENTADO | CP051 | `GMP_LIMITS_UPDATE`. |
| HU0018-4 | CP052 | IMPLEMENTADO | CP052 | `ML_MODEL_PROMOTED` con R², RMSE y lote. |
| HU0019-1 | CP053 | IMPLEMENTADO | CP053 | Botón "Exportar" (CSV con BOM para Excel) y botón "PDF". |
| HU0019-2 | CP054 | IMPLEMENTADO | CP054 | Filtro Desde/Hasta que acota la lista y las exportaciones; un rango sin eventos devuelve solo el encabezado; rango invertido → 400. |

## Qué se corrigió en esta revisión

**Ingesta (HU0001)**
- PLC y Clima aceptan `.xlsx` (UI y backend); un `.xls` binario del datalogger también se lee.
- Una sola fecha se acepta (antes se ignoraban ambas). Fechas invertidas o iguales se rechazan en front y backend.
- Se valida el formato de fecha (`DD/MM/AAAA HH:MM`); las filas vacías al final del datalogger no cuentan como error.
- El toast de error de la ingesta usa el texto del CP y el detalle (archivo/columna) queda visible bajo el formulario.

**Entrenamiento y GMP (HU0002, HU0004)**
- Los límites GMP no admiten negativos ni valores > 100 al digitar.
- Se quitaron los valores inventados (`87.00%`, `87.59%`) y la etiqueta "R² Hold-out" de *IA Control*.

**Usuarios y auditoría (HU0005, HU0018, HU0019)**
- Alta, edición y baja de usuarios generan `USER_CREATED`, `USER_UPDATED` y `USER_DELETED`.
- Toasts de alta y edición con el texto de la HU.
- La auditoría y sus exportaciones aceptan `desde` / `hasta`; botón "Exportar" (CSV) y "PDF"; el CSV lleva BOM para Excel.

**Simulador (HU0006–HU0012, HU0017)**
- Avisos por grupo de variables faltantes (clima externo, UMA, potencia) o el mensaje general.
- La recomendación es siempre un entero.
- Botones "Sí, aplicada" / "Ignorar" con el texto de la HU; el toast incluye "Recomendación Aplicada".
- El modal de descarte ya no usa `required`: muestra la alerta GxP también con el campo vacío; el backend exige ≥ 10 caracteres.
- Temperaturas con rango 0–50 °C también en el backend.
- La alerta GMP añade el rótulo "Alerta de incumplimiento".

**Dashboard (HU0012–HU0016)**
- Solo las recomendaciones **aplicadas** alimentan la gráfica y los indicadores (antes también los descartes).
- Gráfica de líneas con dos curvas, Estimada vs. Recomendada, y estado vacío.
- El costo kWh no admite negativos.
- La firma térmica usa puntos estacionarios (ya estaba) y el menú dice "Auditoría" con tilde.

## Conflictos entre los Excel (decisión tomada)

Los dos archivos no coinciden en algunos textos. Se siguió la **HU** (el requisito) y, cuando era posible, se incluyó también el texto del CP.

| Tema | HU | CP | Qué hace la app |
|---|---|---|---|
| Alta de usuario | `Nueva identidad GxP dada de alta en el sistema` (CP019 igual) | CP050: `Nueva identidad GxP [Pepito123] dada de alta en el sistema.` | Texto de la HU. **CP050 con el nombre entre corchetes no se cumple literalmente** (la prueba verifica el evento `USER_CREATED`) |
| UMA incompleta | `…Temperatura, Humedad y Presion de la UMA…` | CP027: `…Humeda…` | Texto de la HU. CP025 (clima externo) usa `Humeda` en ambos |
| Potencia vacía | `…llene la variable de Potencia…` | La hoja CP29 coincide; la lista CP dice "todas las variables" | Texto de la hoja CP29 y de la HU |
| Botón aplicar | `Sí, aplicada` | CP036/038/040: `Sí, aplicar` | `Sí, aplicada` (CP049 y la HU) |
| Toast al aplicar | `Ajuste del … %. Transacción cifrada en Audit Trail.` | CP049: `Recomendación Aplicada` | Ambos en el mismo toast |
| Alerta GMP | `Alerta de Riesgo GMP …` | CP047/048: `Alerta de incumplimiento` | Se muestran ambos rótulos |
| Fechas invertidas | `…mayor a la fecha de inicio` | CP005: `…mayor al fecha de inicio` | Texto de la HU |
| Éxito de ingesta | mensaje de operación exitosa | CP004/006: `Sincronizado` | `Operación Exitosa` + `Sincronizado: …` |
| Presión UMA | 0–1000 Pa | CP026 paso 7: valores válidos 1450 y 1080.65 | 0–1000 (la prueba acepta 999.5 y 1000) |
| Humedad de sala | 0–100 % | CP030: rechazar `1.1` | Se rechaza 101; 1.1 es un valor válido |

## Fuera del alcance de los Excel (pendiente)

- **Guard por rol en las rutas del front**: entrar por URL directa muestra la página aunque el rol no corresponda (la API responde 403). Los Excel solo piden ocultar módulos en el menú.
- Navegadores distintos de Chrome sin probar.
- Datos de prueba que dejó la suite en la BD de desarrollo: usuarios `AdministradorTest`, `SupervisorTest`, `GerenteTest` y `AuditorTest` (clave igual al usuario), cargas de Mayo y Julio, modelos entrenados y simulaciones.
- Seguridad y mantenibilidad: ver `DOCUMENTACION_PROYECTO.md` §9 (rotar secretos, cookie sin `httponly`, `POST /audit/log` abierto, sin pruebas unitarias del backend).

## Cómo reproducir

```bash
docker compose up --build -d
cd tests/e2e
npm install          # una sola vez (puppeteer-core, aislado del proyecto)
npm test             # genera los archivos de prueba y ejecuta los 64 casos
node run.js simulador   # una suite: auth_users | ingesta_ml | simulador | dashboard_audit
```
El resultado queda en `tests/e2e/resultados.json`. La suite entrena el modelo tres veces y carga datasets, por lo que tarda varios minutos y deja datos en la BD.
