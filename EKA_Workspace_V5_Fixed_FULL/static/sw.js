const CACHE='eka-ui-v6-3-drive-documents';
const STATIC=['/','/static/style.css?v=6.3','/static/app.js?v=6.3','/static/annual.js?v=6.3','/static/coverage.js?v=6.3','/static/assets/eka-logo-lockup.png','/static/assets/eka-logo-resmi.png','/static/assets/eka-icon-192.png','/static/assets/eka-icon-512.png','/static/assets/eka-emblem.png','/manifest.webmanifest'];
const STATIC_PATHS=new Set(STATIC.map(path=>new URL(path,self.location.origin).pathname));
const serviceWorker=/** @type {ServiceWorkerGlobalScope} */(/** @type {unknown} */(self));

serviceWorker.addEventListener('install',event=>{
 event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(STATIC)).then(()=>serviceWorker.skipWaiting()));
});
serviceWorker.addEventListener('activate',event=>{
 event.waitUntil(caches.keys()
  .then(keys=>Promise.all(keys.filter(key=>key.startsWith('eka-ui-')&&key!==CACHE).map(key=>caches.delete(key))))
  .then(()=>serviceWorker.clients.claim()));
});
serviceWorker.addEventListener('fetch',event=>{
 const url=new URL(event.request.url);
 if(event.request.method!=='GET'||url.origin!==self.location.origin||!STATIC_PATHS.has(url.pathname))return;
 // Fetch the current UI first; keep CSS/JS query versions intact in the offline cache.
 event.respondWith(fetch(event.request).then(response=>{
  if(response.ok){const copy=response.clone();event.waitUntil(caches.open(CACHE).then(cache=>cache.put(event.request,copy)))}
  return response;
 }).catch(async()=>await caches.match(event.request)||Response.error()));
});
