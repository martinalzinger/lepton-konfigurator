const CACHE="lepton-v2";
const ASSETS=["./","./index.html","./manifest.webmanifest","./icon-192.png","./icon-512.png"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()));});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==CACHE).map(x=>caches.delete(x)))).then(()=>self.clients.claim()));});
self.addEventListener("fetch",e=>{
  if(e.request.method!=="GET")return;
  const req=e.request;
  const isHTML=req.mode==="navigate"||(req.headers.get("accept")||"").includes("text/html");
  if(isHTML){
    // App-Seite: zuerst Netzwerk (damit Updates sofort erscheinen), sonst Cache (offline)
    e.respondWith(
      fetch(req).then(resp=>{const cp=resp.clone();caches.open(CACHE).then(c=>c.put("./index.html",cp)).catch(()=>{});return resp;})
        .catch(()=>caches.match(req).then(r=>r||caches.match("./index.html")))
    );
    return;
  }
  // Übrige Dateien: zuerst Cache (schnell/offline), sonst Netzwerk
  e.respondWith(caches.match(req).then(r=>r||fetch(req).then(resp=>{const cp=resp.clone();caches.open(CACHE).then(c=>c.put(req,cp)).catch(()=>{});return resp;}).catch(()=>caches.match("./index.html"))));
});
