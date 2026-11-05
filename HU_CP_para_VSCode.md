# Gemelo Digital HVAC — Historias de Usuario y Casos de Prueba

> Documento para **VS Code / Claude Code**. Objetivo: que el agente contraste cada criterio de aceptación (CA) y cada caso de prueba (CP) con el código real y determine qué está **implementado** y qué hay que **corregir**.
> Fuente: `P20261007_HU.xlsx` (19 HU · 59 CA) y `P20261007_CP.xlsx` (59 CP). Redacción original conservada; las aclaraciones van aparte como **➕ Aclaración**.

---

## 1. Instrucciones para el agente

1. **No modifiques el código** en la primera pasada. Solo analiza y reporta.
2. Por cada **CA** busca en el código dónde se implementa (usa la línea "Dónde buscar" de cada HU) y asigna un estado:

| Estado | Significa |
|---|---|
| `IMPLEMENTADO` | El código cumple el criterio completo, incluidos textos exactos y rangos |
| `PARCIAL` | Existe pero falta algo (validación, mensaje, rol, auditoría, backend) |
| `DIFIERE` | Existe pero hace algo distinto a lo que dice el criterio (indicar qué) |
| `NO_IMPLEMENTADO` | No se encontró |
| `NO_VERIFICABLE` | Depende de ejecutar la app o de datos; indicar qué falta |

3. Cita **evidencia** como `ruta/archivo:línea`. Sin evidencia, el estado es `NO_VERIFICABLE`.
4. Compara **textos de mensajes literalmente** con el catálogo de la sección 4 (usa grep). Una diferencia de texto es `DIFIERE`.
5. Todo lo marcado **[CONFIRMAR]** es una decisión pendiente: no la inventes; repórtala con lo que hace el código hoy y propón el texto o valor.
6. Verifica que las restricciones (rangos, roles, campos obligatorios) existan también en el **backend**, no solo en la interfaz.
7. Entrega el reporte en `docs/ESTADO_IMPLEMENTACION.md` con la plantilla de la sección 8.
8. Después, **espera confirmación** antes de corregir. Corrige por HU, con una prueba automatizada que reproduzca la brecha.

**Prompt sugerido para Claude Code:**
> *Lee `HU_CP_para_VSCode.md`. Sin modificar código, recorre las HU en orden y, para cada criterio de aceptación, determina su estado (IMPLEMENTADO / PARCIAL / DIFIERE / NO_IMPLEMENTADO / NO_VERIFICABLE) con evidencia archivo:línea. Compara los textos con el catálogo de la sección 4. Genera `docs/ESTADO_IMPLEMENTACION.md` con la plantilla de la sección 8 y una lista priorizada de correcciones. No inventes lo marcado [CONFIRMAR].*

---

## 2. Datos y convenciones comunes

**Usuarios de prueba** (según los CP; usuario = contraseña):

| Rol | Usuario / Clave |
|---|---|
| Administrador | `AdministradorTest` |
| Supervisor | `SupervisorTest` |
| Gerente | `GerenteTest` |
| Auditor | `AuditorTest` |

**Rangos de entrada del Simulador** (valores límite incluidos):

| Campo | Rango | Unidad |
|---|---|---|
| Temp. Exterior · Temp. UMA · Temp. Sala | 0 – 50 | °C |
| Humedad Ext. · Humedad UMA · Humedad Sala Actual · Humedad Sala Objetivo | 0 – 100 | % HR |
| Presión Inyección | 0 – 1000 | Pa |
| Potencia Estimada | 0 – 100 | % |

**Datos base de simulación** (los de los CP): Temp. Ext 20.4 · Humedad Ext 78.0 · Temp. UMA 22.5 · Humedad UMA 50.4 · Presión 100.0 · Potencia 70.0 (o 60.0 en algunos CP) · Humedad Sala Actual 44.7 · Objetivo 50.0 · Temp. Sala 22.4.
> Nota: si con estos datos la recomendación coincide con la potencia estimada (sin ahorro), CP038, CP040 y CP042 no mostrarán diferencial. En ese caso construir el vector desde una fila real del dataset estacionario [CONFIRMAR].

**Archivos de prueba**: `DATOS_PLC.csv`, `DATALOGGER.xls`, `EXTERIOR.csv`. Para pruebas negativas, trabajar sobre una **copia** (`COPIA_...`) y no tocar el original.

**Pruebas metamórficas** (cuando no se conoce el valor exacto de la recomendación): misma entrada dos veces → misma potencia; subir la humedad objetivo → la recomendación no sube; subir la humedad exterior → la recomendación no baja; cambiar solo "Humedad Sala Actual" → sin cambio si es informativa.

---

## 3. Matriz de roles (según HU0003)

| Módulo | Administrador | Supervisor | Gerente | Auditor |
|---|---|---|---|---|
| Dashboard | ✅ | ✅ | ✅ | — |
| Ingesta de datos | ✅ | ✅ | — | — |
| Entrenamiento IA (+ Límites GMP) | ✅ | — | — | — |
| Simulador | ✅ | ✅ | — | — |
| Auditoría · Audit Trail | ✅ | — | — | ✅ |
| Auditoría · Usuarios | ✅ | — | — | — |

> Los CP usan roles que contradicen esta matriz (p. ej. Supervisor en Entrenamiento IA, Auditor viendo "Usuarios", Supervisor editando costo kWh). Esta versión de los CP ya los alinea a la matriz. [CONFIRMAR matriz oficial]

---

## 4. Catálogo de textos exactos (para grep)

| Contexto | Texto |
|---|---|
| Login fallido | `Credenciales inválidas` |
| Login (botón en curso) | `Autenticando Firma...` |
| Ingesta · error de proceso | `Ocurrió un error crítico al procesar el pipeline termodinámico. Revisa los logs del servidor.` |
| Ingesta · fechas invertidas | `La fecha de fin debe ser mayor a la fecha de inicio` |
| Ingesta · éxito | `Sincronizado` [CONFIRMAR] |
| Entrenamiento · en curso | `Entrenando Cerebro Digital...` · `Procesando Algoritmo...` |
| Entrenamiento · éxito | `¡Ciclo MLOps completado! El modelo ha sido actualizado.` |
| Entrenamiento · fallo | `Fallo crítico en el pipeline MLOps` |
| Límites GMP · inversión | `El límite mínimo de humedad no puede ser mayor o igual al límite máximo` |
| Límites GMP · error de guardado | `Error al guardar las restricciones operacionales` |
| Límites GMP · éxito | `Umbrales regulatorios actualizados. Cambio firmado en la pista de auditoría` |
| Usuarios · alta | `Nueva identidad GxP dada de alta en el sistema` |
| Usuarios · duplicado | `Transacción rechazada: Conflicto de unicidad en los datos de la cuenta.` |
| Usuarios · campo obligatorio | `Complete el campo` (puede ser el nativo del navegador) |
| Usuarios · edición (botón / éxito) | `Procesando Transacción` / `Identidad GxP actualizada con éxito.` |
| Usuarios · revocar (diálogo / éxito) | `¿Revocar acceso permanentemente?` / `Acceso revocado de manera inmutable en la base de datos de planta` |
| Simulador · exterior vacío | `Por favor, llene las variables de Temperatura y Humeda externa antes de consultar al Gemelo Digital` |
| Simulador · UMA vacía | `Por favor, llene las variables de Temperatura, Humedad y Presion de la UMA antes de consultar al Gemelo Digital` |
| Simulador · potencia vacía | `Por favor, llene la variable de Potencia antes de consultar al Gemelo Digital` |
| Simulador · campos vacíos (genérico) | `Por favor, llene todas las variables de operación antes de consultar al Gemelo Digital` |
| Simulador · aplicar | `Ajuste del potencia secador %. Transacción cifrada en Audit Trail.` |
| Simulador · descartar OK | `Descarte operativo registrado con éxito junto a su sustento técnico.` |
| Simulador · alerta GMP | `Alerta de Riesgo GMP` — `El setpoint solicitado, o las condiciones de humedad logradas por el modelo, apuntan a una violación del marco regulatorio estricto de la sala` |
| Auditoría · eventos | `RECOMMENDATION_APPLIED` · `GMP_LIMITS_UPDATE` · `ML_MODEL_PROMOTED` · `USER_CREATED/UPDATED/DELETED` |

Etiquetas de interfaz que deben ser **únicas**: módulo "Entrenamiento IA" · "Simulador de Ahorro" · botones "Disparar Entrenamiento", "Generar Recomendación", "Sí, aplicada", "Ignorar", "Confirmar descarte" · pestañas "Audit Trail" y "Usuarios". Las variantes encontradas en los Excel están listadas en cada CP.

---

## 5. Historias de usuario, criterios y casos de prueba


---

### HU0001 — Cargar el dataset histórico consolidado (CSV/Excel)

- **Épica:** Inteligencia Predictiva y Gestión de Datos
- **Enunciado:** Como **Administrador** necesito **Cargar el dataset histórico consolidado (CSV/Excel)**, con la finalidad de Entrenar el modelo con los datos obtenidos mediante los dispotivios de telemetría.
- **Dónde buscar en el código:** Pantalla "Ingesta de datos": 3 cargadores de archivos, "Puntos de corte" (fecha/hora inicio y fin), botón "Procesar e Inyectar", "Historial de Procesamiento". Buscar: validación de extensión, validación de columnas/encabezado/fecha, comparación inicio/fin, toasts, endpoint de ingesta y su ETL.

#### HU0001-1 — Carga de archivos en formatos permitidos (CSV/XLSX)

- **Contexto:** En caso que el usuario intente subir un nuevo grupo de datasets a la plataforma en la ventana de Ingesta de Datos (DATOS PLC,DATALOGGER SALA,CLIMA EXTERIOR)
- **Evento:** cuando los archivos sean cargados en la interfaz
- **Resultado esperado:** el sistema debe permitir la carga de archivos en formato .csv y .xlsx.
- **➕ Aclaración:** Fuentes: "Datos PLC" (.csv), "Datalogger Sala" (exportación de texto tabulado, suele llamarse .xls) y "Clima Exterior" (.csv). [CONFIRMAR si el selector acepta .xls]
- **CP asociado:** CP001
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP001 — Carga de archivos en formatos permitidos (CSV/XLSX)**

- **Criterio:** HU0001-1
- **Precondiciones:** - Usuario con rol de Administrador o Supervisor autenticado en el sistema.<br>- Tener a disposición los 3 archivos base provenientes de las fuentes de datos (PLC, Datalogger, Exterior) exclusivamente en formatos válidos .csv o .xlsx.
- **Nota:** El Datalogger se exporta como texto tabulado con extensión .xls; si el selector solo admite .csv/.xlsx, ajustar el archivo de prueba [CONFIRMAR].

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar a la opción de "Ingesta de datos" |  | Se muestra la pantalla Selección de Archivos (CSV), Puntos de corte, Historial de Procesamiento |
| 2 | Visualizar la selección de archivos |  | Pantalla con tres secciones para subir archivos excel |
| 3 | Dar clic en seleccionar archivo |  | Se abre el explorador de archivos |
| 4 | Seleccionar correspondiente a "Datos PLC" y dar click en abrir | Archivo: DATOS_PLC.csv | El sistema procesa el archivo y lo sube a la interfaz. El componente cambia a borde verde (estado "cargado") |
| 5 | Dar clic en seleccionar archivo |  | Se abre el explorador de archivos |
| 6 | Seleccionar correspondiente a "DATALOGGER SALA" y dar click en abrir | Archivo: DATALOGGER.xls | El sistema procesa el archivo y lo sube a la interfaz. El componente cambia a borde verde (estado "cargado") |
| 7 | Dar clic en seleccionar archivo |  | Se abre el explorador de archivos |
| 8 | Seleccionar correspondiente a "CLIMA EXTERIOR" y dar click en abrir | Archivo: EXTERIOR.csv | El sistema procesa el archivo y lo sube a la interfaz. El componente cambia a borde verde (estado "cargado") |

- **Postcondiciones:** Los archivos deben quedar almacenados en la interfaz y listos para darle click en el boton "Procesar e Inyectar"
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0001-2 — Validación de columnas obligatorias del dataset

- **Contexto:** En caso que los datos ya fueron cargados
- **Evento:** cuando el sistema verifique la estructura del documento al momento de procesar e inyectar
- **Resultado esperado:** el sistema debe validar que existan las columnas obligatorias: timestamp, temp_ext, hum_ext, temp_uma, hum_uma, potencia, temp_sala, hum_sala.
- **➕ Aclaración:** Columnas físicas por archivo (según el flujo principal): PLC → `fecha, f20911t, f20911h, f209potsecador, f20910p`; Clima exterior → `timestamp, temp_ext, hum_ext`; Datalogger → `Fecha, Hora, Humedad, Temperatura`. La lista del criterio son nombres lógicos. No incluye la presión de inyección (`f20910p`), que el modelo también usa [CONFIRMAR].
- **CP asociado:** CP002
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP002 — Validación de columnas obligatorias del dataset**

- **Criterio:** HU0001-2
- **Precondiciones:** Usuario autenticado en el sistema. Tener los archivos válidos en formato .csv o .xlsx.
- **Nota:** Si la app muestra un mensaje específico por columna, usarlo como resultado esperado; si no, el toast genérico indicado es el comportamiento vigente [CONFIRMAR].

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Generar copia del archivo"DATOS PLC"  y eliminar una de las siguientes columnas: timestamp, temp_ext, hum_ext, temp_uma, hum_uma, potencia, temp_sala, hum_sala. | Archivo: DATOS_PLC.csv → copia sin la columna `f209potsecador` (potencia) | Copia de archivo DATOS_PLC con columna faltante nombrado como COPIA_DATOS_PLC |
| 2 | Ingresar a la opción de "Ingesta de datos" |  | Se muestra la pantalla de carga de dataset. |
| 3 | Cargar el archivo "COPIA_DATOS_PLC" con columna faltantes a DATOS PLC | Archivo: COPIA_DATOS_PLC.csv | El sistema procesa el archivo y valida su formato. |
| 4 | Dar clic en seleccionar archivo correspondiente a "DATALOGGER SALA" y buscar archivo correspondiente | Archivo: DATALOGGER.xls | El sistema procesa el archivo y valida su formato. |
| 5 | Dar clic en seleccionar archivo correspondiente a "CLIMA EXTERIOR" y buscar archivo correspondiente | Archivo: EXTERIOR.csv | El sistema procesa el archivo y valida su formato. |
| 6 | Dar click en procesar e inyectar |  | El sistema muestra el aviso: Aviso del Sistema<br>Ocurrió un error crítico al procesar el pipeline termodinámico. Revisa los logs del servidor. |

- **Postcondiciones:** El sistema no concreta la carga de archivos, se mantiene a la espera de carga de archivos correctos
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0001-3 — Error por encabezado o formato de fecha inválido

- **Contexto:** En caso que el archivo no contenga la primera fila o encabezado correspondiente al nombre de la columna o formatos de fecha incorrectos (DD/MM/AAAA HH:MM)
- **Evento:** cuando se realice la validación previa de la información al momento de procesar e inyectar
- **Resultado esperado:** el sistema debe mostrar un mensaje de error.
- **➕ Aclaración:** Hoy el sistema muestra el toast genérico "Ocurrió un error crítico al procesar el pipeline termodinámico. Revisa los logs del servidor." Probar 3 variantes: sin encabezado, fecha con otro formato, nombres de columna cambiados.
- **CP asociado:** CP003
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP003 — Error por encabezado o formato de fecha inválido**

- **Criterio:** HU0001-3
- **Precondiciones:** - Usuario con rol de Administrador o Supervisor autenticado en el sistema.<br>- Tener a disposición los 3 archivos base provenientes de las fuentes de datos (PLC, Datalogger, Exterior) exclusivamente en formatos válidos .csv o .xlsx.
- **Nota:** Ejecutar 3 veces, cada una con un error distinto en la COPIA del archivo PLC: (A) borrar la fila de encabezados; (B) cambiar el formato de fecha, p. ej. `2026/07/05 10:00`; (C) cambiar los nombres de las columnas. Resultado esperado idéntico en las tres.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Generar una copia del archivo original "DATOS PLC" e inyectarle un error intencional (modificar el formato de la columna fecha, eliminar la fila de encabezados o cambiar los nombres de columna). | Archivo original: DATOS_PLC.csv<br><br><br>Archivo alterado: COPIA_DATOS_PLC.csv | Se obtiene un archivo de prueba alterado para forzar el fallo de formato durante la interpolación en el backend. |
| 2 | Ingresar al módulo de "Ingesta de datos" desde el menú lateral de navegación. |  | Se carga correctamente la pantalla de selección e inyección de datasets. |
| 3 | Hacer clic en el área de "DATOS PLC" y seleccionar el archivo alterado. | Archivo cargado: COPIA_DATOS_PLC.csv | El componente visual reconoce el archivo y muestra su nombre en verde bajo el icono de carga. |
| 4 | Hacer clic en el área de "DATALOGGER SALA" y seleccionar su respectivo archivo. | Archivo cargado: DATALOGGER.xlsx | El componente visual reconoce el archivo validando que cumple con la extensión de la precondición. |
| 5 | Hacer clic en el área de "CLIMA EXTERIOR" y seleccionar su respectivo archivo. | Archivo cargado: EXTERIOR.csv | El componente visual reconoce el archivo correctamente. |
| 6 | Hacer clic en el botón "Procesar e Inyectar". |  | El sistema detecta la incongruencia de cabeceras/fechas en el archivo alterado y muestra el Toast de error: "Ocurrió un error crítico al procesar el pipeline termodinámico. Revisa los logs del servidor." |

