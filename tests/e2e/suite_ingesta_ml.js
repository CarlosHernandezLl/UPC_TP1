// HU0001 (ingesta), HU0002 (entrenamiento), HU0004 (límites GMP), HU0018-3/4 (auditoría de GMP y entrenamiento).
const path = require('path');
const fs = require('fs');
const L = require('./lib');
const { cp, check, eq, sleep, FIX } = L;

const JULIO = path.join(__dirname, '..', '..', 'docs', 'Entrenamiento Julio');
const PIPELINE_MSG = 'Ocurrió un error crítico al procesar el pipeline termodinámico. Revisa los logs del servidor.';

async function setDateTime(page, index, value) {
  await page.evaluate((i, v) => {
    const el = document.querySelectorAll('input[type=datetime-local]')[i];
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
    setter.call(el, v);
    el.dispatchEvent(new Event('input', { bubbles: true }));
  }, index, value);
}
async function upload(page, files) {
  const inputs = await page.$$('input[type=file]');
  eq(inputs.length, 3, 'inputs de archivo');
  for (let i = 0; i < 3; i++) await inputs[i].uploadFile(files[i]);
  await sleep(300);
}
const std = () => [path.join(FIX, 'DATOS_PLC.csv'), path.join(FIX, 'DATALOGGER.xls'), path.join(FIX, 'EXTERIOR.csv')];
async function ingestionHistory(token) { return (await L.api('/data/ingestion/history', { token })).data; }
async function openIngesta(page) { await L.loginAs(page, 'SUPERVISOR'); await L.goto(page, '/ingesta'); }
async function typeLimits(page, min, max) {
  for (const [label, v] of [['Humedad Relativa Mínima', min], ['Humedad Relativa Máxima', max]]) {
    const el = await L.inputByLabel(page, label);
    await el.click({ clickCount: 3 }); await page.keyboard.press('Backspace'); await el.type(String(v));
  }
}
async function openIA(page) { await L.loginAs(page, 'ADMIN'); await L.goto(page, '/ia-control'); }
async function train(page) {
  await L.clickText(page, 'Disparar Entrenamiento');
}
async function version(token) { return (await L.api('/mlops/metrics', { token })).data.version_tag; }

