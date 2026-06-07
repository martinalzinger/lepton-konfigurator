const CACHE="lepton-v3";
const ASSETS=["./","./index.html","./manifest.webmanifest","./icon-192.png","./icon-512.png"];

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
    // Online: frische Seite holen und in den Cache legen.
    // Offline: direkt die gespeicherte index.html liefern (robust gegen Vary/URL-Mismatch).
    e.respondWith(
      fetch(req).then(resp=>{
        const cp=resp.clone();
        caches.open(CACHE).then(c=>c.put("./index.html",cp)).catch(()=>{});
        return resp;
      }).catch(()=>
        caches.match("./index.html",{ignoreSearch:true})
          .then(r=>r||caches.match("./",{ignoreSearch:true}))
          .then(r=>r||caches.match(req,{ignoreSearch:true,ignoreVary:true}))
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
