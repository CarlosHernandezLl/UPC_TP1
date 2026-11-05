// HU0012–HU0016 (dashboard) y HU0019 (exportación de auditoría).
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const L = require('./lib');
const { cp, check, eq, sleep, DOWNLOADS } = L;

const money = (t) => parseFloat(L.norm(t).match(/ahorro potencial \(periodo\) \$([\d.]+)/)[1]);
const kwh = (t) => parseFloat(L.norm(t).match(/diferencial energético ([\d.]+) kwh/)[1]);
const dash = async (tok) => (await L.api('/dashboard/metrics', { token: tok })).data;
const limaToday = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Lima' }).format(new Date());
const BODY = {
  outdoor_temp: 20.4, outdoor_rh: 78, ahu_temp: 22.5, ahu_rh: 50.4, current_room_rh: 44.7, target_setpoint: 50,
  room_temp: 22.4, injection_pressure: 100, justification: 'N/A',
};

async function setDate(page, label, value) {
  await page.evaluate((l, v) => {
    const el = document.querySelector(`input[aria-label="${l}"]`);
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(el, v);
    el.dispatchEvent(new Event('input', { bubbles: true }));
  }, label, value);
  await sleep(500);
}
function newDownload(before) {
  return fs.readdirSync(DOWNLOADS).filter((f) => !before.includes(f) && !f.endsWith('.crdownload'));
}
async function waitDownload(before, ext, timeout = 15000) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeout) {
    const f = newDownload(before).find((x) => x.endsWith(ext));
    if (f) return path.join(DOWNLOADS, f);
    await sleep(250);
  }
  throw new Error(`no se descargó ningún archivo .${ext}`);
}