- **Postcondiciones:** El sistema intercepta el error, aborta la transacción y no concreta la carga de datos en la base de datos (protegiendo la integridad del pipeline MLOps). El sistema mantiene al usuario en la misma pantalla visualizando el mensaje de alerta.
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0001-4 — Selección válida de fechas de inicio y corte

- **Contexto:** En caso se requiera establecer puntos de inicio y corte para el procesamiento de datos
- **Evento:** cuando se seleccione las fechas de inicio y corte segun la fecha de la adquisicón de los datasets o dentro de ese rango, tambien, si se selecciona de manera parcial (solo una de las dos fechas)
- **Resultado esperado:** el sistema debe aceptar la el procesamiento e inyección de los datos
- **➕ Aclaración:** Ej.: Inicio 05/07/2026 00:00 y Fin 10/07/2026 00:00 [CONFIRMAR rango del dataset]. Se acepta también solo Inicio o solo Fin.
- **CP asociado:** CP004
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP004 — Selección válida de fechas de inicio y corte**

- **Criterio:** HU0001-4
- **Precondiciones:** Usuario autenticado, debe tener los tres archivos válidos cargados en formato .csv o .xlsx.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar a la opción de "Ingesta de datos" |  | Se muestra la pantalla de carga de dataset. |
| 2 | ingresar solo una fecha INICIO o FIN | Fecha/Hora Inicio = 05/07/2026 00:00 (dejar Fin vacío) [CONFIRMAR que esté dentro del rango del dataset]. Repetir solo con Fin, y con ambas. | El sistema permite ingresar la fecha de inicio o de final |
| 3 | Dar click en procesar e inyectar |  | Se muestra un mensaje de "Sincronizado" y se habilita el dataset para el modelo. |

- **Postcondiciones:** El archivo queda almacenado y listo para el entrenamiento del modelo.
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0001-5 — Error por fechas invertidas

- **Contexto:** En caso se ingresen las fechas de inicio y fin para el procesamiento de datos
- **Evento:** cuando se seleccione las fechas invertidas (fecha de fin < la fecha de inicio)
- **Resultado esperado:** el sistema debe mostrar un mensaje de error "La fecha de fin debe ser mayor a la fecha de inicio"
- **➕ Aclaración:** Texto oficial del mensaje: "La fecha de fin debe ser mayor a la fecha de inicio" (el CP traía un error de tipeo). Fin = Inicio también debe ser error [CONFIRMAR].
- **CP asociado:** CP005
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP005 — Error por fechas invertidas**

- **Criterio:** HU0001-5
- **Precondiciones:** Administrador o Supervisor autenticado en el sistema. Tener los archivos 3 válidos provenientes de las fuentes de datos de (PLC, Dataloger, Exterior) en formato .csv o .xlsx.
- **Nota:** Repetir con Inicio = Fin; también debe mostrar el error [CONFIRMAR].

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo de "Ingesta de datos" |  | Se muestra la pantalla de carga de dataset visualizando el seccionde Punto de Corte |
| 2 | Campo Fecha/Hora Inicio | 2026-10-09 00:00:00 |  |
| 3 | Campo Fecha/Hora Fin | 2026-10-02 00:00:00 |  |
| 4 | Dar click en el botón "Procesar e Inyectar" |  | El sistema muestra un toast en la parte inferior derecha: "La fecha de fin debe ser mayor a la fecha de inicio" |

- **Postcondiciones:** El sistema no concreta la carga de archivos hasta que se corriga el error y se haga click en el botón nuevamente
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0001-6 — Mensaje de operación exitosa tras el procesamiento

- **Contexto:** En caso que el dataset cumpla con las validaciones estructurales previas
- **Evento:** cuando se realize el procesamiento e inyección de datos
- **Resultado esperado:** el sistema debe mostrar un mensaje de operación exitosa
- **➕ Aclaración:** Texto de éxito esperado: "Sincronizado" [CONFIRMAR]; además una fila nueva en "Historial de Procesamiento".
- **CP asociado:** CP006
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP006 — Mensaje de operación exitosa tras el procesamiento**

- **Criterio:** HU0001-6
- **Precondiciones:** Tener los tres archivos válidos en formato .csv o .xlsx.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar a la opción de "Ingesta de datos" |  | Se muestra la pantalla de carga de dataset. |
| 2 | Dar clic en seleccionar archivo correspondiente a "Datos PLC" y buscar archivo correspondiente | Archivo: DATOS_PLC.csv | El sistema procesa el archivo y valida su formato. |
| 3 | Dar clic en seleccionar archivo correspondiente a "DATALOGGER SALA" y buscar archivo correspondiente | Archivo: DATALOGGER.xls | El sistema procesa el archivo y valida su formato. |
| 4 | Dar clic en seleccionar archivo correspondiente a "CLIMA EXTERIOR" y buscar archivo correspondiente | Archivo: EXTERIOR.csv | El sistema procesa el archivo y valida su formato. |
| 5 | Dar click en procesar e inyectar |  | Se muestra un mensaje de "Sincronizado" y se habilita el dataset para el modelo. |

- **Postcondiciones:** El archivo queda almacenado y listo para el entrenamiento del modelo.
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)


---

### HU0002 — Reentrenar el gemelo digital con la data histórica

- **Épica:** Inteligencia Predictiva y Gestión de Datos
- **Enunciado:** Como **Administrador** necesito **Reentrenar el gemelo digital con la data histórica**, con la finalidad de que el simulador pueda inferir el comportamiento del sistema HVAC, y validar que el modelo es confiable antes de su uso por el supervisor.
- **Dónde buscar en el código:** Pantalla "Entrenamiento IA": botón "Disparar Entrenamiento", estado del servicio (ONLINE/TRAINING), tarjetas de métricas y versión, "Historial de Entrenamiento". Buscar: endpoint de entrenamiento, registro de historial (éxito/fallo y motivo), actualización de versión/estado del modelo.

#### HU0002-1 — Mensaje de reentrenamiento exitoso en historial de entrenamiento

- **Contexto:** En caso que el "Administrador" ingrese al módulo de "Entrenamiento IA", haga click en el botón Iniciar y el entrenamiento sea exitoso
- **Evento:** cuando el usuario visualice historial de entrenamiento
- **Resultado esperado:** el sistema debe mostrar un log de reentrenamiento exitoso
- **➕ Aclaración:** Rol: Administrador (según HU0003 el Supervisor no ve "Entrenamiento IA") [CONFIRMAR].
- **CP asociado:** CP007
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP007 — Mensaje de reentrenamiento exitoso en historial de entrenamiento**

- **Criterio:** HU0002-1
- **Precondiciones:** Administrador autenticado. Haber cargado datos previamente en "Ingesta de datos".
- **Nota:** Los "Límites de Seguridad" no son datos de entrada del entrenamiento; se prueban en CP014–CP017.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo "Entrenamiento IA" |  | Se muestra el panel con "Entrenamiento del Modelo" e "Historial de Entrenamiento" |
| 2 | Hacer click en el botón "Disparar Entrenamiento" |  | Se muestra "Entrenando Cerebro Digital…", luego las métricas (R² y error) y un toast verde en la parte inferior derecha: "¡Ciclo MLOps completado! El modelo ha sido actualizado." |
| 3 | Visualizar la sección "Historial de Entrenamiento" |  | Aparece una entrada nueva, la más reciente, con estado exitoso |

- **Postcondiciones:** Gemelo digital entrenado para usarlo en el simulador para las recomendaciones
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0002-2 — Mensaje de reentrenamiento fallido en historial de entrenamiento

- **Contexto:** En caso que el "Administrador" ingrese al módulo de "Entrenamiento IA", haga click en el botón Iniciar y el entrenamiento sea erroneo
- **Evento:** cuando el usuario visualice historial de entrenamiento
- **Resultado esperado:** el sistema debe mostrar un log reentrenamiento fallido
- **➕ Aclaración:** Falta definir cómo provocar un fallo de forma reproducible [CONFIRMAR]. Debe verse el toast "Fallo crítico en el pipeline MLOps" y el motivo en el historial.
- **CP asociado:** CP008
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP008 — Mensaje de reentrenamiento fallido en historial de entrenamiento**

- **Criterio:** HU0002-2
- **Precondiciones:** Administrador autenticado. Haber cargado datos erróneos o inservibles en "Ingesta de datos" [CONFIRMAR cómo provocar el fallo de forma reproducible].
- **Nota:** Los "Límites de Seguridad" no son datos de entrada del entrenamiento; se prueban en CP014–CP017.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo "Entrenamiento IA" |  | Se muestra el panel con "Entrenamiento del Modelo" e "Historial de Entrenamiento" |
| 2 | Hacer click en el botón "Disparar Entrenamiento" |  | Toast rojo en la parte inferior derecha: "Fallo crítico en el pipeline MLOps" |
| 3 | Visualizar la sección "Historial de Entrenamiento" |  | Aparece una entrada nueva con estado fallido y el motivo del fallo |

- **Postcondiciones:** Ninguna
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0002-3 — Visualización de métricas del modelo tras entrenamiento exitoso

- **Contexto:** En caso que el "Administrador" ingrese al módulo de "Entrenamiento IA", haga click en el botón Iniciar y el entrenamiento sea exitoso
- **Evento:** cuando el usuario visualice el panel de resultados
- **Resultado esperado:** el sistema debe mostrar las métricas del modelo
- **➕ Aclaración:** "Métricas" = R² (tarjeta "Precisión Real"; más alto es mejor), RMSE (tarjeta "Error Promedio", en g/kg; más bajo es mejor) y "Versión del Modelo" (formato v1.MMDD.HHMM) [CONFIRMAR RMSE vs MAE].
- **CP asociado:** CP009
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP009 — Visualización de métricas del modelo tras entrenamiento exitoso**

- **Criterio:** HU0002-3
- **Precondiciones:** Administrador autenticado. Existe un modelo "Champion" activo (ej. versión v1.0901.1000).

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo de "Entrenamiento IA" desde el menú lateral. |  | Se muestra el panel de resultados de entrenamiento y la conexión con el microservicio (ONLINE) |
| 2 | Visualizar y registrar mentalmente la versión actual del modelo y sus métricas en las tarjetas analíticas antes de operar. | Datos actuales observados (ej. Versión: v1.0901.1000, R²: 75.00%). | El sistema muestra los datos del modelo que se encuentra actualmente en producción (Entrenamiento inicial previo). |
| 3 | Presionar el botón "Disparar Entrenamiento" en el panel de Entrenamiento del Modelo. |  | El estado del ML Service cambia visualmente a TRAINING (color ámbar) y el botón muestra el texto "Procesando Algoritmo...". |
| 4 | Esperar la resolución del pipeline de Machine Learning y observar el mensaje de respuesta. |  | El sistema emite un Toast verde de Operación Exitosa indicando: "¡Ciclo MLOps completado! El modelo ha sido actualizado." |
| 5 | Comprobar la actualización de las tarjetas analíticas (Precisión Real, Error Promedio y Versión del Modelo). | Nueva versión generada (ej. v1.1003.1430). Nuevos valores de R² y RMSE. | La tarjeta "Versión del Modelo" cambia su identificador (v1.xxxx.xxxx), demostrando que un nuevo modelo ha reemplazado al anterior, confirmando que se ejecutó un reentrenamiento exitoso basado en la nueva data. |

- **Postcondiciones:** El nuevo modelo XGBoost asume el estado ACTIVE, el modelo anterior pasa a estado ARCHIVED, y los nuevos pesos matemáticos se cargan en la memoria RAM del servidor para las siguientes simulaciones operativas.
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0002-4 — Reentrenamiento al cargar nuevo dataset

- **Contexto:** En caso que se complete la carga exitosa de un nuevo dataset operativo en el módulo de Ingesta de datos
- **Evento:** cuando el usuario ingrese al módulo de entrenamiento IA y haga click en el botón de reentrenamiento
- **Resultado esperado:** el sistema debe aceptar el entrenamiento cada vez que se reentrene con la carga un nuevo dataset.
- **CP asociado:** CP010
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP010 — Reentrenamiento al cargar nuevo dataset**

- **Criterio:** HU0002-4
- **Precondiciones:** Administrador autenticado. Haber cargado un NUEVO grupo de archivos válidos (.csv/.xlsx) en "Ingesta de datos".
- **Nota:** La hoja original de este caso estaba titulada CP011 por error.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo "Entrenamiento IA" |  | Se muestra el panel con "Entrenamiento del Modelo" e "Historial de Entrenamiento" |
| 2 | Hacer click en el botón "Disparar Entrenamiento" |  | Se muestra "Entrenando Cerebro Digital…", las métricas y el toast "¡Ciclo MLOps completado! El modelo ha sido actualizado." |
| 3 | Visualizar la sección "Historial de Entrenamiento" |  | Se visualiza una entrada nueva con las métricas del nuevo dataset |

- **Postcondiciones:** El sistema queda reentrenado con nuevas metricas de precisión para usarlo en el módulo de simulador
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)


---

### HU0003 — Ingresar al sistema con mis credenciales

- **Épica:** Inteligencia Predictiva y Gestión de Datos
- **Enunciado:** Como **Usuario** necesito **Ingresar al sistema con mis credenciales**, con la finalidad de acceder a las opciones del sistema.
- **Dónde buscar en el código:** Pantalla de login ("Usuario de Planta", "Firma Digital (Contraseña)", "Ingresar al Sistema"/"Autenticando Firma..."), logout ("Finalizar Sesión"), guards de ruta y menú por rol. Verificar que el BACKEND también restringe por rol.

#### HU0003-1 — Login rol "Administrador" con credenciales correctas

- **Contexto:** En caso que el Administrador se encuentre en la pantalla de login
- **Evento:** cuando ingrese sus credenciales correctas (usuario y contraseña) y le de al botón "Ingresar al sistema"
- **Resultado esperado:** el sistema debe permitir acceder al sistema y mostrarle los módulos correspondientes a su rol. Administrador (Dashboard, Ingesta, Entrenamiento, Simulador, Auditoría - Usuarios - Audit Trail)
- **➕ Aclaración:** Debe mostrar ÚNICAMENTE los módulos del rol. Probar también acceso directo por URL a un módulo no permitido (debe denegarse).
- **CP asociado:** CP011
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP011 — Login rol "Administrador" con credenciales correctas**

- **Criterio:** HU0003-1
- **Precondiciones:** El usuario debe encontrarse en la pantalla de login y que debe existir previamente una cuenta válida con las credenciales utilizadas.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar el nombre de usuario en el campo "Usuario de Planta". | Usuario: AdministradorTest | El componente recibe el texto correctamente. |
| 2 | Ingresar la contraseña en el campo "Firma Digital (Contraseña)" | Clave: AdministradorTest | El campo recibe el texto ocultando los caracteres por seguridad |
| 3 | Hacer clic en el botón "Ingresar al Sistema" para enviar las credenciales. |  | .El botón cambia de estado (se opaca) y muestra el texto "Autenticando Firma...". El frontend realiza la petición de autenticación al servidor. |
| 4 | Contar los ítems del menú lateral |  | Se muestran únicamente: Dashboard, Ingesta, Entrenamiento IA, Simulador, Auditoría (pestañas Usuarios y Audit Trail). Ningún otro módulo |

- **Postcondiciones:** Usuario Administrador debe acceder al sistema logeado con rol Administrador con opciones al módulo (Dashboard, Ingesta, Entrenamiento, Simulador, Auditoría - Usuarios - Audit Trail)
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0003-2 — Login rol "Supervisor" con credenciales correctas

- **Contexto:** En caso que el Supervisor se encuentre en la pantalla de login
- **Evento:** cuando ingrese sus credenciales correctas (usuario y contraseña) y le de al botón "Ingresar al sistema"
- **Resultado esperado:** el sistema debe permitir acceder al sistema y mostrarle los módulos correspondientes a su rol. (Ingesta, Simulador, Dashboard)
- **CP asociado:** CP055
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP055 — Login rol "Supervisor" con credenciales correctas**

