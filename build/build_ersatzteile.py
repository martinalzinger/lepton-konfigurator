#!/usr/bin/env python3
# Baut die eigenständige Seite ./ersatzteile.html (Ersatzteilkatalog mit 3D-Ansicht + Warenkorb).
# Quelle: spareparts.json, i18n_ersatzteile.json, assets*.b64.json, modelviewer.min.js, glbgen.py,
#         sowie CAD-Dateien in build/models_cad/ (STEP/STP/GLB/GLTF -> 3D, SEV -> Vorschaubild).
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
I18N_RAW=jload("i18n_ersatzteile.json")
SP_RAW=jload("spareparts.json")
LANGS=["de","en","pl","fr"]

# ---- model-viewer (offline gebündelt) ----
MV=open(os.path.join(HERE,"modelviewer.min.js"),encoding="utf8").read()
MV=MV.replace("</script>","<\\/script>")

# ---- MODELS: GLB-Daten als data-URI ----
MODELS={}   # key -> data:model/gltf-binary;base64,...
def glb_uri(b): return "data:model/gltf-binary;base64,"+base64.b64encode(b).decode()
PROC_KINDS={"scheibe","welle","lager","ritzel","trommel","keilriemen","abstreifer","gehaeuse"}
def proc_model(kind):
    k="proc:"+kind
    if k not in MODELS: MODELS[k]=glb_uri(glbgen.model(kind))
    return k

# ---- CAD-Import aus build/models_cad/ ----
def parse_meta(path, base):
    """Artikelnummer + Bezeichnung aus STEP-PRODUCT bzw. Dateiname."""
    art=name=None
    if path.lower().endswith((".step",".stp")):
        try:
            txt=open(path,encoding="utf8",errors="ignore").read(200000)
            m=re.search(r"PRODUCT\s*\(\s*'([^']*)'\s*,\s*'([^']*)'", txt)
            if m:
                art=(m.group(1) or "").strip() or None
                name=(m.group(2) or "").strip() or None
        except Exception: pass
    fm=re.match(r"^\s*([0-9][0-9A-Za-z._\-/]*)[ _\-]+(.+?)\s*$", base)
    if not art and fm: art=fm.group(1)
    if not name and fm: name=fm.group(2)
    return (art or base), (name or base)

def process_cad():
    """Verarbeitet models_cad/. Gibt Liste importierter Teile zurück und füllt MODELS/IMG."""
    imported=[]
    files=sorted(glob.glob(os.path.join(HERE,"models_cad","*")))
    for path in files:
        b=os.path.basename(path); low=b.lower()
        if low.endswith((".step.glb",".stp.glb")) or b=="README.md":
            continue  # temporäres Konvertierungs-Artefakt / Doku überspringen
        stem=os.path.splitext(b)[0]
        if low.endswith((".step",".stp")):
            try:
                import cascadio
                out=path+".glb"
                cascadio.step_to_glb(path,out)
                MODELS[b]=glb_uri(open(out,"rb").read()); os.remove(out)
                art,name=parse_meta(path,stem)
                imported.append({"art":art,"name":name,"model":b,"img":None})
                print("  3D  STEP ->",b)
            except Exception as e:
                print("  !! STEP fehlgeschlagen:",b,e)
        elif low.endswith((".glb",".gltf")):
            data=open(path,"rb").read()
            MODELS[b]=glb_uri(data) if low.endswith(".glb") else "data:model/gltf+json;base64,"+base64.b64encode(data).decode()
            art,name=parse_meta(path,stem)
            imported.append({"art":art,"name":name,"model":b,"img":None})
            print("  3D  GLB  ->",b)
        elif low.endswith(".sev"):
            uri=sev_preview(path)
            art,name=parse_meta(path,stem)
            if uri:
                IMG["cad:"+b]=uri
                imported.append({"art":art,"name":name,"model":None,"img":"cad:"+b})
                print("  2D  SEV  -> Vorschau",b)
            else:
                imported.append({"art":art,"name":name,"model":None,"img":None})
                print("  ?? SEV ohne Vorschau:",b)
    return imported