module.exports = async function (browser, ctx) {
  const tok = ctx.adminToken;
  const sup = await L.apiLogin(L.USERS.SUPERVISOR.username, L.USERS.SUPERVISOR.password);
  await L.api('/config/gmp/', { method: 'PUT', token: tok, json: { min_hum_limit: 0, max_hum_limit: 100 } });

  console.log('\n[HU0012–HU0013] Dashboard tras aplicar o ignorar');
  await cp('CP038', 'Aplicar recomendación: el Dashboard (Diferencial Energético y gráfica) se actualiza', () =>
    L.withSession(browser, async (page) => {
      const d0 = await dash(sup);
      await L.loginAs(page, 'SUPERVISOR');
      await L.goto(page, '/simulador');
      await L.simFill(page, { pwrActual: 60 });
      await L.simGenerate(page);
      await L.clickText(page, 'Sí, aplicada');
      await L.waitToast(page, 'Operación Exitosa');
      await L.goto(page, '/dashboard');
      await L.waitText(page, 'Diferencial Energético');
      const d1 = await dash(sup);
      check(d1.auditData.length === Math.min(24, d0.auditData.length + 1), `puntos de la gráfica: ${d0.auditData.length} -> ${d1.auditData.length}`);
      const last = d1.auditData[d1.auditData.length - 1];
      eq(last.real, 60, 'potencia estimada del último punto');
      check(Number.isInteger(last.ideal), 'la recomendación del último punto debe ser entera');
    }));

  await cp('CP040', 'Gráfica comparativa: dos curvas de líneas (Estimada vs. Recomendada)', () =>
    L.withSession(browser, async (page) => {
      await L.loginAs(page, 'ADMIN');
      await L.goto(page, '/dashboard');
      await L.waitText(page, 'Auditoría Estacionaria: Consumo Real vs. Recomendación IA');
      await page.waitForSelector('.recharts-line', { timeout: 8000 });
      eq(await page.$$eval('.recharts-line', (e) => e.length), 2, 'curvas de línea');
      await L.waitText(page, 'Estimada');
      await L.waitText(page, 'Recomendada');
    }));

  await cp('CP041', 'Ignorar no actualiza la gráfica ni los indicadores (vista del Dashboard idéntica)', () =>
    L.withSession(browser, async (page) => {
      await L.loginAs(page, 'ADMIN');
      await L.goto(page, '/dashboard');
      await L.waitText(page, 'Diferencial Energético');
      const before = { k: kwh(await L.bodyText(page)), m: money(await L.bodyText(page)), pts: (await dash(sup)).auditData.length };
      await L.goto(page, '/simulador');
      await L.simFill(page, { pwrActual: 70 });
      await L.simGenerate(page);
      await L.clickText(page, 'Ignorar');
      await page.type('textarea', 'Esta es una prueba de justificación');
      await L.clickText(page, 'Confirmar Descarte');
      await L.waitToast(page, 'Descarte operativo registrado con éxito junto a su sustento técnico.');
      await L.goto(page, '/dashboard');
      await L.waitText(page, 'Diferencial Energético');
      eq(kwh(await L.bodyText(page)), before.k, 'kWh');
      eq(money(await L.bodyText(page)), before.m, 'ahorro');
      eq((await dash(sup)).auditData.length, before.pts, 'puntos');
    }));

  await cp('CP041b', 'Estado inicial: sin recomendaciones aplicadas la gráfica queda vacía y los indicadores en 0', () => {
    const py = [
      'from app.services.dashboard_service import DashboardService',
      'class Sim:',
      '    def get_recent_applied_simulations(self, limit=24): return []',
      'class Hvac:',
      '    def get_power_humidity_series(self): return []',
      'r = DashboardService(Sim(), Hvac()).get_plant_analytics()',
      'assert r["auditData"] == [] and r["kpi_ahorro"] == 0 and r["kpi_diferencial"] == 0, r',
      'print("vacio-ok")',
    ].join('\n');
    const out = execSync('docker compose exec -T backend python -', { input: py, cwd: path.join(__dirname, '..', '..'), env: { ...process.env, PATH: `${process.env.PATH};C:\\Program Files\\Docker\\Docker\\resources\\bin` } }).toString();
    check(out.includes('vacio-ok'), out);
  });

  console.log('\n[HU0014–HU0015] Ahorro económico');
  let diffBase;
  await cp('CP042', 'Operador excede la recomendada (80 % vs 60 %): + 20 pp × 1,5 kWh × tarifa 0,15 = + $4.50', () =>
    L.withSession(browser, async (page) => {
      const d0 = await dash(sup);
      const r = await L.api('/simulation/log-action', { method: 'POST', token: sup, json: { ...BODY, current_power: 80, recommended_power: 60, applied_power: 60, action: 'RECOMMENDATION_APPLIED' } });
      eq(r.status, 201, 'registro de la decisión');
      const d1 = await dash(sup);
      eq(+(d1.kpi_diferencial - d0.kpi_diferencial).toFixed(1), 30, 'incremento de kWh');
      await L.loginAs(page, 'GERENTE');
      await L.goto(page, '/dashboard');
      await L.waitText(page, 'Ahorro Potencial (Periodo)');
      const body = await L.bodyText(page);
      eq(money(body), +(d1.kpi_diferencial * 0.15).toFixed(2), 'monto mostrado');
      eq(+(money(body) - +(d0.kpi_diferencial * 0.15)).toFixed(2), 4.5, 'incremento del monto');
      diffBase = d1.kpi_diferencial;
    }));

  await cp('CP043', 'Operador sigue o mejora la recomendación (igual o menor): no suma ahorro', async () => {
    const d0 = await dash(sup);
    for (const [cur, rec] of [[60, 60], [50, 60]]) {
      const r = await L.api('/simulation/log-action', { method: 'POST', token: sup, json: { ...BODY, current_power: cur, recommended_power: rec, applied_power: rec, action: 'RECOMMENDATION_APPLIED' } });
      eq(r.status, 201, 'registro');
    }
    const d1 = await dash(sup);
    eq(d1.kpi_diferencial, d0.kpi_diferencial, 'kWh tras seguir/mejorar la recomendación');
  });

  await cp('CP044', 'Costo kWh 5.0: el ahorro pasa a Costo × Diferencial Energético', () =>
    L.withSession(browser, async (page) => {
      await L.loginAs(page, 'GERENTE');
      await L.goto(page, '/dashboard');
      await L.waitText(page, 'Configuración de Costos');
      const k = kwh(await L.bodyText(page));
      await L.fill(page, 'input[type=number]', '5');
      await sleep(400);
      eq(money(await L.bodyText(page)), +(k * 5).toFixed(2), 'ahorro con costo 5.0');
    }));

  await cp('CP045', 'Costo kWh: solo valores positivos (no deja digitar el signo "-")', () =>
    L.withSession(browser, async (page) => {
      await L.loginAs(page, 'SUPERVISOR');
      await L.goto(page, '/dashboard');
      await L.waitText(page, 'Configuración de Costos');
      await L.fill(page, 'input[type=number]', '-5');
      const v = await L.valueOf(page, 'input[type=number]');
      check(!v.includes('-') && parseFloat(v) >= 0, `el campo aceptó un valor negativo (${v})`);
      await page.keyboard.type('-');
      check(!(await L.valueOf(page, 'input[type=number]')).includes('-'), 'el signo "-" no debe digitarse');
    }));

  await cp('CP059', 'Tarifa 0,15 → 0,20: el monto se recalcula al instante, sin recargar', () =>
    L.withSession(browser, async (page) => {
      await L.loginAs(page, 'GERENTE');
      await L.goto(page, '/dashboard');
      await L.waitText(page, 'Configuración de Costos');
      const k = kwh(await L.bodyText(page));
      eq(money(await L.bodyText(page)), +(k * 0.15).toFixed(2), 'monto inicial con 0.15');
      await L.fill(page, 'input[type=number]', '0.20');
      await sleep(400);
      eq(money(await L.bodyText(page)), +(k * 0.2).toFixed(2), 'monto con 0.20');
      const rej = await (async () => { await L.fill(page, 'input[type=number]', '999999'); await sleep(300); return L.valueOf(page, 'input[type=number]'); })();
      check(parseFloat(rej) <= 5, `una tarifa absurda no debe aceptarse (${rej})`);
    }));

  console.log('\n[HU0016] Firma térmica');
  await cp('CP046', 'Firma Térmica: dispersión Humedad (X) vs Potencia (Y) con puntos estacionarios', () =>
    L.withSession(browser, async (page) => {
      await L.loginAs(page, 'SUPERVISOR');
      await L.goto(page, '/dashboard');
      await L.waitText(page, 'Firma Térmica: Relación Histórica Humedad vs Potencia');
      await page.waitForSelector('.recharts-scatter', { timeout: 8000 });
      const pts = await page.$$eval('.recharts-scatter .recharts-symbols, .recharts-scatter path', (e) => e.length);
      check(pts > 50, `debe graficar muchos puntos históricos (${pts})`);
      await L.waitText(page, 'Humedad de sala (g/kg)');
      await L.waitText(page, 'Potencia (%)');
      const m = await dash(sup);
      check(new Set(m.modelCorrelation.map((p) => p.pwr)).size > 5, 'debe haber varios niveles de potencia (no una sola vertical)');
    }));

  console.log('\n[HU0019] Exportación de auditoría');
  fs.rmSync(DOWNLOADS, { recursive: true, force: true });
  fs.mkdirSync(DOWNLOADS, { recursive: true });

  await cp('CP053', 'Auditor exporta el Audit Trail: se descarga un CSV con el resumen', () =>
    L.withSession(browser, async (page) => {
      await L.loginAs(page, 'AUDITOR');
      await L.goto(page, '/auditoria');
      await L.waitText(page, 'Registro Histórico Inmutable');
      const before = fs.readdirSync(DOWNLOADS);
      await L.clickText(page, 'Exportar');
      const file = await waitDownload(before, '.csv');
      const text = fs.readFileSync(file, 'utf-8').replace(/^\uFEFF/, '');
      const lines = text.trim().split(/\r?\n/);
      eq(lines[0], 'id,action,user,timestamp,details', 'encabezado del CSV');
      check(lines.length > 5 && text.includes('RECOMMENDATION_APPLIED'), 'el CSV debe traer los eventos de simulaciones');
    }));

  await cp('CP054', 'Exportación filtrada por rango de fechas (CSV y PDF)', () =>
    L.withSession(browser, async (page) => {
      const today = limaToday();
      await L.loginAs(page, 'AUDITOR');
      await L.goto(page, '/auditoria');
      await L.waitText(page, 'Registro Histórico Inmutable');
      const all = (await L.api('/audit/', { token: tok })).data.length;

      await setDate(page, 'Fecha desde', today);
      await setDate(page, 'Fecha hasta', today);
      let before = fs.readdirSync(DOWNLOADS);
      await L.clickText(page, 'Exportar');
      const csv = await waitDownload(before, '.csv');
      const rows = fs.readFileSync(csv, 'utf-8').replace(/^\uFEFF/, '').trim().split(/\r?\n/).slice(1);
      check(rows.length > 0 && rows.length <= all, `filas en el rango de hoy: ${rows.length}`);
      const [d, m, y] = [today.slice(8, 10), today.slice(5, 7), today.slice(0, 4)];
      check(rows.every((r) => r.includes(`${d}/${m}/${y}`)), 'todas las filas deben ser de la fecha filtrada');

      await setDate(page, 'Fecha desde', '2000-01-01');
      await setDate(page, 'Fecha hasta', '2000-01-02');
      before = fs.readdirSync(DOWNLOADS);
      await L.clickText(page, 'Exportar');
      const empty = await waitDownload(before, '.csv');
      eq(fs.readFileSync(empty, 'utf-8').replace(/^\uFEFF/, '').trim().split(/\r?\n/).length, 1, 'un rango sin eventos solo trae el encabezado');
      await L.waitText(page, 'No hay registros de auditoría disponibles');

      await setDate(page, 'Fecha desde', today);
      await setDate(page, 'Fecha hasta', today);
      before = fs.readdirSync(DOWNLOADS);
      await L.clickText(page, 'PDF');
      const pdf = await waitDownload(before, '.pdf');
      eq(fs.readFileSync(pdf).subarray(0, 4).toString(), '%PDF', 'cabecera del PDF');

      const bad = await L.api('/audit/?desde=2026-02-02&hasta=2026-01-01', { token: tok });
      eq(bad.status, 400, 'rango invertido en la API');
    }));
};
