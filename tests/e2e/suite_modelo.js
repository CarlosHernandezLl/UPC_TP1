// Disponibilidad del modelo de IA: respaldo compatible, Champion guardado en BD, arranque sin archivo y error explícito.
// Requiere Docker (docker compose exec / restart sobre el backend).
const path = require('path');
const { execSync } = require('child_process');
const L = require('./lib');
const { cp, check, eq, sleep } = L;

const ROOT = path.join(__dirname, '..', '..');
const env = { ...process.env, PATH: `${process.env.PATH};C:\\Program Files\\Docker\\Docker\\resources\\bin` };
const sh = (cmd, input) => execSync(cmd, { cwd: ROOT, env, input, stdio: ['pipe', 'pipe', 'pipe'] }).toString();
const py = (code) => sh('docker compose exec -T backend python -', code);
const psql = (sql) => sh(`docker compose exec -T db psql -U postgres -d hvac_db -tA -c "${sql}"`).trim();

async function waitBackend() {
  for (let i = 0; i < 60; i++) {
    try { if ((await fetch(`${L.API}/`)).ok) return; } catch { /* arrancando */ }
    await sleep(1500);
  }
  throw new Error('el backend no volvió a responder');
}
const BODY = { outdoor_temp: 20.4, outdoor_rh: 78, ahu_temp: 22.5, ahu_rh: 50.4, current_room_rh: 44.7, room_temp: 22.4, injection_pressure: 100, target_setpoint: 50 };
async function predict(token, power) {
  return (await L.api('/simulation/predict', { method: 'POST', token, json: { ...BODY, current_power: power } }));
}

module.exports = async function (browser, ctx) {
  const sup = await L.apiLogin(L.USERS.SUPERVISOR.username, L.USERS.SUPERVISOR.password);
  const aud = await L.apiLogin(L.USERS.AUDITOR.username, L.USERS.AUDITOR.password);

  console.log('\n[Modelo] Disponibilidad de la IA');
  await cp('MOD1', 'El modelo base (respaldo) ya es compatible: recomienda sin errores de nombres de variable', () => {
    const out = py([
      'from app.ml_engine.simulator_engine import SimulatorEngine',
      'e = SimulatorEngine()',
      'pw, alerta = e.recomendar_potencia(current_power=70, room_temp=22.4, target_setpoint=50, outdoor_temp=20.4, outdoor_rh=78, ahu_temp=22.5, ahu_rh=50.4, injection_pressure=100)',
      'print("RESULT", e.model_loaded, pw, alerta)',
    ].join('\n'));
    const m = out.match(/RESULT (\w+) ([\d.]+) (\w+)/);
    check(m && m[1] === 'True' && parseFloat(m[2]) <= 70, `salida: ${out}`);
  });

  await cp('MOD2', 'El Champion queda guardado en la BD (model_blob) y /mlops/metrics informa qué modelo está en memoria', async () => {
    const blobLen = parseInt(psql("select coalesce(length(model_blob),0) from ml_model_versions where status='ACTIVE'"), 10);
    check(blobLen > 1000, `el Champion no tiene contenido en la BD (${blobLen} bytes)`);
    const m = (await L.api('/mlops/metrics', { token: aud })).data;
    check(m.modelo_en_memoria && m.modelo_en_memoria.cargado === true, `modelo_en_memoria: ${JSON.stringify(m.modelo_en_memoria)}`);
    eq(m.modelo_en_memoria.version_tag, m.version_tag, 'versión en memoria vs. Champion');
  });

  await cp('MOD3', 'Sin el archivo del Champion (disco efímero) el simulador sigue recomendando: carga desde la BD', async () => {
    const tag = psql("select version_tag from ml_model_versions where status='ACTIVE'");
    const file = `/app/app/ml_engine/saved_models/xgboost_hvac_${tag}.json`;
    sh(`docker compose exec -T backend sh -c "mv ${file} ${file}.bak"`);
    try {
      sh('docker compose restart backend');
      await waitBackend();
      const r = await predict(sup, 85);
      eq(r.status, 200, 'predict sin archivo');
      check(r.data.potencia_recomendada < 85, `debe recomendar con el Champion (recomendó ${r.data.potencia_recomendada}% para 85%)`);
      const m = (await L.api('/mlops/metrics', { token: aud })).data;
      eq(m.modelo_en_memoria.origen, 'base de datos', 'origen del modelo en memoria');
      eq(m.modelo_en_memoria.version_tag, tag, 'versión en memoria');
    } finally {
      sh(`docker compose exec -T backend sh -c "mv ${file}.bak ${file}"`);
      sh('docker compose restart backend');
      await waitBackend();
    }
  });

  await cp('MOD4', 'Sin modelo utilizable la recomendación falla de forma explícita (no devuelve la potencia ingresada)', () => {
    const out = py([
      'from app.services.simulation_service import SimulationService, ModelUnavailableError',
      'class G:',
      '    def get_active_config(self): return None',
      'class E: model_loaded = False',
      's = SimulationService(None, G(), None, None, E())',
      'try:',
      '    s.predict_optimal_power({"current_power": 70, "room_temp": 22, "injection_pressure": 100})',
      '    print("SIN-ERROR")',
      'except ModelUnavailableError:',
      '    print("ERROR-EXPLICITO")',
    ].join('\n'));
    check(out.includes('ERROR-EXPLICITO'), `salida: ${out}`);
  });
};