def sev_preview(path):
    """Extrahiert das eingebettete PNG-Vorschaubild aus einer Solid-Edge .sev-Datei."""
    try:
        txt=open(path,encoding="utf8",errors="ignore").read()
        m=re.search(r"<SEModelPreview[^>]*>\s*<script[^>]*>(.*?)</script>", txt, re.S)
        if not m: return None
        raw=base64.b64decode(m.group(1).strip())
        s=raw.find(b"\x89PNG\r\n\x1a\n"); e=raw.find(b"IEND")
        if s<0 or e<0: return None
        return "data:image/png;base64,"+base64.b64encode(raw[s:e+8]).decode()
    except Exception:
        return None

cad_imported=process_cad()

# ---- Katalog aufbauen (Kategorien + Auto-Import) ----
def resolve_model(part):
    m=part.get("model")
    if not m: return None
    if m in PROC_KINDS: return proc_model(m)
    if m in MODELS: return m
    return None  # referenzierte Datei (noch) nicht vorhanden

CAT=[]
seen_art=set()
for cat in SP_RAW["kategorien"]:
    items=[]
    for p in cat["teile"]:
        seen_art.add(p["art"])
        mk=resolve_model(p)
        items.append({
            "id":p["id"], "art":p["art"],
            "name":p["name"], "name_en":p.get("name_en"),
            "desc":p.get("desc",""), "desc_en":p.get("desc_en"),
            "price":p.get("price",0),
            "model": mk, "modelKind": p.get("model") if p.get("model") in PROC_KINDS else None,
            "img": p.get("img")
        })
    CAT.append({"h":cat["h"], "h_en":cat.get("h_en"), "items":items})

auto=[p for p in cad_imported if p["art"] not in seen_art]
if auto:
    CAT.append({"h":"Aus CAD importiert","h_en":"Imported from CAD","items":[{
        "id":"cad-"+str(i), "art":p["art"], "name":p["name"], "name_en":None,
        "desc":"", "desc_en":None, "price":0,
        "model": p["model"] if p["model"] in MODELS else None, "modelKind":None, "img":p["img"]
    } for i,p in enumerate(auto)]})

# ---- i18n lang-major ----
I18N={lg:{k:I18N_RAW[k][lg] for k in I18N_RAW} for lg in LANGS}

# ---- nur tatsächlich referenzierte Bilder einbetten (spart ~1 MB) ----
used_img=set()
for c in CAT:
    for p in c["items"]:
        if p.get("img"): used_img.add(p["img"])
IMG={k:IMG[k] for k in used_img if k in IMG}

print("Modelle eingebettet:",len(MODELS)," Bilder:",len(IMG))

