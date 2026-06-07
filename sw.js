const CACHE="lepton-v6";
const ASSETS=["./","./index.html","./ersatzteile.html","./manifest.webmanifest","./ersatzteile.webmanifest","./icon-192.png","./icon-512.png",
  "./vendor/three.module.min.js","./vendor/GLTFLoader.js","./vendor/OrbitControls.js","./vendor/BufferGeometryUtils.js"];

self.addEventListener("install",e=>{
  // Einzeln cachen, damit ein einzelner Fehler nicht das ganze Precaching verhindert
  e.waitUntil(
    caches.open(CACHE)
      .then(c=>Promise.all(ASSETS.map(u=>c.add(u).catch(()=>{}))))
      .then(()=>self.skipWaiting())
  );
});

self.addEventListener("activate",e=>{
  e.waitUntil(
    caches.keys()
      .then(k=>Promise.all(k.filter(x=>x!==CACHE).map(x=>caches.delete(x))))
      .then(()=>self.clients.claim())
  );
});

self.addEventListener("fetch",e=>{
  const req=e.request;
  if(req.method!=="GET")return;
  const isHTML=req.mode==="navigate"||(req.headers.get("accept")||"").includes("text/html");
  if(isHTML){
    // Online: frische Seite holen und unter ihrer EIGENEN URL cachen.
    // Offline: die passende Seite liefern (ersatzteile.html bleibt ersatzteile.html),
    // erst danach auf index.html zurückfallen.
    e.respondWith(
      fetch(req).then(resp=>{
        const cp=resp.clone();
        caches.open(CACHE).then(c=>{c.put(req,cp).catch(()=>{});}).catch(()=>{});
        return resp;
      }).catch(()=>
        caches.match(req,{ignoreSearch:true})
          .then(r=>r||caches.match("./index.html",{ignoreSearch:true}))
          .then(r=>r||caches.match("./",{ignoreSearch:true}))
      )
    );
    return;
  }
  // Übrige Dateien (Icons, Manifest, Schriften): zuerst Cache, sonst Netzwerk (und cachen)
  e.respondWith(
    caches.match(req,{ignoreVary:true}).then(r=>r||fetch(req).then(resp=>{
      const cp=resp.clone();
      caches.open(CACHE).then(c=>c.put(req,cp)).catch(()=>{});
      return resp;
    }).catch(()=>caches.match("./index.html",{ignoreSearch:true})))
  );
});
