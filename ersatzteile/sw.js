// Eigener Service-Worker der eigenständigen Ersatzteilseite (Scope: /ersatzteile/).
// Komplett getrennt vom Konfigurator – eigener Cache-Namespace "ersatzteile-".
const CACHE="ersatzteile-v3";
const ASSETS=["./","./index.html","./manifest.webmanifest","./icon-192.png","./icon-512.png",
  "./vendor/three.module.min.js","./vendor/GLTFLoader.js","./vendor/OrbitControls.js","./vendor/BufferGeometryUtils.js","./vendor/RoomEnvironment.js"];

self.addEventListener("install",e=>{
  e.waitUntil(
    caches.open(CACHE)
      .then(c=>Promise.all(ASSETS.map(u=>c.add(u).catch(()=>{}))))
      .then(()=>self.skipWaiting())
  );
});

self.addEventListener("activate",e=>{
  // NUR eigene (ersatzteile-) Caches aufräumen – fremde (z.B. lepton-) bleiben unberührt
  e.waitUntil(
    caches.keys()
      .then(k=>Promise.all(k.filter(x=>x.startsWith("ersatzteile-")&&x!==CACHE).map(x=>caches.delete(x))))
      .then(()=>self.clients.claim())
  );
});

self.addEventListener("fetch",e=>{
  const req=e.request;
  if(req.method!=="GET")return;
  const isHTML=req.mode==="navigate"||(req.headers.get("accept")||"").includes("text/html");
  if(isHTML){
    // Online: IMMER frische Seite vom Netz holen (HTTP-Cache umgehen) und cachen.
    // Offline: gespeicherte Seite liefern.
    e.respondWith(
      fetch(req.url,{cache:"reload",credentials:"same-origin"}).then(resp=>{
        const cp=resp.clone();
        caches.open(CACHE).then(c=>{c.put("./index.html",cp).catch(()=>{});}).catch(()=>{});
        return resp;
      }).catch(()=>
        caches.match("./index.html",{ignoreSearch:true}).then(r=>r||caches.match("./",{ignoreSearch:true}))
      )
    );
    return;
  }
  // Übrige Dateien (3D-Modelle, three.js, Icons, Manifest): zuerst Cache, sonst Netzwerk (und cachen)
  e.respondWith(
    caches.match(req,{ignoreVary:true}).then(r=>r||fetch(req).then(resp=>{
      const cp=resp.clone();
      caches.open(CACHE).then(c=>c.put(req,cp)).catch(()=>{});
      return resp;
    }).catch(()=>caches.match("./index.html",{ignoreSearch:true})))
  );
});