# ================= HTML-TEMPLATE =================
TPL=r'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Alzinger · Ersatzteilkatalog Lepton 5100</title>
<meta name="theme-color" content="#c00000">
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
/* 3D modal */
.mvmodal{position:fixed;inset:0;background:rgba(16,17,19,.72);z-index:97;display:none;align-items:center;justify-content:center;padding:20px}
.mvmodal.open{display:flex}
.mvbox{background:#fff;border-radius:14px;width:min(720px,96vw);max-height:92vh;overflow:hidden;position:relative;display:flex;flex-direction:column}
.mvbox .mvtop{display:flex;justify-content:space-between;align-items:flex-start;padding:16px 18px 10px}
.mvbox .mvname{font-weight:700;font-size:17px}
.mvbox .mvart{font-family:var(--mono);font-size:11px;color:var(--faint);margin-top:2px}
.mvbox .mvx{background:var(--field);border:0;width:34px;height:34px;border-radius:50%;font-size:20px;cursor:pointer;color:var(--ink);flex-shrink:0}
.mvbox .mvx:hover{background:var(--line)}
model-viewer{width:100%;height:min(56vh,440px);background:linear-gradient(180deg,#fbfbf9,#eceae4);--poster-color:transparent}
.mvno{padding:50px 20px;text-align:center;color:var(--faint);font-size:14px}
.mvhint{font-family:var(--mono);font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--faint);text-align:center;padding:10px 0 16px}
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
</head>
<body>
<header class="topbar">
  <div class="topbar-in"><div class="tb-row">
    <a class="tb-back" href="index.html">‹ <span data-i18n="nav_back">Konfigurator</span></a>
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
    <model-viewer id="mv" camera-controls auto-rotate auto-rotate-delay="0" rotation-per-second="22deg" shadow-intensity="1" exposure="1.05" interaction-prompt="none" touch-action="pan-y"></model-viewer>
    <div class="mvno" id="mvNo" style="display:none"></div>
    <div class="mvhint" data-i18n="viewer_hint"></div>
  </div>
</div>
<div id="toast"></div>
<div id="doc"></div>
<script type="module">%%MV%%</script>
<script>
const IMG=%%IMG%%; const MODELS=%%MODELS%%; const CAT=%%CAT%%; const I18N=%%I18N%%;
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
   if(!items.length)return;
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
 function setQty(id,q){q=Math.max(0,q|0);if(q===0)delete cart[id];else cart[id]=q;saveCart();updateBadge();renderCatalog();renderCart();}
 function renderCart(){
  var ids=Object.keys(cart).filter(function(id){return byId[id];});
  var empty=document.getElementById("cartEmpty"),tail=document.getElementById("cartTail"),wrap=document.getElementById("cartItems");
  if(!ids.length){empty.style.display="block";tail.style.display="none";wrap.innerHTML="";document.getElementById("sendMail").disabled=true;document.getElementById("printReq").disabled=true;return;}
  empty.style.display="none";tail.style.display="block";
  document.getElementById("sendMail").disabled=false;document.getElementById("printReq").disabled=false;
  var h="",sub=0,anyPrice=false;
  ids.forEach(function(id){var p=byId[id],q=cart[id];if(p.price>0){sub+=p.price*q;anyPrice=true;}
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
 // ---- 3D ----
 var mv=document.getElementById("mv");
 function open3D(id){
  var p=byId[id];document.getElementById("mvName").textContent=pName(p);document.getElementById("mvArt").textContent=t("art_prefix")+p.art;
  var ok=p.model&&MODELS[p.model];
  document.getElementById("mvNo").style.display=ok?"none":"block";mv.style.display=ok?"block":"none";
  if(ok){mv.setAttribute("src",MODELS[p.model]);mv.setAttribute("alt",pName(p));}
  else document.getElementById("mvNo").textContent=t("no_3d");
  document.getElementById("mvModal").classList.add("open");
 }
 function close3D(){document.getElementById("mvModal").classList.remove("open");mv.removeAttribute("src");}
 // ---- toast ----
 var toTimer;function toast(m){var el=document.getElementById("toast");el.textContent=m;el.classList.add("show");clearTimeout(toTimer);toTimer=setTimeout(function(){el.classList.remove("show");},1600);}
 // ---- fields persist ----
 var FLDS=["c_firma","c_name","c_tel","c_mail","c_masch","c_msg"];
 function loadFields(){try{var o=JSON.parse(localStorage.getItem(FKEY)||"{}");FLDS.forEach(function(id){if(o[id]!=null){var e=document.getElementById(id);if(e)e.value=o[id];}});}catch(e){}}
 function saveFields(){try{var o={};FLDS.forEach(function(id){var e=document.getElementById(id);if(e)o[id]=e.value;});localStorage.setItem(FKEY,JSON.stringify(o));}catch(e){}}
 function fv(id){var e=document.getElementById(id);return e?(e.value||"").trim():"";}
 // ---- request lines (shared by mail + print) ----
 function lines(){return Object.keys(cart).filter(function(id){return byId[id];}).map(function(id){return {p:byId[id],q:cart[id]};});}
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
  document.getElementById("sendMail").addEventListener("click",sendMail);
  document.getElementById("printReq").addEventListener("click",printReq);
  document.getElementById("clearCart").addEventListener("click",function(){cart={};saveCart();updateBadge();renderCatalog();renderCart();});
  FLDS.forEach(function(id){var e=document.getElementById(id);if(e)e.addEventListener("input",saveFields);});
  document.addEventListener("keydown",function(e){if(e.key==="Escape"){close3D();closeCart();}});
 }
 init();
})();
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
out=out.replace("%%MV%%",MV)   # zuletzt (großer Block)

for tok in ["%%RED%%","%%RED2%%","%%HERO%%","%%LOGOL%%","%%LOGOD%%","%%MAIL%%","%%IMG%%","%%MODELS%%","%%CAT%%","%%I18N%%","%%MV%%"]:
    assert tok not in out, "Token übrig: "+tok
for need in ['id="cartBtn"','id="mv"','customElements','renderCatalog','data-lang="pl"','model-viewer']:
    assert need in out, "fehlt: "+need

p=os.path.join(HERE,"..","ersatzteile.html")
open(p,"w",encoding="utf8").write(out)
print("ersatzteile.html erzeugt – bytes",len(out.encode("utf8")))
