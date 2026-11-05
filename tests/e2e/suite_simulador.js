// HU0006–HU0012, HU0017, HU0018-1: validaciones del simulador, recomendación, aplicar/ignorar y alertas GMP.
const L = require('./lib');
const { cp, check, eq, sleep } = L;

const MSG = {
  ext: 'Por favor, llene las variables de Temperatura y Humeda externa antes de consultar al Gemelo Digital',
  uma: 'Por favor, llene las variables de Temperatura, Humedad y Presion de la UMA antes de consultar al Gemelo Digital',
  pwr: 'Por favor, llene la variable de Potencia antes de consultar al Gemelo Digital',
  all: 'Por favor, llene todas las variables de operación antes de consultar al Gemelo Digital',
};

async function open(page, role = 'SUPERVISOR') {
  await L.loginAs(page, role);
  await L.goto(page, '/simulador');
  await page.waitForSelector('#field-tempExt');
}
// Intenta digitar un valor: devuelve lo que el campo realmente conservó
async function typed(page, key, text) {
  await L.fill(page, `#field-${key}`, text);
  return L.valueOf(page, `#field-${key}`);
}
async function expectBlocked(page, key, texts) {
  for (const t of texts) check((await typed(page, key, t)) !== t, `${key}: se aceptó el valor fuera de rango "${t}"`);
}
async function expectAccepted(page, key, texts) {
  for (const t of texts) eq(await typed(page, key, t), t, `${key}: valor válido "${t}"`);
}
async function missingMessage(page, overrides, expected) {
  await L.simFill(page, overrides);
  await L.clickText(page, 'Generar Recomendación');
  await L.waitToast(page, expected, 6000);
  check(!(await page.$('.text-6xl')), 'no debe mostrarse una recomendación');
  await L.waitToast(page, 'Aviso del Sistema', 2000);
}
const dash = async (tok) => (await L.api('/dashboard/metrics', { token: tok })).data;
const simLogs = async (tok) => (await L.api('/audit/', { token: tok })).data;

