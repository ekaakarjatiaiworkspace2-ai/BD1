"""Render using real bootstrap data; no fake completed business results."""
import sys,os,asyncio,base64
from pathlib import Path
from fastapi.testclient import TestClient
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
os.environ['EKA_DATA_DIR']='/tmp/eka_v5_preview_data'
sys.path.insert(0,str(ROOT))
import app
passw=dict(l.split(': ',1) for l in (Path(os.environ['EKA_DATA_DIR'])/'AKUN_AWAL.txt').read_text().strip().splitlines())
D={}
for user,pwd in passw.items():
 c=TestClient(app.app);r=c.post('/api/login',json={'username':user,'password':pwd});assert r.status_code==200
 D[user]=c.get('/api/bootstrap').json()
html=(ROOT/'static/index.html').read_text()
html=html.replace('<link rel="stylesheet" href="/static/style.css">','').replace('<script defer src="/static/app.js"></script>','')
css=(ROOT/'static/style.css').read_text();js=(ROOT/'static/app.js').read_text()
# Use file-origin favicon/icon link disabled in screenshot; CSS/auth/logo images are file paths available to chromium with file access.
for name in ['eka-icon-192.png','eka-emblem.png','eka-logo-resmi.png']:
 mime='image/png';uri='data:'+mime+';base64,'+base64.b64encode((ROOT/'static/assets'/name).read_bytes()).decode()
 html=html.replace('/static/assets/'+name,uri)
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--allow-file-access-from-files'])
  for user,size in [('ahmad',(1440,950)),('donny',(1366,900)),('angga',(390,844)),('management',(390,844)),('ahmad',(390,844)),('ahmad',(320,730))]:
   key=f'{user}_{size[0]}'
   page=await browser.new_page(viewport={'width':size[0],'height':size[1]},device_scale_factor=1)
   errors=[];page.on('pageerror',lambda e: errors.append(str(e)))
   await page.set_content(html)
   await page.add_style_tag(content=css)
   # Inject read-only server snapshot, refresh API return. Buttons for state-changing actions are separately tested through FastAPI.
   await page.evaluate("payload=>{window.fetch=async()=>({ok:true,json:async()=>payload})}",D[user])
   await page.add_script_tag(content=js)
   await page.wait_for_timeout(700);await page.wait_for_selector('#app:not([hidden])',timeout=3000)
   await page.screenshot(path=str(ROOT/'static'/f'preview_{key}.png'),full_page=True)
   print(key,'view',await page.locator('#content h1').first.inner_text(),'nav',await page.locator('#mainNav button').count(),'errors',errors[:3])
   if size[0]<=390:
    await page.locator('#openMobile').click()
    await page.wait_for_timeout(300)
    await page.screenshot(path=str(ROOT/'static'/f'preview_{key}_menu.png'),full_page=True)
    print('mobile menu visible',await page.locator('#sidebar').evaluate('(el)=>el.classList.contains("mobile-open")'))
    await page.locator('#closeMobile').click()
   if user=='ahmad' and size[0]==1440:
    await page.locator('[data-nav=timeline]').first.click()
    await page.screenshot(path=str(ROOT/'static'/'preview_timeline.png'),full_page=True)
    print('timeline',await page.locator('.gantt-row').count())
   await page.close()
  await browser.close()
asyncio.run(main())
