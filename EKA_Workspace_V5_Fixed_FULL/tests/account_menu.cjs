// Run: node tests/account_menu.cjs (Python venv and Chrome required).
// Uses an isolated temporary database and Chrome profile; never touches data/.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const { spawn } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(fn) {
 for (let i = 0; i < 100; i++) { try { const result = await fn(); if (result) return result; } catch {} await delay(100); }
 throw new Error('Timed out waiting for browser/server');
}
async function main() {
 const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'eka-account-test-'));
 const base = 'http://127.0.0.1:18765';
 const server = spawn(path.join(root, '.venv/Scripts/python.exe'), ['-m', 'uvicorn', 'app:app', '--host', '127.0.0.1', '--port', '18765'], {
  cwd: root, windowsHide: true, env: { ...process.env, EKA_DATA_DIR: path.join(tmp, 'data') }, stdio: 'ignore'
 });
 let chrome, socket;
 try {
  await until(async () => (await fetch(base + '/api/health')).ok);
  const credentials = Object.fromEntries((await fs.readFile(path.join(tmp, 'data/AKUN_AWAL.txt'), 'utf8')).trim().split('\n').map(line => line.trim().split(': ')));
  chrome = spawn(process.env.EKA_CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe', [
   '--headless=new', '--disable-gpu', '--no-first-run', '--remote-debugging-port=19222', '--remote-allow-origins=*', `--user-data-dir=${path.join(tmp, 'chrome')}`, 'about:blank'
  ], { windowsHide: true, stdio: 'ignore' });
  const target = await until(async () => (await (await fetch('http://127.0.0.1:19222/json')).json()).find(t => t.type === 'page'));
  socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
  let serial = 0; const pending = new Map(), errors = [];
  socket.onmessage = event => {
   const message = JSON.parse(event.data);
   if (message.method === 'Runtime.exceptionThrown') errors.push(message.params.exceptionDetails.text);
   if (message.id) { const p = pending.get(message.id); pending.delete(message.id); message.error ? p.reject(Error(message.error.message)) : p.resolve(message.result); }
  };
  const send = (method, params = {}) => new Promise((resolve, reject) => { const id = ++serial; pending.set(id, { resolve, reject }); socket.send(JSON.stringify({ id, method, params })); });
  const evaluate = async expression => {
   const result = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
   if (result.exceptionDetails) throw Error(JSON.stringify(result.exceptionDetails));
   return result.result.value;
  };
  const click = async selector => {
   const point = await evaluate(`(()=>{const el=document.querySelector(${JSON.stringify(selector)}),r=el.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2,reachable:el.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))}})()`);
   assert(point.reachable, selector + ' must be reachable by pointer');
   await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: point.x, y: point.y, button: 'left', clickCount: 1 });
   await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: point.x, y: point.y, button: 'left', clickCount: 1 });
  };
  await send('Runtime.enable'); await send('Page.enable');
  await send('Page.navigate', { url: base });
  await until(() => evaluate(`!!document.querySelector('#login:not([hidden])')`));
  const login = async (username='ahmad') => {
   await evaluate(`document.querySelector('[name=username]').value=${JSON.stringify(username)};document.querySelector('[name=password]').value=${JSON.stringify(credentials[username])};document.querySelector('#loginForm').requestSubmit()`);
   await until(() => evaluate(`!!document.querySelector('#app:not([hidden]) #content h1')`));
  };
  for (const width of [1440, 390, 320]) {
   await send('Emulation.setDeviceMetricsOverride', { width, height: 900, deviceScaleFactor: 1, mobile: width < 961 });
   await evaluate(`document.querySelector('#login-password').value='uji-tombol-mata'`);
   await click('#loginForm [data-password-toggle]');
   assert(await evaluate(`document.querySelector('#login-password').type==='text' && document.querySelector('#login-password').value==='uji-tombol-mata' && document.querySelector('#loginForm [data-password-toggle]').getAttribute('aria-pressed')==='true' && !document.querySelector('#login').hidden`));
   await click('#loginForm [data-password-toggle]');
   assert(await evaluate(`document.querySelector('#login-password').type==='password' && document.querySelector('#loginForm [data-password-toggle]').getAttribute('aria-label')==='Tampilkan kata sandi'`));
   await click('#loginForm [data-password-toggle]');
   await login();
   assert.equal(await evaluate(`document.querySelector('#login-password').type`), 'password');
   await click('#topAvatar');
   const layout = await evaluate(`(()=>{const menu=document.querySelector('#accountMenu'),r=menu.getBoundingClientRect();return {visible:!menu.hidden,left:r.left,right:r.right,width:innerWidth,display:getComputedStyle(document.querySelector('#logout')).display,description:getComputedStyle(document.querySelector('#logout small')).display,name:getComputedStyle(document.querySelector('#accountDisplayName')).display}})()`);
   assert(layout.visible && layout.left >= 0 && layout.right <= layout.width);
   assert.equal(layout.display, 'flex'); assert.equal(layout.description, 'block'); assert.equal(layout.name, 'block');
   await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape' });
   assert(await evaluate(`document.querySelector('#accountMenu').hidden && document.activeElement.id==='topAvatar'`));
   await click('#topAvatar');
   await click('#changePassword');
   assert(await evaluate(`!document.querySelector('#drawerBackdrop').hidden && !!document.querySelector('#passwordForm')`));
   await click('[aria-controls="edit-old"]');
   assert(await evaluate(`document.querySelector('#edit-old').type==='text' && document.querySelector('#edit-new').type==='password'`));
   await click('[aria-controls="edit-new"]');
   assert(await evaluate(`document.querySelector('#edit-old').type==='text' && document.querySelector('#edit-new').type==='text' && !document.querySelector('#drawerBackdrop').hidden`));
   const passwordLayout = await evaluate(`(()=>{const input=document.querySelector('#edit-new'),button=document.querySelector('[aria-controls="edit-new"]'),r=input.getBoundingClientRect(),b=button.getBoundingClientRect();return {padding:parseFloat(getComputedStyle(input).paddingRight),buttonWidth:b.width,inside:b.left>=r.left&&b.right<=r.right}})()`);
   assert(passwordLayout.inside && passwordLayout.padding >= passwordLayout.buttonWidth);
   await click('#closeDrawer'); await click('#topAvatar');
   // Failure keeps the account open and reports a useful error, so retry is possible.
   await evaluate(`window.realFetch=window.fetch;window.fetch=(url,init)=>url==='/api/logout'?Promise.resolve(new Response(JSON.stringify({detail:'Uji server gagal'}),{status:500})):realFetch(url,init)`);
   await click('#logout');
   await until(() => evaluate(`!document.querySelector('#logout').disabled`));
   assert(await evaluate(`!document.querySelector('#app').hidden && document.querySelector('#toast').textContent.includes('Gagal keluar')`));
   // Delay the real request to check busy state and duplicate-click protection.
   await evaluate(`window.logoutRequests=0;window.fetch=async(url,init)=>{if(url==='/api/logout'){logoutRequests++;await new Promise(r=>setTimeout(r,300))}return realFetch(url,init)}`);
   await click('#logout');
   assert(await evaluate(`document.querySelector('#logout').disabled && document.querySelector('#logout').getAttribute('aria-busy')==='true'`));
   await evaluate(`logout()`);
   await until(() => evaluate(`!document.querySelector('#login').hidden`));
   assert.equal(await evaluate(`logoutRequests`), 1);
   assert.equal(await evaluate(`fetch('/api/bootstrap').then(r=>r.status)`), 401);
   assert(await evaluate(`document.querySelector('#content').childElementCount===0 && document.querySelector('[name=password]').value==='' && document.querySelector('[name=password]').type==='password'`));
   await evaluate(`window.fetch=realFetch`);
   console.log(`PASS ${width}px: password visibility (login/old/new), layout, logout failure/retry, busy state, server session revoked`);
  }
  // A bootstrap response arriving after logout must never reopen the workspace.
  await login();
  await evaluate(`window.fetch=(url,init)=>url==='/api/bootstrap'?realFetch(url,init).then(response=>new Promise(resolve=>{window.releaseBootstrap=()=>resolve(response)})):realFetch(url,init);window.pendingRefresh=refresh();undefined`);
  await until(() => evaluate(`typeof releaseBootstrap==='function'`));
  await click('#topAvatar'); await click('#logout');
  await until(() => evaluate(`!document.querySelector('#login').hidden`));
  await evaluate(`releaseBootstrap();pendingRefresh`);
  assert(await evaluate(`document.querySelector('#app').hidden && !document.querySelector('#login').hidden`));
  await evaluate(`window.fetch=realFetch`);
  // Expired sessions also return to login cleanly.
  await login();
  await evaluate(`request('/api/logout',{method:'POST',body:'{}'})`);
  await click('#topAvatar'); await click('#logout');
  await until(() => evaluate(`!document.querySelector('#login').hidden`));
  assert.deepEqual(errors, []);
  const cache = await evaluate(`navigator.serviceWorker.ready.then(async()=>({keys:await caches.keys(),assets:(await(await caches.open('eka-ui-v6-3-drive-documents')).keys()).map(r=>new URL(r.url).pathname+new URL(r.url).search)}))`);
  assert(cache.keys.includes('eka-ui-v6-3-drive-documents'));
  assert(cache.assets.includes('/static/style.css?v=6.3') && cache.assets.includes('/static/app.js?v=6.3') && cache.assets.includes('/static/coverage.js?v=6.3'));
  await fs.mkdir(path.join(root, 'tests/artifacts'), { recursive: true });
  await evaluate(`document.querySelector('#toast').classList.remove('on')`);
  const loginShot = await send('Page.captureScreenshot');
  await fs.writeFile(path.join(root, 'tests/artifacts/password-toggle-mobile.png'), Buffer.from(loginShot.data, 'base64'));
  await login(); await click('#topAvatar');
  await evaluate(`document.querySelector('#toast').classList.remove('on')`);
  await fs.mkdir(path.join(root, 'tests/artifacts'), { recursive: true });
  const shot = await send('Page.captureScreenshot');
  await fs.writeFile(path.join(root, 'tests/artifacts/account-menu-mobile.png'), Buffer.from(shot.data, 'base64'));
  console.log('PASS late bootstrap after logout, expired session, PWA versioned assets, no browser exceptions; screenshot: tests/artifacts/account-menu-mobile.png');
  await click('#logout');
  await until(() => evaluate(`!document.querySelector('#login').hidden`));
  await login('angga');
  const fixtures=[path.join(tmp,'Laporan.pdf'),path.join(tmp,'Neraca.xlsx')];
  await fs.writeFile(fixtures[0],'%PDF-1.4\nLaporan dummy');
  await fs.writeFile(fixtures[1],Buffer.from('504b0304','hex'));
  const selectFiles=async()=>{
   const {root:document}=await send('DOM.getDocument');
   const {nodeId}=await send('DOM.querySelector',{nodeId:document.nodeId,selector:'#annualForm input[name=files]'});
   await send('DOM.setFileInputFiles',{nodeId,files:fixtures});
  };
  for(const width of [1440,390]){
   const year=width===1440?2021:2022;
   await send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:width<961});
   await evaluate(`goto('data')`);
   await until(()=>evaluate(`!!document.querySelector('#annualForm') && !archiveLoading && !coverageLoading`));
   await evaluate(`document.querySelector('#annualForm [name=fiscal_year]').value=${year};document.querySelector('#annualCategory').value='Laporan Keuangan';document.querySelector('#annualCategory').dispatchEvent(new Event('change',{bubbles:true}))`);
   assert(await evaluate(`D.data.find(row=>row.id===document.querySelector('#annualForm [name=data_ref]').value).category==='Laporan Keuangan'`));
   await selectFiles();
   assert(await evaluate(`document.querySelector('#annualFileList').textContent.includes('2 file dipilih')`));
   await evaluate(`document.querySelector('#dataSearch').value='Laba';document.querySelector('#dataSearch').dispatchEvent(new Event('input',{bubbles:true}))`);
   assert.equal(await evaluate(`document.querySelector('#annualForm [name=files]').files.length`),2);
   await evaluate(`document.querySelector('#dataSearch').value='';document.querySelector('#dataSearch').dispatchEvent(new Event('input',{bubbles:true}))`);
   // Archive filters must preserve files already selected for upload.
   await evaluate(`document.querySelector('#archiveYear').value='2024';document.querySelector('#archiveYear').dispatchEvent(new Event('change',{bubbles:true}))`);
   await until(()=>evaluate(`!archiveLoading && !coverageLoading && coverageScopeKey===coverageKey(selectedCoverageScope())`));
   assert.equal(await evaluate(`document.querySelector('#annualForm [name=files]').files.length`),2);
   await evaluate(`document.querySelector('#annualSubmit').scrollIntoView({block:'center'})`);
   await click('#annualSubmit');
   await until(()=>evaluate(`document.querySelector('#annualResult').textContent.includes('2 dokumen tersimpan') && !archiveLoading && !coverageLoading`));
   assert(await evaluate(`archiveDocs.length===2 && archiveDocs.every(doc=>doc.fiscal_year===${year}&&doc.category==='Laporan Keuangan')`));
   assert(await evaluate(`coverageData.current.done && coverageData.current.missing_periods.length===0 && document.querySelector('#coverageSummary').textContent.includes('Data bulanan tidak wajib')`));
   assert.equal(await evaluate(`document.documentElement.scrollWidth<=innerWidth`),true);
   await evaluate(`document.querySelector('.annual-title').scrollIntoView({block:'start'});document.querySelector('#toast').classList.remove('on')`);
   const batchShot=await send('Page.captureScreenshot',{captureBeyondViewport:true});
   await fs.writeFile(path.join(root,`tests/artifacts/batch-upload-${width}.png`),Buffer.from(batchShot.data,'base64'));
   await selectFiles();
   await evaluate(`document.querySelector('#annualSubmit').scrollIntoView({block:'center'})`);
   await click('#annualSubmit');
   await until(()=>evaluate(`document.querySelector('#annualResult').textContent.includes('0 dokumen tersimpan') && !archiveLoading`));
   assert(await evaluate(`document.querySelector('#annualResult').textContent.includes('2 file identik dilewati') && archiveTotal===2`));
   // Explicit monthly requirements can be tracked independently from annual-only years.
   await evaluate(`document.querySelector('#coverageMode').value='bulanan';document.querySelector('#coverageMode').dispatchEvent(new Event('change',{bubbles:true}));document.querySelector('#saveCoverage').scrollIntoView({block:'center'})`);
   await click('#saveCoverage');
   await until(()=>evaluate(`!coverageLoading && coverageData.current.mode==='bulanan'`));
   assert(await evaluate(`!coverageData.current.done && coverageData.current.missing_periods.length===12`));
   // A justified custom plan can request only the periods actually needed.
   await evaluate(`document.querySelector('#coverageMode').value='khusus';document.querySelector('#coverageMode').dispatchEvent(new Event('change',{bubbles:true}));document.querySelector('[name=coverage_period][value=jan]').checked=true;document.querySelector('[name=coverage_period][value=mar]').checked=true;document.querySelector('[name=coverage_note]').value='Kajian hanya membutuhkan Januari dan Maret';document.querySelector('#saveCoverage').scrollIntoView({block:'center'})`);
   await click('#saveCoverage');
   await until(()=>evaluate(`!coverageLoading && coverageData.current.mode==='khusus'`));
   assert(await evaluate(`coverageData.current.missing_periods.join(',')==='jan,mar'`));
   await evaluate(`document.querySelector('#coverageMode').value='tahunan';document.querySelector('#coverageMode').dispatchEvent(new Event('change',{bubbles:true}));document.querySelector('[name=coverage_note]').value='Hanya data tahunan tersedia; bulanan tidak diperlukan';document.querySelector('#saveCoverage').scrollIntoView({block:'center'})`);
   await click('#saveCoverage');
   await until(()=>evaluate(`!coverageLoading && coverageData.current.mode==='tahunan' && coverageData.current.done`));
   assert.equal(await evaluate(`document.documentElement.scrollWidth<=innerWidth`),true);
   await evaluate(`document.querySelector('.coverage-settings').scrollIntoView({block:'start'});document.querySelector('#toast').style.transition='none';document.querySelector('#toast').classList.remove('on')`);
   const coverageShot=await send('Page.captureScreenshot');
   await fs.writeFile(path.join(root,`tests/artifacts/coverage-${width}.png`),Buffer.from(coverageShot.data,'base64'));
   console.log(`PASS ${width}px: Angga batch Excel/PDF, year/category, selected-file preview, filters preserve files, duplicate retry, no horizontal overflow`);
   console.log(`PASS ${width}px: annual-only Done, monthly missing periods, custom plan, saved annual requirement and year history`);
  }
  assert(await evaluate(`coverageData.history.some(row=>row.fiscal_year===2021&&row.done)&&coverageData.history.some(row=>row.fiscal_year===2022&&row.done)`));
  await evaluate(`goto('home');goto('data')`);
  await until(()=>evaluate(`!coverageLoading && document.querySelector('#coverageSummary').textContent.includes('Done')`));
  assert(await evaluate(`document.querySelector('#coverageMode').value==='tahunan' && coverageData.current.fiscal_year===2022 && coverageData.current.done`));
  for(const width of [1440,390]){
   const year=width===1440?2020:2019;
   await send('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:width<961});
   await evaluate(`document.querySelector('#annualForm').elements.fiscal_year.value=${year};document.querySelector('#annualForm').elements.fiscal_year.dispatchEvent(new Event('change',{bubbles:true}))`);
   await until(()=>evaluate(`!coverageLoading && coverageData.current.fiscal_year===${year}`));
   await evaluate(`document.querySelector('#annualForm').elements.gdrive_url.value='https://drive.google.com/drive/folders/folder-finance-${year}';document.querySelector('#annualForm').elements.link_title.value='Laporan tahunan ${year} dari Drive';document.querySelector('#annualSubmit').scrollIntoView({block:'center'})`);
   await click('#annualSubmit');
   await until(()=>evaluate(`!archiveLoading && !coverageLoading && coverageData.current.done && coverageData.current.link_count===1 && coverageData.current.file_count===0`));
   assert(await evaluate(`archiveDocs.length===1 && archiveDocs[0].source_type==='google_drive' && document.querySelector('#annualArchive a').textContent==='Buka Google Drive' && document.querySelector('#annualArchive a').target==='_blank'`));
   await selectFiles();
   await evaluate(`document.querySelector('#annualForm').elements.gdrive_url.value='https://example.com/not-drive';document.querySelector('#annualSubmit').scrollIntoView({block:'center'})`);
   await click('#annualSubmit');
   await until(()=>evaluate(`document.querySelector('#annualResult').textContent.includes('Pengiriman gagal')`));
   assert(await evaluate(`document.querySelector('#annualForm').elements.files.files.length===2 && document.querySelector('#annualForm').elements.gdrive_url.value==='https://example.com/not-drive'`));
   await evaluate(`document.querySelector('#annualForm').elements.gdrive_url.value='https://docs.google.com/spreadsheets/d/sheet-finance-${year}/edit';document.querySelector('#annualSubmit').scrollIntoView({block:'center'})`);
   await click('#annualSubmit');
   await until(()=>evaluate(`!archiveLoading && !coverageLoading && coverageData.current.link_count===2 && coverageData.current.file_count===2`));
   assert(await evaluate(`archiveTotal===4 && document.querySelector('#annualForm').elements.files.files.length===0 && document.querySelector('#annualForm').elements.gdrive_url.value===''`));
   assert.equal(await evaluate(`document.documentElement.scrollWidth<=innerWidth`),true);
   await evaluate(`document.querySelector('.drive-inputs').scrollIntoView({block:'start'});document.querySelector('#toast').classList.remove('on')`);
   const driveShot=await send('Page.captureScreenshot');
   await fs.writeFile(path.join(root,`tests/artifacts/drive-upload-${width}.png`),Buffer.from(driveShot.data,'base64'));
   console.log(`PASS ${width}px: Google Drive only, annual Done, external action, invalid URL preserves input, mixed files/link, no horizontal overflow`);
  }
  // Exercise the shared form handler with text fields and repeated checkbox values.
  await evaluate(`goto('tasks')`);
  await click('#content [data-open]');
  await evaluate(`document.querySelector('#drawerBody [data-open^="sub:"]').scrollIntoView({block:'center'})`);
  await click('#drawerBody [data-open^="sub:"]');
  const editedTask=await evaluate(`detail.id`);
  await evaluate(`document.querySelector('#subForm [name=actual_result]').value='Hasil uji formulir JavaScript';document.querySelector('#subForm [name=check]').checked=true;document.querySelector('#subForm [value=save]').scrollIntoView({block:'center'})`);
  await click('#subForm [value=save]');
  await until(()=>evaluate(`D.tasks.find(task=>task.id===${JSON.stringify(editedTask)}).actual_result==='Hasil uji formulir JavaScript'`));
  assert(await evaluate(`document.querySelector('#subForm [name=check]').checked`));
  await click('#closeDrawer');
  await evaluate(`goto('chat');document.querySelector('#chatForm [name=body]').value='Uji kirim pesan setelah pemeriksaan JavaScript';document.querySelector('#chatForm button').scrollIntoView({block:'center'})`);
  await click('#chatForm button');
  await until(()=>evaluate(`D.messages.some(message=>message.body==='Uji kirim pesan setelah pemeriksaan JavaScript')`));
  assert.equal(await evaluate(`dayDifference('2024-03-01','2024-02-28')`),2);
  console.log('PASS shared handlers: open task, save text/checklist, send chat, date calculation');
  assert.deepEqual(errors,[]);
 } finally {
  if (socket) socket.close();
  if (chrome) chrome.kill();
  server.kill();
  // Keep temporary files out of the project; the OS temporary directory owns cleanup.
 }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
