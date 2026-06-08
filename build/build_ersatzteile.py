#!/usr/bin/env python3
# Baut die eigenständige Seite ./ersatzteile.html (Ersatzteilkatalog mit 3D-Ansicht + Warenkorb).
# Quelle: spareparts.json, i18n_ersatzteile.json, assets*.b64.json, modelviewer.min.js, glbgen.py,
#         sowie CAD-Dateien in build/models_cad/ (STEP/STP/GLB/GLTF -> 3D, SEV -> Vorschaubild).
# 3D-Modelle werden nach ./models/*.glb AUSGELAGERT und im Browser bei Bedarf
# nachgeladen (Service-Worker cacht sie offline) -> ersatzteile.html bleibt klein.
# Aufruf:  python3 build/build_ersatzteile.py
import os, json, base64, re, glob, sys
HERE=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import glbgen

MAIL="martin@alzinger-maschinenbau.de"

def jload(name): return json.load(open(os.path.join(HERE,name),encoding="utf8"))

A=jload("assets.b64.json")
IMG=dict(A["IMG"]); LOGO_L=A["LOGO_L"]; LOGO_D=A["LOGO_D"]; HERO=A["HERO"]; RED=A["RED"]; RED2=A["RED2"]
SPA=jload("assets_spareparts.b64.json")          # zusätzliche Bilder (z.B. Bunker-Vorschau)
IMG.update(SPA)
# Zuordnung PDM-Nummer -> echte Artikelnummer + Bezeichnung (für den 3D-Teile-Explorer)
try: PARTMAP=jload("subparts.json")
except Exception: PARTMAP={}
I18N_RAW=jload("i18n_ersatzteile.json")
SP_RAW=jload("spareparts.json")
LANGS=["de","en","pl","fr"]

# ---- 3D-Viewer: three.js liegt als vendor/*.js (offline, bei Bedarf geladen) ----
# (kein model-viewer mehr; der interaktive Explorer nutzt three.js direkt)

# ---- Modelle als EXTERNE Dateien (Nachladen bei Bedarf) ----
# 3D-Modelle werden NICHT in die HTML eingebettet, sondern als models/*.glb ausgelagert
# und erst beim Klick auf "3D ansehen" geladen (offline via Service-Worker gecacht).
OUTDIR=os.path.normpath(os.path.join(HERE,"..","ersatzteile"))   # eigenständiger Ordner /ersatzteile/
MODELS_DIR=os.path.join(OUTDIR,"models")
os.makedirs(MODELS_DIR,exist_ok=True)
MODELS={}   # key -> relative URL "models/datei.glb"
SEV_IMG={}  # key -> data-URI (kleine Vorschaubilder bleiben eingebettet)
PROC_KINDS={"scheibe","welle","lager","ritzel","trommel","keilriemen","abstreifer","gehaeuse"}

def safe(name): return re.sub(r"[^A-Za-z0-9._-]","_",str(name))

def write_model(fname, data):
    open(os.path.join(MODELS_DIR,fname),"wb").write(data)
    return fname

def file_model(fname):
    k="file:"+fname
    if k not in MODELS: MODELS[k]="models/"+fname
    return k

def proc_model(kind):
    k="proc:"+kind
    if k not in MODELS:
        write_model("proc-"+kind+".glb", glbgen.model(kind))
        MODELS[k]="models/proc-"+kind+".glb"
    return k

def parse_meta(orig_base, step_path=None):
    """Artikelnummer + Bezeichnung aus STEP-PRODUCT bzw. Dateiname (Trenner: Space/_/-)."""
    art=name=None
    if step_path:
        try:
            txt=open(step_path,encoding="utf8",errors="ignore").read(300000)
            m=re.search(r"PRODUCT\s*\(\s*'([^']*)'\s*,\s*'([^']*)'", txt)
            if m:
                a=(m.group(1) or "").strip(); n=(m.group(2) or "").strip()
                if a: art=a
                if n and n!=a: name=n
        except Exception: pass
    stem=os.path.splitext(orig_base)[0]
    fm=re.match(r"^\s*([0-9][0-9A-Za-z.\-/]*)[ _\-]+(.+?)\s*$", stem)
    if not art: art=fm.group(1) if fm else stem
    if not name: name=(fm.group(2).replace("_"," ") if fm else stem)
    return art, name

def sev_preview(path):
    """Extrahiert das eingebettete PNG-Vorschaubild aus einer Solid-Edge .sev-Datei."""
    try:
        txt=open(path,encoding="utf8",errors="ignore").read()
        m=re.search(r"<SEModelPreview[^>]*>\s*<script[^>]*>(.*?)</script>", txt, re.S)
        if not m: return None
        b64=re.search(r'"([A-Za-z0-9+/=\s]+)"', m.group(1))
        raw=base64.b64decode(re.sub(r"\s+","",(b64.group(1) if b64 else m.group(1))))
        s=raw.find(b"\x89PNG\r\n\x1a\n"); e=raw.find(b"IEND")
        if s<0 or e<0: return None
        return "data:image/png;base64,"+base64.b64encode(raw[s:e+8]).decode()
    except Exception:
        return None

CAD=[]   # {art,name,model(servedFilename|None),img(key|None)}
def process_inputs():
    """models_cad/ -> models/ : STEP konvertieren, GLB/GLTF kopieren, SEV-Vorschau einbetten."""
    for path in sorted(glob.glob(os.path.join(HERE,"models_cad","*"))):
        b=os.path.basename(path); low=b.lower()
        if b=="README.md" or low.endswith((".step.glb",".stp.glb",".out.glb")): continue
        stem=os.path.splitext(b)[0]
        if low.endswith((".step",".stp")):
            fname=safe(stem)+".glb"; dst=os.path.join(MODELS_DIR,fname)
            if os.path.exists(dst) and os.path.getmtime(dst)>=os.path.getmtime(path):
                art,name=parse_meta(b,step_path=path); CAD.append({"art":art,"name":name,"model":fname,"img":None})
                print("  STEP (aktuell) ->",fname); continue
            try:
                import cascadio
                tmp=path+".out.glb"
                cascadio.step_to_glb(path,tmp,tol_linear=0.5,tol_angular=0.7)
                write_model(fname, open(tmp,"rb").read()); os.remove(tmp)
                art,name=parse_meta(b,step_path=path); CAD.append({"art":art,"name":name,"model":fname,"img":None})
                print("  STEP ->",fname)
            except Exception as e:
                print("  !! STEP fehlgeschlagen:",b,e)
        elif low.endswith((".glb",".gltf")):
            fname=safe(stem)+(".glb" if low.endswith(".glb") else ".gltf")
            write_model(fname, open(path,"rb").read())
            art,name=parse_meta(b); CAD.append({"art":art,"name":name,"model":fname,"img":None})
            print("  GLB  ->",fname)
        elif low.endswith(".sev"):
            uri=sev_preview(path)
            art,name=parse_meta(b)
            if uri:
                key="sev:"+safe(stem); SEV_IMG[key]=uri
                CAD.append({"art":art,"name":name,"model":None,"img":key})
                print("  SEV  -> Vorschau",b)
            else:
                CAD.append({"art":art,"name":name,"model":None,"img":None})
                print("  ?? SEV ohne Vorschau:",b)
process_inputs()

# bereits vorhandene (committete) models/*.glb ohne Quelle ebenfalls erfassen
proc_files={"proc-"+k+".glb" for k in PROC_KINDS}
produced={c["model"] for c in CAD if c["model"]}
for f in sorted(glob.glob(os.path.join(MODELS_DIR,"*.glb"))+glob.glob(os.path.join(MODELS_DIR,"*.gltf"))):
    fn=os.path.basename(f)
    if fn in produced or fn in proc_files: continue
    art,name=parse_meta(fn)
    CAD.append({"art":art,"name":name,"model":fn,"img":None})

AVAIL={c["model"] for c in CAD if c["model"]}

# ---- Katalog aufbauen (Kategorien + Auto-Import) ----
def resolve_model(m):
    if not m: return None,None
    if m in PROC_KINDS: return proc_model(m), m       # (key, modelKind)
    if m in AVAIL: return file_model(m), None
    return None,None

CAT=[]; seen_art=set(); ref_files=set()
for cat in SP_RAW["kategorien"]:
    items=[]
    for p in cat["teile"]:
        seen_art.add(p["art"])
        if p.get("model") in AVAIL: ref_files.add(p["model"])
        mk,kind=resolve_model(p.get("model"))
        items.append({
            "id":p["id"], "art":p["art"],
            "name":p["name"], "name_en":p.get("name_en"),
            "desc":p.get("desc",""), "desc_en":p.get("desc_en"),
            "price":p.get("price",0),
            "model": mk, "modelKind": kind, "img": p.get("img")
        })
    CAT.append({"h":cat["h"], "h_en":cat.get("h_en"), "items":items})

auto=[c for c in CAD if c["art"] not in seen_art and (c["model"] is None or c["model"] not in ref_files)]
if auto:
    CAT.append({"h":"Aus CAD importiert","h_en":"Imported from CAD","items":[{
        "id":"cad-"+str(i), "art":c["art"], "name":c["name"], "name_en":None,
        "desc":"", "desc_en":None, "price":0,
        "model": (file_model(c["model"]) if c["model"] else None), "modelKind":None, "img":c["img"]
    } for i,c in enumerate(auto)]})

# ---- i18n lang-major ----
I18N={lg:{k:I18N_RAW[k][lg] for k in I18N_RAW} for lg in LANGS}

