// Utilidades compartidas: cliente de API, navegador, registro de resultados.
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const BASE = process.env.E2E_BASE || 'http://localhost:3000';
const API = process.env.E2E_API || 'http://localhost:8000';
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const FIX = path.join(__dirname, 'fixtures');
const DOWNLOADS = path.join(__dirname, 'downloads');

const results = [];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const norm = (s) => String(s).toLowerCase().replace(/\s+/g, ' ').trim();

// ---------- registro de casos ----------
async function cp(id, title, fn) {
  const t0 = Date.now();
  try {
    await fn();
    results.push({ id, title, ok: true, ms: Date.now() - t0 });
    console.log(`  PASA   ${id}  ${title}`);
  } catch (e) {
    results.push({ id, title, ok: false, ms: Date.now() - t0, error: e.message });
    console.log(`  FALLA  ${id}  ${title}\n         -> ${e.message.split('\n')[0]}`);
  }
}
function check(cond, msg) { if (!cond) throw new Error(msg); }
function eq(actual, expected, msg) {
  if (actual !== expected) throw new Error(`${msg}: esperado ${JSON.stringify(expected)}, obtenido ${JSON.stringify(actual)}`);
}

// ---------- API ----------
async function api(p, { method = 'GET', token, json, form } = {}) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  let body;
  if (json !== undefined) { headers['Content-Type'] = 'application/json'; body = JSON.stringify(json); }
  if (form) { headers['Content-Type'] = 'application/x-www-form-urlencoded'; body = new URLSearchParams(form).toString(); }
  const res = await fetch(`${API}${p}`, { method, headers, body });
  const text = await res.text();
  let data; try { data = JSON.parse(text); } catch { data = text; }
  return { status: res.status, data };
}
async function apiLogin(username, password) {
  const r = await api('/auth/login', { method: 'POST', form: { username, password } });
  check(r.status === 200, `login API ${username}: HTTP ${r.status}`);
  return r.data.access_token;
}

// ---------- usuarios de prueba (uno por rol) ----------
const USERS = {
  ADMIN: { username: 'AdministradorTest', full_name: 'Administrador de Prueba', password: 'AdministradorTest' },
  SUPERVISOR: { username: 'SupervisorTest', full_name: 'Supervisor de Prueba', password: 'SupervisorTest' },
  GERENTE: { username: 'GerenteTest', full_name: 'Gerente de Prueba', password: 'GerenteTest' },
  AUDITOR: { username: 'AuditorTest', full_name: 'Auditor de Prueba', password: 'AuditorTest' },
};
async function ensureUsers(adminToken) {
  for (const [role, u] of Object.entries(USERS)) {
    const r = await api('/users/', { method: 'POST', token: adminToken, json: { ...u, role } });
    check([201, 409].includes(r.status), `crear ${u.username}: HTTP ${r.status} ${JSON.stringify(r.data)}`);
  }
}

// ---------- navegador ----------
async function launch() {
  fs.mkdirSync(DOWNLOADS, { recursive: true });
  return puppeteer.launch({ executablePath: CHROME, headless: 'new', args: ['--no-sandbox'] });
}
async function newSession(browser) {
  const ctx = await browser.createBrowserContext();
  const page = await ctx.newPage();
  await page.setViewport({ width: 1440, height: 1000 });
  page.dialogs = []; // confirm("¿Revocar acceso permanentemente?") se acepta y se registra
  page.on('dialog', async (d) => { page.dialogs.push(d.message()); await d.accept(); });
  const cdp = await browser.target().createCDPSession();
  await cdp.send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: DOWNLOADS, browserContextId: ctx.id });
  return { ctx, page };
}
async function withSession(browser, fn) {
  const { ctx, page } = await newSession(browser);
  try { return await fn(page); } finally { await ctx.close(); }
}

