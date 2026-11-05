# Pruebas de aceptación (HU/CP P20261007)

Siguen los pasos de `docs/P20261007_CP.xlsx` contra la app real, con Chrome automatizado (`puppeteer-core`) y llamadas a la API.
Viven en su propia carpeta para no añadir dependencias al proyecto.

## Requisitos
- App arriba: `docker compose up --build -d` (frontend en :3000, API en :8000).
- Node 18+, Python con `openpyxl` (para generar los archivos de prueba) y Google Chrome.

## Uso
```bash
cd tests/e2e
npm install
npm test                  # todo: genera fixtures y ejecuta los 64 casos
node run.js simulador     # una suite: auth_users | ingesta_ml | simulador | dashboard_audit
```

Variables opcionales: `E2E_BASE`, `E2E_API`, `CHROME_PATH`, `E2E_ADMIN`, `E2E_ADMIN_PASS` (por defecto `admin_hvac` / `Admin12345`).

## Qué hace y qué deja
- Crea los usuarios `AdministradorTest`, `SupervisorTest`, `GerenteTest` y `AuditorTest` (clave igual al usuario).
- Carga datasets (Mayo y Julio), entrena el modelo varias veces, aplica y descarta recomendaciones.
- Cambia los límites GMP durante la ejecución y los restaura al terminar.
- Los datos creados quedan en la BD; para empezar limpio: `docker compose down -v`.
- Resultado en `resultados.json`; el proceso termina con código 1 si falla algún caso.