module.exports = async function (browser, ctx) {
  const tok = ctx.adminToken;
  const sup = await L.apiLogin(L.USERS.SUPERVISOR.username, L.USERS.SUPERVISOR.password);
  await L.api('/config/gmp/', { method: 'PUT', token: tok, json: { min_hum_limit: 0, max_hum_limit: 100 } });

  console.log('\n[HU0006–HU0009] Validación de variables');
  await cp('CP024', 'Clima externo: solo 0–50 °C y 0–100 %, decimales permitidos', () =>
    L.withSession(browser, async (page) => {
      await open(page);
      await expectBlocked(page, 'tempExt', ['60', '-10']);
      await expectAccepted(page, 'tempExt', ['25', '25.56']);
      await expectBlocked(page, 'humExt', ['150', '-50']);
      await expectAccepted(page, 'humExt', ['20', '21.65']);
      await typed(page, 'tempExt', 'abc');
      eq(await L.valueOf(page, '#field-tempExt'), '', 'letras en el campo');
    }));

  await cp('CP025', 'Clima externo vacío: aviso "…Temperatura y Humeda externa…" y no se consulta al modelo', () =>
    L.withSession(browser, async (page) => {
      await open(page);
      await missingMessage(page, { tempExt: '', humExt: '', tempUma: 22.5, humUma: 50.4, presionInyeccion: 100, pwrActual: 70, humSala: 44.7, setpoint: 50, tempSala: 22.4 }, MSG.ext);
    }));

  await cp('CP026', 'UMA: Temp 0–50, Humedad 0–100 y Presión 0–1000 Pa (CP cita 1450/1080.65, fuera de la HU)', () =>
    L.withSession(browser, async (page) => {
      await open(page);
      await expectBlocked(page, 'tempUma', ['60', '-10']);
      await expectAccepted(page, 'tempUma', ['25', '25.56']);
      await expectBlocked(page, 'humUma', ['150', '-50']);
      await expectAccepted(page, 'humUma', ['20', '21.65']);
      await expectBlocked(page, 'presionInyeccion', ['1600', '-50', '1000.5']);
      await expectAccepted(page, 'presionInyeccion', ['999.5', '1000', '0']);
    }));

  await cp('CP027', 'UMA vacía: aviso "…Temperatura, Humedad y Presion de la UMA…"', () =>
    L.withSession(browser, async (page) => {
      await open(page);
      await missingMessage(page, { tempUma: '', humUma: '', presionInyeccion: '' }, MSG.uma);
    }));

  await cp('CP028', 'Potencia estimada: 0–100 %, rechaza 150 y negativos, acepta 55', () =>
    L.withSession(browser, async (page) => {
      await open(page);
      await expectBlocked(page, 'pwrActual', ['150', '-5']);
      await expectAccepted(page, 'pwrActual', ['55']);
    }));

  await cp('CP029', 'Potencia vacía: aviso "…llene la variable de Potencia…"', () =>
    L.withSession(browser, async (page) => {
      await open(page);
      await missingMessage(page, { pwrActual: '' }, MSG.pwr);
    }));

  await cp('CP030', 'Sala: temperatura 0–50 °C y humedad 0–100 % (rechaza 60 °C y 101 %)', () =>
    L.withSession(browser, async (page) => {
      await open(page);
      await expectBlocked(page, 'tempSala', ['60']);
      await expectAccepted(page, 'tempSala', ['23']);
      await expectBlocked(page, 'humSala', ['101']);
      await expectAccepted(page, 'humSala', ['55']);
    }));

  await cp('CP031', 'Sala vacía: aviso general de variables de operación', () =>
    L.withSession(browser, async (page) => {
      await open(page);
      await missingMessage(page, { tempSala: '', humSala: '' }, MSG.all);
    }));

  await cp('CP032', 'Objetivo de humedad: rechaza 110 y acepta 55', () =>
    L.withSession(browser, async (page) => {
      await open(page);
      await expectBlocked(page, 'setpoint', ['110']);
      await expectAccepted(page, 'setpoint', ['55']);
    }));

  await cp('CP033', 'Objetivo vacío: aviso general y no se ejecuta el modelo', () =>
    L.withSession(browser, async (page) => {
      await open(page);
      await missingMessage(page, { setpoint: '' }, MSG.all);
    }));

  await cp('CP035', 'Todo vacío: "Por favor, llene todas las variables de operación…" y borde rojo', () =>
    L.withSession(browser, async (page) => {
      await open(page);
      await missingMessage(page, Object.fromEntries(L.SIM_FIELDS.map((k) => [k, ''])), MSG.all);
      check((await page.$$('.border-rose-500')).length >= 1, 'deben resaltarse los campos incompletos');
    }));

  console.log('\n[HU0010–HU0012] Recomendación, aplicar e ignorar');
  await cp('CP034', 'La potencia recomendada es un entero entre 0 y 100 %', () =>
    L.withSession(browser, async (page) => {
      await open(page);
      for (const pwr of [60, 70.5]) {
        await L.simFill(page, { pwrActual: pwr });
        const txt = await L.simGenerate(page);
        check(/^\d{1,3}%$/.test(txt), `la recomendación debe ser un entero (${txt}) para potencia ${pwr}`);
        const n = parseInt(txt, 10);
        check(n >= 0 && n <= 100, `fuera de rango: ${n}`);
        await sleep(300);
      }
    }));

  await cp('CP036', 'Aplicar: toast "Ajuste del … Transacción cifrada en Audit Trail" y log con el usuario', () =>
    L.withSession(browser, async (page) => {
      await open(page);
      await L.simFill(page, { pwrActual: 60 });
      await L.simGenerate(page);
      const before = (await simLogs(tok)).filter((l) => l.action === 'RECOMMENDATION_APPLIED').length;
      await L.clickText(page, 'Sí, aplicada');
      await L.waitToast(page, 'Ajuste del');
      await L.waitToast(page, 'Transacción cifrada en Audit Trail.');
      await L.waitToast(page, 'Operación Exitosa');
      const logs = (await simLogs(tok)).filter((l) => l.action === 'RECOMMENDATION_APPLIED');
      eq(logs.length, before + 1, 'eventos RECOMMENDATION_APPLIED');
      eq(logs[0].user, L.USERS.SUPERVISOR.full_name, 'usuario del log');
    }));

  await cp('CP037', 'Ignorar: modal de justificación obligatoria; Cancelar no registra nada', () =>
    L.withSession(browser, async (page) => {
      await open(page);
      await L.simFill(page, { pwrActual: 70 });
      await L.simGenerate(page);
      const before = (await simLogs(tok)).length;
      await L.clickText(page, 'Ignorar');
      await L.waitText(page, 'Justificación Técnica Obligatoria');
      await L.clickText(page, 'Cancelar');
      await L.expectNoText(page, 'Justificación Técnica Obligatoria');
      eq((await simLogs(tok)).length, before, 'registros de auditoría');
    }));

  await cp('CP039', 'Descartar con justificación: toast de descarte, auditoría y Dashboard sin cambios', () =>
    L.withSession(browser, async (page) => {
      await open(page);
      const d0 = await dash(sup);
      await L.simFill(page, { pwrActual: 70 });
      await L.simGenerate(page);
      await L.clickText(page, 'Ignorar');
      await page.type('textarea', 'Esta es una prueba de justificación');
      await L.clickText(page, 'Confirmar Descarte');
      await L.waitToast(page, 'Descarte operativo registrado con éxito junto a su sustento técnico.');
      const logs = (await simLogs(tok)).filter((l) => l.action === 'RECOMMENDATION_OVERRIDDEN');
      check(logs[0] && logs[0].details.includes('Esta es una prueba de justificación'), 'la justificación debe quedar en el log');
      const d1 = await dash(sup);
      eq(d1.auditData.length, d0.auditData.length, 'puntos de la gráfica tras descartar');
      eq(d1.kpi_diferencial, d0.kpi_diferencial, 'diferencial energético tras descartar');
      eq(d1.kpi_ahorro, d0.kpi_ahorro, 'ahorro tras descartar');
    }));

  await cp('CP058', 'Descarte sin sustento (vacío o < 10 caracteres): bloqueado, alerta GxP y sin escrituras', () =>
    L.withSession(browser, async (page) => {
      await open(page);
      await L.simFill(page, { pwrActual: 70 });
      await L.simGenerate(page);
      const logs0 = (await simLogs(tok)).length;
      await L.clickText(page, 'Ignorar');
      for (const text of ['', 'prueba']) {
        await L.fill(page, 'textarea', text);
        await L.clickText(page, 'Confirmar Descarte');
        await L.waitText(page, 'Por normativa GxP, debe ingresar una justificación técnica detallada');
        check(await page.$('textarea'), 'el modal debe seguir abierto');
      }
      eq((await simLogs(tok)).length, logs0, 'registros de auditoría tras el bloqueo');
      // El backend también lo exige
      const body = { outdoor_temp: 20, outdoor_rh: 70, ahu_temp: 22, ahu_rh: 50, current_room_rh: 45, target_setpoint: 50, current_power: 70, room_temp: 22, injection_pressure: 100, recommended_power: 60, applied_power: 70, action: 'RECOMMENDATION_OVERRIDDEN' };
      for (const justification of ['', 'n/a', 'corto']) {
        const r = await L.api('/simulation/log-action', { method: 'POST', token: sup, json: { ...body, justification } });
        eq(r.status, 422, `API con justificación "${justification}"`);
      }
    }));

  console.log('\n[HU0017] Alerta de riesgo GMP');
  await cp('CP047', 'Recomendación fuera de los límites GMP: "Alerta de Riesgo GMP" (y "Alerta de incumplimiento")', () =>
    L.withSession(browser, async (page) => {
      await L.api('/config/gmp/', { method: 'PUT', token: tok, json: { min_hum_limit: 1, max_hum_limit: 2 } });
      await open(page);
      await L.simFill(page, { pwrActual: 70 });
      await L.simGenerate(page);
      await L.waitText(page, 'Alerta de Riesgo GMP');
      await L.waitText(page, 'Alerta de incumplimiento');
      await L.waitText(page, 'El setpoint solicitado, o las condiciones de humedad logradas por el modelo, apuntan a una violación del marco regulatorio estricto de la sala');
    }));

  await cp('CP048', 'Recomendación dentro de los límites GMP: sin alerta', () =>
    L.withSession(browser, async (page) => {
      await L.api('/config/gmp/', { method: 'PUT', token: tok, json: { min_hum_limit: 0, max_hum_limit: 100 } });
      await open(page);
      await L.simFill(page, { pwrActual: 70 });
      await L.simGenerate(page);
      await L.expectNoText(page, 'Alerta de Riesgo GMP');
      await L.expectNoText(page, 'Alerta de incumplimiento');
    }));

  console.log('\n[HU0018-1] Auditoría de recomendaciones');
  await cp('CP049', 'Aplicar y revisar: RECOMMENDATION_APPLIED en Auditoría > Audit Trail con fecha', () =>
    L.withSession(browser, async (page) => {
      await open(page, 'ADMIN');
      await L.simFill(page, { pwrActual: 70 });
      await L.simGenerate(page);
      await L.clickText(page, 'Sí, aplicada');
      await L.waitToast(page, 'Recomendación Aplicada');
      await L.goto(page, '/auditoria');
      await L.waitText(page, 'Directorio de Personal');
      await L.clickText(page, 'Audit Trail');
      await L.waitText(page, 'RECOMMENDATION_APPLIED');
      const hit = (await simLogs(tok)).find((l) => l.action === 'RECOMMENDATION_APPLIED');
      check(/\d{2}\/\d{2}\/\d{4}/.test(hit.timestamp) && hit.details, `registro incompleto: ${JSON.stringify(hit)}`);
    }));
};