# ---- nur tatsächlich referenzierte (eingebettete) Bilder behalten ----
IMG=dict(SPA); IMG.update(SEV_IMG)
used_img=set()
for c in CAT:
    for p in c["items"]:
        if p.get("img"): used_img.add(p["img"])
IMG={k:v for k,v in IMG.items() if k in used_img}   # stabile Reihenfolge (reproduzierbarer Build)

print("Modelle ausgelagert:",len([k for k in MODELS]),"-> models/   eingebettete Bilder:",len(IMG))

# ================= HTML-TEMPLATE =================
TPL=r'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Alzinger · Ersatzteilkatalog Lepton 5100</title>
<meta name="theme-color" content="#c00000">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Ersatzteile">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-192.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{--red:%%RED%%;--red2:%%RED2%%;--paper:#f1f1ee;--surface:#fff;--ink:#16181a;--muted:#5e6166;--faint:#9a9aa0;--line:#e4e2db;--line-strong:#d3cfc4;--field:#f7f6f2;--gold:#a28231;--slate:#4e5258;--pos:#15803d;--red-soft:rgba(192,0,0,.08);--sans:'Manrope','Helvetica Neue',Arial,sans-serif;--mono:'IBM Plex Mono',ui-monospace,Menlo,monospace;}
*{box-sizing:border-box;margin:0;padding:0}
html{-webkit-text-size-adjust:100%}
body{font-family:var(--sans);background:var(--paper);color:var(--ink);line-height:1.45;font-size:15px;-webkit-font-smoothing:antialiased}
#gate{position:fixed;inset:0;z-index:1000;background:linear-gradient(160deg,#16181a,#2a2c2f);display:flex;align-items:center;justify-content:center;padding:24px}
#gate.hidden{display:none}
#gate .gc{width:100%;max-width:340px;background:#fff;border-radius:16px;padding:30px 26px 26px;box-shadow:0 24px 60px rgba(0,0,0,.4);text-align:center}
#gate .gl{height:34px;margin:0 auto 16px;display:block}
#gate .gh{font-size:20px;font-weight:800;letter-spacing:-.01em}
#gate .gs{font-family:var(--mono);font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);margin-top:6px}
#gate form{margin-top:20px;display:flex;flex-direction:column;gap:10px}
#gate input{font-family:var(--sans);font-size:15px;border:1px solid var(--line-strong);background:var(--field);border-radius:9px;padding:12px 13px;color:var(--ink);outline:none;width:100%}
#gate input:focus{border-color:var(--red);box-shadow:0 0 0 3px var(--red-soft);background:#fffdfc}
#gate button{margin-top:4px;background:var(--red);color:#fff;border:0;border-radius:9px;padding:13px;font-family:var(--mono);font-size:12px;letter-spacing:.06em;text-transform:uppercase;font-weight:600;cursor:pointer}
#gate button:hover{background:var(--red2)}
#gate .ge{color:var(--red);font-size:12.5px;min-height:16px;font-weight:600}
.topbar{position:sticky;top:0;z-index:80;background:var(--red);color:#fff}
.topbar-in{max-width:1180px;margin:0 auto;padding:12px 20px}
.tb-row{display:flex;align-items:center;justify-content:space-between;gap:12px}
.tb-back{color:#fff;text-decoration:none;font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;font-weight:600;display:inline-flex;align-items:center;gap:6px;opacity:.9}
.tb-back:hover{opacity:1}
.tb-logo img{height:30px;display:block}
.tb-right{display:flex;align-items:center;gap:10px}
.langsel{display:inline-flex;gap:2px;background:rgba(255,255,255,.16);border-radius:8px;padding:3px}
.langsel button{background:none;border:0;color:#fff;font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:.04em;padding:5px 7px;border-radius:6px;cursor:pointer;opacity:.72;transition:.12s}
.langsel button:hover{opacity:1}.langsel button.active{background:#fff;color:var(--red);opacity:1}
.cartbtn{position:relative;background:rgba(255,255,255,.14);border:0;color:#fff;cursor:pointer;border-radius:8px;padding:7px 9px;display:inline-flex;align-items:center;gap:7px;font-family:var(--mono);font-size:11px;font-weight:600}
.cartbtn:hover{background:rgba(255,255,255,.26)}
.cartbtn svg{width:20px;height:20px;stroke:#fff;fill:none;stroke-width:1.8}
.cartbtn .badge{position:absolute;top:-6px;right:-6px;min-width:19px;height:19px;background:var(--ink);color:#fff;border-radius:10px;font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;padding:0 5px;border:2px solid var(--red)}
.cartbtn .badge.zero{display:none}
.hero{position:relative;min-height:210px;background-image:linear-gradient(90deg,rgba(16,17,19,.86),rgba(16,17,19,.45) 60%,rgba(16,17,19,.2)),url("%%HERO%%");background-size:cover;background-position:center;color:#fff;display:flex;align-items:flex-end}
.hero-in{max-width:1180px;margin:0 auto;width:100%;padding:34px 20px 30px}
.hero .kick{font-family:var(--mono);font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:#ff9d8c;font-weight:500}
.hero h1{font-size:clamp(26px,5vw,40px);font-weight:800;letter-spacing:-.02em;margin-top:10px}
.hero .hsub{font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#e7e5e0;margin-top:11px}
.wrap{max-width:1180px;margin:0 auto;padding:24px 20px 120px}
.toolbar{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:6px;position:sticky;top:62px;z-index:40;background:var(--paper);padding:10px 0}
.search{flex:1;min-width:220px;position:relative}
.search input{width:100%;font-family:var(--sans);font-size:14px;border:1px solid var(--line-strong);background:#fff;border-radius:9px;padding:11px 13px 11px 38px;outline:none}
.search input:focus{border-color:var(--red);box-shadow:0 0 0 3px var(--red-soft)}
.search svg{position:absolute;left:12px;top:50%;transform:translateY(-50%);width:17px;height:17px;stroke:var(--faint);fill:none;stroke-width:1.8}
.chips{display:flex;gap:7px;flex-wrap:wrap}
.chips button{font-family:var(--mono);font-size:11px;letter-spacing:.03em;border:1px solid var(--line-strong);background:#fff;color:var(--muted);border-radius:20px;padding:8px 13px;cursor:pointer;font-weight:600;transition:.12s}
.chips button:hover{border-color:var(--ink)}
.chips button.active{background:var(--ink);color:#fff;border-color:var(--ink)}
.catblk{margin-top:24px}
.catblk>.ch{font-family:var(--mono);font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--slate);font-weight:600;display:flex;align-items:center;gap:9px;margin:0 2px 12px}
.catblk>.ch::before{content:"";width:5px;height:15px;background:var(--gold);border-radius:1px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(232px,1fr));gap:14px}
.phnote{grid-column:1/-1;border:1px dashed var(--line-strong);border-radius:10px;padding:18px 16px;color:var(--faint);font-size:13px;font-style:italic;background:var(--field)}
.pcard{background:var(--surface);border:1px solid var(--line);border-radius:13px;overflow:hidden;display:flex;flex-direction:column;transition:.14s}
.pcard:hover{border-color:var(--line-strong);box-shadow:0 8px 22px rgba(0,0,0,.07)}
.pcard.incart{border-color:var(--red);box-shadow:0 0 0 2px var(--red-soft)}
.pthumb{position:relative;height:150px;background:#f3f2ee;display:flex;align-items:center;justify-content:center;cursor:pointer}
.pthumb img{max-width:100%;max-height:100%;object-fit:contain}
.pthumb svg{width:74px;height:74px;stroke:#b7b3a8;fill:none;stroke-width:1.3}
.badge3d{position:absolute;top:9px;left:9px;background:var(--ink);color:#fff;font-family:var(--mono);font-size:9px;letter-spacing:.1em;font-weight:600;padding:4px 7px;border-radius:5px;display:flex;align-items:center;gap:4px}
.badge3d svg{width:12px;height:12px;stroke:#fff;stroke-width:2}
.pbody{padding:13px 14px 14px;display:flex;flex-direction:column;gap:5px;flex:1}
.pname{font-size:14px;font-weight:600;line-height:1.3}
.pdesc{font-size:11.5px;color:var(--muted);line-height:1.4;flex:1}
.pfoot{display:flex;justify-content:space-between;align-items:center;margin-top:3px;gap:8px}
.part{font-family:var(--mono);font-size:10px;color:var(--faint)}
.pprice{font-family:var(--mono);font-weight:600;font-size:14px;color:var(--red);white-space:nowrap}
.pacts{display:flex;gap:7px;margin-top:9px}
.pacts button{flex:1;font-family:var(--mono);font-size:10.5px;letter-spacing:.03em;text-transform:uppercase;font-weight:600;border-radius:8px;padding:9px 6px;cursor:pointer;border:1px solid var(--line-strong);background:#fff;color:var(--ink);transition:.12s}
.pacts .b3d:hover{border-color:var(--ink)}
.pacts .b3d[disabled]{opacity:.4;cursor:not-allowed}
.pacts .badd{background:var(--red);border-color:var(--red);color:#fff}
.pacts .badd:hover{background:var(--red2)}
.emptymsg{text-align:center;color:var(--faint);padding:50px 0;font-size:14px}
/* Drawer */
.drawer-backdrop{position:fixed;inset:0;background:rgba(16,17,19,.45);opacity:0;pointer-events:none;transition:.2s;z-index:95}
.drawer-backdrop.open{opacity:1;pointer-events:auto}
.drawer{position:fixed;top:0;right:0;height:100%;width:420px;max-width:92vw;background:var(--paper);box-shadow:-12px 0 40px rgba(0,0,0,.25);transform:translateX(100%);transition:.24s;z-index:96;display:flex;flex-direction:column}
.drawer.open{transform:none}
.dhead{background:var(--ink);color:#fff;padding:16px 18px;display:flex;justify-content:space-between;align-items:center}
.dhead .t{font-weight:700;font-size:17px}
.dhead button{background:none;border:0;color:#fff;font-size:26px;line-height:1;cursor:pointer;opacity:.8}.dhead button:hover{opacity:1}
.dbody{flex:1;overflow:auto;padding:14px 18px}
.citem{display:flex;gap:11px;padding:11px 0;border-bottom:1px solid var(--line);align-items:center}
.citem .ci-th{width:52px;height:44px;border-radius:6px;background:#fff;border:1px solid var(--line);flex-shrink:0;display:flex;align-items:center;justify-content:center;overflow:hidden}
.citem .ci-th img{max-width:100%;max-height:100%;object-fit:contain}
.citem .ci-th svg{width:30px;height:30px;stroke:#b7b3a8;fill:none;stroke-width:1.4}
.citem .ci-n{flex:1;min-width:0}
.citem .ci-name{font-size:13px;font-weight:600;line-height:1.25}
.citem .ci-art{font-family:var(--mono);font-size:10px;color:var(--faint)}
.citem .ci-price{font-family:var(--mono);font-size:11.5px;color:var(--red);margin-top:2px}
.qty{display:inline-flex;align-items:center;border:1px solid var(--line-strong);border-radius:7px;overflow:hidden;background:#fff}
.qty button{background:#fff;border:0;width:26px;height:28px;font-size:15px;cursor:pointer;color:var(--ink)}
.qty button:hover{background:var(--field)}
.qty input{width:34px;height:28px;border:0;border-left:1px solid var(--line);border-right:1px solid var(--line);text-align:center;font-family:var(--mono);font-size:13px;outline:none}
.ci-rm{background:none;border:0;color:var(--faint);cursor:pointer;font-size:11px;text-decoration:underline;padding:0;margin-top:5px}
.ci-rm:hover{color:var(--red)}
.subtotal{display:flex;justify-content:space-between;align-items:baseline;margin:14px 0 4px;font-size:14px}
.subtotal .v{font-family:var(--mono);font-weight:700;font-size:18px}
.cnote{font-size:10.5px;color:var(--muted);line-height:1.5;font-style:italic;margin-bottom:8px}
.custform{margin-top:14px;border-top:1px dashed var(--line-strong);padding-top:14px}
.custform .ct{font-family:var(--mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--gold);font-weight:600;margin-bottom:10px}
.fld{display:flex;flex-direction:column;gap:5px;margin-bottom:10px}
.fld label{font-size:12px;color:var(--muted);font-weight:600}
.fld input,.fld textarea{font-family:var(--sans);font-size:13.5px;border:1px solid var(--line-strong);background:#fff;border-radius:8px;padding:9px 11px;outline:none}
.fld input:focus,.fld textarea:focus{border-color:var(--red);box-shadow:0 0 0 3px var(--red-soft)}
.fld textarea{min-height:60px;resize:vertical}
.frow{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.dfoot{padding:14px 18px;border-top:1px solid var(--line);display:flex;flex-direction:column;gap:8px}
.btn{font-family:var(--mono);font-size:11.5px;letter-spacing:.05em;text-transform:uppercase;padding:13px;border:0;border-radius:9px;cursor:pointer;font-weight:600;transition:.15s}
.btn.p{background:var(--red);color:#fff}.btn.p:hover{background:var(--red2)}
.btn.s{background:#fff;border:1px solid var(--line-strong);color:var(--ink)}.btn.s:hover{border-color:var(--ink)}
.btn.t{background:none;color:var(--muted);padding:6px}.btn.t:hover{color:var(--red)}
.btn[disabled]{opacity:.45;cursor:not-allowed}
/* 3D explorer modal */
.mvmodal{position:fixed;inset:0;background:rgba(16,17,19,.74);z-index:97;display:none;align-items:center;justify-content:center;padding:10px}
.mvmodal.open{display:flex}
.mvbox{background:#fff;border-radius:14px;width:min(1500px,98vw);height:94vh;max-height:94vh;overflow:hidden;position:relative;display:flex;flex-direction:column}
.mvbox .mvtop{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:12px 16px;border-bottom:1px solid var(--line);flex-shrink:0}
.mvbox .mvname{font-weight:700;font-size:17px}
.mvbox .mvart{font-family:var(--mono);font-size:11px;color:var(--faint);margin-top:2px}
.mvbox .mvx{background:var(--field);border:0;width:34px;height:34px;border-radius:50%;font-size:20px;cursor:pointer;color:var(--ink);flex-shrink:0}
.mvbox .mvx:hover{background:var(--line)}
.mvsplit{display:flex;min-height:0;flex:1}
.mvstage{position:relative;flex:2.2;min-width:0;background:linear-gradient(180deg,#fcfcfb,#e3e1da);display:flex;flex-direction:column}
#tcanvas{width:100%;height:100%;display:block;touch-action:none;cursor:grab}
#tcanvas:active{cursor:grabbing}
.mvload{position:absolute;inset:0;display:flex;align-items:center;justify-content:center}
.mvload .spin{width:34px;height:34px;border:3px solid var(--line-strong);border-top-color:var(--red);border-radius:50%;animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.mvno{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;text-align:center;color:var(--faint);font-size:14px;padding:30px}
.mvtools{position:absolute;top:10px;left:10px;display:flex;gap:6px}
.mvtools button{background:rgba(255,255,255,.9);border:1px solid var(--line-strong);border-radius:7px;padding:7px 10px;font-family:var(--mono);font-size:10.5px;font-weight:600;color:var(--ink);cursor:pointer}
.mvtools button:hover{border-color:var(--ink)}
.mvhint{position:absolute;bottom:8px;left:0;right:0;font-family:var(--mono);font-size:9.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);text-align:center;pointer-events:none}
.mvparts{flex:1;min-height:0;max-width:400px;min-width:260px;display:flex;flex-direction:column;border-left:1px solid var(--line);background:#fff}
.mvph{display:flex;align-items:center;gap:8px;padding:12px 14px 8px;font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--slate);font-weight:600}
.mvph .cnt{background:var(--ink);color:#fff;border-radius:10px;padding:1px 8px;font-size:11px}
.psearch{margin:0 14px 8px;font-family:var(--sans);font-size:13px;border:1px solid var(--line-strong);background:var(--field);border-radius:8px;padding:8px 11px;outline:none}
.psearch:focus{border-color:var(--red);box-shadow:0 0 0 3px var(--red-soft)}
.mvlist{flex:1;overflow:auto;padding:0 8px 10px}
.prow{display:flex;align-items:center;gap:8px;padding:8px 8px;border-radius:8px;cursor:pointer;border:1px solid transparent}
.prow:hover{background:var(--field)}
.prow.active{background:var(--red-soft);border-color:var(--red)}
.prow.hidden .pmid{opacity:.4}
.prow .eye{background:none;border:0;cursor:pointer;color:var(--muted);flex-shrink:0;padding:2px;display:inline-flex}
.prow .eye svg{width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:1.7}
.prow.hidden .eye{color:var(--faint)}
.prow .pmid{flex:1;min-width:0}
.prow .pml{font-size:12.5px;font-weight:600;line-height:1.25;word-break:break-word}
.prow .pma{font-family:var(--mono);font-size:10px;color:var(--faint)}
.prow .qbadge{font-family:var(--mono);font-size:10px;color:var(--slate);background:var(--field);border:1px solid var(--line);border-radius:5px;padding:1px 5px;flex-shrink:0}
.prow .pcartbtn{background:var(--red);border:0;color:#fff;border-radius:7px;width:30px;height:30px;cursor:pointer;flex-shrink:0;display:inline-flex;align-items:center;justify-content:center}
.prow .pcartbtn:hover{background:var(--red2)}
.prow .pcartbtn svg{width:16px;height:16px;stroke:#fff;fill:none;stroke-width:1.8}
@media (max-width:760px){
  .mvmodal{padding:0;align-items:stretch}
  .mvbox{width:100vw;height:100vh;height:100dvh;max-height:none;border-radius:0}
  .mvsplit{flex-direction:column;min-height:0}
  .mvstage{flex:none;height:42vh;height:42dvh}
  .mvparts{flex:1;min-height:0;max-width:none;border-left:0;border-top:1px solid var(--line)}
}
/* Toast */
#toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(20px);background:var(--ink);color:#fff;padding:12px 20px;border-radius:30px;font-size:13px;font-weight:600;opacity:0;pointer-events:none;transition:.25s;z-index:99;box-shadow:0 10px 30px rgba(0,0,0,.25)}
#toast.show{opacity:1;transform:translateX(-50%)}
/* Print document */
#doc{display:none}
.dtbl{width:100%;border-collapse:collapse;margin-top:14px;font-size:12px}
.dtbl th{text-align:left;font-family:var(--mono);font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);border-bottom:2px solid var(--ink);padding:6px 8px}
.dtbl td{padding:7px 8px;border-bottom:1px solid var(--line)}
.dtbl td.r,.dtbl th.r{text-align:right;font-family:var(--mono)}
@media (max-width:560px){.drawer{width:100%}.frow{grid-template-columns:1fr}}
@media print{
  @page{margin:14mm}
  body{background:#fff}
  body>*{display:none!important}
  #doc{display:block!important}
  #doc .topstr{display:flex;height:6px}#doc .topstr span{flex:1}
  .dpad{padding:0}
  .dhd{display:flex;justify-content:space-between;align-items:flex-start;gap:20px}
  .dlogo{height:30px}
  .dfirm{font-size:11px;color:#5e6166;line-height:1.5}.dfirm .fnm{font-weight:800;color:#16181a;font-size:13px}
  .dmeta{text-align:right;font-family:var(--mono);font-size:11px;color:#5e6166;line-height:1.7}.dmeta b{color:#16181a}
  .dtitle{margin-top:24px;font-size:23px;font-weight:800}
  .dparties{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:18px;font-size:12px;line-height:1.5}
  .dparties .s{font-family:var(--mono);font-size:8.5px;letter-spacing:.16em;text-transform:uppercase;color:#9a9aa0;display:block;margin-bottom:4px}
  .dtot{margin-top:6px;text-align:right;font-size:14px;font-weight:700}
  .dmsg{margin-top:16px;font-size:12px;white-space:pre-line}
  .dfo{margin-top:22px;padding-top:10px;border-top:1px solid #e4e2db;font-size:10px;color:#5e6166}
}
</style>
<script type="importmap">{"imports":{"three":"./vendor/three.module.min.js"}}</script>
</head>
<body>
<div id="gate" class="noprint">
  <div class="gc">
    <img class="gl" src="%%LOGOD%%" alt="Alzinger">
    <div class="gh" id="gateH">Händler-Login</div>
    <div class="gs" id="gateS">Ersatzteilkatalog Lepton 5100</div>
    <form id="gateForm" autocomplete="on">
      <input id="gu" name="username" placeholder="Benutzername" autocomplete="username" autocapitalize="none" autocorrect="off" spellcheck="false">
      <input id="gp" name="password" type="password" placeholder="Passwort" autocomplete="current-password">
      <button type="submit" id="gateBtn">Anmelden</button>
      <div class="ge" id="gerr"></div>
    </form>
  </div>
</div>
<script>
(function(){
 function sha256(ascii){function r(v,a){return (v>>>a)|(v<<(32-a));}var mp=Math.pow,mw=mp(2,32),res="",words=[],bl=ascii.length*8;var hash=sha256.h=sha256.h||[],k=sha256.k=sha256.k||[],pc=k.length,ic={},i,j;for(var c=2;pc<64;c++){if(!ic[c]){for(i=0;i<313;i+=c)ic[i]=c;hash[pc]=(mp(c,.5)*mw)|0;k[pc++]=(mp(c,1/3)*mw)|0;}}ascii+="\x80";while(ascii.length%64-56)ascii+="\x00";for(i=0;i<ascii.length;i++){j=ascii.charCodeAt(i);if(j>>8)return;words[i>>2]|=j<<((3-i)%4)*8;}words[words.length]=((bl/mw)|0);words[words.length]=bl;for(j=0;j<words.length;){var w=words.slice(j,j+=16),oh=hash;hash=hash.slice(0,8);for(i=0;i<64;i++){var w15=w[i-15],w2=w[i-2],a=hash[0],e=hash[4],t1=hash[7]+(r(e,6)^r(e,11)^r(e,25))+((e&hash[5])^((~e)&hash[6]))+k[i]+(w[i]=i<16?w[i]:(w[i-16]+(r(w15,7)^r(w15,18)^(w15>>>3))+w[i-7]+(r(w2,17)^r(w2,19)^(w2>>>10)))|0),t2=(r(a,2)^r(a,13)^r(a,22))+((a&hash[1])^(a&hash[2])^(hash[1]&hash[2]));hash=[(t1+t2)|0].concat(hash);hash[4]=(hash[4]+t1)|0;}for(i=0;i<8;i++)hash[i]=(hash[i]+oh[i])|0;}for(i=0;i<8;i++){for(j=3;j+1;j--){var b=(hash[i]>>(j*8))&255;res+=((b<16)?0:"")+b.toString(16);}}return res;}
 var HASHES=["f5939f6c9e00e5336ad0f89fc338cc1f33852adeb5912db03eca1004b7ea560b","e1e7cf21dbe88d824482ca87474e7610f60a04a7447b745623c1951312958589","48a0f14ca81a59a4aee853de72c3cb531920352e67a757d15a60682165418d1b","50b9f421b5a362836fbb38ba11d8d59b76c287ef29d6c445df771a0c8f1116df"];
 var AKEY="amb_ersatzteile_auth";
 var T={de:{h:"Händler-Login",s:"Ersatzteilkatalog Lepton 5100",u:"Benutzername",p:"Passwort",b:"Anmelden",e:"Benutzername oder Passwort falsch."},
        en:{h:"Dealer login",s:"Spare parts catalogue Lepton 5100",u:"Username",p:"Password",b:"Sign in",e:"Wrong username or password."},
        pl:{h:"Logowanie dealera",s:"Katalog części Lepton 5100",u:"Nazwa użytkownika",p:"Hasło",b:"Zaloguj się",e:"Błędna nazwa użytkownika lub hasło."},
        fr:{h:"Connexion revendeur",s:"Catalogue de pièces Lepton 5100",u:"Identifiant",p:"Mot de passe",b:"Se connecter",e:"Identifiant ou mot de passe incorrect."}};
 var lang="de";
 try{var sl=localStorage.getItem("amb_lepton_lang");if(sl&&T[sl])lang=sl;else{var n=(navigator.language||"").slice(0,2).toLowerCase();if(T[n])lang=n;}}catch(e){}
 var tt=T[lang]||T.de;
 document.getElementById("gateH").textContent=tt.h;document.getElementById("gateS").textContent=tt.s;
 document.getElementById("gu").placeholder=tt.u;document.getElementById("gp").placeholder=tt.p;document.getElementById("gateBtn").textContent=tt.b;
 var gate=document.getElementById("gate");
 function authed(v){return !!v&&HASHES.indexOf(v)>=0;}
 function pass(){gate.classList.add("hidden");}
 try{if(authed(localStorage.getItem(AKEY)))pass();}catch(e){}
 document.getElementById("gateForm").addEventListener("submit",function(ev){ev.preventDefault();
  var u=(document.getElementById("gu").value||"").trim().toLowerCase(),p=(document.getElementById("gp").value||"");
  var h=sha256(u+":"+p);
  if(authed(h)){try{localStorage.setItem(AKEY,h);}catch(_){}document.getElementById("gerr").textContent="";pass();}
  else{document.getElementById("gerr").textContent=tt.e;var gp=document.getElementById("gp");gp.value="";gp.focus();}
 });
})();
</script>
<header class="topbar">
  <div class="topbar-in"><div class="tb-row">
    <div class="tb-logo"><img id="tbLogo" alt="Alzinger"></div>
    <div class="tb-right">
      <div class="langsel" id="langsel">
        <button type="button" data-lang="de">DE</button><button type="button" data-lang="en">EN</button><button type="button" data-lang="pl">PL</button><button type="button" data-lang="fr">FR</button>
      </div>
      <button class="cartbtn" id="cartBtn"><svg viewBox="0 0 24 24"><path d="M3 4h2l2.4 12.3a1 1 0 001 .8h8.2a1 1 0 001-.8L21 8H6"/><circle cx="9" cy="20" r="1.4"/><circle cx="18" cy="20" r="1.4"/></svg><span class="badge zero" id="badge">0</span></button>
    </div>
  </div></div>
</header>
<section class="hero">
  <div class="hero-in">
    <div class="kick" data-i18n="hero_kick"></div>
    <h1 data-i18n="hero_title"></h1>
    <div class="hsub" data-i18n="hero_sub"></div>
  </div>
</section>
<div class="wrap">
  <div class="toolbar">
    <div class="search"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg><input id="search" data-i18n-ph="search_ph" type="search"></div>
    <div class="chips" id="chips"></div>
  </div>
  <div id="catalog"></div>
  <div id="empty" class="emptymsg" data-i18n="no_results" style="display:none"></div>
</div>
<div class="drawer-backdrop" id="backdrop"></div>
<aside class="drawer" id="drawer" aria-hidden="true">
  <div class="dhead"><span class="t" data-i18n="cart_title">Warenkorb</span><button id="cartClose" aria-label="close">×</button></div>
  <div class="dbody">
    <div id="cartItems"></div>
    <div id="cartEmpty" class="emptymsg" data-i18n="cart_empty" style="padding:30px 0"></div>
    <div id="cartTail" style="display:none">
      <div class="subtotal"><span data-i18n="cart_subtotal">Zwischensumme netto</span><span class="v" id="subtotal">—</span></div>
      <div class="cnote" data-i18n="cart_note"></div>
      <div class="custform">
        <div class="ct" data-i18n="cust_title">Ihre Kontaktdaten</div>
        <div class="fld"><label data-i18n="lbl_firma">Firma</label><input id="c_firma"></div>
        <div class="frow">
          <div class="fld"><label data-i18n="lbl_name">Ansprechpartner</label><input id="c_name"></div>
          <div class="fld"><label data-i18n="lbl_tel">Telefon</label><input id="c_tel" data-i18n-ph="ph_optional"></div>
        </div>
        <div class="fld"><label data-i18n="lbl_mail">E-Mail</label><input id="c_mail" type="email"></div>
        <div class="fld"><label data-i18n="lbl_masch">Maschinen-Nr. / Baujahr</label><input id="c_masch" data-i18n-ph="ph_optional"></div>
        <div class="fld"><label data-i18n="lbl_msg">Nachricht</label><textarea id="c_msg" data-i18n-ph="ph_optional"></textarea></div>
      </div>
    </div>
  </div>
  <div class="dfoot">
    <button class="btn p" id="sendMail" data-i18n="btn_send_mail">Per E-Mail senden</button>
    <button class="btn s" id="printReq" data-i18n="btn_print">Anfrage drucken</button>
    <button class="btn t" id="clearCart" data-i18n="btn_clear">Leeren</button>
  </div>
</aside>
<div class="mvmodal" id="mvModal">
  <div class="mvbox">
    <div class="mvtop"><div><div class="mvname" id="mvName"></div><div class="mvart" id="mvArt"></div></div><button class="mvx" id="mvClose" aria-label="close">×</button></div>
    <div class="mvsplit">
      <div class="mvstage">
        <canvas id="tcanvas"></canvas>
        <div class="mvload" id="mvLoad"><div class="spin"></div></div>
        <div class="mvno" id="mvNo" style="display:none"></div>
        <div class="mvtools">
          <button id="mvReset" data-i18n="view_reset">Ansicht</button>
          <button id="mvShowAll" data-i18n="show_all">Alle einblenden</button>
        </div>
        <div class="mvhint" data-i18n="viewer_hint"></div>
      </div>
      <aside class="mvparts">
        <div class="mvph"><span data-i18n="parts_title">Einzelteile</span><span class="cnt" id="partCount">0</span></div>
        <input id="partSearch" class="psearch" data-i18n-ph="parts_search" type="search">
        <div class="mvlist" id="partList"></div>
      </aside>
    </div>
  </div>
</div>
<div id="toast"></div>
<div id="doc"></div>
<script>
const IMG=%%IMG%%; const MODELS=%%MODELS%%; const CAT=%%CAT%%; const I18N=%%I18N%%; const PARTMAP=%%PARTMAP%%;
const MAIL="%%MAIL%%"; const LOGO_L="%%LOGOL%%"; const LOGO_D="%%LOGOD%%";
const LOCALE={de:"de-DE",en:"en-GB",pl:"pl-PL",fr:"fr-FR"};
const LKEY="amb_lepton_lang", CKEY="amb_lepton_cart", FKEY="amb_lepton_et_fields";
const ICONS={
 scheibe:'<svg viewBox="0 0 48 48"><path d="M24 6l4 5 6-2 1 6 6 1-2 6 5 4-5 4 2 6-6 1-1 6-6-2-4 5-4-5-6 2-1-6-6-1 2-6-5-4 5-4-2-6 6-1 1-6 6 2z"/><circle cx="24" cy="24" r="6"/></svg>',
 ritzel:'<svg viewBox="0 0 48 48"><path d="M24 6l3 4 5-1 1 5 5 1-1 5 4 3-4 3 1 5-5 1-1 5-5-1-3 4-3-4-5 1-1-5-5-1 1-5-4-3 4-3-1-5 5-1 1-5 5 1z"/><circle cx="24" cy="24" r="7"/></svg>',
 welle:'<svg viewBox="0 0 48 48"><rect x="6" y="20" width="36" height="8" rx="2"/><rect x="2" y="17" width="6" height="14" rx="1"/><rect x="40" y="17" width="6" height="14" rx="1"/></svg>',
 trommel:'<svg viewBox="0 0 48 48"><rect x="8" y="14" width="32" height="20" rx="3"/><ellipse cx="8" cy="24" rx="3" ry="10"/><ellipse cx="40" cy="24" rx="3" ry="10"/></svg>',
 lager:'<svg viewBox="0 0 48 48"><circle cx="24" cy="24" r="17"/><circle cx="24" cy="24" r="8"/><circle cx="24" cy="9" r="2"/><circle cx="24" cy="39" r="2"/><circle cx="9" cy="24" r="2"/><circle cx="39" cy="24" r="2"/></svg>',
 keilriemen:'<svg viewBox="0 0 48 48"><ellipse cx="24" cy="24" rx="18" ry="11"/><ellipse cx="24" cy="24" rx="12" ry="6"/></svg>',
 abstreifer:'<svg viewBox="0 0 48 48"><rect x="6" y="20" width="36" height="7" rx="2"/><path d="M10 27v6M18 27v6M26 27v6M34 27v6"/></svg>',
 gehaeuse:'<svg viewBox="0 0 48 48"><rect x="10" y="8" width="28" height="32" rx="3"/><path d="M16 16h16M16 24h16M16 32h10"/></svg>',
 _default:'<svg viewBox="0 0 48 48"><path d="M24 5l16 9v20l-16 9-16-9V14z"/><path d="M24 5v18M8 14l16 9M40 14L24 23"/></svg>'
};
(function(){
 "use strict";
 var lang="de";
 try{var sl=localStorage.getItem(LKEY);if(sl&&I18N[sl])lang=sl;}catch(e){}
 var cart=loadCart();
 var filter="";   // category filter (h key) or ""
 var query="";
 function t(k){var L=I18N[lang]||I18N.de;return (L&&L[k]!=null)?L[k]:(I18N.de[k]!=null?I18N.de[k]:k);}
 function esc(s){return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
 function money(x){var dd=Number.isInteger(x)?0:2;return x.toLocaleString(LOCALE[lang]||"de-DE",{minimumFractionDigits:dd,maximumFractionDigits:2})+" €";}
 function loadCart(){try{return JSON.parse(localStorage.getItem(CKEY)||"{}")||{};}catch(e){return {};}}
 function saveCart(){try{localStorage.setItem(CKEY,JSON.stringify(cart));}catch(e){}}
 function catName(c){return (lang!=="de"&&c["h_"+lang])?c["h_"+lang]:c.h;}
 function pName(p){return (lang!=="de"&&p["name_"+lang])?p["name_"+lang]:p.name;}
 function pDesc(p){return (lang!=="de"&&p["desc_"+lang])?p["desc_"+lang]:(p.desc||"");}
 // index parts by id
 var byId={}; CAT.forEach(function(c){c.items.forEach(function(p){byId[p.id]=p;});});
 // Registry für aus 3D-Baugruppen einzeln entnommene Bauteile (im Warenkorb)
 var SUBKEY="amb_lepton_subparts";
 function loadSub(){try{return JSON.parse(localStorage.getItem(SUBKEY)||"{}")||{};}catch(e){return {};}}
 function saveSub(){try{localStorage.setItem(SUBKEY,JSON.stringify(subReg));}catch(e){}}
 var subReg=loadSub();
 function item(id){return byId[id]||subReg[id]||null;}
 function thumbHTML(p,small){
  if(p.img&&IMG[p.img])return '<img src="'+IMG[p.img]+'" alt="">';
  var ic=ICONS[p.modelKind]||ICONS._default;
  return ic;
 }
 function priceHTML(p){return p.price>0?money(p.price):'<span style="color:var(--faint)">'+t("price_request")+'</span>';}
 function cartCount(){var n=0;for(var k in cart)n+=cart[k];return n;}
 function updateBadge(){var n=cartCount();var b=document.getElementById("badge");b.textContent=n;b.classList.toggle("zero",n===0);}
 function buildChips(){
  var h='<button data-f="" class="'+(filter===""?"active":"")+'">'+esc(t("filter_all"))+'</button>';
  CAT.forEach(function(c){h+='<button data-f="'+esc(c.h)+'" class="'+(filter===c.h?"active":"")+'">'+esc(catName(c))+'</button>';});
  var el=document.getElementById("chips");el.innerHTML=h;
  el.querySelectorAll("button").forEach(function(b){b.addEventListener("click",function(){filter=b.getAttribute("data-f");buildChips();renderCatalog();});});
 }
 function matches(p){
  if(!query)return true;
  var q=query.toLowerCase();
  return (p.art||"").toLowerCase().indexOf(q)>=0 || pName(p).toLowerCase().indexOf(q)>=0 || pDesc(p).toLowerCase().indexOf(q)>=0;
 }
 function renderCatalog(){
  var html="",any=false;
  CAT.forEach(function(c){
   if(filter&&c.h!==filter)return;
   var items=c.items.filter(matches);
   if(!items.length){
    if(query)return;            // bei aktiver Suche leere Kategorien ausblenden
    any=true;
    html+='<div class="catblk"><div class="ch">'+esc(catName(c))+'</div><div class="cards"><div class="phnote">'+esc(t("sub_soon"))+'</div></div></div>';
    return;
   }
   any=true;
   html+='<div class="catblk"><div class="ch">'+esc(catName(c))+'</div><div class="cards">';
   items.forEach(function(p){
    var has3d=!!(p.model&&MODELS[p.model]);
    var incart=cart[p.id]>0;
    html+='<article class="pcard'+(incart?' incart':'')+'" data-id="'+esc(p.id)+'">'
       +'<div class="pthumb" data-3d="'+esc(p.id)+'">'+(has3d?'<div class="badge3d"><svg viewBox="0 0 24 24" fill="none"><path d="M12 2l9 5v10l-9 5-9-5V7z"/></svg>3D</div>':'')+thumbHTML(p)+'</div>'
       +'<div class="pbody"><div class="pname">'+esc(pName(p))+'</div><div class="pdesc">'+esc(pDesc(p))+'</div>'
       +'<div class="pfoot"><span class="part">'+t("art_prefix")+esc(p.art)+'</span><span class="pprice">'+priceHTML(p)+'</span></div>'
       +'<div class="pacts"><button class="b3d" data-3d="'+esc(p.id)+'"'+(has3d?'':' disabled')+'>'+t("btn_3d")+'</button>'
       +'<button class="badd" data-add="'+esc(p.id)+'">'+(incart?t("in_cart"):t("btn_add"))+'</button></div></div></article>';
   });
   html+='</div></div>';
  });
  document.getElementById("catalog").innerHTML=html;
  document.getElementById("empty").style.display=any?"none":"block";
  document.querySelectorAll("[data-add]").forEach(function(b){b.addEventListener("click",function(){addToCart(b.getAttribute("data-add"));});});
  document.querySelectorAll("[data-3d]").forEach(function(b){b.addEventListener("click",function(){var id=b.getAttribute("data-3d");var p=byId[id];if(p&&p.model&&MODELS[p.model])open3D(id);});});
 }
 // ---- Cart ----
 function addToCart(id){cart[id]=(cart[id]||0)+1;saveCart();updateBadge();renderCatalog();renderCart();toast(t("toast_added"));}
 function addSub(art,name){var id="sub:"+art;subReg[id]={art:art,name:name,price:0};saveSub();cart[id]=(cart[id]||0)+1;saveCart();updateBadge();renderCart();toast(t("toast_added"));}
 function setQty(id,q){q=Math.max(0,q|0);if(q===0){delete cart[id];if(subReg[id]){delete subReg[id];saveSub();}}else cart[id]=q;saveCart();updateBadge();renderCatalog();renderCart();}
 function renderCart(){
  var ids=Object.keys(cart).filter(function(id){return item(id);});
  var empty=document.getElementById("cartEmpty"),tail=document.getElementById("cartTail"),wrap=document.getElementById("cartItems");
  if(!ids.length){empty.style.display="block";tail.style.display="none";wrap.innerHTML="";document.getElementById("sendMail").disabled=true;document.getElementById("printReq").disabled=true;return;}
  empty.style.display="none";tail.style.display="block";
  document.getElementById("sendMail").disabled=false;document.getElementById("printReq").disabled=false;
  var h="",sub=0,anyPrice=false;
  ids.forEach(function(id){var p=item(id),q=cart[id];if(p.price>0){sub+=p.price*q;anyPrice=true;}
   h+='<div class="citem"><div class="ci-th">'+thumbHTML(p)+'</div><div class="ci-n"><div class="ci-name">'+esc(pName(p))+'</div><div class="ci-art">'+t("art_prefix")+esc(p.art)+'</div><div class="ci-price">'+priceHTML(p)+'</div>'
    +'<button class="ci-rm" data-rm="'+esc(id)+'">'+t("cart_remove")+'</button></div>'
    +'<div class="qty"><button data-dec="'+esc(id)+'">−</button><input data-q="'+esc(id)+'" value="'+q+'" inputmode="numeric"><button data-inc="'+esc(id)+'">+</button></div></div>';
  });
  wrap.innerHTML=h;
  document.getElementById("subtotal").textContent=anyPrice?money(sub):t("price_request");
  wrap.querySelectorAll("[data-inc]").forEach(function(b){b.addEventListener("click",function(){setQty(b.getAttribute("data-inc"),cart[b.getAttribute("data-inc")]+1);});});
  wrap.querySelectorAll("[data-dec]").forEach(function(b){b.addEventListener("click",function(){setQty(b.getAttribute("data-dec"),cart[b.getAttribute("data-dec")]-1);});});
  wrap.querySelectorAll("[data-rm]").forEach(function(b){b.addEventListener("click",function(){setQty(b.getAttribute("data-rm"),0);});});
  wrap.querySelectorAll("[data-q]").forEach(function(inp){inp.addEventListener("change",function(){setQty(inp.getAttribute("data-q"),parseInt(inp.value,10)||0);});});
 }
 function openCart(){document.getElementById("drawer").classList.add("open");document.getElementById("backdrop").classList.add("open");renderCart();}
 function closeCart(){document.getElementById("drawer").classList.remove("open");document.getElementById("backdrop").classList.remove("open");}
 // ===== 3D-Explorer (three.js wird BEI BEDARF dynamisch geladen) =====
 var THREE,GLTFLoader,OrbitControls,RoomEnvironment,loader,hlMat;
 var renderer,scene,camera,controls,raycaster,curRoot=null,pivot=null,autoSpin=true,groups=[],activeG=null,fitR=1,vinit=false,viewerActive=false,threeReady=false;
 function ensureThree(){
  if(threeReady)return Promise.resolve(true);
  return Promise.all([import("./vendor/three.module.min.js"),import("./vendor/GLTFLoader.js"),import("./vendor/OrbitControls.js"),import("./vendor/RoomEnvironment.js")]).then(function(m){
   THREE=m[0];GLTFLoader=m[1].GLTFLoader;OrbitControls=m[2].OrbitControls;RoomEnvironment=m[3].RoomEnvironment;
   loader=new GLTFLoader();
   hlMat=new THREE.MeshStandardMaterial({color:0xff6a4d,emissive:0xc00000,emissiveIntensity:0.5,metalness:0.2,roughness:0.45});
   threeReady=true;return true;
  });
 }
 function initViewer(){
  if(vinit)return; vinit=true;
  var canvas=document.getElementById("tcanvas");
  renderer=new THREE.WebGLRenderer({canvas:canvas,antialias:true,alpha:true});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
  renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.5;
  scene=new THREE.Scene();
  // Neutrale Studio-Umgebung -> metallische Teile werden hell & plastisch (statt schwarz)
  var pmrem=new THREE.PMREMGenerator(renderer);
  scene.environment=pmrem.fromScene(new RoomEnvironment(),0.04).texture;
  camera=new THREE.PerspectiveCamera(45,1,0.01,1e7);
  controls=new OrbitControls(camera,canvas);
  controls.enableDamping=true;controls.dampingFactor=0.08;
  controls.autoRotate=false;       // Idle-Drehung erfolgt am Modell (pivot), nicht an der Kamera
  controls.enableRotate=false;     // Kamera-Rotation aus -> freie Modell-Rotation (Pointer-Handler unten)
  controls.rotateSpeed=0.75;          // ruhigeres Drehen
  controls.zoomSpeed=0.9;             // feinerer Zoom
  controls.panSpeed=1.2;              // leichtgängigeres Verschieben
  controls.zoomToCursor=true;         // zum Mauszeiger zoomen (statt zur Mitte)
  controls.screenSpacePanning=true;   // intuitives Verschieben in der Bildebene
  // Rundum-Beleuchtung: gleichmäßig hell von allen Seiten (keine dunkle Seite mehr)
  scene.add(new THREE.HemisphereLight(0xffffff,0x9a9aa0,1.6));
  scene.add(new THREE.AmbientLight(0xffffff,0.45));
  var dl=[[1,2,1.4,1.5],[-1,-0.6,-1,1.5],[-1.5,0.8,1,1.1],[1.5,0.6,-1.2,1.1],[0,-1.6,0.4,0.7]];
  dl.forEach(function(p){var d=new THREE.DirectionalLight(0xffffff,p[3]);d.position.set(p[0],p[1],p[2]);scene.add(d);});
  raycaster=new THREE.Raycaster();
  // --- Freie 360°-Rotation des Modells (Pivot, kein Pol-Stopp); Zoom/Pan via OrbitControls ---
  var dn=null,last=null,drag=false;
  var vR=new THREE.Vector3(),vU=new THREE.Vector3(),vT=new THREE.Vector3(),qa=new THREE.Quaternion(),qb=new THREE.Quaternion();
  canvas.addEventListener("pointerdown",function(e){
   if(e.isPrimary===false){drag=false;last=null;return;}   // zweiter Finger -> OrbitControls pant/zoomt
   dn={x:e.clientX,y:e.clientY,t:Date.now()};last={x:e.clientX,y:e.clientY};drag=true;
  });
  canvas.addEventListener("pointermove",function(e){
   if(!drag||!last||!pivot||e.isPrimary===false)return;
   var dx=e.clientX-last.x,dy=e.clientY-last.y;last={x:e.clientX,y:e.clientY};
   if(!dx&&!dy)return;
   autoSpin=false;
   camera.matrixWorld.extractBasis(vR,vU,vT);             // bildschirm-relative Achsen
   qa.setFromAxisAngle(vU,dx*0.006);qb.setFromAxisAngle(vR,dy*0.006);
   pivot.quaternion.premultiply(qa).premultiply(qb);
  });
  window.addEventListener("pointerup",function(e){
   if(drag&&dn&&Math.hypot(e.clientX-dn.x,e.clientY-dn.y)<5&&Date.now()-dn.t<500)pickAt(e);
   drag=false;dn=null;last=null;
  });
  window.addEventListener("resize",resizeViewer);
  var WUP=new THREE.Vector3(0,1,0);
  (function loop(){requestAnimationFrame(loop);if(viewerActive&&renderer){if(autoSpin&&pivot)pivot.rotateOnWorldAxis(WUP,0.004);controls.update();renderer.render(scene,camera);}})();
 }
 function resizeViewer(){if(!renderer)return;var c=renderer.domElement,w=c.clientWidth||1,h=c.clientHeight||1;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}
 function clearModel(){if(curRoot){if(curRoot.parent)curRoot.parent.remove(curRoot);curRoot.traverse(function(o){if(o.isMesh&&o.geometry&&o.geometry.dispose)o.geometry.dispose();});curRoot=null;}groups=[];activeG=null;}
 function nodeName(o){var n=o;while(n){if(n.name)return n.name;n=n.parent;}return "";}
 // Instanz-/Versions-Suffixe entfernen -> Artikelnummer (z.B. 248027_24 -> 248027)
 // PDM-Export (Solid Edge/STEP): nach führender Artikelnummer gruppieren
 // (z.B. PDM_025419_25421 / PDM_045732_cecd62 -> PDM_025419 bzw. PDM_045732)
 function normPart(s){var n=String(s||"");var pdm=n.match(/^(PDM_\d+)/i);if(pdm)return pdm[1];n=n.replace(/_-_\d{4}.*$/,"");n=n.replace(/_oa_\d+$/i,"");n=n.replace(/_v?\d+(\.\d+)+$/i,"");n=n.replace(/_\d{1,3}$/,"");n=n.replace(/_oa$/i,"");return n.trim()||String(s||"");}
 function cleanLabel(s){return String(s||"").replace(/_/g," ").replace(/\s+/g," ").trim()||"Bauteil";}
 // PDM-Nummer normalisieren (führende Nullen egal) -> Artikelnummer+Bezeichnung aus PARTMAP
 function pdmCanon(s){var m=String(s||"").match(/^PDM_0*(\d+)/i);return m?("PDM_"+m[1]):String(s||"");}
 function buildGroups(root){
  var map={},order=[];
  root.traverse(function(o){if(o.isMesh){var key=normPart(nodeName(o)||"(unbenannt)");var g=map[key];if(!g){var info=PARTMAP[pdmCanon(key)];g={raw:key,label:cleanLabel(key),art:(info&&info.art)||key,name:(info&&info.name)||cleanLabel(key),meshes:[],visible:true,count:0};map[key]=g;order.push(g);}g.meshes.push(o);o.userData._g=g;}});
  // echte Stückzahl = Anzahl Instanz-Wurzeln (Knoten mit Artikelname ohne gleichnamigen Vorfahren),
  // NICHT die Mesh-Anzahl (ein Bauteil besteht oft aus mehreren Meshes)
  root.traverse(function(o){if(o.name){var nm=normPart(o.name);var g=map[nm];if(!g)return;var anc=o.parent,isRoot=true;while(anc){if(anc.name&&normPart(anc.name)===nm){isRoot=false;break;}anc=anc.parent;}if(isRoot)g.count++;}});
  order.forEach(function(g){if(!g.count)g.count=g.meshes.length;});
  order.sort(function(a,b){return b.count-a.count||a.label.localeCompare(b.label);});
  groups=order;
 }
 function frameModel(){
  if(!pivot){pivot=new THREE.Group();scene.add(pivot);}
  if(curRoot.parent!==pivot){if(curRoot.parent)curRoot.parent.remove(curRoot);pivot.add(curRoot);}
  pivot.quaternion.identity();curRoot.position.set(0,0,0);pivot.updateMatrixWorld(true);
  var box=new THREE.Box3().setFromObject(curRoot);var c=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3());var r=Math.max(size.x,size.y,size.z)||1;fitR=r;
  curRoot.position.copy(c).multiplyScalar(-1);          // Modell-Mittelpunkt = Pivot-Ursprung
  controls.target.set(0,0,0);var d=r*1.9;camera.position.set(d*0.7,d*0.55,d*0.9);camera.near=r/200;camera.far=r*200;camera.updateProjectionMatrix();controls.minDistance=r*0.05;controls.maxDistance=r*12;controls.update();autoSpin=true;}
 function resetView(){if(!curRoot)return;if(pivot)pivot.quaternion.identity();controls.target.set(0,0,0);var d=fitR*1.9;camera.position.set(d*0.7,d*0.55,d*0.9);autoSpin=true;controls.update();}
 function setHighlight(g,on){g.meshes.forEach(function(m){if(on){if(m.userData._om===undefined)m.userData._om=m.material;m.material=hlMat;}else if(m.userData._om!==undefined){m.material=m.userData._om;m.userData._om=undefined;}});}
 function selectGroup(g,scroll){if(activeG===g)return;if(activeG)setHighlight(activeG,false);activeG=g;if(g)setHighlight(g,true);autoSpin=false;document.querySelectorAll(".prow").forEach(function(r){r.classList.toggle("active",r.__g===g);});if(scroll&&g){var rows=[].slice.call(document.querySelectorAll(".prow"));for(var i=0;i<rows.length;i++){if(rows[i].__g===g){rows[i].scrollIntoView({block:"nearest"});break;}}}}
 function toggleGroup(g){g.visible=!g.visible;g.meshes.forEach(function(m){m.visible=g.visible;});document.querySelectorAll(".prow").forEach(function(r){if(r.__g===g)r.classList.toggle("hidden",!g.visible);});}
 function showAllParts(){groups.forEach(function(g){g.visible=true;g.meshes.forEach(function(m){m.visible=true;});});document.querySelectorAll(".prow").forEach(function(r){r.classList.remove("hidden");});}
 function pickAt(e){if(!curRoot)return;var c=renderer.domElement,r=c.getBoundingClientRect();var p=new THREE.Vector2(((e.clientX-r.left)/r.width)*2-1,-((e.clientY-r.top)/r.height)*2+1);raycaster.setFromCamera(p,camera);var hits=raycaster.intersectObject(curRoot,true);for(var i=0;i<hits.length;i++){var o=hits[i].object;if(o.visible&&o.userData&&o.userData._g){selectGroup(o.userData._g,true);return;}}}
 var EYE_ON='<svg viewBox="0 0 24 24"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/></svg>';
 var EYE_OFF='<svg viewBox="0 0 24 24"><path d="M3 3l18 18M10 5.2A8.6 8.6 0 0112 5c6.5 0 10 7 10 7a18 18 0 01-3.2 4M6.5 6.6C3.6 8.2 2 12 2 12s3.5 7 10 7c1.4 0 2.7-.3 3.8-.7M9.9 9.9a3 3 0 004.2 4.2"/></svg>';
 var CART_S='<svg viewBox="0 0 24 24"><path d="M3 4h2l2 11h10l2-8H6"/><circle cx="9" cy="20" r="1.3"/><circle cx="17" cy="20" r="1.3"/></svg>';
 function renderPartList(q){
  var list=document.getElementById("partList"),html="";
  groups.forEach(function(g,idx){
   if(q){if((g.raw+" "+g.name+" "+g.art).toLowerCase().indexOf(q)<0)return;}
   html+='<div class="prow'+(g===activeG?' active':'')+(g.visible?'':' hidden')+'" data-i="'+idx+'">'
    +'<button class="eye" data-eye="'+idx+'" title="'+esc(t("tip_toggle"))+'">'+(g.visible?EYE_ON:EYE_OFF)+'</button>'
    +'<div class="pmid" data-sel="'+idx+'"><div class="pml">'+esc(g.name)+'</div><div class="pma">'+esc(g.art)+'</div></div>'
    +(g.count>1?'<span class="qbadge" title="'+esc(t("qty_in_assembly"))+'">×'+g.count+'</span>':'')
    +'<button class="pcartbtn" data-pcart="'+idx+'" title="'+esc(t("btn_add"))+'">'+CART_S+'</button></div>';
  });
  list.innerHTML=html||'<div style="padding:20px;text-align:center;color:var(--faint);font-size:12px">'+esc(t("no_results"))+'</div>';
  document.getElementById("partCount").textContent=groups.length;
  list.querySelectorAll(".prow").forEach(function(r){r.__g=groups[+r.getAttribute("data-i")];});
  list.querySelectorAll("[data-sel]").forEach(function(el){el.addEventListener("click",function(){selectGroup(groups[+el.getAttribute("data-sel")],false);});});
  list.querySelectorAll("[data-eye]").forEach(function(b){b.addEventListener("click",function(e){e.stopPropagation();toggleGroup(groups[+b.getAttribute("data-eye")]);});});
  list.querySelectorAll("[data-pcart]").forEach(function(b){b.addEventListener("click",function(e){e.stopPropagation();var g=groups[+b.getAttribute("data-pcart")];addSub(g.art,g.name);});});
 }
 function showNo(msg){document.getElementById("mvLoad").style.display="none";var no=document.getElementById("mvNo");no.style.display="flex";no.textContent=msg||t("no_3d");}
 function open3D(id){
  var p=byId[id];document.getElementById("mvName").textContent=pName(p);document.getElementById("mvArt").textContent=t("art_prefix")+p.art;
  document.getElementById("mvModal").classList.add("open");viewerActive=true;
  document.getElementById("mvNo").style.display="none";
  document.getElementById("partList").innerHTML="";document.getElementById("partCount").textContent="0";
  var ps=document.getElementById("partSearch");if(ps)ps.value="";
  document.getElementById("mvLoad").style.display="flex";
  var url=p.model&&MODELS[p.model];
  if(!url){showNo();return;}
  ensureThree().then(function(){
   initViewer();setTimeout(resizeViewer,30);clearModel();
   loader.load(url,function(gltf){
    curRoot=gltf.scene||(gltf.scenes&&gltf.scenes[0]);scene.add(curRoot);
    // Umgebungslicht je Material verstärken -> Teile auch im Schatten gut sichtbar
    curRoot.traverse(function(o){if(o.isMesh&&o.material){(Array.isArray(o.material)?o.material:[o.material]).forEach(function(mt){if("envMapIntensity" in mt){mt.envMapIntensity=1.3;mt.needsUpdate=true;}});}});
    buildGroups(curRoot);frameModel();resizeViewer();renderPartList("");
    document.getElementById("mvLoad").style.display="none";
   },undefined,function(){showNo();});
  }).catch(function(){showNo(t("three_fail"));});
 }
 function close3D(){document.getElementById("mvModal").classList.remove("open");viewerActive=false;autoSpin=true;}
 // ---- toast ----
 var toTimer;function toast(m){var el=document.getElementById("toast");el.textContent=m;el.classList.add("show");clearTimeout(toTimer);toTimer=setTimeout(function(){el.classList.remove("show");},1600);}
 // ---- fields persist ----
 var FLDS=["c_firma","c_name","c_tel","c_mail","c_masch","c_msg"];
 function loadFields(){try{var o=JSON.parse(localStorage.getItem(FKEY)||"{}");FLDS.forEach(function(id){if(o[id]!=null){var e=document.getElementById(id);if(e)e.value=o[id];}});}catch(e){}}
 function saveFields(){try{var o={};FLDS.forEach(function(id){var e=document.getElementById(id);if(e)o[id]=e.value;});localStorage.setItem(FKEY,JSON.stringify(o));}catch(e){}}
 function fv(id){var e=document.getElementById(id);return e?(e.value||"").trim():"";}
 // ---- request lines (shared by mail + print) ----
 function lines(){return Object.keys(cart).filter(function(id){return item(id);}).map(function(id){return {p:item(id),q:cart[id]};});}
 function subtotal(){var s=0;lines().forEach(function(l){if(l.p.price>0)s+=l.p.price*l.q;});return s;}
 // ---- send mail ----
 function sendMail(){
  var L=lines();if(!L.length){toast(t("alert_empty"));return;}
  var body=t("mail_intro")+"\n\n";
  L.forEach(function(l){body+="  "+l.q+"× "+l.p.art+"  "+pName(l.p)+(l.p.price>0?"   "+money(l.p.price*l.q):"")+"\n";});
  var sub=subtotal();if(sub>0)body+="\n"+t("cart_subtotal")+": "+money(sub)+"\n";
  if(fv("c_masch"))body+="\n"+t("lbl_masch")+": "+fv("c_masch")+"\n";
  if(fv("c_msg"))body+="\n"+fv("c_msg")+"\n";
  body+="\n"+t("mail_regards")+"\n"+[fv("c_name"),fv("c_firma")].filter(Boolean).join("\n");
  var contact=[fv("c_mail"),fv("c_tel")].filter(Boolean).join(" · ");if(contact)body+="\n"+contact;
  var href="mailto:"+MAIL+"?subject="+encodeURIComponent(t("mail_subject"))+"&body="+encodeURIComponent(body);
  window.location.href=href;
 }
 // ---- print ----
 function buildDoc(){
  var L=lines();
  var stripe='<div class="topstr"><span style="background:var(--red)"></span><span style="background:var(--slate)"></span><span style="background:#fff"></span><span style="background:var(--gold)"></span></div>';
  var date=new Date().toLocaleDateString(LOCALE[lang]||"de-DE",{day:"2-digit",month:"2-digit",year:"numeric"});
  var rows="",sub=0,anyP=false;
  L.forEach(function(l,i){var line=l.p.price>0?l.p.price*l.q:0;if(l.p.price>0){sub+=line;anyP=true;}
   rows+='<tr><td>'+(i+1)+'</td><td>'+esc(l.p.art)+'</td><td>'+esc(pName(l.p))+'</td><td class="r">'+l.q+'</td><td class="r">'+(l.p.price>0?money(l.p.price):t("price_request"))+'</td><td class="r">'+(l.p.price>0?money(line):"—")+'</td></tr>';});
  var from=[fv("c_firma"),fv("c_name"),fv("c_mail"),fv("c_tel")].filter(Boolean).map(esc).join("<br>")||'<span style="color:#9a9aa0">—</span>';
  var doc=stripe+'<div class="dpad">'
   +'<div class="dhd"><div class="dfirm"><img class="dlogo" src="'+LOGO_D+'"><div class="fnm" style="margin-top:3px">Maschinenbau GmbH</div>Am Gewerbering 14 · D-84069 Schierling<br>www.alzinger-recyclingtechnik.com<br>'+MAIL+'</div>'
   +'<div class="dmeta">'+t("doc_date")+' <b>'+esc(date)+'</b></div></div>'
   +'<div class="dtitle">'+esc(t("doc_title"))+'</div>'
   +'<div class="dparties"><div><span class="s">'+t("doc_from")+'</span>'+from+(fv("c_masch")?'<br><span style="color:#9a9aa0;font-size:11px">'+t("doc_machine")+': '+esc(fv("c_masch"))+'</span>':'')+'</div>'
   +'<div><span class="s">'+t("doc_to")+'</span><b>Alzinger Maschinenbau GmbH</b><br>Am Gewerbering 14<br>D-84069 Schierling</div></div>'
   +'<table class="dtbl"><thead><tr><th>'+t("col_pos")+'</th><th>'+t("col_art")+'</th><th>'+t("col_name")+'</th><th class="r">'+t("col_qty")+'</th><th class="r">'+t("col_price")+'</th><th class="r">'+t("col_sum")+'</th></tr></thead><tbody>'+rows+'</tbody></table>'
   +(anyP?'<div class="dtot">'+t("doc_total")+': '+money(sub)+'</div>':'')
   +(fv("c_msg")?'<div class="dmsg"><b>'+t("doc_msg")+':</b>\n'+esc(fv("c_msg"))+'</div>':'')
   +'<div class="dfo">'+t("doc_foot")+'</div></div>';
  document.getElementById("doc").innerHTML=doc;
 }
 function printReq(){if(!lines().length){toast(t("alert_empty"));return;}buildDoc();window.print();}
 // ---- i18n apply ----
 function applyLang(){
  document.documentElement.lang=lang;
  document.querySelectorAll("[data-i18n]").forEach(function(el){el.textContent=t(el.getAttribute("data-i18n"));});
  document.querySelectorAll("[data-i18n-ph]").forEach(function(el){el.setAttribute("placeholder",t(el.getAttribute("data-i18n-ph")));});
  document.querySelectorAll("#langsel button").forEach(function(b){b.classList.toggle("active",b.getAttribute("data-lang")===lang);});
  document.title=t("page_title");
 }
 function setLang(l){if(!I18N[l])return;lang=l;try{localStorage.setItem(LKEY,l);}catch(e){}applyLang();buildChips();renderCatalog();renderCart();}
 function init(){
  document.getElementById("tbLogo").src=LOGO_L;
  applyLang();buildChips();renderCatalog();updateBadge();renderCart();loadFields();
  document.getElementById("search").addEventListener("input",function(e){query=e.target.value;renderCatalog();});
  document.querySelectorAll("#langsel button").forEach(function(b){b.addEventListener("click",function(){setLang(b.getAttribute("data-lang"));});});
  document.getElementById("cartBtn").addEventListener("click",openCart);
  document.getElementById("cartClose").addEventListener("click",closeCart);
  document.getElementById("backdrop").addEventListener("click",closeCart);
  document.getElementById("mvClose").addEventListener("click",close3D);
  document.getElementById("mvModal").addEventListener("click",function(e){if(e.target.id==="mvModal")close3D();});
  document.getElementById("mvReset").addEventListener("click",resetView);
  document.getElementById("mvShowAll").addEventListener("click",showAllParts);
  document.getElementById("partSearch").addEventListener("input",function(e){renderPartList((e.target.value||"").toLowerCase());});
  document.getElementById("sendMail").addEventListener("click",sendMail);
  document.getElementById("printReq").addEventListener("click",printReq);
  document.getElementById("clearCart").addEventListener("click",function(){cart={};saveCart();updateBadge();renderCatalog();renderCart();});
  FLDS.forEach(function(id){var e=document.getElementById(id);if(e)e.addEventListener("input",saveFields);});
  document.addEventListener("keydown",function(e){if(e.key==="Escape"){close3D();closeCart();}});
 }
 init();
})();
</script>
<script>
if("serviceWorker" in navigator){window.addEventListener("load",function(){navigator.serviceWorker.register("sw.js").catch(function(){});});}
</script>
</body>
</html>
'''

out=TPL
out=out.replace("%%RED%%",RED).replace("%%RED2%%",RED2)
out=out.replace("%%HERO%%",HERO)
out=out.replace("%%LOGOL%%",LOGO_L).replace("%%LOGOD%%",LOGO_D)
out=out.replace("%%MAIL%%",MAIL)
out=out.replace("%%IMG%%",json.dumps(IMG))
out=out.replace("%%MODELS%%",json.dumps(MODELS))
out=out.replace("%%CAT%%",json.dumps(CAT,ensure_ascii=False))
out=out.replace("%%I18N%%",json.dumps(I18N,ensure_ascii=False))
out=out.replace("%%PARTMAP%%",json.dumps(PARTMAP,ensure_ascii=False))

for tok in ["%%RED%%","%%RED2%%","%%HERO%%","%%LOGOL%%","%%LOGOD%%","%%MAIL%%","%%IMG%%","%%MODELS%%","%%CAT%%","%%I18N%%","%%PARTMAP%%"]:
    assert tok not in out, "Token übrig: "+tok
for need in ['id="cartBtn"','id="tcanvas"','id="partList"','renderCatalog','data-lang="pl"','ensureThree','importmap','./vendor/GLTFLoader.js']:
    assert need in out, "fehlt: "+need
# vendor/three.js muss vorhanden sein (Laufzeit-Abhängigkeit der 3D-Ansicht)
for vf in ["three.module.min.js","GLTFLoader.js","OrbitControls.js","BufferGeometryUtils.js"]:
    assert os.path.exists(os.path.join(OUTDIR,"vendor",vf)), "vendor fehlt: ersatzteile/vendor/"+vf

p=os.path.join(OUTDIR,"index.html")
open(p,"w",encoding="utf8").write(out)
print("ersatzteile/index.html erzeugt – bytes",len(out.encode("utf8")))