- **Criterio:** HU0003-2
- **Precondiciones:** El usuario debe encontrarse en la pantalla de login y que debe existir previamente una cuenta válida con las credenciales utilizadas.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar el nombre de usuario en el campo "Usuario de Planta". | Usuario: SupervisorTest | El componente recibe el texto correctamente. |
| 2 | Ingresar la contraseña en el campo "Firma Digital (Contraseña)" | Clave: SupervisorTest | El campo recibe el texto ocultando los caracteres por seguridad |
| 3 | Hacer clic en el botón "Ingresar al Sistema" para enviar las credenciales. |  | .El botón cambia de estado (se opaca) y muestra el texto "Autenticando Firma...".. |
| 4 | Contar los ítems del menú lateral |  | Se muestran únicamente: Ingesta, Simulador, Dashboard. Ningún otro módulo |

- **Postcondiciones:** Usuario Supervisor debe acceder al sistema logeado con rol Supervisor con opciones al módulo (Ingesta, Simulador, Dashboard)
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0003-3 — Login rol "Gerente" con credenciales correctas

- **Contexto:** En caso que el Gerente se encuentre en la pantalla de login
- **Evento:** cuando ingrese sus credenciales correctas (usuario y contraseña) y le de al botón "Ingresar al sistema"
- **Resultado esperado:** el sistema debe permitir acceder al sistema y mostrarle los módulos correspondientes a su rol. (Dashboard)
- **CP asociado:** CP056
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP056 — Login rol "Gerente" con credenciales correctas**

- **Criterio:** HU0003-3
- **Precondiciones:** El usuario debe encontrarse en la pantalla de login y que debe existir previamente una cuenta válida con las credenciales utilizadas.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar el nombre de usuario en el campo "Usuario de Planta". | Usuario: GerenteTest | El componente recibe el texto correctamente. |
| 2 | Ingresar la contraseña en el campo "Firma Digital (Contraseña)" | Clave: GerenteTest | El campo recibe el texto ocultando los caracteres por seguridad |
| 3 | Hacer clic en el botón "Ingresar al Sistema" para enviar las credenciales. |  | .El botón cambia de estado (se opaca) y muestra el texto "Autenticando Firma...".. |
| 4 | Contar los ítems del menú lateral |  | Se muestran únicamente: Dashboard. Ningún otro módulo |

- **Postcondiciones:** Usuario Gerente debe acceder al sistema logeado con rol Gerente con opciones al módulo (Dashboard)
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0003-4 — Login rol "Auditor" con credenciales correctas

- **Contexto:** En caso que el Auditor se encuentre en la pantalla de login
- **Evento:** cuando ingrese sus credenciales correctas (usuario y contraseña) y le de al botón "Ingresar al sistema"
- **Resultado esperado:** el sistema debe permitir acceder al sistema y mostrarle los módulos correspondientes a su rol. (Auditoría - Audit Trail)
- **CP asociado:** CP057
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP057 — Login rol "Auditor" con credenciales correctas**

- **Criterio:** HU0003-4
- **Precondiciones:** El usuario debe encontrarse en la pantalla de login y que debe existir previamente una cuenta válida con las credenciales utilizadas.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar el nombre de usuario en el campo "Usuario de Planta". | Usuario: AuditorTest | El componente recibe el texto correctamente. |
| 2 | Ingresar la contraseña en el campo "Firma Digital (Contraseña)" | Clave: AuditorTest | El campo recibe el texto ocultando los caracteres por seguridad |
| 3 | Hacer clic en el botón "Ingresar al Sistema" para enviar las credenciales. |  | .El botón cambia de estado (se opaca) y muestra el texto "Autenticando Firma...". |
| 4 | Contar los ítems del menú lateral |  | Se muestran únicamente: Auditoría (Audit Trail). Ningún otro módulo |

- **Postcondiciones:** Usuario Auditor debe acceder al sistema logeado con rol Auditor con opciones al módulo (Auditoría - Audit Trail)
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0003-5 — Login usuario cualquier rol con credenciales incorrectas

- **Contexto:** En caso que el usuario sin importar el rol se encuentre en la pantalla de login
- **Evento:** cuando ingrese sus credenciales incorrectas (usuario y contraseña)
- **Resultado esperado:** el sistema debe el mensaje "Credenciales inválidas" y no permitir acceder al sistema
- **➕ Aclaración:** Probar: usuario inexistente, contraseña errónea, campos vacíos. Mensaje único "Credenciales inválidas".
- **CP asociado:** CP012
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP012 — Login usuario cualquier rol con credenciales incorrectas**

- **Criterio:** HU0003-5
- **Precondiciones:** El usuario debe encontrarse en la pantalla de login y que no debe tener cuenta existente registrado en el sistema o puede existir previamente una cuenta creada previamente en el sistema. Ejm: <br>Usuario: AdministradorTest<br>Contraseña: AdministradorTest
- **Nota:** Repetir con: usuario inexistente, contraseña vacía y usuario vacío. El mensaje debe ser siempre "Credenciales inválidas".

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar credenciales usuario | AdministradorTest |  |
| 2 | Ingresar contraseña incorrecta | 123456789.0 |  |
| 3 | Hacer click en el botón "Ingresar al sistema" |  | Botón cambia de estado se opaca y aparece "Autenticando Firma". |
| 4 | Visualizar en la pantalla de login |  | Mensaje error "Credenciales inválidas" en la pantalla |

- **Postcondiciones:** Usuario debe quedarse en la pantalla de Login hasta que coloque sus credenciales correctas
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0003-6 — Cierre de sesión de usuario

- **Contexto:** En caso el usuario le de finalizar sesión
- **Evento:** cuando el usuario se encuentre dentro del sistema
- **Resultado esperado:** el sistema finaliza sesión y redirige a pantalla de login
- **➕ Aclaración:** En la redacción, contexto y evento están invertidos; se prueba: estando dentro del sistema, pulsar "Finalizar Sesión". Al volver atrás con el navegador no debe reabrirse una ruta protegida.
- **CP asociado:** CP013
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP013 — Cierre de sesión de usuario**

- **Criterio:** HU0003-6
- **Precondiciones:** - El usuario ha iniciado sesión previamente con credenciales válidas y se encuentra navegando dentro de un módulo protegido del sistema (ej. Dashboard o Simulador).

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ubicar y hacer clic en el botón "Finalizar Sesión" (o icono de logout) en el menú lateral de navegación. |  | El sistema procesa la solicitud de cierre, limpia la sesión actual y redirige inmediatamente a la pantalla de Login (/login). |
| 2 | Intentar regresar a la página anterior protegida utilizando el botón "Atrás" del navegador web. |  | El sistema deniega el acceso y mantiene al usuario en la pantalla de Login, validando que la sesión ya no existe. |

- **Postcondiciones:** Los tokens de autenticación y los datos de perfil son eliminados completamente del navegador (cookies y LocalStorage). El sistema bloquea cualquier acceso futuro a rutas protegidas, requiriendo que el usuario ingrese nuevamente sus credenciales correctas para volver a operar.
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)


---

### HU0004 — Configurar visualizar los límites de seguridad de humedad de la sala farmaceutica (parámetros GMP)

- **Épica:** Administración de Seguridad y Parámetros de Entorno
- **Enunciado:** Como **Administrador** necesito **Configurar visualizar los límites de seguridad de humedad de la sala farmaceutica (parámetros GMP)**, con la finalidad de que el simulador restrinja las recomendaciones de ahorro que pongan en riesgo el producto.
- **Dónde buscar en el código:** Panel "Límites de Seguridad (GMP)" dentro de "Entrenamiento IA": campos mínimo/máximo, botón "Guardar Límites", validación 0–100 y mínimo < máximo (frontend y backend), persistencia en BD y evento de auditoría.

#### HU0004-1 — Validación de los límites físicos y acotamiento de rangos

- **Contexto:** Dado que el Administrador ha ingresado con el rol autorizado al centro de control y configuración del sistema
- **Evento:** Cuando visualice el panel de gestión de restricciones de seguridad (Parámetros GMP)
- **Resultado esperado:** Entonces el sistema mostrará los campos habilitados para configurar los límites de humedad mínimo y máximo Y validará estrictamente que cualquier valor ingresado se encuentre dentro de un rango porcentual físicamente posible de 0% a 100%
- **➕ Aclaración:** Si se fuerza un valor fuera de 0–100 (saltándose el bloqueo del campo), debe rechazarse con "Error al guardar las restricciones operacionales" y no persistir.
- **CP asociado:** CP014
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP014 — Validación de los límites físicos y acotamiento de rangos**

- **Criterio:** HU0004-1
- **Precondiciones:** - El usuario se encuentra autenticado en el sistema con el rol de Administrador.<br>- El usuario se encuentra en el módulo de "Entrenamiento IA" (Centro de Control de IA).
- **Nota:** "Evasión visual" = saltarse el bloqueo del campo, p. ej. editando el atributo `max`/`min` del input con las herramientas del navegador (F12) o enviando la petición con Postman.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ir al módulo "Entrenamiento IA" y ubicar "Límites de Seguridad (GMP)" |  | Se muestra el panel con los campos de humedad mínima y máxima |
| 2 | En "Humedad Relativa Mínima (%)" intentar ingresar un valor negativo | -20 | El campo no permite valores menores a 0 |
| 3 | En "Humedad Relativa Máxima (%)" intentar ingresar un valor negativo | -10 | El campo no permite valores menores a 0 |
| 4 | En "Humedad Relativa Máxima (%)" intentar ingresar un valor mayor a 100 | 150 | El campo no permite valores mayores a 100 |
| 5 | Forzar un valor fuera de rango saltándose el bloqueo del campo y pulsar "Guardar Límites" (ver nota) | Máxima = 150 | El sistema rechaza y muestra "Aviso del Sistema: Error al guardar las restricciones operacionales". No se guarda nada |

- **Postcondiciones:** El sistema restringe por completo la persistencia de valores negativos, descartando la operación y manteniendo vigentes los parámetros regulatorios seguros en la base de datos.
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0004-2 — Restricción y bloqueo de configuración por inversión de umbrales

- **Contexto:** Dado que el Administrador se encuentra modificando los umbrales de humedad de la sala
- **Evento:** Cuando intente configurar un límite máximo que sea menor o igual al límite mínimo (ej. Mínimo: 60% y Máximo: 50%) y haga clic en "Guardar Límites"
- **Resultado esperado:** Entonces el sistema interceptará la transacción y bloqueará la persistencia en la base de datos Y desplegará de inmediato un mensaje de error impidiendo el guardado: "El límite mínimo de humedad no puede ser mayor o igual al límite máximo"
- **➕ Aclaración:** También aplica Mínimo = Máximo (ej. 50 y 50).
- **CP asociado:** CP015
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP015 — Restricción y bloqueo de configuración por inversión de umbrales**

- **Criterio:** HU0004-2
- **Precondiciones:** Estar logueado en el sistema con el rol Administrador. Tener datos correctamente cargados previamente en el módulo de Ingesta de Datos
- **Nota:** Repetir con Mínimo = 50 y Máximo = 50: también debe rechazarse con el mismo mensaje.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo de "Entrenamiento IA" |  | Se muestra la pantalla con secciones de "Entrenamiento del Modelo", "Límites de Seguridad", "Historial de entrenamientos" |
| 2 | Visualizar Límites de Seguridad |  |  |
| 3 | Ingresar valor Humedad Relativa Mínima (%) | 60.0 |  |
| 4 | Ingresar valor Humedad Relativa Máxima (%) | 40.0 |  |
| 5 | Dar clic en "Guardar Límites" |  | Aviso del Sistema "El límite mínimo de humedad no puede ser mayor o igual al límite máximo" |

- **Postcondiciones:** El sistema no permite guardar esos limites hasta que el usuario coloque un valor mínimo < máxima
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0004-3 — Persistencia exitosa y respuesta de confirmación visual

- **Contexto:** Dado que el Administrador ingresa valores numéricos coherentes y válidos dentro de la banda regulatoria permitida
- **Evento:** Cuando presione el botón de guardado en el panel de configuración GMP
- **Resultado esperado:** Entonces se actualizará los parámetros en la tabla central de la base de datos de forma inmediata Y mostrará la confirmación en la interfaz: "Umbrales regulatorios actualizados. Cambio firmado en la pista de auditoría"
- **➕ Aclaración:** El toast muestra el título "Operación Exitosa" y el texto indicado.
- **CP asociado:** CP016
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP016 — Persistencia exitosa y respuesta de confirmación visual**

- **Criterio:** HU0004-3
- **Precondiciones:** Estar logueado en el sistema con el rol Administrador

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ir a la módulo "Entrenamiento IA" |  | Pantalla cargada con secciones de entrenamiento de modelo, historial de entrenamiento, limites de seguridad GMP |
| 2 | Ir al panel de límites de seguridad GMP |  |  |
| 3 | Ingresar valor mínimo de humedad | 30.0 |  |
| 4 | Ingresar valor máximo de humedad | 50.0 |  |
| 5 | Dar clic en "Guardar Límites" |  | El sistema debe mostrar un toast con Mensaje: Operación Exitosa<br>Umbrales regulatorios actualizados. Cambio firmado en la pista de auditoría. |

- **Postcondiciones:** El sistema guarda los valores de seguridad ingresados, y el simulador podrá tener el comportamiento con límites de seguridad cuando se hagan las recomendaciones
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0004-4 — Validación de la consecuencia en el sistema (Impacto en Auditoría y en el Simulador)

- **Contexto:** Dado que los nuevos límites GMP han sido guardados exitosamente por el Administrador
- **Evento:** Cuando un operador ejecute una simulación cuyos resultados se encuentren fuera de la nueva banda de seguridad.
- **Resultado esperado:** Y de forma concurrente, el servicio de auditoría generará un registro inmutable en el módulo de "Auditoría" vinculando el ID del Administrador, la fecha, y el detalle exacto de los nuevos límites configurados, cumpliendo con la directiva FDA 21 CFR Part 11
- **➕ Aclaración:** La redacción del resultado está incompleta (empieza en "Y de forma concurrente…"). Lo verificable es el registro inmutable en Auditoría con usuario, fecha/hora y valores. El efecto en el simulador se prueba en HU0017.
- **CP asociado:** CP017
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP017 — Validación de la consecuencia en el sistema (Impacto en Auditoría y en el Simulador)**

- **Criterio:** HU0004-4
- **Precondiciones:** Usuario autenticado, y datasets cargados

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ir a la ventana "Entrenamiento IA" |  |  |
| 2 | Ingresar valor mínimo de humedad | 30.0 |  |
| 3 | Ingresar valor máximo de humedad | 50.0 |  |
| 4 | Dar clic en "Guardar Límites" |  | Mensaje: Operación Exitosa<br>Umbrales regulatorios actualizados. Cambio firmado en la pista de auditoría. |
| 5 | Ir a ventana auditoria y seleccionar AUDIT TRAIL |  | Se debe visualizar la fecha , hora y valores de registro actualizados del limite de seguridad |

- **Postcondiciones:** El sistema registra en el audit trail los valores de seguridad ingresados
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)


---

### HU0005 — Gestionar la creación de usuarios y asignación de roles

- **Épica:** Administración de Seguridad y Parámetros de Entorno
- **Enunciado:** Como **Administrador** necesito **Gestionar la creación de usuarios y asignación de roles**, con la finalidad de asegurar que solo personal autorizado acceda al módulo correspondiente.
- **Dónde buscar en el código:** Módulo "Auditoría" → pestaña "Usuarios": cards, modal "Nuevo Registro" ("Crear identidad GXP"), "Editar" ("Guardar cambios"), "Revocar". Buscar: unicidad de username, campos obligatorios, hash de contraseña, baja lógica/física, eventos de auditoría.

#### HU0005-1 — Listado de usuarios en el módulo Auditoría

- **Contexto:** En caso que el Administrador acceda módulo de "Auditoría"
- **Evento:** cuando el usuario acceda al Tab de usuarios
- **Resultado esperado:** el sistema debe listar a los usuarios con su respectiva informacion de accesos al sistema
- **➕ Aclaración:** Cada card muestra datos del usuario y su acceso [CONFIRMAR campos exactos].
- **CP asociado:** CP018
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP018 — Listado de usuarios en el módulo Auditoría**

- **Criterio:** HU0005-1
- **Precondiciones:** Estar logueado en el sistema con el rol Administrador

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ir al módulo "Auditoria" |  | Pantalla con Tab "Audit Trail" y "Usuarios" |
| 2 | Hacer click en el Tab "Usuarios" |  | Listado de usuarios en cards con información personal. |

- **Postcondiciones:** El usuario podrá ver y gestionar los usuarios solo si tiene el rol de Administrador
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0005-2 — Registro exitoso de nuevo usuario

