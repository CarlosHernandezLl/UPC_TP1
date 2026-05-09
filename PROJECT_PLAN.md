# PROJECT PLAN: Simulador de Eficiencia Energética (Microservicio ML)

## 1. Arquitectura del Sistema
- **Raíz:** `UPC_TP1/`
- **Servicios:** `./TP1_BACKEND` (Microservicio ML) y `./TP1_FRONTEND` (Interfaz)


## 2. Pipeline de Datos Multifuente (HU-01)
El sistema debe procesar **3 archivos independientes** (fuentes diferentes) antes del entrenamiento:

### Fase A: Ingestión y Limpieza Individual (`ingestion.py`)
- **Archivos:** Se reciben 3 archivos (.csv/.xlsx).
- **Limpieza de Ruido:** El script debe eliminar automáticamente las primeras y últimas N filas de cada archivo (limpieza de manipulación de datalogger).
- **Validación:** Cada fuente debe cumplir con sus columnas específicas antes de unirse.

### Fase B: Sincronización y Merge (`processing.py`)
- **Merge:** Unir los 3 dataframes usando la columna `timestamp` como clave.
- **Ingeniería de Variables:** Calcular **Entalpía** y **Humedad Absoluta** sobre el dataframe consolidado.
- **Tratamiento:** Manejo de valores nulos tras el merge por desajustes de segundos entre sensores.


### Fase C: Modelado (`training.py`)
- **Algoritmo:** XGBoost Regressor.
- **Salida:** Modelo persistido y métricas (HU-02).



## 3. Historias de Usuario Detalladas

### Módulo A: Inteligencia Predictiva (Administrador)
- **HU-01:** Subida de 3 fuentes, limpieza de ruido de datalogger y merge.
- **HU-03:** Límites GMP (40-70% Humedad).
- **HU-10:** Predicción de potencia recomendada en < 3s.
- **HU-18:** Audit Trail de todas las acciones (Trazabilidad Farmacéutica).

### Módulo B: Parámetros y Seguridad (Administrador)
- **HU-03 [GMP]:** Configurar límites de humedad (40% - 70%).
- **HU-04 [Auth]:** Gestión de perfiles (Admin, Supervisor, Gerente) con hashing de contraseñas.

### Módulo C: Simulación (Supervisor)
- **HU-05 a HU-09 [Inputs]:** Ingreso de datos actuales (Exterior, UMA, Potencia Secador, Humedad Sala, Setpoint). Validar rangos lógicos.
- **HU-10 [Predicción]:** El microservicio devuelve la potencia recomendada (0-100%) en < 3 seg.
- **HU-12 [Alerta]:** Banner visual si la predicción está a +/- 2% del límite GMP.

### Módulo D: Dashboard y Auditoría (Gerente/Auditor)
- **HU-11 [Ahorro]:** Cálculo de kW ahorrados (Actual vs Recomendado).
- **HU-15 a HU-16 [Costos]:** Dashboard en USD basado en costo de kWh configurable.
- **HU-18 [Audit Trail]:** Registro inmutable de quién ingresó qué datos y cuándo.
- **HU-19 [Reporte]:** Exportar informe de cumplimiento ambiental en PDF.

## 4. Reglas Técnicas Generales
- Las comunicaciones entre Frontend y Backend serán vía JSON (REST API).
- El modelo entrenado debe persistirse (.pkl o .json) para predicciones rápidas sin re-entrenar.
- El backend debe exponer un endpoint `/upload-sources` que reciba los 3 archivos simultáneamente.
- Usar `pandas` para la manipulación y `XGBoost` para la lógica predictiva.