// Ejecuta las suites de aceptación (HU/CP P20261007) contra la app levantada con docker compose.
const fs = require('fs');
const L = require('./lib');

const only = process.argv.slice(2); // p.ej.: node run.js auth_users simulador

(async () => {
  const browser = await L.launch();
  const ctx = {};
  try {
    ctx.adminToken = await L.apiLogin(process.env.E2E_ADMIN || 'admin_hvac', process.env.E2E_ADMIN_PASS || 'Admin12345');
    await L.ensureUsers(ctx.adminToken);
    const suites = ['auth_users', 'ingesta_ml', 'simulador', 'dashboard_audit'];
    for (const name of suites) {
      if (only.length && !only.includes(name)) continue;
      await require(`./suite_${name}`)(browser, ctx);
    }
  } finally {
    // Deja los límites GMP como estaban antes de las pruebas
    if (ctx.gmpInitial) {
      await L.api('/config/gmp/', { method: 'PUT', token: ctx.adminToken, json: { min_hum_limit: ctx.gmpInitial.min_hum_limit, max_hum_limit: ctx.gmpInitial.max_hum_limit } });
    }
    await browser.close();
  }
  const failed = L.results.filter((r) => !r.ok);
  console.log(`\nResultado: ${L.results.length - failed.length}/${L.results.length} casos pasan.`);
  failed.forEach((f) => console.log(` - ${f.id}: ${f.error.split('\n')[0]}`));
  fs.writeFileSync(__dirname + '/resultados.json', JSON.stringify(L.results, null, 2));
  process.exit(failed.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(2); });