- **Contexto:** En caso que el Administrador se encuentre el mòdulo de Auditoría y haga click "Nuevo Registro"
- **Evento:** cuando complete los campos adecuadamente y le de click al boton "Guardar"
- **Resultado esperado:** el sistema deberá mostrar un mensaje exitoso "Nueva identidad GxP dada de alta en el sistema"
- **CP asociado:** CP019
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP019 — Registro exitoso de nuevo usuario**

- **Criterio:** HU0005-2
- **Precondiciones:** Estar logueado en el sistema con el rol Administrador

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo "Auditoria" |  | Pantalla con Tab "Audit Trail" y "Usuarios" |
| 2 | Hacer click en el Tab "Usuarios" |  | Pantallas de Gestión de Usuarios |
| 3 | Hacer click en "Nuevo Registro" |  | Apertura de modal con campos a completar |
| 4 | Ingresar Nombre Completo | Carlos Hernandez |  |
| 5 | Ingresar Username | CarlosHernandezTest |  |
| 6 | Ingresar Rol de Acceso | Elegir del combo Supervisor o Auditor o Administrador o Gerente |  |
| 7 | Ingresar Contraseña | 123456789.0 |  |
| 8 | Hacer click en "Crear identidad GXP" |  | Mensaje en un toast de "Nueva identidad GxP dada de alta en el sistema" y aparición en lista. |

- **Postcondiciones:** El sistema crea un nuevo usuario. Asimismo, este usuario podrá acceder al sistema con el rol que fue asignado  ycon las credenciales que le brinde el Administrador
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0005-3 — Rechazo por nombre de usuario (username) duplicado

- **Contexto:** En caso que el Administrador se encuentre el mòdulo de Auditoría y haga click "Nuevo Registro"
- **Evento:** cuando coloque un nombre de usuario (username) existente y le de click al boton "Guardar"
- **Resultado esperado:** el sistema deberá mostrar un mensaje de rechazo"Transacción rechazada: Conflicto de unicidad en los datos de la cuenta."
- **CP asociado:** CP020
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP020 — Rechazo por nombre de usuario (username) duplicado**

- **Criterio:** HU0005-3
- **Precondiciones:** Estar logueado en el sistema con el rol Administrador y ya debe existir un usuario con "Username" registrado. Ejm "CarlosHernandezTest"

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo "Auditoria" |  | Pantalla con Tab "Audit Trail" y "Usuarios" |
| 2 | Hacer click en el Tab "Usuarios" |  | Pantallas de Gestión de Usuarios |
| 3 | Hacer click en "Nuevo Registro" |  | Apertura de modal con campos a completar |
| 4 | Ingresar Nombre Completo | Carlos Hernandez |  |
| 5 | Ingresar Username | CarlosHernandezTest |  |
| 6 | Ingresar Rol de Acceso | Elegir del combo Supervisor o Auditor o Administrador o Gerente |  |
| 7 | Ingresar Contraseña | 123456789.0 |  |
| 8 | Hacer click en "Crear identidad GXP" |  | Mensaje en un toast de "Transacción rechazada: Conflicto de unicidad en los datos de la cuenta" |

- **Postcondiciones:** El sistema no debe permitir crear un usuario con username duplicado.
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0005-4 — Rechazo de creación de usuarios por campos obligatorios incompletos

- **Contexto:** En caso que el Administrador se encuentre el mòdulo de Auditoría y haga click "Nuevo Registro"
- **Evento:** cuando deje campos sin completar
- **Resultado esperado:** el sistema debe avisar que "Complete el campo"
- **➕ Aclaración:** "Complete el campo" corresponde probablemente al mensaje nativo del navegador (varía por idioma) [CONFIRMAR]. El modal debe seguir abierto y no crearse el usuario.
- **CP asociado:** CP021
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP021 — Rechazo de creación de usuarios por campos obligatorios incompletos**

- **Criterio:** HU0005-4
- **Precondiciones:** Estar logueado en el sistema con el rol Administrador
- **Nota:** El mensaje puede ser el nativo del navegador ("Completa este campo"); cambia según el idioma del navegador [CONFIRMAR].

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo "Auditoria" |  | Pantalla con Tab "Audit Trail" y "Usuarios" |
| 2 | Hacer click en el Tab "Usuarios" |  | Pantallas de Gestión de Usuarios |
| 3 | Hacer click en "Nuevo Registro" |  | Apertura de formulario modal con campos a completar |
| 4 | Ingresar Nombre Completo | Dejar Vacio |  |
| 5 | Ingresar Username | CarlosHernandezTest |  |
| 6 | Ingresar Rol de Acceso | Elegir del combo Supervisor o Auditor o Administrador o Gerente |  |
| 7 | Ingresar Contraseña | 123456789.0 |  |
| 8 | Hacer click en "Crear identidad GXP" |  | Debe salir un mensaje "Completar este campo" |

- **Postcondiciones:** El sistema debe quedarse con el formulario y no debe permitir crear un usuario con datos incompletos
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0005-5 — Actualización de datos al editar usuario

- **Contexto:** En caso que el Administrador se encuentre el mòdulo de Auditoría y haga click "Editar"
- **Evento:** cuando complete los campos adecuadamente y le de click al boton "Guardar"
- **Resultado esperado:** el sistema debe actualizar la información y acceso en caso corresponda.
- **➕ Aclaración:** Tras editar, iniciar sesión con la clave nueva (entra) y con la anterior (falla).
- **CP asociado:** CP022
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP022 — Actualización de datos al editar usuario**

- **Criterio:** HU0005-5
- **Precondiciones:** Estar logueado en el sistema con el rol Administrador y debe existir al menos un usuario creado para la edición

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo "Auditoria" |  | Pantalla con Tab "Audit Trail" y "Usuarios" |
| 2 | Hacer click en el Tab "Usuarios" |  | Pantallas de Gestión de Usuarios |
| 3 | Visualizar card de usuario existente y Hacer click en "Editar" |  | Apertura de formulario modal con datos llenados con la información del usuario editado |
| 4 | Ingresar Nombre Completo | Carlos Hernandez Editado |  |
| 5 | Ingresar Username | CarlosHernandezTest |  |
| 6 | Ingresar Rol de Acceso | Elegir del combo Supervisor o Auditor o Administrador o Gerente |  |
| 7 | Ingresar Contraseña | ContraseñaCambiada |  |
| 8 | Hacer click en "Guardar cambios" |  | Botón cambia de estado a "Procesando Transacción" y  cuando complete la carga el sistema muestra un mensaje Toast "Identidad GxP actualizada con éxito." |

- **Postcondiciones:** El sistema mostrar el mensaje y cuando el usuario vuelva a ingresar al sistema deberá colocar sus nuevas credenciales. De caso contrario el sistema no permitira su acceso
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0005-6 — Revocación de acceso de usuario

- **Contexto:** En caso que el Administrador haga click "Revocar"
- **Evento:** cuando acepte la revocación
- **Resultado esperado:** el sistema deberá mostrar un mensaje exitoso "Acceso revocado de manera inmutable en la base de datos de planta"
- **➕ Aclaración:** Antes aparece el diálogo "¿Revocar acceso permanentemente?". Tras revocar, el usuario sale de la lista y al ingresar recibe "Credenciales inválidas" [CONFIRMAR si es baja lógica o física].
- **CP asociado:** CP023
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP023 — Revocación de acceso de usuario**

- **Criterio:** HU0005-6
- **Precondiciones:** Estar logueado en el sistema con el rol Administrador y existir usuarios registrados en el sistema

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo "Auditoria" |  | Pantalla con Tab "Audit Trail" y "Usuarios" |
| 2 | Hacer click en el Tab "Usuarios" |  | Pantallas de Gestión de Usuarios |
| 3 | Hacer click en "REVOCAR" de algún usuario creado |  | Aviso: ¿Revocar acceso permanentemente? |
| 4 | Cick en el botón "Aceptar" |  | El sistema debe desaparecer al usuario de la lista de usuarios. Mostrar un Toast con el mensaje de "Acceso revocado de manera inmutable en la base de datos de planta." |

- **Postcondiciones:** El usuario revocado no podrá acceder al sistema la próxima vez que se vuelva a loguear mostrandole el mensaje "Credenciales inválidas"
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)


---

### HU0006 — Ingresar manualmente los datos de temperatura y humedad externa

- **Épica:** Simulación y Soporte a la Toma de Decisiones
- **Enunciado:** Como **Supervisor** necesito **Ingresar manualmente los datos de temperatura y humedad externa**, con la finalidad de considerar la carga externa en la simulación.
- **Dónde buscar en el código:** Formulario del Simulador: campos "Temp. Exterior (°C)" y "Humedad Ext. (HR %)". Buscar: atributos min/max/step o validación JS, validación previa al llamado al backend, mensaje de campos vacíos.

#### HU0006-1 — Validación estricta de las variables de carga climática externa

- **Contexto:** Dado que el Supervisor se encuentra en el módulo de "Simulación", registrando la carga climática que impacta a la planta
- **Evento:** Cuando introduzca los valores físicos en los campos de "Temp. Exterior (°C)" y "Humedad Ext. (HR %)"
- **Resultado esperado:** Entonces el sistema validará que los tipos de datos ingresados sean estrictamente valores numéricos (incluyendo soporte para números decimales) Y bloqueará el ingreso de letras o caracteres especiales, limitando el rango permitido de Temperatura entre 0°C y 50°C, y la Humedad Relativa entre 0% y 100%, asegurando que el modelo predictivo reciba variables físicas realistas
- **➕ Aclaración:** Límites inclusivos (0 y 50 válidos). Decimales con punto (25.56). No admite letras ni símbolos [CONFIRMAR si bloquea al teclear o muestra error al enviar].
- **CP asociado:** CP024
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP024 — Validación estricta de las variables de carga climática externa**

- **Criterio:** HU0006-1
- **Precondiciones:** - El usuario se encuentra autenticado en el sistema con el rol de Administrador o Supervisor.<br>- El usuario tiene acceso al menú lateral de navegación.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Seleccionar la opción "Simulador de Ahorro" en el menú de navegación lateral. |  | Apertura correcta de la ventana: "Simulador de Optimización Energética". |
| 2 | Posicionarse en el campo "Temp. Exterior (°C)" e intentar ingresar valores fuera de los límites físicos establecidos (0 a 50). | Valores inválidos: 60 o -10 | El componente de interfaz bloquea la entrada del dato, no permitiendo que el campo se llene con valores fuera del rango (0 a 50°C). |
| 3 | Limpiar el campo e ingresar valores numéricos enteros o decimales dentro del rango permitido. | Valores válidos: 25 o 25.56 | El sistema permite digitar y llenar el campo correctamente con los valores positivos enteros o decimales. |
| 4 | Posicionarse en el campo "Humedad Ext. (HR %)" e intentar ingresar valores fuera del rango porcentual (0 a 100). | Valores inválidos: 150 o -50 | El componente de interfaz restringe el input y no permite el ingreso del valor, respetando el límite estricto máximo de 100%. |
| 5 | Limpiar el campo e ingresar valores numéricos de humedad dentro del rango permitido. | Valores válidos: 20 o 21.65 | El sistema permite digitar y llenar el campo correctamente con los valores porcentuales válidos. |

- **Postcondiciones:** Las variables de condiciones externas quedan validadas y temporalmente almacenadas en la vista, listas para ser procesadas de manera segura por el motor matemático del Gemelo Digital.
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0006-2 — Prevención de errores de inferencia por ausencia de datos externos

- **Contexto:** Dado que el Supervisor está configurando el panel de variables operativas para solicitar la estimación del Gemelo Digital Y omite ingresar el dato de temperatura o humedad exterior (dejando uno o ambos campos con valor nulo/vacío)
- **Evento:** Cuando el usuario haga clic en el botón de acción para generar una recomendación predictiva
- **Resultado esperado:** Entonces la plataforma interrumpirá la transacción hacia el backend para prevenir que el algoritmo falle por insuficiencia de parámetros de carga externa Y el sistema mostrará inmediatamente el mensaje de validación: "Por favor, llene las variables de Temperatura y Humeda externa antes de consultar al Gemelo Digital"
- **➕ Aclaración:** El texto trae el error de tipeo "Humeda" [CONFIRMAR texto real mostrado por la app].
- **CP asociado:** CP025
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP025 — Prevención de errores de inferencia por ausencia de datos externos**

- **Criterio:** HU0006-2
- **Precondiciones:** Estar logueado en el sistema con el rol Administrador o Supervisor.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Seleccionar la opción "Simulación de ahorro" |  | Apertura de ventana: Simulador de Optimización Energética |
| 2 | Ingresar en el Simulador los datos de entrada indicados | Temp. Exterior (°C) = Vacio<br>Humedad Ext. (HR %) = Vacio<br>Temp. UMA (°C) = 22.5<br>Humedad UMA (HR %) = 50.4<br>Presión Inyección (Pa) = 100.0<br>Potencia Estimada (%) = 70.0<br>Humedad Sala Actual (HR %) = 44.7<br>Humedad Sala Objetivo (HR %) = 50.0<br>Temp. Sala (°C) = 22.4 | Los campos aceptan los valores y quedan completos |
| 3 | Dar click en "Generar Recomendación" |  | El sistema muestra un mensaje "Por favor, llene las variables de Temperatura y Humeda externa antes de consultar al Gemelo Digital" |

- **Postcondiciones:** El sistema no debe permitir o no debe generar una recomendación hasta que el usuario complete los datos correctamente
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)


---

### HU0007 — Ingresar manualmente los datos de la Unidad Manejadora de Aire (UMA)

- **Épica:** Simulación y Soporte a la Toma de Decisiones
- **Enunciado:** Como **Supervisor** necesito **Ingresar manualmente los datos de la Unidad Manejadora de Aire (UMA)**, con la finalidad de considerar los datos de la uma en la simulación del sistema HVAC de planta.
- **Dónde buscar en el código:** Formulario del Simulador: "Temp. UMA (°C)", "Humedad UMA (HR %)", "Presión Inyección (Pa)". Buscar rangos 0–50, 0–100, 0–1000 y mensaje específico de UMA.

#### HU0007-1 — Validación numérica de temperatura, humedad y presión UMA

- **Contexto:** En caso que el Supervisor ingrese al módulo de "Simulación"
- **Evento:** cuando introduzca los datos correspondientes a la UMA
- **Resultado esperado:** el sistema solo debe permitir campos numéricos para Temperatura en el rango (0°C - 50°C), en el rango Humedad Relativa (0% - 100%) y Presion de Inyeccion (0 Pa a 1000 Pa)
- **➕ Aclaración:** Presión de inyección en Pascales (Pa), rango 0–1000. Válidos de prueba: 100 y 999.5; inválidos: 1600 y -50.
- **CP asociado:** CP026
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP026 — Validación numérica de temperatura, humedad y presión UMA**

- **Criterio:** HU0007-1
- **Precondiciones:** Estar logueado en el sistema con el rol Administrador o Supervisor.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Seleccionar la opción "Simulador de Ahorro" en el menú de navegación lateral. |  | Apertura correcta de la ventana: "Simulador de Optimización Energética". |
| 2 | Posicionarse en el campo "Temp. UMA(°C)" e intentar ingresar valores fuera de los límites físicos establecidos (0 a 50). | Valores inválidos: 60 o -10 | El componente de interfaz bloquea la entrada del dato, no permitiendo que el campo se llene con valores fuera del rango (0 a 50°C). |
| 3 | Limpiar el campo e ingresar valores numéricos enteros o decimales dentro del rango permitido. | Valores válidos: 25 o 25.56 | El sistema permite digitar y llenar el campo correctamente con los valores positivos enteros o decimales. |
| 4 | Posicionarse en el campo "Humedad UMA. (HR %)" e intentar ingresar valores fuera del rango porcentual (0 a 100). | Valores inválidos: 150 o -50 | El componente de interfaz restringe el input y no permite el ingreso del valor, respetando el límite estricto máximo de 100%. |
| 5 | Limpiar el campo e ingresar valores numéricos de humedad dentro del rango permitido. | Valores válidos: 20 o 21.65 | El sistema permite digitar y llenar el campo correctamente con los valores porcentuales válidos. |
| 6 | Posicionarse en el campo "Presión Inyección (Pa)" e intentar ingresar valores fuera del rango (0 a 1000). | Valores inválidos: 1600 o -50 | El componente de interfaz restringe el input y no permite el ingreso del valor, respetando el límite estricto máximo de 1000 |
| 7 | Limpiar el campo e ingresar valores numéricos de humedad dentro del rango permitido. | Valores válidos: 100 o 999.5 | El sistema permite digitar el valor de presión dentro del rango 0–1000 |

- **Postcondiciones:** Las variables de condiciones de la UMA quedan validadas y temporalmente almacenadas en la vista, listas para ser procesadas de manera segura por el motor matemático del Gemelo Digital.
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0007-2 — Aviso por campos de UMA incompletos