async function bodyText(page) { return page.evaluate(() => document.body.innerText); }
async function waitText(page, text, timeout = 12000) {
  const t = norm(text);
  try {
    await page.waitForFunction((x) => document.body.innerText.toLowerCase().replace(/\s+/g, ' ').includes(x), { timeout, polling: 100 }, t);
  } catch {
    const body = norm((await bodyText(page)).slice(0, 700));
    throw new Error(`no apareció el texto "${text}". Pantalla: "${body}"`);
  }
}
// Espera el texto dentro del toast (esquina inferior derecha), no en el resto de la pantalla
async function waitToast(page, text, timeout = 12000) {
  const t = norm(text);
  try {
    await page.waitForFunction((x) => {
      const el = document.querySelector('div.fixed.bottom-6.right-6');
      return !!el && el.innerText.toLowerCase().replace(/\s+/g, ' ').includes(x);
    }, { timeout, polling: 100 }, t);
  } catch {
    const el = await page.$('div.fixed.bottom-6.right-6');
    const now = el ? norm(await page.evaluate((e) => e.innerText, el)) : '(sin toast)';
    throw new Error(`el toast no mostró "${text}". Toast actual: "${now}"`);
  }
}
async function expectNoText(page, text, settleMs = 600) {
  await sleep(settleMs);
  check(!norm(await bodyText(page)).includes(norm(text)), `no debía aparecer "${text}"`);
}

async function uiLogin(page, username, password, { waitHome = true } = {}) {
  await page.goto(`${BASE}/login`, { waitUntil: 'networkidle0' });
  await page.type('input:not([type=password])', username);
  await page.type('input[type=password]', password);
  await page.click('button[type=submit]');
  if (waitHome) await page.waitForFunction(() => !location.pathname.startsWith('/login'), { timeout: 15000 });
}
async function loginAs(page, role) { await uiLogin(page, USERS[role].username, USERS[role].password); await sleep(400); }
async function goto(page, p) { await page.goto(`${BASE}${p}`, { waitUntil: 'networkidle0' }); await sleep(300); }

async function menuItems(page) {
  await sleep(500);
  return page.$$eval('a[href^="/"]', (as) => as.map((a) => a.innerText.trim()).filter(Boolean));
}

async function clickText(page, text, tag = 'button') {
  const [el] = await page.$$(`xpath/.//${tag}[contains(normalize-space(.), "${text}")]`);
  check(el, `no existe ${tag} con texto "${text}"`);
  await el.click();
}
async function clear(page, sel) {
  await page.click(sel, { clickCount: 3 });
  await page.keyboard.press('Backspace');
}
async function fill(page, sel, value) {
  await clear(page, sel);
  if (value !== '' && value !== null && value !== undefined) await page.type(sel, String(value));
}
async function inputByLabel(page, labelText) {
  const [el] = await page.$$(`xpath/.//label[contains(normalize-space(.), "${labelText}")]/following::input[1]`);
  check(el, `no existe input para la etiqueta "${labelText}"`);
  return el;
}
async function valueOf(page, sel) { return page.$eval(sel, (e) => e.value); }

// ---------- simulador ----------
const SIM_FIELDS = ['tempExt', 'humExt', 'tempUma', 'humUma', 'presionInyeccion', 'pwrActual', 'humSala', 'setpoint', 'tempSala'];
const SIM_BASE = { tempExt: 20.4, humExt: 78, tempUma: 22.5, humUma: 50.4, presionInyeccion: 100, pwrActual: 70, humSala: 44.7, setpoint: 50, tempSala: 22.4 };
async function simFill(page, overrides = {}) {
  const values = { ...SIM_BASE, ...overrides };
  for (const k of SIM_FIELDS) await fill(page, `#field-${k}`, values[k] ?? '');
}
async function simGenerate(page) {
  await clickText(page, 'Generar Recomendación');
  await page.waitForSelector('.text-6xl', { timeout: 30000 });
  return page.$eval('.text-6xl', (e) => e.innerText.trim());
}

module.exports = {
  BASE, API, FIX, DOWNLOADS, USERS, results, sleep, norm, cp, check, eq, api, apiLogin, ensureUsers, launch, newSession, withSession,
  bodyText, waitText, waitToast, expectNoText, uiLogin, loginAs, goto, menuItems, clickText, clear, fill, inputByLabel, valueOf, SIM_FIELDS, SIM_BASE, simFill, simGenerate,
};