module.exports = async function (browser, ctx) {
  const tok = ctx.adminToken;
  ctx.gmpInitial = (await L.api('/config/gmp/', { token: tok })).data;

  console.log('\n[HU0001] Ingesta de datos');
  await cp('CP001', 'Carga de archivos CSV/XLSX: tres zonas, borde verde y selector admite .csv y .xlsx', () =>
    L.withSession(browser, async (page) => {
      await openIngesta(page);
      for (const t of ['Selección de Archivos', 'Historial']) await L.waitText(page, t);
      const accepts = await page.$$eval('input[type=file]', (els) => els.map((e) => e.accept));
      accepts.forEach((a, i) => check(a.includes('.csv') && a.includes('.xlsx'), `el selector ${i + 1} debe admitir .csv y .xlsx (tiene "${a}")`));
      await upload(page, std());
      eq(await page.$$eval('.border-green-400', (e) => e.length), 3, 'zonas en borde verde');
    }));

  await cp('CP001b', 'XLSX en PLC y Clima se procesa en el backend (ventana corta)', () =>
    L.withSession(browser, async (page) => {
      await openIngesta(page);
      await upload(page, [path.join(FIX, 'DATOS_PLC.xlsx'), path.join(FIX, 'DATALOGGER.xls'), path.join(FIX, 'EXTERIOR.xlsx')]);
      await setDateTime(page, 0, '2026-05-09T15:00');
      await setDateTime(page, 1, '2026-05-09T16:30');
      await L.clickText(page, 'Procesar e Inyectar');
      await L.waitToast(page, 'Sincronizado', 60000);
    }));

  const failCases = [
    ['CP002', 'Columna obligatoria faltante: aviso del pipeline y detalle', 'COPIA_DATOS_PLC_sin_columna.csv', 'f209potsecador'],
    ['CP003', 'Encabezado ausente: aviso del pipeline', 'COPIA_DATOS_PLC_sin_encabezado.csv', null],
    ['CP003b', 'Formato de fecha inválido: aviso del pipeline', 'COPIA_DATOS_PLC_fecha_invalida.csv', 'fecha'],
  ];
  for (const [id, title, file, detail] of failCases) {
    await cp(id, title, () =>
      L.withSession(browser, async (page) => {
        const before = (await ingestionHistory(tok)).length;
        await openIngesta(page);
        await upload(page, [path.join(FIX, file), path.join(FIX, 'DATALOGGER.xls'), path.join(FIX, 'EXTERIOR.csv')]);
        await L.clickText(page, 'Procesar e Inyectar');
        await L.waitToast(page, PIPELINE_MSG, 60000);
        if (detail) await L.waitText(page, detail);
        check(page.url().includes('/ingesta'), 'debe quedarse en la pantalla de ingesta');
        const h = (await ingestionHistory(tok)).sort((a, b) => b.id - a.id);
        eq(h.length, before + 1, 'filas en el historial');
        check(/ERROR/.test(h[0].status), `la carga debe quedar como error (estado: ${h[0].status})`);
      }));
  }

  console.log('\n[HU0002] Entrenamiento con carga fallida');
  await cp('CP008', 'Reentrenamiento fallido: toast "Fallo crítico en el pipeline MLOps" y log con motivo', () =>
    L.withSession(browser, async (page) => {
      const before = await version(tok);
      await openIA(page);
      await typeLimits(page, 30, 60);
      await train(page);
      await L.waitToast(page, 'Fallo crítico en el pipeline MLOps');
      await sleep(800);
      await L.waitText(page, 'Entrenamiento fallido');
      eq(await version(tok), before, 'la versión del modelo no debe cambiar');
    }));

  console.log('\n[HU0001] Fechas y éxito');
  await cp('CP005', 'Fechas invertidas: "La fecha de fin debe ser mayor a la fecha de inicio" y no se envía', () =>
    L.withSession(browser, async (page) => {
      const before = (await ingestionHistory(tok)).length;
      await openIngesta(page);
      await upload(page, std());
      await setDateTime(page, 0, '2026-10-09T00:00');
      await setDateTime(page, 1, '2026-10-02T00:00');
      await L.clickText(page, 'Procesar e Inyectar');
      await L.waitToast(page, 'La fecha de fin debe ser mayor a la fecha de inicio');
      eq((await ingestionHistory(tok)).length, before, 'no debe registrarse ninguna carga');
    }));

  await cp('CP004', 'Una sola fecha (solo inicio): se acepta, procesa e inyecta ("Sincronizado")', () =>
    L.withSession(browser, async (page) => {
      await openIngesta(page);
      await upload(page, std());
      await setDateTime(page, 0, '2026-05-10T00:00');
      await L.clickText(page, 'Procesar e Inyectar');
      await L.waitToast(page, 'Sincronizado', 90000);
      const h = (await ingestionHistory(tok)).sort((a, b) => b.id - a.id);
      check(h[0].record_count > 100, `debe inyectar el tramo posterior al corte (registros: ${h[0].record_count})`);
      check(!/ERROR/.test(h[0].status), `estado ${h[0].status}`);
    }));

  await cp('CP006', 'Operación exitosa: "Sincronizado" y el lote queda registrado', () =>
    L.withSession(browser, async (page) => {
      await openIngesta(page);
      await upload(page, std());
      await L.clickText(page, 'Procesar e Inyectar');
      await L.waitToast(page, 'Sincronizado', 90000);
      await L.waitToast(page, 'Operación Exitosa');
      const h = (await ingestionHistory(tok)).sort((a, b) => b.id - a.id);
      check(h[0].record_count > 1000 && !/ERROR/.test(h[0].status), `último lote: ${JSON.stringify(h[0])}`);
    }));

  console.log('\n[HU0004] Límites de seguridad GMP');
  await cp('CP014', 'Límites 0–100: la UI no deja digitar negativos y la API rechaza valores fuera de rango', () =>
    L.withSession(browser, async (page) => {
      await openIA(page);
      await L.waitText(page, 'Límites de Seguridad (GMP)');
      for (const label of ['Humedad Relativa Mínima', 'Humedad Relativa Máxima']) {
        const el = await L.inputByLabel(page, label);
        await el.click({ clickCount: 3 }); await page.keyboard.press('Backspace');
        await el.type('-20');
        const v = await page.evaluate((e) => parseFloat(e.value), el);
        check(!(v < 0), `${label}: se permitió un valor negativo (${v})`);
        await el.click({ clickCount: 3 }); await page.keyboard.press('Backspace');
        await el.type('150');
        const v2 = await page.evaluate((e) => parseFloat(e.value), el);
        check(!(v2 > 100), `${label}: se permitió un valor mayor a 100 (${v2})`);
      }
      const bad = await L.api('/config/gmp/', { method: 'PUT', token: tok, json: { min_hum_limit: -20, max_hum_limit: 50 } });
      eq(bad.status, 422, 'API con mínimo negativo');
      const bad2 = await L.api('/config/gmp/', { method: 'PUT', token: tok, json: { min_hum_limit: 10, max_hum_limit: 150 } });
      eq(bad2.status, 422, 'API con máximo > 100');
    }));

  await cp('CP015', 'Umbrales invertidos (60/40): mensaje de error y no se persiste', () =>
    L.withSession(browser, async (page) => {
      const before = (await L.api('/config/gmp/', { token: tok })).data;
      await openIA(page);
      await typeLimits(page, 60, 40);
      await L.clickText(page, 'Guardar Límites');
      await L.waitToast(page, 'El límite mínimo de humedad no puede ser mayor o igual al límite máximo');
      const after = (await L.api('/config/gmp/', { token: tok })).data;
      eq(after.min_hum_limit, before.min_hum_limit, 'mínimo persistido');
      eq(after.max_hum_limit, before.max_hum_limit, 'máximo persistido');
    }));

  await cp('CP016', 'Persistencia exitosa (30/50): confirmación visual y valores en BD', () =>
    L.withSession(browser, async (page) => {
      await openIA(page);
      await typeLimits(page, 30, 50);
      await L.clickText(page, 'Guardar Límites');
      await L.waitToast(page, 'Umbrales regulatorios actualizados. Cambio firmado en la pista de auditoría');
      await L.waitToast(page, 'Operación Exitosa');
      const g = (await L.api('/config/gmp/', { token: tok })).data;
      eq([g.min_hum_limit, g.max_hum_limit].join('/'), '30/50', 'límites guardados');
    }));

  await cp('CP017', 'Impacto en auditoría: GMP_LIMITS_UPDATE con fecha, usuario y valores (Audit Trail)', () =>
    L.withSession(browser, async (page) => {
      await L.loginAs(page, 'ADMIN');
      await L.goto(page, '/auditoria');
      await L.clickText(page, 'Audit Trail');
      await L.waitText(page, 'GMP_LIMITS_UPDATE');
      await L.waitText(page, 'Min=30.0%, Max=50.0%');
      const logs = (await L.api('/audit/', { token: tok })).data;
      const hit = logs.find((l) => l.action === 'GMP_LIMITS_UPDATE');
      check(/\d{2}\/\d{2}\/\d{4} \d{2}:\d{2}:\d{2}/.test(hit.timestamp), `fecha/hora: ${hit.timestamp}`);
      check(hit.user && hit.user !== 'System/Unknown', 'debe vincular al administrador');
    }));

  await cp('CP051', 'Auditoría por actualización de límites (40/60) tras guardar', () =>
    L.withSession(browser, async (page) => {
      await openIA(page);
      await typeLimits(page, 40, 60);
      await L.clickText(page, 'Guardar Límites');
      await L.waitToast(page, 'Umbrales regulatorios actualizados');
      await L.goto(page, '/auditoria');
      await L.clickText(page, 'Audit Trail');
      await L.waitText(page, 'Min=40.0%, Max=60.0%');
    }));

  console.log('\n[HU0002] Entrenamiento');
  await cp('CP007', 'Reentrenamiento exitoso: estado, métricas, toast y log exitoso', () =>
    L.withSession(browser, async (page) => {
      await openIA(page);
      await typeLimits(page, 30, 50);
      await train(page);
      await L.waitText(page, 'Entrenando Cerebro Digital...', 8000);
      await L.waitText(page, 'TRAINING', 8000);
      await L.waitText(page, 'Procesando Algoritmo...', 8000);
      await L.waitToast(page, '¡Ciclo MLOps completado! El modelo ha sido actualizado.', 180000);
      await sleep(800);
      await L.waitText(page, 'Entrenamiento exitoso');
      const m = (await L.api('/mlops/metrics', { token: tok })).data;
      check(m.r2_score > 0 && m.rmse > 0, `métricas: ${JSON.stringify(m)}`);
    }));

  let versionBefore;
  await cp('CP009', 'Métricas tras entrenar: nueva versión reemplaza a la anterior (Champion/Archived)', () =>
    L.withSession(browser, async (page) => {
      versionBefore = await version(tok);
      await openIA(page);
      await L.waitText(page, versionBefore);
      await L.waitText(page, 'Precisión Real (R²)');
      await train(page);
      await L.waitToast(page, '¡Ciclo MLOps completado!', 180000);
      await sleep(800);
      const after = await version(tok);
      check(after !== versionBefore, 'la versión del modelo debe cambiar');
      await L.waitText(page, after);
      const hist = (await L.api('/mlops/history', { token: tok })).data.data;
      eq(hist.filter((h) => h.status === 'ACTIVE').length, 1, 'modelos ACTIVE');
      eq(hist.find((h) => h.version_tag === versionBefore).status, 'ARCHIVED', 'modelo anterior');
      const m = (await L.api('/mlops/metrics', { token: tok })).data;
      check(Array.isArray(m.feature_importance) && m.feature_importance.length === 6, 'debe incluir el análisis SHAP de 6 variables');
      await L.waitText(page, 'Impacto de variables (SHAP)');
    }));

  await cp('CP010', 'Carga de un dataset nuevo (Julio) para reentrenar', () =>
    L.withSession(browser, async (page) => {
      await openIngesta(page);
      await upload(page, [path.join(JULIO, 'DATOS_PLC.csv'), path.join(JULIO, 'DATALOGGER.xls'), path.join(JULIO, 'EXTERIOR.csv')]);
      await L.clickText(page, 'Procesar e Inyectar');
      await L.waitToast(page, 'Sincronizado', 90000);
    }));
  await cp('CP010b', 'Entrenar tras la nueva carga: ciclo completado y nuevo log', () =>
    L.withSession(browser, async (page) => {
      const prev = await version(tok);
      await openIA(page);
      await train(page);
      await L.waitToast(page, '¡Ciclo MLOps completado! El modelo ha sido actualizado.', 180000);
      await sleep(800);
      check((await version(tok)) !== prev, 'debe generarse una nueva versión');
      await L.waitText(page, 'Entrenamiento exitoso');
    }));

  await cp('CP052', 'Auditoría por nuevo entrenamiento: ML_MODEL_PROMOTED en el Audit Trail', () =>
    L.withSession(browser, async (page) => {
      await L.loginAs(page, 'ADMIN');
      await L.goto(page, '/auditoria');
      await L.clickText(page, 'Audit Trail');
      await L.waitText(page, 'ML_MODEL_PROMOTED');
      const logs = (await L.api('/audit/', { token: tok })).data;
      const hit = logs.find((l) => l.action === 'ML_MODEL_PROMOTED');
      check(/R²=/.test(hit.details) && /RMSE=/.test(hit.details), `detalle: ${hit.details}`);
    }));
};