- **Contexto:** Dado que el Supervisor está configurando el panel de variables operativas para solicitar la estimación del Gemelo Digital Y omite ingresar el dato de temperatura o humedad o presión inyección (dejando uno o ambos campos con valor nulo/vacío)
- **Evento:** Cuando el usuario haga clic en el botón de acción para generar una recomendación predictiva
- **Resultado esperado:** el sistema debe mostrar el mensaje "Por favor, llene las variables de Temperatura, Humedad y Presion de la UMA antes de consultar al Gemelo Digital"
- **➕ Aclaración:** El mensaje específico de UMA es el de este criterio. La lista de CP traía el genérico por error.
- **CP asociado:** CP027
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP027 — Aviso por campos de UMA incompletos**

- **Criterio:** HU0007-2
- **Precondiciones:** Estar logueado en el sistema con el rol Administrador o Supervisor.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Seleccionar la opción "Simulación de ahorro" |  | Apertura de ventana: Simulador de Optimización Energética |
| 2 | Ingresar en el Simulador los datos de entrada indicados | Temp. Exterior (°C) = 22.5<br>Humedad Ext. (HR %) = 50.4<br>Temp. UMA (°C) = Vacio<br>Humedad UMA (HR %) = Vacio<br>Presión Inyección (Pa) = Vacio<br>Potencia Estimada (%) = 70.0<br>Humedad Sala Actual (HR %) = 44.7<br>Humedad Sala Objetivo (HR %) = 50.0<br>Temp. Sala (°C) = 22.4 | Los campos aceptan los valores y quedan completos |
| 3 | Dar click en "Generar Recomendación" |  | El sistema muestra un mensaje "Por favor, llene las variables de Temperatura, Humeda y Presion de la UMA antes de consultar al Gemelo Digital" |

- **Postcondiciones:** El sistema no debe permitir o no debe generar una recomendación hasta que el usuario complete los datos correctamente
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)


---

### HU0008 — Ingresar manualmente el porcentaje de potencia actual del secador

- **Épica:** Simulación y Soporte a la Toma de Decisiones
- **Enunciado:** Como **Supervisor** necesito **Ingresar manualmente el porcentaje de potencia actual del secador**, con la finalidad de establecer la línea base de consumo contra la cual se comparará la optimización..
- **Dónde buscar en el código:** Formulario del Simulador: "Potencia Estimada (%)", rango 0–100 y mensaje específico de potencia.

#### HU0008-1 — Validación de rango físico para la línea base de potencia

- **Contexto:** Dado que el Supervisor se encuentra en el módulo de "Simulación" para establecer la línea base de consumo del equipo HVAC
- **Evento:** Cuando el usuario introduzca un valor en el campo de "Potencia Estimada (%)" actual del secador
- **Resultado esperado:** Entonces el sistema validará que el dato ingresado sea de formato numérico Y limitará la aceptación del valor a un rango operativo físicamente posible entre el 0% y el 100%, bloqueando automáticamente cualquier número negativo o superior al 100%
- **➕ Aclaración:** "Potencia Estimada (%)" = potencia con la que opera hoy el secador (línea base). [CONFIRMAR si admite decimales]
- **CP asociado:** CP028
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP028 — Validación de rango físico para la línea base de potencia**

- **Criterio:** HU0008-1
- **Precondiciones:** Usuario logeado y ubicado en ventana "Simulador de ahorro"
- **Nota:** Verificar también un valor negativo (-5): debe rechazarse.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Seleccionar la opción "Simulación de ahorro" |  | Apertura de ventana: Simulador de Optimización Energética |
| 2 | Ingresar potencia estimada | 150.0 | Dato rechazado El sistema valida e impide el ingreso (Rango máximo de 0 a 100%). |
| 3 | Ingresar potencia estimada | 55.0 | Dato aceptado. |

- **Postcondiciones:** Variables listas para ser tomadas por el gemelo digital.
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0008-2 — Restricción del cálculo predictivo por ausencia de línea base de potencia

- **Contexto:** Dado que el Supervisor está configurando los parámetros para consultar al motor de Inteligencia  Y omite ingresar la potencia actual base, dejando el campo vacío
- **Evento:** Cuando el usuario haga clic en el botón de acción para generar una recomendación predictiva
- **Resultado esperado:** Entonces el sistema detendrá la petición Y desplegará de inmediato el mensaje de validación: "Por favor, llene la variable de Potencia antes de consultar al Gemelo Digital", exigiendo el dato para poder calcular el diferencial de ahorro
- **➕ Aclaración:** Mensaje específico de potencia (la lista de CP traía el genérico por error).
- **CP asociado:** CP029
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP029 — Restricción del cálculo predictivo por ausencia de línea base**

- **Criterio:** HU0008-2
- **Precondiciones:** Estar logueado en el sistema con el rol Administrador o Supervisor.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Seleccionar la opción "Simulación de ahorro" |  | Apertura de ventana: Simulador de Optimización Energética |
| 2 | Ingresar en el Simulador los datos de entrada indicados | Temp. Exterior (°C) = 20.4<br>Humedad Ext. (HR %) = 78.0<br>Temp. UMA (°C) = 22.5<br>Humedad UMA (HR %) = 50.4<br>Presión Inyección (Pa) = 100.0<br>Potencia Estimada (%) = VACIO<br>Humedad Sala Actual (HR %) = 44.7<br>Humedad Sala Objetivo (HR %) = 50.0<br>Temp. Sala (°C) = 22.4 | Los campos aceptan los valores y quedan completos |
| 3 | Dar click en "Generar Recomendación" |  | El sistema muestra un mensaje "Por favor, llene la variable de Potencia antes de consultar al Gemelo Digital" |

- **Postcondiciones:** El sistema no debe permitir o no debe generar una recomendación hasta que el usuario complete los datos correctamente
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)


---

### HU0009 — Ingresar los datos correspondientes a la sala

- **Épica:** Simulación y Soporte a la Toma de Decisiones
- **Enunciado:** Como **Supervisor** necesito **Ingresar los datos correspondientes a la sala**, con la finalidad de considerar los datos de la sala farmacéutica en la simulación.
- **Dónde buscar en el código:** Formulario del Simulador: "Temperatura de Sala", "Humedad Sala Actual", "Humedad Sala Objetivo". Buscar rangos y mensaje genérico. Verificar si "Humedad Sala Actual" interviene o no en el cálculo.

#### HU0009-1 — Validación de rangos numéricos permitidos para el estado de la sala

- **Contexto:** Dado que el Supervisor se encuentra en la interfaz del módulo de "Simulación"
- **Evento:** Cuando introduzca los parámetros físicos en los campos de "Temperatura de Sala" y "Humedad Relativa"
- **Resultado esperado:** Entonces el sistema validará que los caracteres ingresados sean estrictamente valores numéricos Y el sistema solo aceptará el ingreso de la Temperatura si se encuentra en el rango físico válido de 0°C a 50°C, y la Humedad Relativa en el rango porcentual de 0% a 100%, bloqueando valores fuera de estos límites
- **➕ Aclaración:** La temperatura de sala se usa para convertir el objetivo de humedad. "Humedad Sala Actual" puede ser solo informativa [CONFIRMAR].
- **CP asociado:** CP030
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP030 — Validación de rangos numéricos permitidos para el estado de la sala**

- **Criterio:** HU0009-1
- **Precondiciones:** Usuario logeado y ubicado en ventana "Simulador de ahorro"
- **Nota:** Escribir solo números, sin unidades (°C, %).

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo "Simulador de Ahorro" |  | Se muestra "Simulador de Optimización Energética" con los campos de operación |
| 2 | Ingresar Temp. Sala | 60 | Dato rechazado: el sistema impide el ingreso (rango 0–50 °C) |
| 3 | Ingresar Temp. Sala | 23 | Dato aceptado |
| 4 | Ingresar Humedad Sala Actual | 110 | Dato rechazado: el sistema impide el ingreso (rango 0–100 %) |
| 5 | Ingresar Humedad Sala Actual | 55 | Dato aceptado |

- **Postcondiciones:** Variables listas para ser tomadas por el gemelo digital.
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0009-2 — Restricción de simulación por campos obligatorios incompletos

- **Contexto:** Dado que el Supervisor está preparando una simulación operativa en el módulo Y ha dejado vacíos uno o más datos correspondientes a las variables de la sala
- **Evento:** Cuando el usuario haga clic en el botón de acción para generar una recomendación predictiva
- **Resultado esperado:** Entonces el sistema interceptará la petición y bloqueará la consulta al Gemelo Digital Y mostrará inmediatamente en pantalla el mensaje de alerta: "Por favor, llene todas las variables de operación antes de consultar al Gemelo Digital"
- **➕ Aclaración:** Mensaje genérico. Usar solo números en las pruebas (sin unidades).
- **CP asociado:** CP031
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP031 — Restricción de simulación por campos obligatorios incompletos**

- **Criterio:** HU0009-2
- **Precondiciones:** Usuario logeado y ubicado en ventana "Simulador de ahorro"

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo "Simulador de Ahorro" |  | Se muestra "Simulador de Optimización Energética" con los campos de operación |
| 2 | Ingresar datos válidos en todos los campos, DEJANDO VACÍOS "Temp. Sala" y "Humedad Sala Actual" | Exterior 20.4 / 78.0 · UMA 22.5 / 50.4 / 100.0 · Potencia 70.0 · Objetivo 50.0 | Los campos vacíos quedan sin valor |
| 3 | Dar click en "Generar Recomendación" |  | Toast: "Por favor, llene todas las variables de operación antes de consultar al Gemelo Digital". No aparece la tarjeta "Potencia Recomendada IA" |

- **Postcondiciones:** Variables incompletas , no pueden ser tomadas por el gemelo digital.
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)


---

### HU0010 — Definir el setpoint de humedad objetivo en la interfaz

- **Épica:** Simulación y Soporte a la Toma de Decisiones
- **Enunciado:** Como **Supervisor** necesito **Definir el setpoint de humedad objetivo en la interfaz**, con la finalidad de que el sistema busque el punto de operación de menor consumo que cumpla dicha meta..
- **Dónde buscar en el código:** Botón "Generar Recomendación": validación de todos los campos obligatorios, llamada al endpoint de inferencia, objetivo (setpoint) tomado del campo y no de una constante.

#### HU0010-1 — Generación exitosa de una recomendación de ahorro energético

- **Contexto:** Dado que el operador ha evaluado las condiciones físicas actuales de la sala limpia (temperatura, humedad, presión, etc.) Y se encuentra en el módulo de simulación de la plataforma
- **Evento:** Cuando el usuario ingrese correctamente todos los parámetros ambientales requeridos en el formulario y ejecute la simulación
- **Resultado esperado:** Entonces el modelo de Machine Learning debe procesar la información ingresada Y el sistema debe mostrar en pantalla la recomendación de potencia óptima (ej. 50%) calculada para esas condiciones específicas
- **➕ Aclaración:** El "50 %" del ejemplo es ilustrativo, no un valor esperado. Criterio adicional propuesto que documenta lo que CP032 ya prueba: el campo "Humedad Sala Objetivo" solo acepta 0–100.
- **CP asociado:** CP032
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP032 — Generación exitosa de una recomendación de ahorro energético**

- **Criterio:** HU0010-1
- **Precondiciones:** Usuario logeado y ubicado en ventana "Simulador de ahorro"

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo "Simulador de Ahorro" |  | Se muestra "Simulador de Optimización Energética" con los campos de operación |
| 2 | Ingresar Humedad Sala Objetivo | 110 | Dato rechazado: el sistema impide el ingreso (rango 0–100 %) |
| 3 | Ingresar Humedad Sala Objetivo | 55 | Dato aceptado |
| 4 | Ingresar en el Simulador los datos de entrada indicados | Temp. Exterior (°C) = 20.4<br>Humedad Ext. (HR %) = 78.0<br>Temp. UMA (°C) = 22.5<br>Humedad UMA (HR %) = 50.4<br>Presión Inyección (Pa) = 100.0<br>Potencia Estimada (%) = 70.0<br>Humedad Sala Actual (HR %) = 44.7<br>Humedad Sala Objetivo (HR %) = 50.0<br>Temp. Sala (°C) = 22.4 | Los campos aceptan los valores y quedan completos |
| 5 | Dar click en "Generar Recomendación" |  | El modelo procesa y se muestra la potencia óptima recomendada para esas condiciones |

- **Postcondiciones:** Variables listas para ser tomadas por el gemelo digital.
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0010-2 — Validación de campos obligatorios en el ingreso de datos

- **Contexto:** Dado que el operador requiere ejecutar una nueva simulación para obtener la recomendación de la IA.
- **Evento:** Cuando el usuario intente iniciar el cálculo dejando vacíos uno o más parámetros críticos en el formulario de ingreso
- **Resultado esperado:** Entonces el sistema debe impedir la ejecución del modelo predictivo Y mostrar un mensaje de advertencia indicando "Por favor, llene todas las variables de operación antes de consultar al Gemelo Digital"
- **CP asociado:** CP033
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP033 — Validación de campos obligatorios en el ingreso de datos**

- **Criterio:** HU0010-2
- **Precondiciones:** Usuario logeado y ubicado en ventana "Simulador de ahorro"

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo "Simulador de Ahorro" |  | Se muestra "Simulador de Optimización Energética" con los campos de operación |
| 2 | Ingresar datos válidos en todos los campos, DEJANDO VACÍO "Humedad Sala Objetivo" | Exterior 20.4 / 78.0 · UMA 22.5 / 50.4 / 100.0 · Potencia 70.0 · Sala 44.7 / 22.4 | Campo objetivo vacío |
| 3 | Dar click en "Generar Recomendación" |  | Toast: "Por favor, llene todas las variables de operación antes de consultar al Gemelo Digital". No se ejecuta el modelo ni aparece recomendación |

- **Postcondiciones:** Variables incompletas, no pueden ser tomadas por el gemelo digital.
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)


---

### HU0011 — Visualizar la potencia del deshumidificador recomendada generada por el simulador

- **Épica:** Simulación y Soporte a la Toma de Decisiones
- **Enunciado:** Como **Supervisor** necesito **Visualizar la potencia del deshumidificador recomendada generada por el simulador**, con la finalidad de tener una línea base científica para realizar el ajuste de la variable recomendada manualmente en el HMI del propio sistema HVAC en planta.
- **Dónde buscar en el código:** Tarjeta "Potencia Recomendada IA", botones "Sí, aplicada" e "Ignorar", modal de justificación. Buscar: formato entero 0–100, toast de aplicación, escritura en Auditoría.

#### HU0011-1 — Visualización del porcentaje de potencia recomendada

- **Contexto:** En caso que el Supervisor ingrese al módulo de "Simulación"
- **Evento:** cuando complete todos los campos en el simulador adecuadamente y haga click en generar una recomendacion
- **Resultado esperado:** el sistema debe mostrar un número entero entre 0 y 100 que represente el % de Potencia Recomendada por la IA
- **➕ Aclaración:** No existe un valor "exacto" a comprobar; se verifica forma y rango: entero 0–100 [CONFIRMAR: y menor o igual a la Potencia Estimada].
- **CP asociado:** CP034
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP034 — Visualización del porcentaje de potencia recomendada**

- **Criterio:** HU0011-1
- **Precondiciones:** Estar logueado en el sistema con el rol Supervisor

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo "Simulador de Ahorro" |  | Se muestra "Simulador de Optimización Energética" con los campos de operación |
| 2 | Ingresar en el Simulador los datos de entrada indicados | Temp. Exterior (°C) = 20.4<br>Humedad Ext. (HR %) = 78.0<br>Temp. UMA (°C) = 22.5<br>Humedad UMA (HR %) = 50.4<br>Presión Inyección (Pa) = 100.0<br>Potencia Estimada (%) = 60.0<br>Humedad Sala Actual (HR %) = 44.7<br>Humedad Sala Objetivo (HR %) = 50.0<br>Temp. Sala (°C) = 22.4 | Los campos aceptan los valores y quedan completos |
| 3 | Dar click en "Generar Recomendación" |  | Tarjeta "Potencia Recomendada IA" con un número ENTERO entre 0 y 100 [CONFIRMAR: además ≤ Potencia Estimada] |

- **Postcondiciones:** Visualizar el card Potencia Recomendada IA con valor recomendado
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0011-2 — Aviso por campos vacíos al generar recomendación

- **Contexto:** En caso que el Supervisor ingrese al módulo de "Simulación"
- **Evento:** cuando no introduzca ningun campo en el simulador y haga click en generar una recomendacion
- **Resultado esperado:** el sistema debe mostrar el mensaje "Por favor, llene todas las variables de operación antes de consultar al Gemelo Digital"
- **CP asociado:** CP035
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP035 — Aviso por campos vacíos al generar recomendación**

