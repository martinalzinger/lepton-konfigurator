// Eigener Service-Worker der eigenständigen Vertriebs-/CRM-Seite (Scope /vertrieb/).
// Komplett getrennt von Konfigurator & Ersatzteilkatalog – eigener Cache "vertrieb-".
const CACHE="vertrieb-v4";
const ASSETS=["./","./index.html","./manifest.webmanifest","./icon-192.png","./icon-512.png"];

self.addEventListener("install",e=>{
  e.waitUntil(
    caches.open(CACHE)
      .then(c=>Promise.all(ASSETS.map(u=>c.add(u).catch(()=>{}))))
      .then(()=>self.skipWaiting())
  );
});

self.addEventListener("activate",e=>{
  // NUR eigene (vertrieb-) Caches aufräumen – fremde bleiben unberührt
  e.waitUntil(
    caches.keys()
      .then(k=>Promise.all(k.filter(x=>x.startsWith("vertrieb-")&&x!==CACHE).map(x=>caches.delete(x))))
      .then(()=>self.clients.claim())
  );
});

self.addEventListener("fetch",e=>{
  const req=e.request;
  if(req.method!=="GET")return;
  if(req.url.indexOf("api.php")>=0)return;            // dynamische API immer direkt ans Netz, nie cachen
  if(req.url.indexOf("nominatim")>=0||req.url.indexOf("overpass")>=0)return; // Karten-Lead-Suche: immer live
  const isHTML=req.mode==="navigate"||(req.headers.get("accept")||"").includes("text/html");
  if(isHTML){
    e.respondWith(
      fetch(req).then(resp=>{
        const cp=resp.clone();
        caches.open(CACHE).then(c=>{c.put("./index.html",cp).catch(()=>{});}).catch(()=>{});
        return resp;
      }).catch(()=>
        caches.match("./index.html",{ignoreSearch:true}).then(r=>r||caches.match("./",{ignoreSearch:true}))
      )
    );
    return;
  }
  e.respondWith(
    caches.match(req,{ignoreVary:true}).then(r=>r||fetch(req).then(resp=>{
      const cp=resp.clone();
      caches.open(CACHE).then(c=>c.put(req,cp)).catch(()=>{});
      return resp;
    }).catch(()=>caches.match("./index.html",{ignoreSearch:true})))
  );
});
