// HU0003 (login/logout), HU0005 (usuarios) y HU0018-2 (auditoría de usuarios).
const L = require('./lib');
const { cp, check, eq, USERS, sleep } = L;

const MENUS = {
  ADMIN: ['Dashboard', 'Ingesta de Datos', 'Entrenamiento IA', 'Simulador de Ahorro', 'Auditoría'],
  SUPERVISOR: ['Dashboard', 'Ingesta de Datos', 'Simulador de Ahorro'],
  GERENTE: ['Dashboard'],
  AUDITOR: ['Auditoría'],
};

module.exports = async function (browser, ctx) {
  console.log('\n[HU0003] Login y cierre de sesión');

  const loginCases = [
    ['CP011', 'ADMIN', 'Login rol Administrador'],
    ['CP055', 'SUPERVISOR', 'Login rol Supervisor'],
    ['CP056', 'GERENTE', 'Login rol Gerente'],
    ['CP057', 'AUDITOR', 'Login rol Auditor'],
  ];
  for (const [id, role, title] of loginCases) {
    await cp(id, `${title}: "Autenticando Firma..." y módulos de su rol`, () =>
      L.withSession(browser, async (page) => {
        const u = USERS[role];
        await page.goto(`${L.BASE}/login`, { waitUntil: 'networkidle0' });
        await page.type('input:not([type=password])', u.username);
        await page.type('input[type=password]', u.password);
        const hidden = await page.$eval('input[type=password]', (e) => e.type);
        eq(hidden, 'password', 'la contraseña debe ocultarse');
        await page.click('button[type=submit]');
        await L.waitText(page, 'Autenticando Firma...', 4000);
        await page.waitForFunction(() => !location.pathname.startsWith('/login'), { timeout: 15000 });
        const items = await L.menuItems(page);
        const norm = (a) => a.map((x) => x.toLowerCase()).sort().join('|');
        eq(norm(items), norm(MENUS[role]), `menú de ${role}`);
      }));
  }

  await cp('CP012', 'Credenciales incorrectas: "Credenciales inválidas" y se queda en login', () =>
    L.withSession(browser, async (page) => {
      await L.uiLogin(page, USERS.ADMIN.username, '123456789', { waitHome: false });
      await L.waitText(page, 'Credenciales inválidas');
      check(page.url().includes('/login'), 'debe permanecer en /login');
    }));

  await cp('CP013', 'Cierre de sesión: redirige a login, limpia sesión y "Atrás" no la restaura', () =>
    L.withSession(browser, async (page) => {
      await L.loginAs(page, 'SUPERVISOR');
      await L.goto(page, '/simulador');
      const token = (await page.cookies()).find((c) => c.name === 'scada_token')?.value;
      await L.clickText(page, 'Finalizar Sesión');
      await page.waitForFunction(() => location.pathname === '/login', { timeout: 10000 });
      eq((await page.cookies()).length, 0, 'cookies restantes');
      const ls = await page.evaluate(() => Object.keys(localStorage).filter((k) => k.startsWith('scada_')));
      eq(ls.length, 0, 'claves scada_* en localStorage');
      for (let i = 0; i < 3; i++) {
        await page.goBack({ waitUntil: 'domcontentloaded' }).catch(() => {});
        await sleep(900);
        const where = page.url() === 'about:blank' ? '/login' : new URL(page.url()).pathname;
        check(where === '/login', `tras "Atrás" (${i + 1}) debía estar en /login y está en ${page.url()}`);
      }
      const r = await L.api('/dashboard/metrics', { token });
      eq(r.status, 401, 'el token cerrado debe rechazarse en el servidor');
    }));

  console.log('\n[HU0005] Gestión de usuarios');
  const tag = String(Date.now()).slice(-6);
  const nu = { username: `CarlosHT${tag}`, full_name: `Carlos Hernandez ${tag}`, password: '123456789' };

  async function openUsers(page) {
    await L.loginAs(page, 'ADMIN');
    await L.goto(page, '/auditoria');
    await sleep(500);
  }
  async function openModal(page) {
    await L.clickText(page, 'Nuevo Registro');
    await page.waitForSelector('form input[type=password]');
  }
  async function modalFill(page, { full_name, username, role, password }) {
    const inputs = await page.$$('form input[type=text]');
    if (full_name !== undefined) { await inputs[0].click({ clickCount: 3 }); await page.keyboard.press('Backspace'); if (full_name) await inputs[0].type(full_name); }
    if (username !== undefined) { await inputs[1].click({ clickCount: 3 }); await page.keyboard.press('Backspace'); if (username) await inputs[1].type(username); }
    if (role) await page.select('form select', role);
    if (password !== undefined) { await page.click('form input[type=password]', { clickCount: 3 }); await page.keyboard.press('Backspace'); if (password) await page.type('form input[type=password]', password); }
  }

  await cp('CP018', 'Listado de usuarios en cards (tab Usuarios activo para el Administrador)', () =>
    L.withSession(browser, async (page) => {
      await openUsers(page);
      await L.waitText(page, 'Directorio de Personal');
      await L.waitText(page, USERS.SUPERVISOR.full_name);
      await L.waitText(page, 'Audit Trail');
    }));

  await cp('CP019', 'Registro exitoso: "Nueva identidad GxP dada de alta en el sistema" y aparece en la lista', () =>
    L.withSession(browser, async (page) => {
      await openUsers(page);
      await openModal(page);
      await modalFill(page, { ...nu, role: 'SUPERVISOR' });
      await L.clickText(page, 'Crear Identidad');
      await L.waitText(page, 'Nueva identidad GxP dada de alta en el sistema');
      await L.waitText(page, nu.full_name);
    }));

  await cp('CP020', 'Username duplicado: "Transacción rechazada: Conflicto de unicidad en los datos de la cuenta"', () =>
    L.withSession(browser, async (page) => {
      await openUsers(page);
      await openModal(page);
      await modalFill(page, { full_name: `Otro Nombre ${tag}`, username: nu.username, role: 'AUDITOR', password: '123456789' });
      await L.clickText(page, 'Crear Identidad');
      await L.waitText(page, 'Transacción rechazada: Conflicto de unicidad en los datos de la cuenta');
    }));

  await cp('CP021', 'Campo obligatorio vacío: el formulario avisa "Completar este campo" y no crea el usuario', () =>
    L.withSession(browser, async (page) => {
      await openUsers(page);
      await openModal(page);
      await modalFill(page, { full_name: '', username: `Vacio${tag}`, role: 'AUDITOR', password: '123456789' });
      await L.clickText(page, 'Crear Identidad');
      await sleep(400);
      const missing = await page.$eval('form input[type=text]', (e) => e.validity.valueMissing);
      check(missing, 'el campo Nombre Completo debe marcarse como obligatorio');
      check(await page.$('form input[type=password]'), 'el formulario debe seguir abierto');
      const users = await L.api('/users/', { token: ctx.adminToken });
      check(!users.data.some((u) => u.username === `Vacio${tag}`), 'no debía crearse el usuario');
    }));

  await cp('CP022', 'Edición: "Identidad GxP actualizada con éxito" y nueva clave vigente', () =>
    L.withSession(browser, async (page) => {
      await openUsers(page);
      await L.waitText(page, nu.full_name);
      const [btn] = await page.$$(`xpath/.//*[contains(text(), "${nu.full_name}")]/ancestor::div[.//button[contains(., "Editar")]][1]//button[contains(., "Editar")]`);
      check(btn, 'no se halló el botón Editar de la card');
      await btn.click();
      await page.waitForSelector('form input[type=password]');
      await modalFill(page, { full_name: `${nu.full_name} Editado`, password: 'ContraseñaCambiada1' });
      await L.clickText(page, 'Guardar');
      await L.waitText(page, 'Identidad GxP actualizada con éxito');
      await L.waitText(page, `${nu.full_name} Editado`);
      await L.apiLogin(nu.username, 'ContraseñaCambiada1');
      const old = await L.api('/auth/login', { method: 'POST', form: { username: nu.username, password: nu.password } });
      eq(old.status, 401, 'la clave anterior debe dejar de funcionar');
    }));

  await cp('CP023', 'Revocación: confirmación, desaparece de la lista y el login queda "Credenciales inválidas"', () =>
    L.withSession(browser, async (page) => {
      await openUsers(page);
      await L.waitText(page, `${nu.full_name} Editado`);
      const [btn] = await page.$$(`xpath/.//*[contains(text(), "${nu.full_name} Editado")]/ancestor::div[.//button[contains(., "Revocar")]][1]//button[contains(., "Revocar")]`);
      check(btn, 'no se halló el botón Revocar');
      await btn.click();
      await L.waitText(page, 'Acceso revocado de manera inmutable en la base de datos de planta');
      check(page.dialogs.includes('¿Revocar acceso permanentemente?'), 'faltó el aviso de confirmación');
      await L.expectNoText(page, `${nu.full_name} Editado`);
    }));
  await cp('CP023b', 'Revocado: no puede iniciar sesión', () =>
    L.withSession(browser, async (page) => {
      await L.uiLogin(page, nu.username, 'ContraseñaCambiada1', { waitHome: false });
      await L.waitText(page, 'Credenciales inválidas');
    }));

  await cp('CP050', 'Auditoría de gestión de usuarios: USER_CREATED, USER_UPDATED y USER_DELETED', async () => {
    const logs = (await L.api('/audit/', { token: ctx.adminToken })).data;
    for (const action of ['USER_CREATED', 'USER_UPDATED', 'USER_DELETED']) {
      const hit = logs.find((l) => l.action === action && l.details.includes(nu.username));
      check(hit, `falta el evento ${action} de ${nu.username}`);
    }
    await L.withSession(browser, async (page) => {
      await L.loginAs(page, 'ADMIN');
      await L.goto(page, '/auditoria');
      await L.clickText(page, 'Audit Trail');
      await L.waitText(page, 'USER_CREATED');
      await L.waitText(page, 'USER_DELETED');
    });
  });
};