- **Criterio:** HU0011-2
- **Precondiciones:** Estar logueado en el sistema con el rol Supervisor

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo "Simulador de Ahorro" |  | Se muestra "Simulador de Optimización Energética" con los campos de operación |
| 2 | Dejar vacíos los 9 campos del simulador |  | Todos los campos sin valor |
| 3 | Dar click en "Generar Recomendación" |  | Toast en la esquina inferior derecha: "Por favor, llene todas las variables de operación antes de consultar al Gemelo Digital" |

- **Postcondiciones:** Visualizar el mensaje en la esquina inferior derecha
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0011-3 — Confirmación y auditoría al aplicar recomendación

- **Contexto:** En caso que el Supervisor ingrese al módulo de "Simulación" y genere una recomendación
- **Evento:** cuando haga click en el boton "Sí, aplicada"
- **Resultado esperado:** el sistema debe mostrar un mensaje "Ajuste del potencia secador %. Transacción cifrada en Audit Trail." y generar un log de auditoría con información del personal en el módulo de "Auditoría"
- **➕ Aclaración:** Etiqueta del botón: "Sí, aplicada" [CONFIRMAR; aparece también como "Sí, aplicar" y "Aplicar Recomendación"]. Los toasts de CP036 y CP049 difieren del texto de este criterio [CONFIRMAR].
- **CP asociado:** CP036
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP036 — Confirmación y auditoría al aplicar recomendación**

- **Criterio:** HU0011-3
- **Precondiciones:** Estar logueado en el sistema con el rol Supervisor

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo "Simulador de Ahorro" |  | Se muestra "Simulador de Optimización Energética" con los campos de operación |
| 2 | Ingresar en el Simulador los datos de entrada indicados | Temp. Exterior (°C) = 20.4<br>Humedad Ext. (HR %) = 78.0<br>Temp. UMA (°C) = 22.5<br>Humedad UMA (HR %) = 50.4<br>Presión Inyección (Pa) = 100.0<br>Potencia Estimada (%) = 60.0<br>Humedad Sala Actual (HR %) = 44.7<br>Humedad Sala Objetivo (HR %) = 50.0<br>Temp. Sala (°C) = 22.4 | Los campos aceptan los valores y quedan completos |
| 3 | Dar click en "Generar Recomendación" |  | El sistema procesa los datos y muestra la tarjeta "Potencia Recomendada IA" con una potencia |
| 4 | Dar click en "Sí, aplicada" [CONFIRMAR etiqueta real; el original decía "Sí, aplicar"] |  | Toast verde en la esquina inferior derecha: "Ajuste del potencia secador %. Transacción cifrada en Audit Trail." [CONFIRMAR texto] |

- **Postcondiciones:** Se registra el evento en Auditoría (verificar en CP049 con un usuario Administrador o Auditor).
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0011-4 — Justificación obligatoria al ignorar recomendación

- **Contexto:** En caso que el Supervisor ingrese al módulo de "Simulación" y genere una recomendación
- **Evento:** cuando haga click en el boton "Ignorar"
- **Resultado esperado:** el sistema debe mostrar el diálogo pidiendo una justificación obligatoria. Escribe una justificación y confírmala; luego revisa en el módulo de Auditoría que haya quedado registrada esa acción.
- **➕ Aclaración:** Redactado como instrucción de prueba. Resultado verificable: el modal exige justificación; al confirmar con texto válido queda un registro en Auditoría (usuario, fecha/hora, justificación); al cancelar no se registra nada.
- **CP asociado:** CP037
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP037 — Justificación obligatoria al ignorar recomendación**

- **Criterio:** HU0011-4
- **Precondiciones:** Estar logueado en el sistema con el rol Supervisor

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo "Simulador de Ahorro" |  | Se muestra "Simulador de Optimización Energética" con los campos de operación |
| 2 | Ingresar en el Simulador los datos de entrada indicados | Temp. Exterior (°C) = 20.4<br>Humedad Ext. (HR %) = 78.0<br>Temp. UMA (°C) = 22.5<br>Humedad UMA (HR %) = 50.4<br>Presión Inyección (Pa) = 100.0<br>Potencia Estimada (%) = 70.0<br>Humedad Sala Actual (HR %) = 44.7<br>Humedad Sala Objetivo (HR %) = 50.0<br>Temp. Sala (°C) = 22.4 | Los campos aceptan los valores y quedan completos |
| 3 | Dar click en "Generar Recomendación" |  | El sistema procesa los datos y muestra la tarjeta "Potencia Recomendada IA" con una potencia |
| 4 | Dar click en "Ignorar" |  | Se muestra el modal de justificación técnica obligatoria |
| 5 | Ingresar la justificación y pulsar "Confirmar descarte" | Esta es una prueba de justificación | Se confirma el descarte y queda registrado en Auditoría (verificar con Administrador o Auditor) |

- **Postcondiciones:** Probar también "Cancelar" en el modal: se cierra sin registrar nada.
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)


---

### HU0012 — consultar el ahorro energético estimado (kW)

- **Épica:** Monitoreo de Eficiencia Energética y Ahorro Económico
- **Enunciado:** Como **Supervisor** necesito **consultar el ahorro energético estimado (kW)**, con la finalidad de entender el beneficio inmediato de aplicar la sugerencia del simulador.
- **Dónde buscar en el código:** Flujo de decisión del Simulador (aplicar / ignorar con justificación): validación de longitud mínima, estado guardado en BD, que NO se escriba nada si la justificación es inválida.

#### HU0012-1 — El Supervisor aplica exitosamente la recomendación del modelo

- **Contexto:** Dado que el Gemelo Digital ha sugerido reducir la potencia Y el Supervisor valida que el entorno físico es seguro para el ajuste
- **Evento:** Cuando el usuario haga clic en "Aplicar Recomendación"
- **Resultado esperado:** Entonces el sistema registrará la decisión con el estado" Operación Exitosa"
- **➕ Aclaración:** El ahorro en kW/kWh se ve en el Dashboard (HU0013–HU0015), no en este flujo. Estado guardado: aplicada.
- **CP asociado:** CP038
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP038 — El Supervisor aplica exitosamente la recomendación del modelo**

- **Criterio:** HU0012-1
- **Precondiciones:** Estar logueado en el sistema con el rol Supervisor

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo "Simulador de Ahorro" |  | Se muestra "Simulador de Optimización Energética" con los campos de operación |
| 2 | Ingresar en el Simulador los datos de entrada indicados | Temp. Exterior (°C) = 20.4<br>Humedad Ext. (HR %) = 78.0<br>Temp. UMA (°C) = 22.5<br>Humedad UMA (HR %) = 50.4<br>Presión Inyección (Pa) = 100.0<br>Potencia Estimada (%) = 60.0<br>Humedad Sala Actual (HR %) = 44.7<br>Humedad Sala Objetivo (HR %) = 50.0<br>Temp. Sala (°C) = 22.4 | Los campos aceptan los valores y quedan completos |
| 3 | Dar click en "Generar Recomendación" |  | El sistema procesa los datos y muestra la tarjeta "Potencia Recomendada IA" con una potencia |
| 4 | Dar click en "Sí, aplicada" |  | Se muestra un mensaje de éxito |
| 5 | Ingresar al módulo "Dashboard" |  | Sistema recopilando información |
| 6 | Visualizar la sección "Diferencial Energético" |  | El gráfico se actualiza con la última recomendación aplicada |

- **Postcondiciones:** El Dashboard refleja la recomendación aplicada.
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0012-2 — El Supervisor descarta la recomendación e ingresa una justificación

- **Contexto:** Dado que el Gemelo Digital sugiere un ajuste, pero el Supervisor identifica un riesgo operativo
- **Evento:** Cuando el usuario seleccione "Ignorar Recomendación"  Y complete el campo obligatorio de justificación técnica
- **Resultado esperado:** Entonces el sistema registrará la acción con el estado: Operación Exitosa Descarte operativo registrado con éxito junto a su sustento técnico.
- **➕ Aclaración:** Al descartar se registra el descarte con su justificación [CONFIRMAR estado guardado en BD; "Operación Exitosa" describe la transacción].
- **CP asociado:** CP039
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP039 — El Supervisor descarta la recomendación e ingresa una justificación**

- **Criterio:** HU0012-2
- **Precondiciones:** Supervisor autenticado. Tomar captura del Dashboard (sección "Diferencial Energético") ANTES de iniciar.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo de Simulador |  | Se muestra el simulador con campos de operación |
| 2 | Ingresar en el Simulador los datos de entrada indicados | Temp. Exterior (°C) = 20.4<br>Humedad Ext. (HR %) = 78.0<br>Temp. UMA (°C) = 22.5<br>Humedad UMA (HR %) = 50.4<br>Presión Inyección (Pa) = 100.0<br>Potencia Estimada (%) = 70.0<br>Humedad Sala Actual (HR %) = 44.7<br>Humedad Sala Objetivo (HR %) = 50.0<br>Temp. Sala (°C) = 22.4 | Los campos aceptan los valores y quedan completos |
| 3 | Dar click en "Generar Recomendación" |  | El sistema procesa los datos y recomienda una potencia |
| 4 | Dar click en "Ignorar" |  | Se muestra modal de justificación |
| 5 | Ingresar Justificación Técnica Obligatoria | Esta es una prueba de justificación |  |
| 6 | Dar click en "Confirmar descarte" |  | Se muestra el mensaje "Descarte operativo registrado con éxito junto a su sustento técnico." |
| 7 | Ingresar al módulo de Dashboard |  | Visualizar cards |
| 8 | Visualizar la sección "Diferencial Energético<br>" |  | Sin modificaciones |

- **Postcondiciones:** Card debe mantenerse con el último valor de recomendación "APLICADA"
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0012-3 — Bloqueo del sistema ante falta de justificación técnica (Validación GxP)

- **Contexto:** Dado que el Supervisor decide ignorar la sugerencia de la IA
- **Evento:** Cuando intente guardar la decisión dejando el campo de justificación vacío o con un texto insuficiente
- **Resultado esperado:** Entonces la interfaz de usuario bloqueará la transacción. No se ejecutará ninguna escritura en la base de datos de simulaciones ni de auditoría, y se emitirá una alerta visual indicando que la normativa GxP exige un sustento técnico obligatorio
- **➕ Aclaración:** "Texto insuficiente" = menos de 10 caracteres [CONFIRMAR mínimo real].
- **CP asociado:** CP058
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP058 — Bloqueo del sistema ante falta de justificación técnica (Validación GxP)**

- **Criterio:** HU0012-3
- **Precondiciones:** -El usuario ha iniciado sesión con el rol de Supervisor.<br>-El usuario se encuentra en el módulo del Simulador de Ahorro, habiendo generado previamente una recomendación predictiva por parte del Gemelo Digital.<br>- El Supervisor ha seleccionado la opción de "Ignorar Recomendación", abriéndose el modal o campo de descarte operativo.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Interactuar con la interfaz del simulador tras recibir la sugerencia de la IA y hacer clic en el botón "IGNORAR". |  | El sistema despliega el componente o modal de justificación técnica obligatorio para registrar el desvío. |
| 2 | Intentar confirmar el descarte de la recomendación dejando el campo de justificación totalmente vacío o ingresando un texto insuficiente (ej. "n/a" o menos de 10 caracteres). | Texto vacío "" o "prueba" (menos de 10 caracteres) [CONFIRMAR mínimo] | La interfaz de usuario detecta el incumplimiento de la longitud mínima requerida por la directiva GxP. |
| 3 | Hacer clic en el botón de confirmación de descarte (ej. "Confirmar Descarte"). | Acción de envío de formulario con datos incompletos. | El sistema bloquea de inmediato la transacción y no permite procesar el formulario de registro. |
| 4 | Comprobar el comportamiento del sistema a nivel de base de datos y respuesta visual en pantalla. |  | Se emite una alerta visual clara indicando que la normativa GxP exige un sustento técnico obligatorio. Ningún dato es escrito en la base de datos de simulaciones ni en la pista de auditoría. |

- **Postcondiciones:** El estado de la simulación se mantiene en pausa y el modal de justificación permanece abierto en la interfaz, permitiendo al usuario corregir el texto e ingresar un sustento válido para reintentar la operación.
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)


---

### HU0013 — visualizar una gráfica comparativa de escenarios ("Estimado" vs "Recomendado")

- **Épica:** Monitoreo de Eficiencia Energética y Ahorro Económico
- **Enunciado:** Como **Supervisor** necesito **visualizar una gráfica comparativa de escenarios ("Estimado" vs "Recomendado")**, con la finalidad de analizar las tendencias de las recomendaciones ..
- **Dónde buscar en el código:** Dashboard: gráfica de líneas "Estimada vs Recomendada" (secciones "Diferencial Energético" / "Auditoría Estacionaria: Consumo Real vs. Recomendación IA"). Buscar: ventana de 24 registros, solo decisiones aplicadas, estado vacío inicial.

#### HU0013-1 — Gráfica comparativa Estimado vs Recomendado

- **Contexto:** En caso que el usuario haya aplicado una recomendación
- **Evento:** cuando ingrese al módulo de Dashboard
- **Resultado esperado:** el sistema debe mostrar una gráfica de líneas con dos curvas de potencia (Estimada vs. Recomendada) para un horizonte de tiempo determinado.
- **➕ Aclaración:** Horizonte = últimas 24 simulaciones aplicadas [CONFIRMAR]. "Estimada" = potencia ingresada; "Recomendada" = salida del modelo. Nombre de sección en pantalla [CONFIRMAR: "Diferencial Energético" o "Auditoría Estacionaria: Consumo Real vs. Recomendación IA"].
- **CP asociado:** CP040
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP040 — Gráfica comparativa Estimado vs Recomendado**

- **Criterio:** HU0013-1
- **Precondiciones:** Administrador autenticado.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo de Simulador |  | Se muestra el simulador con campos de operación |
| 2 | Ingresar en el Simulador los datos de entrada indicados | Temp. Exterior (°C) = 20.4<br>Humedad Ext. (HR %) = 78.0<br>Temp. UMA (°C) = 22.5<br>Humedad UMA (HR %) = 50.4<br>Presión Inyección (Pa) = 100.0<br>Potencia Estimada (%) = 70.0<br>Humedad Sala Actual (HR %) = 44.7<br>Humedad Sala Objetivo (HR %) = 50.0<br>Temp. Sala (°C) = 22.4 | Los campos aceptan los valores y quedan completos |
| 3 | Dar click en "Generar Recomendación" |  | El sistema procesa los datos y recomienda una potencia |
| 4 | Dar click en "Sí, aplicar" |  | Se muestra un mensaje de exito |
| 5 | Ingresar al módulo de Dashboard |  | Sistema recopilando información |
| 6 | Visualizar la sección "Auditoría Estacionaria: Consumo Real vs. Recomendación IA" |  | Gráfico cargado correctamente con la ultima recomendación aplicada |

- **Postcondiciones:** Gráfico cargado correctamente
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0013-2 — Sin actualización de gráfica sin recomendación aplicada

- **Contexto:** En caso que el usuario no haya aplicado una recomendación
- **Evento:** cuando ingrese al módulo de Dashboard
- **Resultado esperado:** Entonces si el usuario no ha aplicado una recomendación, el sistema no sumará ese evento al registro y la gráfica no se actualizará. Adicionalmente, como estado inicial, si todavía no existe ninguna recomendación aplicada previamente en toda la planta, el componente gráfico se renderizará en su estado vacío y los indicadores económicos partirán desde cero (0) hasta que se registre el primer diferencial
- **➕ Aclaración:** Tomar captura de la gráfica antes de la prueba; debe quedar igual tras "Ignorar".
- **CP asociado:** CP041
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP041 — Sin actualización de gráfica sin recomendación aplicada**

- **Criterio:** HU0013-2
- **Precondiciones:** Administrador autenticado. Tomar captura de la sección "Auditoría Estacionaria: Consumo Real vs. Recomendación IA" ANTES de iniciar.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo de Simulador |  | Se muestra el simulador con campos de operación |
| 2 | Ingresar en el Simulador los datos de entrada indicados | Temp. Exterior (°C) = 20.4<br>Humedad Ext. (HR %) = 78.0<br>Temp. UMA (°C) = 22.5<br>Humedad UMA (HR %) = 50.4<br>Presión Inyección (Pa) = 100.0<br>Potencia Estimada (%) = 70.0<br>Humedad Sala Actual (HR %) = 44.7<br>Humedad Sala Objetivo (HR %) = 50.0<br>Temp. Sala (°C) = 22.4 | Los campos aceptan los valores y quedan completos |
| 3 | Dar click en "Generar Recomendación" |  | El sistema procesa los datos y recomienda una potencia |
| 4 | Dar click en "Ignorar" |  | Se muestra modal de justificación |
| 5 | Ingresar Justificación Técnica Obligatoria | Esta es una prueba de justificación |  |
| 6 | Dar click en "Confirmar descarte" |  | Se muestra el mensaje "Descarte operativo registrado con éxito junto a su sustento técnico." |
| 7 | Ingresar al módulo de Dashboard |  | Visualizar cards |
| 8 | Visualizar la sección "Auditoría Estacionaria: Consumo Real vs. Recomendación IA" |  | Sin modificaciones |

- **Postcondiciones:** Sin modificaciones en la sección "Auditoría Estacionaria: Consumo Real vs. Recomendación IA"
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)


---

### HU0014 — visualizar un dashboard con información de ahorro económico en USD acumulado

- **Épica:** Monitoreo de Eficiencia Energética y Ahorro Económico
- **Enunciado:** Como **Gerente** necesito **visualizar un dashboard con información de ahorro económico en USD acumulado**, con la finalidad de cuantificar y estimar el ahorro monetario por cada recomendación aplicada que se haya registrado en el sistema.
- **Dónde buscar en el código:** Dashboard: tarjeta "Ahorro Potencial". Buscar: fórmula (diferencia de potencia × factor de conversión kWh × tarifa), acumulador solo con exceso positivo, ventana de 24 registros.

#### HU0014-1 — Cálculo de ahorro cuando el operador excede la potencia recomendada

- **Contexto:** Dado que el sistema tiene un registro de las últimas 24 simulaciones en el backend y en una o más de esas simulaciones, la potencia aplicada por el operador fue mayor a la recomendada por la IA
- **Evento:** Cuando el usuario visualice la tarjeta de "Ahorro Potencial" en el Dashboard
- **Resultado esperado:** Entonces el sistema debe calcular la diferencia porcentual acumulada, multiplicarla por el factor de conversión a energía (kWh) y multiplicarla por la tarifa configurada (ej. $0.15) y mostrar el monto final en dólares ($) como oportunidad de ahorro
- **➕ Aclaración:** Fórmula: Ahorro (USD) = Σ máx(0, Potencia estimada − Potencia recomendada) × factor de conversión × tarifa. Ejemplo: 80 % vs 60 % → 20 × 1.5 × 0.15 = $4.50 [CONFIRMAR factor y su origen].
- **CP asociado:** CP042
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP042 — Cálculo de ahorro cuando el operador excede la potencia recomendada**

- **Criterio:** HU0014-1
- **Precondiciones:** - El usuario ha iniciado sesión con un rol autorizado (ej. Gerente o Administrador) y se encuentra visualizando el panel del Dashboard.<br>- El factor de conversión a energía (kWh) y la tarifa eléctrica por defecto (ej. $0.15 USD / kWh) se encuentran configurados en el sistema.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Acceder al módulo del Dashboard de la aplicación web con un rol gerencial o administrativo. |  | La interfaz carga de manera correcta el panel principal del Dashboard y conecta con el servicio de analítica. |
| 2 | Verificar el registro de las últimas simulaciones almacenadas en el backend (ventana de hasta 24 registros) | Simulación de prueba: Potencia aplicada = 80%, Potencia recomendada = 60% (Diferencial porcentual = 20%). | El sistema identifica correctamente los eventos de sobreconsumo donde el operador no siguió la recomendación óptima. |
| 3 | Visualizar la tarjeta de "Ahorro Potencial" y el cuadro de dinero correspondiente en el Dashboard. | Potencia aplicada = 80 %, recomendada = 60 % (diferencial 20 puntos). Factor de conversión = 1.5 [CONFIRMAR origen]. Tarifa = $0.15 USD/kWh | El sistema procesa la diferencia porcentual acumulada, aplica el factor de conversión a energía (kWh) y multiplica por la tarifa. |
| 4 | Comprobar el monto monetario final reflejado en pantalla como oportunidad de ahorro. |  | El monto mostrado es $4.50 (20 × 1.5 × 0.15) |

- **Postcondiciones:** El cuadro de dinero muestra de forma exacta el monto total calculado en dólares ($), reflejando correctamente la oportunidad de ahorro por el exceso de energía.
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0014-2 — Comportamiento del cálculo cuando el operador sigue o mejora la recomendación de la IA

- **Contexto:** Dado que el sistema evalúa una nueva simulación dentro de la ventana de 24 registros y la potencia aplicada por el operador es igual o menor a la potencia óptima recomendada
- **Evento:** Cuando el servicio de analítica procese los datos para el diferencial
- **Resultado esperado:** Entonces esa simulación específica no sumará ningún valor al acumulador de exceso de energía (diferencial = 0 para ese registro) y el cuadro de ahorro económico se mantendrá sin incrementar por dicha simulación
- **➕ Aclaración:** "Potencia aplicada" es la potencia base ingresada. Si es menor o igual a la recomendada, el aporte es 0.
- **CP asociado:** CP043
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP043 — Comportamiento del cálculo cuando el operador sigue o mejora la recomendación de la IA**

- **Criterio:** HU0014-2
- **Precondiciones:** Administrador autenticado. Tomar captura del card "Ahorro Potencial" ANTES de iniciar.
- **Nota:** El CP original probaba "Ignorar", que corresponde a HU0013-2. Aquí se prueba HU0014-2.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo "Simulador de Ahorro" |  | Se muestra "Simulador de Optimización Energética" con los campos de operación |
| 2 | Ingresar en el Simulador los datos de entrada indicados | Temp. Exterior (°C) = 20.4<br>Humedad Ext. (HR %) = 78.0<br>Temp. UMA (°C) = 22.5<br>Humedad UMA (HR %) = 50.4<br>Presión Inyección (Pa) = 100.0<br>Potencia Estimada (%) = 70.0<br>Humedad Sala Actual (HR %) = 44.7<br>Humedad Sala Objetivo (HR %) = 50.0<br>Temp. Sala (°C) = 22.4 | Los campos aceptan los valores y quedan completos |
| 3 | Dar click en "Generar Recomendación" |  | El sistema procesa los datos y muestra la tarjeta "Potencia Recomendada IA" con una potencia |
| 4 | Dar click en "Sí, aplicada" en un caso donde la Potencia Recomendada sea IGUAL o MAYOR a la Potencia Estimada (sin exceso) [CONFIRMAR dato de entrada que lo produzca] |  | Se confirma la decisión |
| 5 | Ingresar al módulo "Dashboard" y visualizar el card "Ahorro Potencial" |  | El monto NO se incrementa respecto a la captura (diferencial = 0 para esa simulación) |

- **Postcondiciones:** Sin modificaciones en el card "Ahorro Potencial"
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0014-3 — Actualización dinámica del costo de la tarifa eléctrica

- **Contexto:** Dado que el Dashboard muestra un "Ahorro Potencial" calculado en base a una tarifa eléctrica por defecto (ej. $0.15 USD / kWh)
- **Evento:** Cuando el usuario modifique el valor del costo por kWh a una nueva tarifa en la interfaz de configuración del panel
- **Resultado esperado:** Entonces la aplicación debe recalcular inmediatamente el monto de dinero mostrado Y el nuevo valor debe ser el resultado de multiplicar el total de kWh desperdiciados por la nueva tarifa ingresada
- **➕ Aclaración:** Ej.: 15 kWh × 0.15 = $2.25; con tarifa 0.20 → $3.00.
- **CP asociado:** CP059
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP059 — Actualización dinámica del costo de la tarifa eléctrica**

- **Criterio:** HU0014-3
- **Precondiciones:** -El usuario ha iniciado sesión con un rol autorizado (ej. Administrador o Gerente) y se encuentra visualizando el panel del Dashboard<br>-El sistema cuenta con al menos un registro previo de simulaciones donde el operador haya aplicado una potencia mayor a la recomendada por la IA (generando un acumulado de diferencial de kWh mayor a cero)<br>-El costo por kWh por defecto se encuentra configurado en un valor base conocido (ej. $0.15 USD)

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ubicarse en el módulo del Dashboard de la aplicación web |  | El módulo del Dashboard carga correctamente y muestra las tarjetas de KPIs y la gráfica analítica. |
| 2 | Visualizar el valor numérico actual de la tarjeta de "Ahorro Potencial" en dólares ($) | Diferencial energético acumulado actual: 15.0 kWh. Tarifa por defecto: $0.15 USD / kWh | El sistema muestra el monto calculado inicial en la tarjeta (ej. $2.25 USD). |
| 3 | Dirigirse al panel lateral o sección de Configuración de Costos provisto en la interfaz del Dashboard. |  | El campo de configuración de costos está visible, activo y listo para recibir modificaciones numéricas. |
| 4 | Modificar el campo numérico del costo por kWh ingresando una nueva tarifa de prueba (ej. cambiar de $0.15 a $0.20) | Nuevo valor = 0.20 | La interfaz web acepta el cambio del número de manera fluida y sin restricciones de caracteres no numéricos. |
| 5 | Observar inmediatamente el comportamiento visual de la tarjeta de "Ahorro Potencial" sin necesidad de recargar la página web completa |  | La tarjeta de "Ahorro Potencial" se actualiza dinámicamente de forma instantánea reflejando el nuevo valor correcto |

- **Postcondiciones:** El cuadro de ahorro monetario se mantiene actualizado en el panel analítico basándose en el comportamiento operativo reciente de la planta.
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)


---

### HU0015 — modificar manualmente el costo de kWh en el panel de dashboard

- **Épica:** Monitoreo de Eficiencia Energética y Ahorro Económico
- **Enunciado:** Como **Gerente** necesito **modificar manualmente el costo de kWh en el panel de dashboard**, con la finalidad de recalcular automáticamente el ahorro del periodo basado en los kWh detectados como sobreconsumo por el Gemelo Digital..
- **Dónde buscar en el código:** Dashboard: "Configuración de Costos" (costo por kWh). Buscar: recálculo inmediato, validación de positivos, permisos por rol.

#### HU0015-1 — Cálculo del ahorro potencial según costo de kWh

- **Contexto:** En caso que el Gerente acceda al Dashboard
- **Evento:** cuando modifique manualmente el costo de kWh en el panel de dashboard
- **Resultado esperado:** el sistema debe multiplicar los kW ahorrados por el costo de kWh configurado para actualizar el ahorro monetario
- **➕ Aclaración:** El criterio dice "kW"; el cálculo es en kWh [CONFIRMAR].
- **CP asociado:** CP044
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP044 — Cálculo del ahorro potencial según costo de kWh**

- **Criterio:** HU0015-1
- **Precondiciones:** Gerente autenticado. Existe un Diferencial Energético mayor a 0.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo de Dashboard |  | Se carga resultados de datos procesados de los demás módulos |
| 2 | Visualizar la sección "Configuración de Costos" |  | ComboNumerico dinámico configurable |
| 3 | Ingresar valor de costo | 5.0 |  |
| 4 | Visualizar el card "Ahorro Potencial" |  | El monto pasa a ser (kWh acumulados × 5.00) sin recargar la página |

- **Postcondiciones:** Nuevo valor actualizado en el card "Ahorro Potencial"
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0015-2 — Validación de valores positivos para costo de kWh

- **Contexto:** En caso que el Gerente acceda al Dashboard
- **Evento:** cuando modifique manualmente el costo de kWh en el panel de dashboard
- **Resultado esperado:** el sistema solo debe permitir valores numéricos positivos
- **➕ Aclaración:** Positivos: mayores que 0, decimales con punto; sin "-", letras ni vacío [CONFIRMAR si 0 es válido]. La HU es del Gerente.
- **CP asociado:** CP045
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP045 — Validación de valores positivos para costo de kWh**

- **Criterio:** HU0015-2
- **Precondiciones:** Gerente autenticado.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo "Dashboard" |  | Se cargan los resultados de los demás módulos |
| 2 | Ubicar la sección "Configuración de Costos" |  | Campo numérico configurable |
| 3 | Ingresar costo | -5.0 | No permite escribir el signo "-" |
| 4 | Ingresar costo | abc | No permite letras |
| 5 | Dejar el campo vacío y observar el card "Ahorro Potencial" |  | El monto no cambia a un valor inválido (no NaN ni negativo) |
| 6 | Ingresar costo | 0 | [CONFIRMAR si 0 es válido] |

- **Postcondiciones:** Solo debe permitir valores positivos
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)


---

### HU0016 — visualizar una gráficas de firma térmica (humedad vs potencia)

- **Épica:** Monitoreo de Eficiencia Energética y Ahorro Económico
- **Enunciado:** Como **Supervisor** necesito **visualizar una gráficas de firma térmica (humedad vs potencia)**, con la finalidad de entender la relación o comportamiento de humedad de sala y potencia histórica en estado estacionario de los datos históricos.
- **Dónde buscar en el código:** Dashboard: gráfica de dispersión "Firma Térmica" (X = humedad de sala, Y = potencia). Buscar: origen de datos estacionarios y ejes/unidades.

#### HU0016-1 — Gráfica de dispersión Humedad vs Potencia

- **Contexto:** En caso que el Supervisor acceda al Dashboard
- **Evento:** cuando el panel de resultados termine de cargar completamente
- **Resultado esperado:** El sistema debe generar una gráfica de dispersión que represente la "Firma Térmica" del modelo. Esta gráfica relacionará directamente la variable de "Humedad de Sala" en el eje X (abscisas) contra la "Potencia del Secador" en el eje Y (ordenadas), utilizando los puntos de datos estacionarios históricos almacenados en el sistema
- **➕ Aclaración:** Unidad del eje X [CONFIRMAR: g/kg o %HR]. Eje Y: potencia en %. Debe verse tendencia descendente. Con datos vacíos, gráfica vacía sin error.
- **CP asociado:** CP046
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP046 — Gráfica de dispersión Humedad vs Potencia**

- **Criterio:** HU0016-1
- **Precondiciones:** Estar logueado en el sistema con el rol Supervisor
- **Nota:** Unidad del eje X (g/kg o %HR) [CONFIRMAR].

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo de Dashboard |  | Se carga resultados de datos procesados de los demás módulos |
| 2 | Visualizar la sección "Firma Térmica: Relación Histórica Humedad vs Potencia" |  | Gráfica de dispersión o de dos ejes donde se crucen la relación de "Humedad" frente al "Potencia del deshumidificador". |

- **Postcondiciones:** Gráfica de dispersión de potencia vs humedad
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)


---

### HU0017 — recibir una alerta visual de "Alerta de Riesgo GMP"

- **Épica:** Trazabilidad y Cumplimiento de Estándares Farmacéuticos
- **Enunciado:** Como **Supervisor** necesito **recibir una alerta visual de "Alerta de Riesgo GMP"**, con la finalidad de identificar cuándo un setpoint de humedad de sala es físicamente inalcanzable con baja potencia con riesgo a incumplimiento.
- **Dónde buscar en el código:** Simulador: alerta "Alerta de Riesgo GMP". Buscar: comparación contra los límites guardados en HU0004, regla exacta que dispara la alerta y su texto.

#### HU0017-1 — Alerta de riesgo GMP por recomendación fuera de límites

- **Contexto:** En caso que el Supervisor acceda al módulo de Simulador
- **Evento:** cuando se genere una recomendación fuera de los rangos Límites de Seguridad configurados en el panel de reentrenamiento
- **Resultado esperado:** el sistema debe garantizar debe mostrar una alerta visual "Alerta de Riesgo GMP El setpoint solicitado, o las condiciones de humedad logradas por el modelo, apuntan a una violación del marco regulatorio estricto de la sala"
- **➕ Aclaración:** Probar con límites guardados Mín 30 / Máx 40 y objetivo 50 → fuera de límites → alerta. Texto: "Alerta de Riesgo GMP". [CONFIRMAR regla exacta que dispara la alerta]
- **CP asociado:** CP047
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP047 — Alerta de riesgo GMP por recomendación fuera de límites**

- **Criterio:** HU0017-1
- **Precondiciones:** Administrador autenticado. En "Entrenamiento IA" haber guardado límites GMP: Mínimo = 30 y Máximo = 40.
- **Nota:** Mismos datos de CP048; solo cambian los límites guardados.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo "Simulador de Ahorro" |  | Se muestra "Simulador de Optimización Energética" con los campos de operación |
| 2 | Ingresar en el Simulador los datos de entrada indicados | Temp. Exterior (°C) = 20.4<br>Humedad Ext. (HR %) = 78.0<br>Temp. UMA (°C) = 22.5<br>Humedad UMA (HR %) = 50.4<br>Presión Inyección (Pa) = 100.0<br>Potencia Estimada (%) = 70.0<br>Humedad Sala Actual (HR %) = 44.7<br>Humedad Sala Objetivo (HR %) = 50.0<br>Temp. Sala (°C) = 22.4 | Los campos aceptan los valores y quedan completos |
| 3 | Dar click en "Generar Recomendación" |  | El sistema procesa los datos y muestra la tarjeta "Potencia Recomendada IA" con una potencia |
| 4 | Visualizar la alerta |  | Se muestra la recomendación y la alerta "Alerta de Riesgo GMP — El setpoint solicitado, o las condiciones de humedad logradas por el modelo, apuntan a una violación del marco regulatorio estricto de la sala". (El CP original decía "Alerta de incumplimiento" [CONFIRMAR texto real]) |

- **Postcondiciones:** Se muestra la alerta "Alerta de Riesgo GMP" junto a la recomendación.
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0017-2 — Sin alerta cuando la recomendación está dentro de límites

- **Contexto:** En caso que el Supervisor acceda al módulo de Simulador
- **Evento:** cuando se genere una recomendación dentro de los rangos Límites de Seguridad configurados en el panel de reentrenamiento
- **Resultado esperado:** el sistema no debe mostrar la alerta de límites
- **➕ Aclaración:** Probar con límites Mín 30 / Máx 60 y el mismo formulario → sin alerta.
- **CP asociado:** CP048
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP048 — Sin alerta cuando la recomendación está dentro de límites**

- **Criterio:** HU0017-2
- **Precondiciones:** Administrador autenticado. En "Entrenamiento IA" haber guardado límites GMP: Mínimo = 30 y Máximo = 60.
- **Nota:** Mismos datos de CP047; solo cambian los límites guardados.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo "Simulador de Ahorro" |  | Se muestra "Simulador de Optimización Energética" con los campos de operación |
| 2 | Ingresar en el Simulador los datos de entrada indicados | Temp. Exterior (°C) = 20.4<br>Humedad Ext. (HR %) = 78.0<br>Temp. UMA (°C) = 22.5<br>Humedad UMA (HR %) = 50.4<br>Presión Inyección (Pa) = 100.0<br>Potencia Estimada (%) = 70.0<br>Humedad Sala Actual (HR %) = 44.7<br>Humedad Sala Objetivo (HR %) = 50.0<br>Temp. Sala (°C) = 22.4 | Los campos aceptan los valores y quedan completos |
| 3 | Dar click en "Generar Recomendación" |  | El sistema procesa los datos y muestra la tarjeta "Potencia Recomendada IA" con una potencia |
| 4 | Visualizar la recomendación |  | Se muestra la recomendación y NO aparece la alerta de riesgo GMP |

- **Postcondiciones:** No se muestra la alerta de riesgo GMP.
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)


---

### HU0018 — registrar los eventos relevantes que los usuarios realicen dentro del sistema

- **Épica:** Trazabilidad y Cumplimiento de Estándares Farmacéuticos
- **Enunciado:** Como **Auditor** necesito **registrar los eventos relevantes que los usuarios realicen dentro del sistema**, con la finalidad de mantener un historial de la interacción humana con el sistema de soporte ante temas de auditoría..
- **Dónde buscar en el código:** Servicio de auditoría: eventos RECOMMENDATION_APPLIED/IGNORED, USER_*, GMP_LIMITS_UPDATE, ML_MODEL_PROMOTED. Buscar: tabla inmutable (sin UPDATE/DELETE), fecha de servidor, usuario, metadata.

#### HU0018-1 — Registro de auditoría por recomendación aplicada o ignorada

- **Contexto:** En caso que un usuario acceda al módulo de Simulador
- **Evento:** cuando se ejecute el evento de recomendación aplicada o ignorada
- **Resultado esperado:** el sistema debe registrar la acción el módulo de Auditoría.
- **➕ Aclaración:** El Auditor no registra: consulta lo que el sistema registra automáticamente.
- **CP asociado:** CP049
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP049 — Registro de auditoría por recomendación aplicada o ignorada**

- **Criterio:** HU0018-1
- **Precondiciones:** Estar logueado en el sistema con el rol Administrador

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo de Simulador |  | Se muestra el simulador con campos de operación |
| 2 | Ingresar en el Simulador los datos de entrada indicados | Temp. Exterior (°C) = 20.4<br>Humedad Ext. (HR %) = 78.0<br>Temp. UMA (°C) = 22.5<br>Humedad UMA (HR %) = 50.4<br>Presión Inyección (Pa) = 100.0<br>Potencia Estimada (%) = 70.0<br>Humedad Sala Actual (HR %) = 44.7<br>Humedad Sala Objetivo (HR %) = 50.0<br>Temp. Sala (°C) = 22.4 | Los campos aceptan los valores y quedan completos |
| 3 | Dar click en "Generar Recomendación" |  | El sistema procesa los datos y recomienda una potencia |
| 4 | Dar click en "Sí, aplicada" |  | Se muestra el mensaje "Recomendación Aplicada" |
| 5 | Ingresar al Módulo de Auditoría |  | Se muestra la pantalla con el Tab de Usuarios activo |
| 6 | Dar click en el Tab Audit Trail |  | Registros de auditoría del sistema |
| 7 | Visualizar un nuevo registro |  | Registro nuevo con fecha registrada con título RECOMMENDATION_APPLIED<br> y metadata relacionada al evento |

- **Postcondiciones:** Nuevo registro de recomendación aplicada en el Módulo de Auditoría - Audit Trail
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0018-2 — Registro de auditoría por gestión de usuarios

- **Contexto:** En caso que un usuario acceda al módulo de Usuarios
- **Evento:** cuando registre, edite o elimine un usuario
- **Resultado esperado:** el sistema debe registrar la acción el módulo de Auditoría.
- **➕ Aclaración:** "Elimine" equivale a "Revocar". Eventos: USER_CREATED / USER_UPDATED / USER_DELETED [CONFIRMAR nombres].
- **CP asociado:** CP050
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP050 — Registro de auditoría por gestión de usuarios**

- **Criterio:** HU0018-2
- **Precondiciones:** Estar logueado en el sistema con el rol Administrador
- **Nota:** Repetir para editar (USER_UPDATED) y revocar (USER_DELETED) [CONFIRMAR nombres de evento]. El mensaje del toast puede incluir el username: "Nueva identidad GxP [Pepito123] dada de alta en el sistema." [CONFIRMAR].

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al Módulo de Auditoría |  | Se muestra la pantalla con el Tab de Usuarios activo |
| 2 | Dar click en Nuevo Registro |  | Abrir Modal de Nuevo Registro |
| 3 | Ingresar Nombre Completo | Usuario Test |  |
| 4 | Ingresar Nombre de Usuario | Pepito123 |  |
| 5 | Seleccionar Rol | Supervisor |  |
| 6 | Ingresar Contraseña | 12345678.0 |  |
| 7 | Dar clic en "Crear Identidad GXP" |  | Se muestra mensaje "Nueva identidad GxP [Pepito123] dada de alta en el sistema." |
| 8 | Dar click en el Tab Audit Trail |  | Registros de auditoría del sistema |
| 9 | Visualizar un nuevo registro |  | Registro nuevo con fecha y tipo USER_CREATED (el original decía "HUER_CREATED", error de tipeo) y metadata del evento |

- **Postcondiciones:** Nuevo registro de usuarios en el Módulo de Auditoría - Audit Trail
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0018-3 — Registro de auditoría por actualización de límites de seguridad

- **Contexto:** En caso que un usuario acceda al módulo de Reentrenamiento IA
- **Evento:** cuando guarde nuevos limites de seguridad
- **Resultado esperado:** el sistema debe registrar la acción el módulo de Auditoría.
- **➕ Aclaración:** Evento GMP_LIMITS_UPDATE. "Reentrenamiento IA" = módulo "Entrenamiento IA".
- **CP asociado:** CP051
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP051 — Registro de auditoría por actualización de límites de seguridad**

- **Criterio:** HU0018-3
- **Precondiciones:** Estar logueado en el sistema con el rol Administrador y tener datos cargados previamente en el Módulo de Ingesta de datos

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al Módulo Entrenamiento |  | Pantalla con sección de Limites de Seguridad |
| 2 | Ingresar nuevo valor de Humedad Mínima | 40.0 |  |
| 3 | Ingresar nuevo valor de Humedad Máxima | 60.0 |  |
| 4 | Dar click en el botón Guardar Límites |  | Mensaje "Umbrales regulatorios actualizados. Cambio firmado en la pista de auditoría" |
| 5 | Ingresar al Módulo Auditoría |  | Pantalla con Tab Audit Trail y Usuarios |
| 6 | Dar click en el Tab Audit Trail |  | Registros de auditoría del sistema |
| 7 | Visualizar un nuevo registro |  | Registro nuevo con fecha registrada con título GMP_LIMITS_UPDATE y metadata relacionada al evento |

- **Postcondiciones:** Nuevo registro de límites configurados en el Módulo de Auditoría - Audit Trail
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0018-4 — Registro de auditoría por nuevo entrenamiento

- **Contexto:** En caso que un usuario acceda al módulo de Reentrenamiento IA
- **Evento:** cuando se genere un nuevo entrenamiento
- **Resultado esperado:** el sistema debe registrar la acción el módulo de Auditoría.
- **➕ Aclaración:** Evento ML_MODEL_PROMOTED.
- **CP asociado:** CP052
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP052 — Registro de auditoría por nuevo entrenamiento**

- **Criterio:** HU0018-4
- **Precondiciones:** Estar logueado en el sistema con el rol Administrador y tener datos cargados previamente en el Módulo de Ingesta de datos

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al Módulo Entrenamiento IA |  | Pantalla con boton de Dispara Entrenamiento |
| 2 | Dar click en el botón "Disparar Entrenamiento" |  | Mensaje "¡Ciclo MLOps completado! El modelo ha sido actualizado" |
| 3 | Ingresar al Módulo Auditoría |  | Pantalla con Tab Audit Trail y Usuarios |
| 4 | Dar click en el Tab Audit Trail |  | Registros de auditoría del sistema |
| 5 | Visualizar un nuevo registro |  | Registro nuevo con fecha registrada con título ML_MODEL_PROMOTED y metadata relacionada al modelo entrenado |

- **Postcondiciones:** Nuevo registro de modelo entrenado en el Módulo de Auditoría - Audit Trail
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)


---

### HU0019 — generar reportes de auditoría

- **Épica:** Trazabilidad y Cumplimiento de Estándares Farmacéuticos
- **Enunciado:** Como **Auditor** necesito **generar reportes de auditoría**, con la finalidad de garantizar la trazabilidad de quién y cuándo alimentó el simulador..
- **Dónde buscar en el código:** Módulo "Auditoría" → "Audit Trail": filtro por fechas y botón "Exportar" (CSV/PDF). Buscar: generación del archivo, filtro por rango, columnas.

#### HU0019-1 — Exportación del resumen de auditoría en CSV/PDF

- **Contexto:** En caso que el Auditor acceda al módulo de Auditoría
- **Evento:** cuando acceda al Audit Trail y haga click en el botón de exportación documental
- **Resultado esperado:** el sistema debe generar un archivo csv o pdf con el resumen de las simulaciones y el cumplimiento GMP
- **➕ Aclaración:** Columnas mínimas: fecha/hora, usuario, rol, tipo de evento, detalle [CONFIRMAR]. Formatos CSV y/o PDF [CONFIRMAR].
- **CP asociado:** CP053
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP053 — Exportación del resumen de auditoría en CSV/PDF**

- **Criterio:** HU0019-1
- **Precondiciones:** Auditor autenticado. Existen registros en el Audit Trail.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo Auditoría |  | Se muestra la pantalla con el Tab de Usuarios activo |
| 2 | Dar click en el Audit Trail |  | Se muestra la pantalla con el Tab de Audit Trail activo |
| 3 | Dar click en Exportar |  | Se descarga un archivo CSV con las acciones registradas; la cantidad de filas coincide con la tabla en pantalla |

- **Postcondiciones:** El archivo es generado y descargado en la carpeta Descargas del dispositivo del usuario
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)

#### HU0019-2 — Exportación filtrada por rango de fechas

- **Contexto:** En caso que el Auditor acceda al módulo de Auditoría
- **Evento:** cuando acceda al Audit Trail, filtre por fecha y haga click en el botón de exportación documental
- **Resultado esperado:** el sistema debe generar un archivo csv o pdf con el resumen de las simulaciones en el rango de fecha seleccionado
- **➕ Aclaración:** Ej.: 01/10/2026 a 04/10/2026. Todas las filas del archivo deben caer dentro del rango (inclusive).
- **CP asociado:** CP054
- **Estado en código:** `PENDIENTE` · **Evidencia:** — · **Observación:** —

**CP054 — Exportación filtrada por rango de fechas**

- **Criterio:** HU0019-2
- **Precondiciones:** Auditor autenticado. Existen registros en el Audit Trail dentro y fuera del rango.

| # | Paso | Datos de prueba | Resultado esperado |
|---|---|---|---|
| 1 | Ingresar al módulo Auditoría |  | Se muestra la pantalla con el Tab de Usuarios activo |
| 2 | Hacer click en el Audit Trail |  | Se muestra la pantalla con el Tab de Audit Trail activo |
| 3 | Colocar filtro de fecha | Desde 01/10/2026 hasta 04/10/2026 (DD/MM/AAAA) |  |
| 4 | Dar click en Exportar |  | Se descarga un CSV cuyas filas están TODAS dentro del rango (inclusive) |

- **Postcondiciones:** El archivo es generado y descargado en la carpeta Descargas del dispositivo del usuario
- **Resultado en la app:** `PENDIENTE` (PASA / FALLA / BLOQUEADO)


---

## 6. Trazabilidad HU → CA → CP

| HU | Criterios | Casos de prueba |
|---|---|---|
| HU0001 | 6 | CP001, CP002, CP003, CP004, CP005, CP006 |
| HU0002 | 4 | CP007, CP008, CP009, CP010 |
| HU0003 | 6 | CP011, CP055, CP056, CP057, CP012, CP013 |
| HU0004 | 4 | CP014, CP015, CP016, CP017 |
| HU0005 | 6 | CP018, CP019, CP020, CP021, CP022, CP023 |
| HU0006 | 2 | CP024, CP025 |
| HU0007 | 2 | CP026, CP027 |
| HU0008 | 2 | CP028, CP029 |
| HU0009 | 2 | CP030, CP031 |
| HU0010 | 2 | CP032, CP033 |
| HU0011 | 4 | CP034, CP035, CP036, CP037 |
| HU0012 | 3 | CP038, CP039, CP058 |
| HU0013 | 2 | CP040, CP041 |
| HU0014 | 3 | CP042, CP043, CP059 |
| HU0015 | 2 | CP044, CP045 |
| HU0016 | 1 | CP046 |
| HU0017 | 2 | CP047, CP048 |
| HU0018 | 4 | CP049, CP050, CP051, CP052 |
| HU0019 | 2 | CP053, CP054 |

---

## 7. Decisiones pendientes ([CONFIRMAR])

1. ¿El selector de Ingesta acepta `.xls` (texto tabulado del Datalogger)?
2. ¿Mensajes específicos por tipo de error de archivo, o se mantiene el toast genérico?
3. Texto oficial de éxito de Ingesta ("Sincronizado") y comportamiento con fechas fuera de rango o fin = inicio.
4. ¿Cómo provocar un entrenamiento fallido de forma reproducible? ¿El nuevo dataset reemplaza o se acumula?
5. Matriz de roles oficial (Supervisor en Entrenamiento, Auditor en Usuarios, quién edita el costo del kWh).
6. ¿Revocar es baja lógica o borrado físico? ¿Se puede reutilizar el username?
7. ¿"Humedad Sala Actual" interviene en el cálculo o es informativa?
8. ¿La recomendación debe ser siempre ≤ Potencia Estimada? ¿Es entera?
9. Etiqueta del botón de aplicar y textos de éxito (HU0011-3 vs CP036 vs CP049).
10. Longitud mínima de la justificación (10) y estado guardado al descartar.
11. Factor de conversión a kWh, ventana de 24 registros y si la tarifa 0 es válida.
12. Nombre real de las secciones del Dashboard y unidad del eje X de la firma térmica.
13. Regla exacta que dispara la "Alerta de Riesgo GMP" y su texto.
14. Nombres de eventos de auditoría (incluido el de "ignorar") y columnas/formatos de exportación.

---

## 8. Plantilla del reporte `docs/ESTADO_IMPLEMENTACION.md`

```markdown
# Estado de implementación (fecha)

## Resumen
| Estado | Cantidad |
|---|---|
| IMPLEMENTADO | n |
| PARCIAL | n |
| DIFIERE | n |
| NO_IMPLEMENTADO | n |
| NO_VERIFICABLE | n |

## Detalle por criterio
| CA | Estado | Evidencia (archivo:línea) | Brecha / Qué falta | Prioridad (Alta/Media/Baja) |
|---|---|---|---|---|
| HU0001-1 | | | | |

## Textos que difieren del catálogo
| Texto esperado | Texto en código | Archivo:línea |
|---|---|---|

## Casos de prueba que no se pueden ejecutar tal cual
| CP | Motivo | Cambio sugerido |
|---|---|---|

## Correcciones propuestas (orden sugerido)
1. ...
```
