#!/usr/bin/env python3
# Baut die eigenständige Vertriebs-/CRM-Seite ./vertrieb/index.html.
# Vollständig getrennt vom Konfigurator und vom Ersatzteilkatalog:
#  - eigener Ordner/URL  (…/vertrieb/)
#  - eigener Service-Worker (vertrieb/sw.js, Scope /vertrieb/, Cache-Namespace "vertrieb-")
#  - eigenes Manifest/Icons
# Daten liegen offline im Browser (localStorage "amb_lepton_crm"), pro Gerät.
# Verknüpfung zum Konfigurator: gleicher Origin -> liest gespeicherte Angebote
# (localStorage "amb_lepton_configs") und nutzt dieselbe Anmeldung
# (amb_lepton_auth / amb_lepton_user), um den eingeloggten Vertriebler zu kennen.
#
# Aufruf:  python3 build/build_vertrieb.py
import os, json, shutil

HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.normpath(os.path.join(HERE,".."))
OUTDIR=os.path.join(ROOT,"vertrieb")
os.makedirs(OUTDIR,exist_ok=True)

def jload(name): return json.load(open(os.path.join(HERE,name),encoding="utf8"))

A=jload("assets.b64.json")
LOGO_L=A["LOGO_L"]; LOGO_D=A["LOGO_D"]; RED=A["RED"]; RED2=A["RED2"]

# Dieselbe Anmelde-Benutzerliste wie der Konfigurator (build.py). Bewusst gespiegelt,
# damit /vertrieb/ eigenständig funktioniert und den eingeloggten Vertriebler kennt.
USERS_JS='[{h:"2a0e88896d2303027849314ab026e16a096c8234cc0bb3b4eb9ffe5e1fbfd324",n:""},{h:"e5dca8f9c2337bcc4fc9df0c78714044754ce68c0685d5bb7c250dcaf7069615",n:"Johannes Rudel"},{h:"b6b00d05870bc4a123c79e339113393677abc681c59f1f82808b72770499e9dd",n:"Tobias Ermel"},{h:"c88ea0954fae0ae122032164bcd08d488841e5083c218766b77578068a054af9",n:"Richard Alzinger",tel:"+49 170 3336025",mail:"richard@alzinger-maschinenbau.de"},{h:"9833d8644a16501b9eab7a849a294b8b209e32db63366041b50bbfa0107da4d3",n:"Adam Domaradzki",hd:1},{h:"0ad1350f32d0d469d4c044cb1ad38b4964763caf497112c76bfc462a81ccda9b",n:"Łukasz Zdziennicki",hd:1},{h:"6dce472c58a319f6b55518c7ddcb0e438cdc50c1566ff46ec420a12289df2980",n:"Martin Alzinger",tel:"+49 170 3128533",mail:"martin@alzinger-maschinenbau.de"}]'

TPL = r'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>Alzinger · Vertrieb / CRM</title>
<meta name="theme-color" content="#c00000">
<link rel="manifest" href="manifest.webmanifest">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Vertrieb CRM">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="apple-touch-icon" href="icon-192.png">
<link rel="icon" type="image/png" sizes="32x32" href="icon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="icon-192.png">
<link rel="shortcut icon" href="favicon.ico">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="vendor/leaflet.css">
<style>
:root{--red:%%RED%%;--red2:%%RED2%%;--paper:#f1f1ee;--surface:#fff;--ink:#16181a;--muted:#5e6166;--faint:#9a9aa0;--line:#e4e2db;--line-strong:#d3cfc4;--field:#f7f6f2;--gold:#a28231;--slate:#4e5258;--pos:#15803d;--warn:#b45309;--red-soft:rgba(192,0,0,.08);--sans:'Manrope','Helvetica Neue',Arial,sans-serif;--mono:'IBM Plex Mono',ui-monospace,Menlo,monospace;}
*{box-sizing:border-box;margin:0;padding:0}
html{-webkit-text-size-adjust:100%}
body{font-family:var(--sans);background:var(--paper);color:var(--ink);line-height:1.45;font-size:15px;-webkit-font-smoothing:antialiased;padding-bottom:env(safe-area-inset-bottom)}
button{font-family:inherit}
input,select,textarea{font-family:var(--sans);font-size:15px}
.mono{font-family:var(--mono)}
.hidden{display:none!important}

/* Topbar */
.topbar{position:sticky;top:0;z-index:80;background:var(--red);color:#fff}
.topbar-in{max-width:1120px;margin:0 auto;padding:9px 16px calc(9px + env(safe-area-inset-top)) 16px;padding-top:max(9px,env(safe-area-inset-top))}
.tb-row{display:flex;align-items:center;justify-content:space-between;gap:12px}
.tb-brand{display:flex;flex-direction:column;align-items:flex-start;gap:2px;min-width:0}
.tb-brand img{height:58px;display:block;padding-bottom:11px;border-bottom:1.6px solid rgba(255,255,255,.9)}
.tb-sub{font-family:var(--mono);font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:#fff;opacity:.97;font-weight:700;margin-top:9px}
.conn{font-family:var(--mono);font-size:11px;letter-spacing:.02em;white-space:nowrap;display:inline-flex;align-items:center;gap:4px;margin-top:2px}
.conn svg{width:14px;height:14px;flex:none}
.conn.on{color:#bbf7d0}.conn.off{color:rgba(255,255,255,.72)}
.tb-user{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:600}
.tb-user .av{width:30px;height:30px;border-radius:50%;background:rgba(255,255,255,.18);display:inline-flex;align-items:center;justify-content:center;font-family:var(--mono);font-size:12px;font-weight:600}
.tb-user button{background:none;border:0;color:rgba(255,255,255,.85);font-size:11px;cursor:pointer;text-decoration:underline;text-underline-offset:2px}
#refreshBtn{display:inline-flex;align-items:center;gap:5px;background:rgba(255,255,255,.16)!important;border-radius:8px;padding:6px 11px;text-decoration:none!important;color:#fff!important;font-size:12px}
#refreshBtn svg{width:15px;height:15px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
#refreshBtn.spin svg{animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
@media(max-width:520px){#refreshBtn span{display:none}#refreshBtn{padding:7px}}

/* Tab-Navigation – Pills mit Icon */
.nav{position:sticky;top:0;z-index:70;background:var(--surface);border-bottom:1px solid var(--line)}
.nav-in{max-width:1120px;margin:0 auto;display:flex;gap:8px;padding:11px 12px;overflow-x:auto;scrollbar-width:none}
.nav-in::-webkit-scrollbar{display:none}
.nav button{position:relative;display:inline-flex;align-items:center;gap:7px;background:var(--field);border:1px solid var(--line);border-radius:999px;padding:9px 15px;font-size:13px;font-weight:600;color:var(--muted);cursor:pointer;white-space:nowrap;transition:background .14s,color .14s,border-color .14s,box-shadow .14s}
.nav button:hover{border-color:var(--line-strong);color:var(--ink)}
.nav button svg{width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:1.8}
.nav button.active{background:var(--red);border-color:var(--red);color:#fff;box-shadow:0 5px 14px rgba(192,0,0,.26)}
.nav button .badge{min-width:18px;height:18px;padding:0 5px;border-radius:9px;background:var(--red);color:#fff;font-family:var(--mono);font-size:9px;font-weight:700;display:inline-flex;align-items:center;justify-content:center}
.nav button.active .badge{background:#fff;color:var(--red)}

.wrap{max-width:1120px;margin:0 auto;padding:18px 16px 40px}
.view{display:none}
.view.active{display:block;animation:fade .18s ease}
@keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}

h2.vh{font-size:20px;font-weight:800;letter-spacing:-.01em;margin-bottom:2px}
.sub{color:var(--muted);font-size:13px;margin-bottom:16px}

/* Karten / Statistik */
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin-bottom:20px}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:13px 14px}
.stat .n{font-family:var(--mono);font-size:24px;font-weight:600;line-height:1}
.stat .l{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-top:6px}
.stat.accent{border-color:var(--red);background:var(--red-soft)}
.stat.accent .n{color:var(--red)}
/* Status-farbige Kacheln */
.stat.s-lead{background:#fff3e0;border-color:#ffe2bd}.stat.s-lead .n{color:var(--warn)}
.stat.s-angebot{background:#e7f0ff;border-color:#cfe0ff}.stat.s-angebot .n{color:#1d4ed8}
.stat.s-kunde{background:#e6f4ea;border-color:#c2e6cd}.stat.s-kunde .n{color:var(--pos)}
.stat.s-haendler{background:#f1ecfb;border-color:#ddd0f5}.stat.s-haendler .n{color:#6d28d9}

.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px;margin-bottom:12px}
.card h3{font-size:13px;font-family:var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:10px;display:flex;align-items:center;gap:8px}
.card h3 .cnt{margin-left:auto;font-family:var(--mono);font-size:11px;background:var(--field);border:1px solid var(--line);border-radius:20px;padding:2px 8px;color:var(--ink)}

/* Kontaktliste */
.toolbar{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px}
.toolbar input.search{flex:1;min-width:180px}
.field,input.search,select.filter{width:100%;border:1px solid var(--line-strong);background:var(--field);border-radius:9px;padding:10px 11px;color:var(--ink);outline:none}
.field:focus,input.search:focus,select.filter:focus{border-color:var(--red);background:#fff}
select.filter{width:auto;min-width:120px;flex:0 0 auto}

.clist{display:grid;gap:9px}
.crow{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:13px 14px;cursor:pointer;display:flex;gap:12px;align-items:flex-start;transition:.12s}
.crow:hover{border-color:var(--line-strong);box-shadow:0 2px 10px rgba(0,0,0,.04)}
.crow .av{flex:0 0 auto;width:40px;height:40px;border-radius:10px;background:var(--ink);color:#fff;display:flex;align-items:center;justify-content:center;font-family:var(--mono);font-weight:600;font-size:14px}
.crow .mid{flex:1;min-width:0}
.crow .nm{font-weight:700;font-size:15px}
.crow .meta{font-size:12px;color:var(--muted);margin-top:2px;display:flex;flex-wrap:wrap;gap:4px 10px}
.crow .meta .flag{font-family:var(--mono);font-weight:600;color:var(--ink)}
.crow .hit{font-size:12px;color:var(--muted);margin-top:5px;line-height:1.45;display:flex;align-items:flex-start;gap:5px}
.crow .hit svg{width:13px;height:13px;flex:none;margin-top:2px;fill:none;stroke:currentColor;stroke-width:1.8}
.crow .hit b{color:var(--ink);background:rgba(255,210,0,.4);border-radius:3px;padding:0 1px;font-weight:700}
.crow .hit-w{opacity:.85;white-space:nowrap;font-family:var(--mono);font-size:11px}
.crow .right{flex:0 0 auto;display:flex;flex-direction:column;align-items:flex-end;gap:6px}

.pill{font-family:var(--mono);font-size:10px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;padding:3px 8px;border-radius:20px;white-space:nowrap}
.pill.lead{background:#eef1f4;color:var(--slate)}
.pill.interessent{background:#fff3e0;color:var(--warn)}
.pill.angebot{background:#e7f0ff;color:#1d4ed8}
.pill.kunde{background:#e6f4ea;color:var(--pos)}
.pill.haendler{background:#f1ecfb;color:#6d28d9}
.pill.verloren{background:#f3eceb;color:#8a8a8a}

.due{font-family:var(--mono);font-size:10px;font-weight:600;padding:3px 8px;border-radius:20px;white-space:nowrap}
.due.over{background:var(--red);color:#fff}
.due.today{background:var(--warn);color:#fff}
.due.soon{background:var(--field);color:var(--muted);border:1px solid var(--line)}

.empty{text-align:center;color:var(--faint);padding:42px 16px;font-size:14px}
.empty svg{width:42px;height:42px;stroke:var(--line-strong);fill:none;stroke-width:1.4;margin-bottom:10px}
.spin{display:inline-block;width:16px;height:16px;border:2px solid var(--line-strong);border-top-color:var(--red);border-radius:50%;animation:spin .7s linear infinite;vertical-align:-3px;margin-right:8px}
@keyframes spin{to{transform:rotate(360deg)}}
.skel{height:62px;border-radius:12px;border:1px solid var(--line);margin-bottom:9px;background:linear-gradient(90deg,var(--field) 25%,#e9e7e1 37%,var(--field) 63%);background-size:400% 100%;animation:shimmer 1.4s ease infinite}
@keyframes shimmer{0%{background-position:100% 0}100%{background-position:-100% 0}}

/* Buttons */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:7px;border:1px solid var(--line-strong);background:#fff;color:var(--ink);border-radius:9px;padding:10px 14px;font-size:13px;font-weight:600;cursor:pointer;transition:.12s}
.btn:hover{border-color:var(--ink)}
.btn svg{width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:1.7}
.btn.primary{background:var(--red);border-color:var(--red);color:#fff}
.btn.primary:hover{background:#a30000;border-color:#a30000}
.btn.ghost{background:none;border-color:transparent;color:var(--muted)}
.btn.ghost:hover{color:var(--ink);border-color:transparent}
.btn.sm{padding:7px 11px;font-size:12px}
.btn.danger{color:var(--red);border-color:rgba(192,0,0,.35)}
.btn.danger:hover{border-color:var(--red);background:var(--red-soft)}
.btn.block{width:100%}
.fab{position:fixed;right:18px;bottom:calc(18px + env(safe-area-inset-bottom));z-index:60;width:54px;height:54px;border-radius:50%;background:var(--red);color:#fff;border:0;box-shadow:0 8px 22px rgba(192,0,0,.4);cursor:pointer;display:flex;align-items:center;justify-content:center}
.fab svg{width:26px;height:26px;stroke:#fff;fill:none;stroke-width:2}

/* Formular */
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.fg{display:flex;flex-direction:column;gap:5px}
.fg.full{grid-column:1/-1}
.fg label{font-size:11px;font-family:var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
textarea.field{min-height:74px;resize:vertical;line-height:1.5}
/* Notizfeld groß (mind. halbe Bildschirmhöhe) -> bequem mit Apple Pencil „Kritzeln“ (Handschrift→Text) oder Tastatur */
#actNote{min-height:46vh;font-size:16px;line-height:1.7}
/* Handschrift-Zeichenfeld + Umschalter Text/Handschrift */
#actPad{width:100%;height:48vh;background:#fff;border:1px solid var(--line-strong);border-radius:10px;touch-action:none;display:block;cursor:crosshair}
.nmbtn{display:inline-flex;align-items:center;gap:5px;border:0;background:#fff;color:var(--muted);font-family:var(--sans);font-size:13px;font-weight:600;padding:6px 11px;cursor:pointer}
.nmbtn svg{width:15px;height:15px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.nmbtn.on{background:var(--red);color:#fff}
.nmbtn+.nmbtn{border-left:1px solid var(--line-strong)}
[contenteditable].field{line-height:1.5}
[contenteditable][data-ph]:empty:before{content:attr(data-ph);color:var(--faint)}
[contenteditable] img{max-width:180px;max-height:120px;border-radius:8px;margin:4px 6px 4px 0;vertical-align:middle}
.form-actions{display:flex;gap:8px;margin-top:18px;flex-wrap:wrap}

/* Detail */
.detail-head{display:flex;gap:14px;align-items:flex-start;margin-bottom:6px}
.detail-head .av{width:52px;height:52px;border-radius:12px;background:var(--ink);color:#fff;display:flex;align-items:center;justify-content:center;font-family:var(--mono);font-weight:600;font-size:18px;flex:0 0 auto}
/* Initialen-Kästchen je Status einfärben */
.av.av-lead{background:#64748b}
.av.av-interessent{background:#d97706}
.av.av-angebot{background:#1d4ed8}
.av.av-kunde{background:#15803d}
.av.av-haendler{background:#6d28d9}
.av.av-verloren{background:#9aa0a6}
.detail-head h2{font-size:21px;font-weight:800;letter-spacing:-.01em}
.detail-head .who{color:var(--muted);font-size:13px;margin-top:2px}
.quick{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 4px}
.kv{display:grid;grid-template-columns:auto 1fr;gap:6px 14px;font-size:14px;margin:8px 0}
.kv dt{font-family:var(--mono);font-size:11px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);align-self:center}
.kv dd a{color:var(--red);text-decoration:none}
.kv dd a:hover{text-decoration:underline}

/* Aktivitäten-Timeline */
.tl{position:relative;margin-top:6px;padding-left:22px}
.tl:before{content:"";position:absolute;left:7px;top:4px;bottom:4px;width:2px;background:var(--line)}
.tl-item{position:relative;padding:0 0 16px}
.tl-item:last-child{padding-bottom:2px}
.tl-dot{position:absolute;left:-22px;top:2px;width:16px;height:16px;border-radius:50%;background:#fff;border:2px solid var(--line-strong);display:flex;align-items:center;justify-content:center}
.tl-dot svg{width:9px;height:9px;stroke:var(--muted);fill:none;stroke-width:2}
.tl-item.t-anruf .tl-dot{border-color:var(--pos)}.tl-item.t-anruf .tl-dot svg{stroke:var(--pos)}
.tl-item.t-angebot .tl-dot{border-color:#1d4ed8}.tl-item.t-angebot .tl-dot svg{stroke:#1d4ed8}
.tl-item.t-mailout .tl-dot,.tl-item.t-mailin .tl-dot{border-color:var(--gold)}.tl-item.t-mailout .tl-dot svg,.tl-item.t-mailin .tl-dot svg{stroke:var(--gold)}
.tl-item.t-besuch .tl-dot{border-color:var(--red)}.tl-item.t-besuch .tl-dot svg{stroke:var(--red)}
.tl-top{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
.tl-type{font-weight:700;font-size:14px}
.tl-when{font-family:var(--mono);font-size:11px;color:var(--muted)}
.tl-by{font-size:11px;color:var(--faint)}
.tl-note{font-size:13px;color:var(--ink);margin-top:2px;white-space:pre-wrap}
.tl-offer{margin-top:5px;display:inline-flex;align-items:center;gap:6px;font-size:12px;background:#e7f0ff;color:#1d4ed8;border-radius:8px;padding:4px 9px;text-decoration:none}
.tl-offer svg{width:13px;height:13px;stroke:currentColor;fill:none;stroke-width:1.8}
.tl-del{margin-left:auto;background:none;border:0;color:var(--faint);cursor:pointer;font-size:11px}
.tl-del:hover{color:var(--red)}

/* Wiedervorlage-Box im Detail */
.fu-box{background:var(--field);border:1px solid var(--line);border-radius:12px;padding:13px;margin:12px 0}
.fu-box.active-fu{background:#fff7ed;border-color:#fed7aa}

/* Modal */
.modal-bg{position:fixed;inset:0;background:rgba(16,17,19,.45);z-index:1500;display:none;align-items:flex-end;justify-content:center}
/* Karten in einen eigenen Stapelkontext sperren, damit Leaflet-Ebenen nicht über Topbar/Modal liegen */
#detMap,#osmMap,#cMap{position:relative;z-index:0}
.modal-bg.open{display:flex}
.modal{background:#fff;width:100%;max-width:520px;border-radius:16px 16px 0 0;padding:18px 16px calc(18px + env(safe-area-inset-bottom));max-height:90vh;overflow:auto}
.modal h3{font-size:17px;font-weight:800;margin-bottom:14px}
.seg{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}
.seg button{flex:1;min-width:84px;border:1px solid var(--line-strong);background:#fff;border-radius:9px;padding:9px 6px;font-size:12px;font-weight:600;color:var(--muted);cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:4px}
.seg button svg{width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:1.7}
.seg button.on{border-color:var(--red);color:var(--red);background:var(--red-soft)}
.chk{display:flex;align-items:center;gap:9px;font-size:13px;color:var(--ink);margin:8px 0;cursor:pointer}
.chk input{width:18px;height:18px;accent-color:var(--red)}

@media(min-width:560px){.modal-bg{align-items:center}.modal{border-radius:16px}}
@media(max-width:520px){.form-grid{grid-template-columns:1fr}}

.foot{text-align:center;color:var(--faint);font-size:11px;margin-top:26px;line-height:1.7}
.foot a{color:var(--muted)}

/* Login-Gate */
#gate{position:fixed;inset:0;background:var(--ink);z-index:200;display:flex;align-items:center;justify-content:center;padding:24px}
#gate.hidden{display:none}
#gate .gc{background:#fff;border-radius:16px;padding:28px 24px;width:100%;max-width:340px;text-align:center;box-shadow:0 24px 60px rgba(0,0,0,.4)}
#gate .gl{height:34px;margin-bottom:18px}
#gate .gh{font-size:18px;font-weight:800}
#gate .gs{color:var(--muted);font-size:13px;margin:2px 0 18px}
#gate input{width:100%;border:1px solid var(--line-strong);background:var(--field);border-radius:9px;padding:11px 12px;margin-bottom:10px;outline:none}
#gate input:focus{border-color:var(--red);background:#fff}
#gate button{width:100%;background:var(--red);color:#fff;border:0;border-radius:9px;padding:12px;font-weight:700;cursor:pointer}
#gate .ge{color:var(--red);font-size:12px;margin-top:10px;min-height:16px}
</style>
</head>
<body>

<!-- Login -->
<div id="gate">
  <div class="gc">
    <img class="gl" src="%%LOGOD%%" alt="Alzinger">
    <div class="gh">Vertrieb / CRM</div>
    <div class="gs">Anmeldung</div>
    <form id="gateForm" autocomplete="on">
      <input id="gu" name="username" placeholder="Benutzername" autocomplete="username" autocapitalize="none" autocorrect="off" spellcheck="false">
      <input id="gp" name="password" type="password" placeholder="Passwort" autocomplete="current-password">
      <button type="submit">Anmelden</button>
      <div class="ge" id="gerr"></div>
    </form>
  </div>
</div>

<header class="topbar">
  <div class="topbar-in">
    <div class="tb-row">
      <div class="tb-brand">
        <img src="%%LOGOL%%" alt="Alzinger">
        <span class="tb-sub">CRM Vertrieb</span>
        <span id="connState" class="conn off" title=""></span>
      </div>
      <div class="tb-user">
        <button id="refreshBtn" type="button" title="Daten jetzt aktualisieren"><svg viewBox="0 0 24 24"><path d="M20 11A8 8 0 105.6 16.5M20 5v6h-6"/></svg><span>Aktualisieren</span></button>
        <span class="av" id="uAv">–</span>
        <button id="logoutBtn" type="button">Abmelden</button>
      </div>
    </div>
  </div>
</header>

<nav class="nav">
  <div class="nav-in" id="nav">
    <button data-view="dashboard" class="active"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>Übersicht<span class="badge hidden" id="navBadge"></span></button>
    <button data-view="list"><svg viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 00-4-4H7a4 4 0 00-4 4v2"/><circle cx="9.5" cy="8" r="3.5"/><path d="M22 21v-2a4 4 0 00-3-3.87"/></svg>Kontakte</button>
    <button data-view="leads"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2"/></svg>Leads</button>
    <button data-view="data"><svg viewBox="0 0 24 24"><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/></svg>Daten</button>
  </div>
</nav>

<div class="wrap">

  <!-- ÜBERSICHT -->
  <section class="view active" id="view-dashboard">
    <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:10px;flex-wrap:wrap">
      <div><h2 class="vh" id="greet">Übersicht</h2>
      <div class="sub" id="greetSub">Dein Vertriebs-Cockpit</div></div>
      <div style="text-align:right"><button class="btn sm" id="mailSyncBtn" type="button" title="Deine Outlook-E-Mails (rein/raus) den Kontakten zuordnen"><svg viewBox="0 0 24 24" style="width:15px;height:15px;stroke:currentColor;fill:none;stroke-width:1.7"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>E-Mails abrufen</button>
      <div id="mailSyncMsg" style="font-size:12px;color:var(--muted);margin-top:4px"></div></div>
    </div>

    <div class="stats" id="stats"></div>

    <div class="card" id="inboxCard" style="display:none">
      <h3>
        <svg viewBox="0 0 24 24" style="width:15px;height:15px;stroke:var(--gold);fill:none;stroke-width:1.8"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>
        Posteingang<span class="cnt" id="inboxCnt">0</span>
      </h3>
      <div id="inboxList"></div>
    </div>

    <div class="card">
      <h3>
        <svg viewBox="0 0 24 24" style="width:15px;height:15px;stroke:var(--red);fill:none;stroke-width:1.8"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>
        Wiedervorlagen / Rückrufe<span class="cnt" id="fuCnt">0</span>
      </h3>
      <div id="fuList"></div>
    </div>

    <div class="card">
      <h3>
        <svg viewBox="0 0 24 24" style="width:15px;height:15px;stroke:var(--muted);fill:none;stroke-width:1.8"><path d="M4 6h16M4 12h16M4 18h10"/></svg>
        Letzte Aktivitäten
      </h3>
      <div id="recent"></div>
    </div>

    <div class="card" id="notifCard">
      <h3><svg viewBox="0 0 24 24" style="width:15px;height:15px;stroke:var(--muted);fill:none;stroke-width:1.8"><path d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 01-3.4 0"/></svg> Erinnerungen</h3>
      <p style="font-size:13px;color:var(--muted);margin-bottom:10px">Lass dich automatisch an fällige Rückrufe &amp; Nachfass-Termine erinnern (Browser-Benachrichtigung).</p>
      <button class="btn sm" id="notifBtn" type="button">Erinnerungen aktivieren</button>
    </div>
  </section>

  <!-- KONTAKTE -->
  <section class="view" id="view-list">
    <h2 class="vh">Kontakte</h2>
    <div class="sub" id="listSub">Adressen, Ansprechpartner &amp; Verlauf</div>
    <div class="toolbar">
      <input class="search" id="q" placeholder="Volltextsuche: Firma, Person, Ort, Telefon, E-Mail, Notizen, Verlauf…">
    </div>
    <div class="toolbar">
      <select class="filter" id="fStatus"><option value="">Alle Status</option></select>
      <select class="filter" id="fLand"><option value="">Alle Länder</option></select>
      <select class="filter" id="fBL"><option value="">Alle Bundesländer</option></select>
      <select class="filter" id="fOwner"><option value="">Alle Vertriebler</option></select>
      <select class="filter" id="fSort"><option value="updated">Zuletzt aktiv</option><option value="name">Name A–Z</option><option value="created">Neueste</option><option value="due">Wiedervorlage</option></select>
      <button class="btn sm" id="mapToggle" type="button"><svg viewBox="0 0 24 24" style="width:15px;height:15px;stroke:currentColor;fill:none;stroke-width:1.7"><path d="M9 4L3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/></svg>Karte</button>
    </div>
    <div id="cMap" style="height:70vh;min-height:380px;border:1px solid var(--line);border-radius:12px;margin-bottom:12px;display:none"></div>
    <div class="clist" id="clist"></div>
  </section>

  <!-- LEADS -->
  <section class="view" id="view-leads">
    <h2 class="vh">Leads</h2>
    <div class="sub">Potenzielle Kunden in DE, CH, AT &amp; Co. finden, erfassen und nachverfolgen.</div>
    <div class="card">
      <h3><svg viewBox="0 0 24 24" style="width:15px;height:15px;stroke:var(--red);fill:none;stroke-width:1.8"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a15 15 0 010 18M12 3a15 15 0 000 18"/></svg> Neue Leads im Internet finden</h3>
      <div style="display:flex;flex-wrap:wrap;gap:8px">
        <input class="field" id="osmWas" placeholder="Was? z. B. Kompostierung, Recycling, Erdenwerk" style="flex:2;min-width:200px">
        <input class="field" id="osmWo" placeholder="Wo? z. B. Deutschland, Bayern, München" style="flex:1;min-width:140px">
        <button class="btn primary" id="osmSearch" type="button"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>Suchen</button>
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:12px;margin-top:8px;align-items:center">
        <label style="display:inline-flex;align-items:center;gap:7px;cursor:pointer;font-size:13px"><input type="checkbox" id="osmNearTgl" style="width:18px;height:18px;accent-color:#c00000"><svg viewBox="0 0 24 24" style="width:15px;height:15px;stroke:currentColor;fill:none;stroke-width:1.8"><path d="M12 21s-7-5.2-7-11a7 7 0 0114 0c0 5.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>Umkreis um meinen Standort</label>
        <select class="field" id="osmRadius" style="width:auto;flex:0 0 auto" disabled><option value="25">25 km</option><option value="50">50 km</option><option value="100" selected>100 km</option><option value="200">200 km</option></select>
        <span id="osmNearHint" style="font-size:12px;color:var(--muted)">aus = im ganzen Land/Region suchen</span>
      </div>
      <div id="osmStatus" style="font-size:13px;color:var(--muted);margin-top:10px"></div>
      <div id="osmMap" style="height:340px;border:1px solid var(--line);border-radius:12px;margin-top:10px;display:none"></div>
      <div class="clist" id="osmResults" style="margin-top:10px"></div>
      <p style="font-size:11px;color:var(--faint);margin-top:10px;line-height:1.6">
        Sucht <b>bundesland- und landesweit</b> (z. B. „Bayern" oder „Deutschland"). Ist die <b>KI-Suche</b> eingerichtet (Reiter „Daten"), durchsucht Claude das Web nach echten Firmen; sonst läuft automatisch die kostenlose Karten-Suche (© OpenStreetMap-Mitwirkende). <b>Keine amtliche Vollständigkeit</b> – Treffer kurz prüfen, dann als Lead übernehmen. Nur online.
      </p>
    </div>
    <div class="toolbar">
      <input class="search" id="qLead" placeholder="Eigene Leads durchsuchen…">
      <select class="filter" id="fLeadLand"><option value="">Alle Länder</option></select>
    </div>
    <div class="clist" id="leadlist"></div>
  </section>

  <!-- DATEN -->
  <section class="view" id="view-data">
    <h2 class="vh">Daten</h2>
    <div class="sub">Auswertung, Server-Verbindung, Sichern, Übertragen und Importieren.</div>
    <div class="card" id="evalCard">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-bottom:10px">
        <h3 style="margin:0">Vertriebler-Auswertung</h3>
        <select class="field" id="evalRange" style="width:auto;padding:6px 10px;font-size:13px">
          <option value="7">Letzte 7 Tage</option>
          <option value="30">Letzte 30 Tage</option>
          <option value="month">Dieser Monat</option>
          <option value="year">Dieses Jahr</option>
          <option value="all" selected>Gesamt</option>
        </select>
      </div>
      <div id="evalBody" style="overflow-x:auto"></div>
    </div>
    <div class="card" id="connData">
      <h3>Geteilte Daten / Server</h3>
      <div id="connDataBody"></div>
      <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
        <button class="btn sm" id="reconnBtn" type="button">Verbindung prüfen</button>
        <button class="btn sm primary" id="setupLinkBtn" type="button" title="Internen Link erzeugen, mit dem sich Kollegen mit einem Klick verbinden (kein Eintippen von Schlüsseln)">🔗 Einrichtungs-Link für Vertriebler</button>
        <details style="flex:1;min-width:200px">
          <summary style="cursor:pointer;font-size:12px;color:var(--muted)">Zugriffsschutz (optional, Token)</summary>
          <div style="display:flex;gap:8px;margin-top:8px;align-items:center">
            <input class="field" id="tokenInp" placeholder="geheimer Token (wie in api.php)" style="flex:1">
            <button class="btn sm" id="tokenSave" type="button">Speichern</button>
          </div>
          <p style="font-size:11px;color:var(--muted);margin-top:6px">Nur nötig, wenn in <span class="mono">api.php</span> ein <span class="mono">$TOKEN</span> gesetzt wurde. Muss exakt übereinstimmen.</p>
        </details>
      </div>
    </div>
    <div class="card">
      <h3>Cloud-Datenbank (online &amp; geteilt – empfohlen)</h3>
      <p style="font-size:13px;color:var(--muted);margin-bottom:12px">Kostenlos über <b>Supabase</b>. Trage die Zugangsdaten aus deinem Projekt ein (Supabase → Project Settings → API). Sie bleiben <b>nur auf diesem Gerät</b>. Danach sehen alle Vertriebler denselben Stand – ohne eigenen Server.</p>
      <div class="fg"><label>Project-URL</label><input class="field" id="sbUrl" placeholder="https://xxxxxxxx.supabase.co"></div>
      <div class="fg" style="margin-top:8px"><label>anon public Key</label><input class="field" id="sbKey" placeholder="eyJhbGciOi…"></div>
      <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap">
        <button class="btn primary" id="sbConnect" type="button">Verbinden</button>
        <button class="btn" id="sbDisconnect" type="button">Trennen</button>
        <a class="btn ghost sm" href="#" id="sbHelp">Anleitung (1× einrichten)</a>
      </div>
      <div id="sbHelpBox" class="hidden" style="margin-top:12px;font-size:12px;color:var(--muted);line-height:1.7;border-top:1px solid var(--line);padding-top:10px">
        <b>So richtest du es einmalig ein (ca. 5 Min):</b><br>
        1. Auf <span class="mono">supabase.com</span> kostenlos registrieren → <b>New Project</b> (Region <b>Frankfurt/EU</b> wählen – Datenschutz).<br>
        2. Im Projekt links <b>SQL Editor</b> öffnen, folgendes einfügen und ausführen:
        <pre style="white-space:pre-wrap;background:var(--field);border:1px solid var(--line);border-radius:8px;padding:8px;margin:6px 0;font-family:var(--mono);font-size:11px">create table if not exists contacts (
  id text primary key,
  data jsonb,
  updated_at timestamptz default now()
);
alter table contacts enable row level security;
create policy "crm all" on contacts
  for all using (true) with check (true);</pre>
        3. Links <b>Project Settings → API</b>: <b>Project URL</b> und den <b>anon public</b> Key kopieren und oben eintragen → <b>Verbinden</b>.<br>
        4. Auf jedem weiteren Gerät dieselbe URL + denselben Key eintragen → fertig, alle teilen sich die Daten.<br>
        <span style="color:var(--warn)">Hinweis Sicherheit: Mit diesem Schlüssel kann jeder, der ihn kennt, die Daten lesen/ändern – also nur im Team teilen. Stärkere Absicherung (Login) bauen wir bei Bedarf nach.</span>
      </div>
    </div>
    <div class="card">
      <h3>KI-Lead-Suche (optional)</h3>
      <p style="font-size:13px;color:var(--muted);margin-bottom:10px">Lässt die Lead-Suche (Reiter „Leads") per <b>Claude + Web-Suche</b> echte Firmen finden. Voraussetzung: die Edge Function <span class="mono">lead-ai</span> ist in deinem Supabase-Projekt deployt (Anleitung weiter unten) und ein <span class="mono">CRM_SECRET</span> gesetzt. Hier denselben Wert eintragen.</p>
      <div class="fg"><label>KI-Schlüssel (CRM_SECRET)</label><input class="field" id="aiSecret" placeholder="dasselbe wie in der Edge Function"></div>
      <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;align-items:center">
        <button class="btn primary" id="aiSave" type="button">Speichern</button>
        <span id="aiState" style="font-size:12px;color:var(--muted)"></span>
      </div>
      <p style="font-size:11px;color:var(--faint);margin-top:10px;line-height:1.6">Kosten: pro Suche fallen bei Anthropic einige Cent an (KI + Web-Suche). KI-Treffer sind <b>Vorschläge zum Prüfen</b> – vor dem Kontaktieren verifizieren (DSGVO/UWG beachten). Ohne diesen Schlüssel nutzt die Suche automatisch die kostenlose Karten-Suche (OpenStreetMap).</p>
    </div>
    <div class="card">
      <h3>Sichern &amp; Übertragen</h3>
      <p style="font-size:13px;color:var(--muted);margin-bottom:12px">Exportiere alle Kontakte &amp; Aktivitäten als Datei – zur Sicherung oder um sie auf ein anderes Gerät / zu Kollegen zu übertragen.</p>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <button class="btn primary" id="expBtn" type="button"><svg viewBox="0 0 24 24"><path d="M12 3v12m0 0l-4-4m4 4l4-4M5 21h14"/></svg>Export (JSON)</button>
        <button class="btn" id="impBtn" type="button"><svg viewBox="0 0 24 24"><path d="M12 21V9m0 0l-4 4m4-4l4 4M5 3h14"/></svg>Import (JSON)</button>
        <input type="file" id="impFile" accept="application/json,.json" class="hidden">
      </div>
    </div>
    <div class="card">
      <h3>Leads importieren (CSV)</h3>
      <p style="font-size:13px;color:var(--muted);margin-bottom:12px">CSV mit Kopfzeile. Erkannte Spalten (DE/EN, beliebige Reihenfolge):
        <span class="mono" style="font-size:11px">firma, anrede, vorname, nachname, strasse, plz, ort, land, tel, mobil, mail, web, ustid, quelle, notiz, status</span>.
        Trennzeichen Komma oder Semikolon.</p>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <button class="btn" id="csvBtn" type="button"><svg viewBox="0 0 24 24"><path d="M12 21V9m0 0l-4 4m4-4l4 4M5 3h14"/></svg>CSV wählen</button>
        <input type="file" id="csvFile" accept=".csv,text/csv" class="hidden">
        <a class="btn ghost sm" id="csvTpl" href="#" download="leads-vorlage.csv">Vorlage herunterladen</a>
      </div>
    </div>
    <div class="card">
      <h3>Aus OneNote / Notiz importieren (KI)</h3>
      <p style="font-size:13px;color:var(--muted);margin-bottom:10px">OneNote-Seite öffnen → alles markieren (Strg+A) → kopieren (Strg+C) → unten einfügen (Strg+V). <b>Bilder werden mit eingefügt</b> und am Kontakt gespeichert. Die KI erkennt Firma, Ansprechpartner, Adresse und legt den Kontakt <b>mit komplettem Verlauf</b> an. Eine Seite/Firma pro Durchgang.</p>
      <div class="field" id="noteIn" contenteditable="true" data-ph="OneNote-Seite hier einfügen (Strg+V) – Text und Bilder …" style="width:100%;min-height:140px;max-height:340px;overflow:auto;white-space:pre-wrap"></div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:8px">
        <button class="btn primary" id="noteBtn" type="button"><svg viewBox="0 0 24 24"><path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z"/><path d="M14 3v5h5"/></svg>Per KI auswerten & anlegen</button>
        <button class="btn" id="noteImgBtn" type="button"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>Bild(er) hinzufügen</button>
        <input type="file" id="noteImgs" accept="image/*" multiple class="hidden">
        <button class="btn ghost sm" id="noteClear" type="button">Leeren</button>
        <span id="noteMsg" style="font-size:13px;color:var(--muted)"></span>
      </div>
    </div>
    <div class="card">
      <h3>OneNote automatisch importieren (Microsoft 365)</h3>
      <p style="font-size:13px;color:var(--muted);margin-bottom:10px">Meldet dich bei Microsoft an und zeigt <b>alle deine Notizbücher</b> (auch geteilte). Du wählst, welche importiert werden und <b>welcher Vertriebler welches Land betreut</b>. Pro Seite legt die KI einen Kontakt <b>mit Verlauf und Bildern</b> an (Notizbuch = Land, Abschnitt = Region/Bundesland). Bereits vorhandene werden übersprungen. Läuft nur online – das Fenster offen lassen, bis es fertig ist.</p>
      <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
        <button class="btn primary" id="msBtn" type="button"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="8" height="8"/><rect x="13" y="3" width="8" height="8"/><rect x="3" y="13" width="8" height="8"/><rect x="13" y="13" width="8" height="8"/></svg>Mit Microsoft anmelden</button>
        <button class="btn danger sm hidden" id="msStop" type="button">Stopp</button>
      </div>
      <div id="msBooks" style="display:none;margin-top:12px">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;margin-bottom:6px">
          <b style="font-size:13px">Welche Notizbücher importieren?</b>
          <span><button class="btn ghost sm" id="msAll" type="button">Alle</button> <button class="btn ghost sm" id="msNone" type="button">Keine</button></span>
        </div>
        <div id="msBookList" style="max-height:240px;overflow:auto;border:1px solid var(--line);border-radius:8px;padding:8px;display:flex;flex-direction:column;gap:4px"></div>
        <button class="btn primary" id="msGo" type="button" style="margin-top:10px">Import starten</button>
      </div>
      <div id="msProg" style="display:none;margin-top:10px">
        <div style="height:10px;background:var(--field);border-radius:6px;overflow:hidden;border:1px solid var(--line)"><div id="msBar" style="height:100%;width:0;background:#c00000;transition:width .3s"></div></div>
        <div id="msMsg" style="font-size:13px;color:var(--muted);margin-top:6px"></div>
      </div>
    </div>
    <div class="card">
      <h3>Verknüpfung</h3>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <a class="btn" href="../index.html"><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="14" rx="2"/><path d="M7 20h10"/></svg>Lepton Konfigurator</a>
        <a class="btn" href="../ersatzteile/"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 00-.1-1l2-1.6-2-3.4-2.4 1a7 7 0 00-1.7-1l-.3-2.5H10l-.3 2.5a7 7 0 00-1.7 1l-2.4-1-2 3.4 2 1.6a7 7 0 000 2l-2 1.6 2 3.4 2.4-1a7 7 0 001.7 1l.3 2.5h3.8l.3-2.5a7 7 0 001.7-1l2.4 1 2-3.4-2-1.6c.07-.33.1-.66.1-1z"/></svg>Ersatzteilkatalog</a>
      </div>
    </div>
    <div class="card">
      <h3>Aufräumen</h3>
      <p style="font-size:13px;color:var(--muted);margin-bottom:10px">Entfernt <b>leere Import-Kontakte</b> (aus OneNote, ohne Adresse, Kontaktdaten, Person, Verlauf oder Bilder – meist durch Drosselung beim Import entstanden). Echte Kontakte bleiben unberührt.</p>
      <button class="btn" id="cleanEmptyBtn" type="button">Leere Import-Kontakte entfernen</button>
      <span id="cleanEmptyMsg" style="font-size:13px;color:var(--muted);margin-left:8px"></span>
      <p style="font-size:13px;color:var(--muted);margin:14px 0 8px">Lagert <b>eingebettete Bilder in den Cloud-Speicher</b> aus (Kontakt speichert dann nur noch eine kurze URL). Verkleinert die Daten massiv und verhindert Speicher-Überlauf. Voraussetzung: Storage-Bucket <span class="mono">crm-bilder</span> ist angelegt (Anleitung bekommst du von Martin).</p>
      <button class="btn" id="migImgBtn" type="button">Bilder in den Cloud-Speicher auslagern</button>
      <span id="migImgMsg" style="font-size:13px;color:var(--muted);margin-left:8px"></span>
    </div>
    <div class="card">
      <h3 style="color:var(--red)">Gefahrenzone</h3>
      <button class="btn danger" id="wipeBtn" type="button">Alle CRM-Daten auf diesem Gerät löschen</button>
    </div>
  </section>

  <!-- KONTAKT-DETAIL -->
  <section class="view" id="view-detail"></section>

  <!-- KONTAKT-FORMULAR -->
  <section class="view" id="view-form"></section>

  <div class="foot">
    Alzinger Maschinenbau · Vertrieb / CRM — PWA, online wie offline. <span id="appVer" style="opacity:.6"></span><br>
    <a href="../index.html">Konfigurator</a> · <a href="../ersatzteile/">Ersatzteile</a>
  </div>
</div>

<button class="fab" id="fab" type="button" aria-label="Neuer Kontakt">
  <svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>
</button>

<!-- Aktivität-Modal -->
<div class="modal-bg" id="actModal">
  <div class="modal">
    <h3>Aktivität erfassen</h3>
    <div class="seg" id="actSeg">
      <button data-t="anruf" class="on"><svg viewBox="0 0 24 24"><path d="M5 4h4l2 5-3 2a13 13 0 006 6l2-3 5 2v4a2 2 0 01-2 2A17 17 0 013 6a2 2 0 012-2"/></svg>Anruf</button>
      <button data-t="mailout"><svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>Mail raus</button>
      <button data-t="mailin"><svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>Mail rein</button>
      <button data-t="angebot"><svg viewBox="0 0 24 24"><path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z"/><path d="M14 3v5h5"/></svg>Angebot</button>
      <button data-t="besuch"><svg viewBox="0 0 24 24"><path d="M12 21s-7-5.2-7-11a7 7 0 0114 0c0 5.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>Besuch</button>
      <button data-t="notiz"><svg viewBox="0 0 24 24"><path d="M4 5h16M4 12h16M4 19h10"/></svg>Notiz</button>
    </div>
    <div class="fg" style="margin-bottom:10px">
      <label>Datum &amp; Uhrzeit</label>
      <input class="field" type="datetime-local" id="actDate">
    </div>
    <div id="actOfferWrap" style="margin-bottom:10px">
      <button class="btn primary block" id="actCreateOffer" type="button" style="margin-bottom:10px"><svg viewBox="0 0 24 24" style="width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:1.7"><path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z"/><path d="M14 3v5h5"/></svg>Im Konfigurator erstellen →</button>
      <div class="fg" style="margin-bottom:10px">
        <label>…oder vorhandenes Angebot verknüpfen</label>
        <select class="field" id="actOffer"><option value="">— keines —</option></select>
      </div>
      <div style="display:flex;gap:10px">
        <div class="fg" style="flex:1"><label>Angebot-Nr.</label><input class="field" id="actOfferNr" placeholder="z. B. 2026-118"></div>
        <div class="fg" style="flex:1"><label>Betrag (€)</label><input class="field" id="actBetrag" inputmode="decimal" placeholder="z. B. 340300"></div>
      </div>
    </div>
    <div id="actMailWrap" style="display:none;margin-bottom:10px;border:1px solid var(--line-strong);border-radius:11px;padding:11px;background:#fafafa">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px">
        <label class="chk" style="margin:0"><input type="checkbox" id="actMailSend"> <b>E-Mail jetzt über Microsoft 365 senden</b></label>
        <button type="button" class="btn ghost sm" id="actMailAI" title="KI entwirft eine Antwort"><svg viewBox="0 0 24 24" style="width:15px;height:15px;stroke:currentColor;fill:none;stroke-width:1.7"><path d="M12 3l2 5 5 2-5 2-2 5-2-5-5-2 5-2z"/></svg>KI-Vorschlag</button>
      </div>
      <div id="actMailFields" style="display:none">
        <div class="fg" style="margin-bottom:8px"><label>An</label><input class="field" id="actMailTo" type="email" placeholder="empfaenger@firma.de"></div>
        <div class="fg" style="margin-bottom:8px"><label>Betreff</label><input class="field" id="actMailSubj" placeholder="Betreff"></div>
        <div id="actMailAtt" style="display:none;font-size:12px;margin:2px 0 4px;color:#0a7d3a"><svg viewBox="0 0 24 24" style="width:13px;height:13px;stroke:currentColor;fill:none;stroke-width:1.8;vertical-align:-2px"><path d="M21 11.5l-8.5 8.5a5 5 0 01-7-7l8.5-8.5a3.5 3.5 0 015 5l-8.5 8.5a2 2 0 01-3-3l8-8"/></svg> <span id="actMailAttName"></span></div>
        <div id="actMailHint" style="font-size:12px;color:var(--muted);margin-top:2px">Der Text unten wird als E-Mail gesendet <b>und</b> im Verlauf gespeichert.</div>
      </div>
    </div>
    <div class="fg" style="margin-bottom:6px">
      <div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:4px">
        <label style="margin:0">Notiz</label>
        <div id="noteModeSeg" style="display:inline-flex;border:1px solid var(--line-strong);border-radius:9px;overflow:hidden">
          <button type="button" id="noteModeText" class="nmbtn on" title="Tastatur / Kritzeln (Handschrift→Text)"><svg viewBox="0 0 24 24"><rect x="3" y="6" width="18" height="12" rx="2"/><path d="M7 10h.01M11 10h.01M15 10h.01M7 14h10"/></svg>Text</button>
          <button type="button" id="noteModeDraw" class="nmbtn" title="Echte Handschrift mit dem Stift"><svg viewBox="0 0 24 24"><path d="M16.5 3.5a2.1 2.1 0 013 3L8 18l-4 1 1-4z"/><path d="M14 5l3 3"/></svg>Handschrift</button>
        </div>
      </div>
      <textarea class="field" id="actNote" placeholder="Worum ging es? Ergebnis, Vereinbarung…  (tippen oder mit Apple Pencil ins Feld kritzeln)"></textarea>
      <div id="actPadWrap" style="display:none">
        <canvas id="actPad"></canvas>
        <div style="display:flex;gap:8px;margin-top:6px;align-items:center">
          <button type="button" class="btn ghost sm" id="actPadClear">Löschen</button>
          <span style="font-size:12px;color:var(--muted)">Mit Apple Pencil oder Finger schreiben</span>
        </div>
      </div>
    </div>
    <label class="chk"><input type="checkbox" id="actFu" checked> Wiedervorlage anlegen in
      <input type="number" id="actFuDays" value="7" min="1" max="180" style="width:58px;border:1px solid var(--line-strong);border-radius:7px;padding:4px 6px;text-align:center"> Tagen</label>
    <div class="form-actions">
      <button class="btn primary block" id="actSave" type="button">Speichern</button>
      <button class="btn ghost block" id="actCancel" type="button">Abbrechen</button>
    </div>
  </div>
</div>

<!-- Anruf-Nachfrage (erscheint nach Rückkehr aus der Telefon-App) -->
<div class="modal-bg" id="callModal">
  <div class="modal">
    <h3 id="callTitle">Anruf erfassen?</h3>
    <div class="fg" style="margin-bottom:10px">
      <label>Wie war das Gespräch? (kurze Notiz)</label>
      <textarea class="field" id="callNote" rows="3" placeholder="z. B. Interesse an Vorführung, meldet sich nächste Woche …"></textarea>
    </div>
    <div class="form-actions">
      <button class="btn primary block" id="callSave" type="button">Anruf speichern</button>
      <button class="btn block" id="callNoAnswer" type="button">Nicht erreicht</button>
      <button class="btn ghost block" id="callDiscard" type="button">Verwerfen (kein Anruf)</button>
    </div>
  </div>
</div>

<script>
var USERS=%%USERS%%;
</script>
<script>
(function(){
 "use strict";
 /* ---------- SHA-256 (für Login, identisch zum Konfigurator) ---------- */
 function sha256(ascii){function r(v,a){return (v>>>a)|(v<<(32-a));}var mp=Math.pow,mw=mp(2,32),res="",words=[],bl=ascii.length*8;var hash=sha256.h=sha256.h||[],k=sha256.k=sha256.k||[],pc=k.length,ic={},i,j;for(var c=2;pc<64;c++){if(!ic[c]){for(i=0;i<313;i+=c)ic[i]=c;hash[pc]=(mp(c,.5)*mw)|0;k[pc++]=(mp(c,1/3)*mw)|0;}}ascii+="\x80";while(ascii.length%64-56)ascii+="\x00";for(i=0;i<ascii.length;i++){j=ascii.charCodeAt(i);if(j>>8)return;words[i>>2]|=j<<((3-i)%4)*8;}words[words.length]=((bl/mw)|0);words[words.length]=bl;for(j=0;j<words.length;){var w=words.slice(j,j+=16),oh=hash;hash=hash.slice(0,8);for(i=0;i<64;i++){var w15=w[i-15],w2=w[i-2],a=hash[0],e=hash[4],t1=hash[7]+(r(e,6)^r(e,11)^r(e,25))+((e&hash[5])^((~e)&hash[6]))+k[i]+(w[i]=i<16?w[i]:(w[i-16]+(r(w15,7)^r(w15,18)^(w15>>>3))+w[i-7]+(r(w2,17)^r(w2,19)^(w2>>>10)))|0),t2=(r(a,2)^r(a,13)^r(a,22))+((a&hash[1])^(a&hash[2])^(hash[1]&hash[2]));hash=[(t1+t2)|0].concat(hash);hash[4]=(hash[4]+t1)|0;}for(i=0;i<8;i++)hash[i]=(hash[i]+oh[i])|0;}for(i=0;i<8;i++){for(j=3;j+1;j--){var b=(hash[i]>>(j*8))&255;res+=((b<16)?0:"")+b.toString(16);}}return res;}
 var AKEY="amb_lepton_auth",UKEY="amb_lepton_user";
 function findUser(hash){for(var i=0;i<USERS.length;i++)if(USERS[i].h===hash)return USERS[i];return null;}
 var CUR=null; // eingeloggter Vertriebler {n,tel,mail}
 var ADMINS=["Martin Alzinger"]; // nur Admins sehen den Daten-Reiter (Zugangsdaten/Verbinden/Trennen/Loeschen)
 function isAdmin(){return !!(CUR&&CUR.n&&ADMINS.indexOf(CUR.n)>=0);}
 function applyRole(){var db=document.querySelector('#nav button[data-view="data"]');if(db)db.style.display=isAdmin()?"":"none";if(!isAdmin()&&curView==="data")show("dashboard");}
 var gate=document.getElementById("gate");
 function setUser(u){CUR=u||{n:""};try{localStorage.setItem(UKEY,JSON.stringify({n:u.n||"",tel:u.tel||"",mail:u.mail||""}));}catch(_){}
   var un=document.getElementById("uName");if(un)un.textContent=u.n||"Vertrieb";
   var av=document.getElementById("uAv");if(av){av.textContent=initials(u.n||"?");av.title=u.n||"";}}
 function pass(u){setUser(u);applyRole();gate.classList.add("hidden");boot();}
 // Auto-Login wird am ENDE der IIFE ausgelöst (erst dann sind alle Daten/Funktionen definiert).
 document.getElementById("gateForm").addEventListener("submit",function(ev){ev.preventDefault();
  var u=(document.getElementById("gu").value||"").trim().toLowerCase(),p=(document.getElementById("gp").value||"");
  var hit=findUser(sha256(u+":"+p));
  if(hit){try{localStorage.setItem(AKEY,hit.h);}catch(_){}document.getElementById("gerr").textContent="";pass(hit);}
  else{document.getElementById("gerr").textContent="Benutzername oder Passwort falsch.";var gp=document.getElementById("gp");gp.value="";gp.focus();}
 });
 document.getElementById("logoutBtn").addEventListener("click",function(){try{localStorage.removeItem(AKEY);}catch(_){}location.reload();});
 document.getElementById("refreshBtn").addEventListener("click",function(){
   var b=this;if(b.classList.contains("spin"))return;b.classList.add("spin");
   var p=(MODE==="local")?initBackend():syncFromServer();
   Promise.resolve(p).catch(function(){}).then(function(){setTimeout(function(){b.classList.remove("spin");},500);});
 });
 var _mailBusy=false;
 document.getElementById("mailSyncBtn").addEventListener("click",function(){
   if(_mailBusy)return;_mailBusy=true;var b=this;b.disabled=true;
   var msg=document.getElementById("mailSyncMsg");msg.style.color="var(--muted)";msg.textContent="Verbinde mit Microsoft …";
   importEmails(true).then(function(res){
     msg.style.color="var(--pos)";msg.textContent=res.added?("✓ "+res.added+" E-Mail(s) zu "+res.contacts+" Kontakt(en) zugeordnet."):"Keine neuen E-Mails für vorhandene Kontakte gefunden.";
     if(res.added)renderDashboard();
   }).catch(function(e){msg.style.color="#b91c1c";msg.textContent=String((e&&e.message)||e);})
     .then(function(){b.disabled=false;_mailBusy=false;});
 });

 /* ---------- Konstanten ---------- */
 var KEY="amb_lepton_crm";
 var CFG_KEY="amb_lepton_configs"; // gespeicherte Angebote des Konfigurators (gleicher Origin)
 var STATUS=[["lead","Lead"],["interessent","Interessent"],["angebot","Angebot offen"],["kunde","Kunde"],["haendler","Händler"],["verloren","Verloren"]];
 var LANDS=[["DE","Deutschland"],["AT","Österreich"],["CH","Schweiz"],["IT","Italien"],["FR","Frankreich"],["PL","Polen"],["NL","Niederlande"],["BE","Belgien"],["LU","Luxemburg"],["CZ","Tschechien"],["DK","Dänemark"],["SE","Schweden"],["NO","Norwegen"],["FI","Finnland"],["ES","Spanien"],["PT","Portugal"],["GB","Großbritannien"],["IE","Irland"],["SK","Slowakei"],["SI","Slowenien"],["HU","Ungarn"],["HR","Kroatien"],["RO","Rumänien"],["GR","Griechenland"],["US","USA"],["CA","Kanada"],["XX","Sonstige"]];
 var ACT=[["anruf","Anruf"],["mailout","E-Mail (raus)"],["mailin","E-Mail (rein)"],["angebot","Angebot gesendet"],["besuch","Besuch"],["notiz","Notiz"]];
 function statusLabel(s){for(var i=0;i<STATUS.length;i++)if(STATUS[i][0]===s)return STATUS[i][1];return "Lead";}
 function landLabel(c){for(var i=0;i<LANDS.length;i++)if(LANDS[i][0]===c)return LANDS[i][1];return c||"";}
 function actLabel(t){for(var i=0;i<ACT.length;i++)if(ACT[i][0]===t)return ACT[i][1];return t;}

 /* ---------- Store + Sync ----------
    Zwei Betriebsarten, automatisch erkannt:
     - MODE="server": api.php erreichbar -> zentrale, GETEILTE Datei am Server.
       Jede Änderung geht pro Kontakt (upsert/delete) als Op in eine Warteschlange
       und wird per Batch an den Server geschickt (dort unter Datei-Sperre gemerged).
       localStorage dient als Offline-Spiegel; offline gemachte Änderungen werden
       bei nächster Verbindung nachgereicht.
     - MODE="local": kein Server -> nur localStorage (pro Gerät), wie bisher. */
 var MODE="local";                 // "local" | "server" (PHP) | "cloud" (Supabase)
 var API="api.php";
 var QKEY="amb_lepton_crm_queue";
 var TKEY="amb_crm_token";
 var SBKEY="amb_crm_sb";
 var AIKEY="amb_crm_ai";
 var TOKEN=""; try{TOKEN=localStorage.getItem(TKEY)||"";}catch(e){}
 var SB=null; try{SB=JSON.parse(localStorage.getItem(SBKEY)||"null");}catch(e){}
 var AISECRET=""; try{AISECRET=localStorage.getItem(AIKEY)||"";}catch(e){}
 // Einrichtungs-Link (#s=...) fuer Team-Rollout: Cloud-Zugang automatisch uebernehmen, dann aus der URL entfernen.
 (function(){try{var m=(location.hash||"").match(/[#&]s=([^&]+)/);if(!m)return;var o=JSON.parse(decodeURIComponent(escape(atob(m[1].replace(/-/g,"+").replace(/_/g,"/")))));if(o&&o.u&&o.k){SB={url:o.u,key:o.k};try{localStorage.setItem(SBKEY,JSON.stringify(SB));}catch(e){}}if(o&&o.c){AISECRET=o.c;try{localStorage.setItem(AIKEY,AISECRET);}catch(e){}}history.replaceState(null,"",location.pathname+location.search);}catch(e){}})();
 function cacheRead(){try{var o=JSON.parse(localStorage.getItem(KEY)||"{}");if(!o.contacts)o.contacts=[];return o;}catch(e){return {contacts:[]};}}
 function cacheSave(){
   try{localStorage.setItem(KEY,JSON.stringify(DB));return;}catch(e){}
   // Speicher voll (meist durch eingebettete Bilder) -> lokal OHNE Bilder sichern, damit Textdaten NIE verloren gehen.
   try{var slim={rev:DB.rev,contacts:(DB.contacts||[]).map(function(c){if(c&&c.bilder&&c.bilder.length){var x={};for(var k in c){if(k!=="bilder")x[k]=c[k];}x._imgN=c.bilder.length;return x;}return c;})};localStorage.setItem(KEY,JSON.stringify(slim));}catch(e2){}
 }
 var DB=cacheRead();
 function uid(){return Date.now().toString(36)+Math.random().toString(36).slice(2,7);}
 function byId(id){for(var i=0;i<DB.contacts.length;i++)if(DB.contacts[i].id===id)return DB.contacts[i];return null;}

 /* --- PHP-API (eigener Server) --- */
 function apiGet(){return fetch(API+"?action=all",{cache:"no-store",headers:TOKEN?{"X-CRM-Token":TOKEN}:{}}).then(function(r){if(!r.ok)throw new Error("http "+r.status);return r.json();});}
 function apiPost(action,body){var h={"Content-Type":"application/json"};if(TOKEN)h["X-CRM-Token"]=TOKEN;return fetch(API+"?action="+action,{method:"POST",headers:h,body:JSON.stringify(body)}).then(function(r){if(!r.ok)throw new Error("http "+r.status);return r.json();});}

 /* --- Supabase (kostenlose Cloud-DB) REST: Tabelle "contacts" (id text, data jsonb) --- */
 function sbReady(){return !!(SB&&SB.url&&SB.key);}
 function sbBase(){return SB.url.replace(/\/+$/,"")+"/rest/v1/contacts";}
 function sbHeaders(extra){var h={"apikey":SB.key,"Authorization":"Bearer "+SB.key,"Content-Type":"application/json"};if(extra)for(var k in extra)h[k]=extra[k];return h;}
 /* ---- Bilder in Supabase Storage auslagern (statt base64 im Kontakt) -> klein & skalierbar ---- */
 var IMG_BUCKET="crm-bilder";
 function isStored(s){return /^https?:\/\//.test(String(s||""));}            // schon eine URL?
 // Ein Bild (Data-URI) hochladen -> oeffentliche URL. Wirft, wenn Storage/Bucket nicht erreichbar.
 function sbUploadImage(dataUri){
   if(!(SB&&SB.url&&SB.key))return Promise.reject(new Error("keine Cloud"));
   if(isStored(dataUri))return Promise.resolve(dataUri);
   var base=SB.url.replace(/\/+$/,"");
   return fetch(dataUri).then(function(r){return r.blob();}).then(function(blob){
     var path="c/"+Date.now().toString(36)+Math.random().toString(36).slice(2,9)+".jpg";
     return fetch(base+"/storage/v1/object/"+IMG_BUCKET+"/"+path,{method:"POST",headers:{apikey:SB.key,Authorization:"Bearer "+SB.key,"Content-Type":blob.type||"image/jpeg","x-upsert":"true"},body:blob}).then(function(r){
       if(!r.ok)throw new Error("upload "+r.status);
       return base+"/storage/v1/object/public/"+IMG_BUCKET+"/"+path;
     });
   });
 }
 // Liste von Data-URIs hochladen -> URLs. Bei Fehler bleibt das jeweilige Bild als Data-URI erhalten (kein Verlust).
 function sbStoreImages(uris){
   return (uris||[]).reduce(function(pr,u){return pr.then(function(acc){return sbUploadImage(u).then(function(url){acc.push(url);return acc;},function(){acc.push(u);return acc;});});},Promise.resolve([]));
 }
 // Supabase liefert pro Anfrage max. 1000 Zeilen -> seitenweise alle holen.
 function sbGet(){
   var all=[];
   function page(off){
     return fetch(sbBase()+"?select=data&limit=1000&offset="+off,{cache:"no-store",headers:sbHeaders()})
       .then(function(r){if(!r.ok)throw new Error("sb "+r.status);return r.json();})
       .then(function(rows){for(var i=0;i<rows.length;i++)if(rows[i]&&rows[i].data)all.push(rows[i].data);if(rows.length>=1000)return page(off+1000);return all;});
   }
   return page(0);
 }
 function sbUpsert(list){
   if(!list||!list.length)return Promise.resolve();
   var rows=list.map(function(c){return {id:c.id,data:c};});
   // In ~1-MB-Pakete aufteilen, damit kein Request zu gross wird (Bilder!). Einzelner grosser Kontakt geht allein raus.
   var batches=[],cur=[],size=0;
   rows.forEach(function(r){var s=JSON.stringify(r).length+2;if(cur.length&&size+s>1000000){batches.push(cur);cur=[];size=0;}cur.push(r);size+=s;});
   if(cur.length)batches.push(cur);
   var i=0;
   function step(){if(i>=batches.length)return Promise.resolve();var b=batches[i++];return fetch(sbBase(),{method:"POST",headers:sbHeaders({"Prefer":"resolution=merge-duplicates,return=minimal"}),body:JSON.stringify(b)}).then(function(r){if(!r.ok)throw new Error("sb "+r.status);}).then(step);}
   return step();
 }
 function sbDelete(id){return fetch(sbBase()+"?id=eq."+encodeURIComponent(id),{method:"DELETE",headers:sbHeaders({"Prefer":"return=minimal"})}).then(function(r){if(!r.ok)throw new Error("sb "+r.status);});}
 function sbDeleteAll(){return fetch(sbBase()+"?id=neq.__none__",{method:"DELETE",headers:sbHeaders({"Prefer":"return=minimal"})}).then(function(r){if(!r.ok)throw new Error("sb "+r.status);});}

 /* --- KI-Lead-Suche über Supabase Edge Function "lead-ai" (Claude + Web-Suche) --- */
 function aiReady(){return !!(SB&&SB.url&&SB.key&&AISECRET);}
 function aiPost(name,was,wo){
   var ctl=("AbortController" in window)?new AbortController():null;
   var to=ctl?setTimeout(function(){try{ctl.abort();}catch(_){}},120000):0;
   var done=function(){if(to)clearTimeout(to);};
   // Body als TEXT lesen (nicht .json()): die Funktion streamt während der Recherche
   // Keepalive-Leerzeichen und hängt am Ende das JSON an -> JSON.parse(trim) verträgt beides.
   function parse(t){try{return JSON.parse(String(t||"").trim()||"{}");}catch(_){return {};}}
   return fetch(SB.url.replace(/\/+$/,"")+"/functions/v1/"+name,{method:"POST",headers:{"Authorization":"Bearer "+SB.key,"apikey":SB.key,"Content-Type":"application/json","x-crm-secret":AISECRET},body:JSON.stringify({was:was,wo:wo}),signal:ctl?ctl.signal:undefined})
     .then(function(r){if(!r.ok)return r.text().then(function(t){var e=parse(t);var err=new Error("ai "+r.status+(e&&e.error?(": "+e.error):""));err.status=r.status;throw err;});return r.text().then(parse);})
     .then(function(d){done();return d;},function(e){done();if(e&&(e.name==="AbortError"||/abort/i.test(String(e&&e.message)))){var er=new Error("Zeitüberschreitung – die KI-Suche hat zu lange gebraucht. Bitte Region enger fassen und erneut versuchen.");er.status=0;throw er;}throw e;});
 }
 // "Einfacher" Aufruf OHNE CORS-Vorabpruefung (kein OPTIONS): apikey als Query, Secret im Body,
 // Content-Type text/plain -> kommt auch durch strenge Firmen-Proxies, die /functions-OPTIONS blocken.
 function aiPostSimple(name,was,wo){
   var ctl=("AbortController" in window)?new AbortController():null;
   var to=ctl?setTimeout(function(){try{ctl.abort();}catch(_){}},120000):0;
   function parse(t){try{return JSON.parse(String(t||"").trim()||"{}");}catch(_){return {};}}
   var url=SB.url.replace(/\/+$/,"")+"/functions/v1/"+name+"?apikey="+encodeURIComponent(SB.key);
   return fetch(url,{method:"POST",headers:{"Content-Type":"text/plain;charset=UTF-8"},body:JSON.stringify({was:was,wo:wo,secret:AISECRET}),signal:ctl?ctl.signal:undefined})
     .then(function(r){if(!r.ok)return r.text().then(function(t){var e=parse(t);var err=new Error("ai "+r.status+(e&&e.error?(": "+e.error):""));err.status=r.status;throw err;});return r.text().then(parse);})
     .then(function(d){if(to)clearTimeout(to);return d;},function(e){if(to)clearTimeout(to);if(e&&(e.name==="AbortError"||/abort/i.test(String(e&&e.message)))){var er=new Error("Zeitüberschreitung");er.status=0;throw er;}throw e;});
 }
 // Hintergrund-Job starten (kurzer Aufruf, < 1s -> kommt auch durch strenge Proxies).
 function aiJobStart(name,was,wo,jobId){
   return fetch(SB.url.replace(/\/+$/,"")+"/functions/v1/"+name,{method:"POST",headers:{"Authorization":"Bearer "+SB.key,"apikey":SB.key,"Content-Type":"application/json","x-crm-secret":AISECRET},body:JSON.stringify({was:was,wo:wo,jobId:jobId})})
     .then(function(r){return r.text().then(function(t){var d;try{d=JSON.parse((t||"").trim()||"{}");}catch(_){d={};}if(!r.ok){var err=new Error("ai "+r.status+(d&&d.error?(": "+d.error):""));err.status=r.status;throw err;}return d;});});
 }
 // Ergebnis aus der DB (Tabelle ai_jobs) abholen -> normale DB-Abfrage, kommt durch Proxies.
 function aiJobPoll(jobId){
   var start=Date.now();
   return new Promise(function(res,rej){
     function tick(){
       fetch(SB.url.replace(/\/+$/,"")+"/rest/v1/ai_jobs?id=eq."+encodeURIComponent(jobId)+"&select=result&limit=1",{cache:"no-store",headers:sbHeaders()})
         .then(function(r){return r.ok?r.json():[];})
         .then(function(rows){
           if(rows&&rows[0]&&rows[0].result){res(rows[0].result);return;}
           if(Date.now()-start>95000){rej(new Error("Zeitüberschreitung – die KI-Suche dauert zu lange."));return;}
           setTimeout(tick,3000);
         })
         .catch(function(){if(Date.now()-start>95000)rej(new Error("KI-Ergebnis nicht abrufbar."));else setTimeout(tick,3000);});
     }
     setTimeout(tick,2500);
   });
 }
 function apiAi(was,wo){
   // 1) ZUERST der klassische Aufruf -> funktioniert am iPhone IMMER (bewaehrt).
   // 2) Scheitert der (z. B. Desktop-Firmen-Proxy blockt die CORS-Vorabpruefung) ->
   //    der "einfache" Aufruf ohne Vorabpruefung. So bleibt das iPhone unberuehrt.
   return aiPost("lead-ai",was,wo)
     .catch(function(e){if(e&&e.status===404)return aiPost("lead-ai-",was,wo);throw e;})
     .catch(function(){return aiPostSimple("lead-ai",was,wo).catch(function(e){if(e&&e.status===404)return aiPostSimple("lead-ai-",was,wo);throw e;});})
     .then(function(d){return (d.leads||[]).filter(function(x){return x&&(x.firma||x.name);});});
 }
 /* --- Visitenkarten-Scan (Claude-Vision über dieselbe Edge Function "lead-ai") --- */
 function cardPost(name,dataUri){
   var ctl=("AbortController" in window)?new AbortController():null;
   var to=ctl?setTimeout(function(){try{ctl.abort();}catch(_){}} ,60000):0;
   return fetch(SB.url.replace(/\/+$/,"")+"/functions/v1/"+name,{method:"POST",headers:{"Authorization":"Bearer "+SB.key,"apikey":SB.key,"Content-Type":"application/json","x-crm-secret":AISECRET},body:JSON.stringify({image:dataUri}),signal:ctl?ctl.signal:undefined})
     .then(function(r){return r.text().then(function(t){var d;try{d=JSON.parse((t||"").trim()||"{}");}catch(_){d={};}if(!r.ok){var err=new Error("scan "+r.status+(d&&d.error?(": "+d.error):""));err.status=r.status;throw err;}return d;});})
     .then(function(d){if(to)clearTimeout(to);return d;},function(e){if(to)clearTimeout(to);if(e&&(e.name==="AbortError"||/abort/i.test(String(e&&e.message)))){var er=new Error("Zeitüberschreitung beim Auswerten.");throw er;}throw e;});
 }
 function apiCardScan(dataUri){
   // Dieselbe Funktion wie die Lead-Suche (lead-ai / lead-ai-): sie erkennt das Bild und
   // wertet die Visitenkarte aus. So gibt es nur EINE Edge Function zu pflegen.
   return cardPost("lead-ai",dataUri).catch(function(e){if(e&&e.status===404)return cardPost("lead-ai-",dataUri);throw e;})
     .then(function(d){return (d&&d.contact)||{};});
 }
 // Notiz/OneNote -> Kontakt + Verlauf. Klassisch zuerst (iPhone), sonst einfacher Aufruf (Desktop-Proxy).
 function apiNoteScan(notiz){
   function call(name,simple){
     var url=SB.url.replace(/\/+$/,"")+"/functions/v1/"+name+(simple?("?apikey="+encodeURIComponent(SB.key)):"");
     var headers=simple?{"Content-Type":"text/plain;charset=UTF-8"}:{"Authorization":"Bearer "+SB.key,"apikey":SB.key,"Content-Type":"application/json","x-crm-secret":AISECRET};
     var body=simple?JSON.stringify({notiz:notiz,secret:AISECRET}):JSON.stringify({notiz:notiz});
     var ctl=("AbortController" in window)?new AbortController():null;var to=ctl?setTimeout(function(){try{ctl.abort();}catch(_){}} ,120000):0;
     return fetch(url,{method:"POST",headers:headers,body:body,signal:ctl?ctl.signal:undefined})
       .then(function(r){return r.text().then(function(t){if(to)clearTimeout(to);var d;try{d=JSON.parse((t||"").trim()||"{}");}catch(_){d={};}if(!r.ok){var e=new Error("note "+r.status+(d&&d.error?(": "+d.error):""));e.status=r.status;throw e;}return d;});},function(e){if(to)clearTimeout(to);throw e;});
   }
   return call("lead-ai",false).catch(function(e){if(e&&e.status===404)return call("lead-ai-",false);throw e;})
     .catch(function(){return call("lead-ai",true).catch(function(e){if(e&&e.status===404)return call("lead-ai-",true);throw e;});})
     .then(function(d){return d||{};});
 }
 // KI-Antwortvorschlag auf eine eingegangene E-Mail -> {subject,body}. Klassisch zuerst (iPhone), sonst einfacher Aufruf.
 function apiMailReply(payload){
   function call(name,simple){
     var url=SB.url.replace(/\/+$/,"")+"/functions/v1/"+name+(simple?("?apikey="+encodeURIComponent(SB.key)):"");
     var headers=simple?{"Content-Type":"text/plain;charset=UTF-8"}:{"Authorization":"Bearer "+SB.key,"apikey":SB.key,"Content-Type":"application/json","x-crm-secret":AISECRET};
     var bodyObj=simple?{mailReply:payload,secret:AISECRET}:{mailReply:payload};
     var ctl=("AbortController" in window)?new AbortController():null;var to=ctl?setTimeout(function(){try{ctl.abort();}catch(_){}} ,90000):0;
     return fetch(url,{method:"POST",headers:headers,body:JSON.stringify(bodyObj),signal:ctl?ctl.signal:undefined})
       .then(function(r){return r.text().then(function(t){if(to)clearTimeout(to);var d;try{d=JSON.parse((t||"").trim()||"{}");}catch(_){d={};}if(!r.ok){var e=new Error("reply "+r.status+(d&&d.error?(": "+d.error):""));e.status=r.status;throw e;}return d;});},function(e){if(to)clearTimeout(to);throw e;});
   }
   return call("lead-ai",false).catch(function(e){if(e&&e.status===404)return call("lead-ai-",false);throw e;})
     .catch(function(){return call("lead-ai",true).catch(function(e){if(e&&e.status===404)return call("lead-ai-",true);throw e;});})
     .then(function(d){return d||{};});
 }
 /* ===== OneNote-Massenimport via Microsoft 365 (Graph) ===== */
 var MS_CLIENT_ID="c4cd70b7-2bbe-41ed-ba3e-5621037c49ae";
 var MS_TENANT_ID="f4c543ca-6d4a-4beb-8f4f-90924543f46a";
 var MS_REDIRECT="https://alzingermaschinenbau.github.io/lepton-konfigurator/vertrieb/";
 var MS_SCOPES=["Notes.Read.All","User.Read"]; // .All -> auch GETEILTE Notizbuecher; Bilder via preAuthenticated-Links (kein Sites-Scope/Admin noetig)
 var _msal=null,_msStop=false;
 function loadScript(src){return new Promise(function(res,rej){var s=document.createElement("script");s.src=src;s.onload=function(){res();};s.onerror=function(){rej(new Error("scr "+src));};document.head.appendChild(s);});}
 function ensureMsal(){
   if(window.msal&&window.msal.PublicClientApplication)return Promise.resolve();
   // Lokal (gleicher Origin, vom SW vorgecacht) -> proxy-/offline-sicher; CDN nur als Notfall.
   return loadScript("vendor/msal-browser.min.js").catch(function(){return loadScript("https://alcdn.msauth.net/browser/3.27.0/js/msal-browser.min.js");})
     .then(function(){if(!(window.msal&&window.msal.PublicClientApplication))throw new Error("MSAL konnte nicht geladen werden.");});
 }
 function msalApp(){if(_msal)return Promise.resolve(_msal);_msal=new msal.PublicClientApplication({auth:{clientId:MS_CLIENT_ID,authority:"https://login.microsoftonline.com/"+MS_TENANT_ID,redirectUri:MS_REDIRECT},cache:{cacheLocation:"localStorage"}});return _msal.initialize().then(function(){return _msal;});}
 function msToken(){
   return ensureMsal().then(msalApp).then(function(app){
     var acc=app.getAllAccounts()[0];
     var req={scopes:MS_SCOPES,account:acc};
     if(acc)return app.acquireTokenSilent(req).then(function(r){return r.accessToken;}).catch(function(){return app.acquireTokenPopup({scopes:MS_SCOPES}).then(function(r){return r.accessToken;});});
     return app.loginPopup({scopes:MS_SCOPES}).then(function(r){return r.accessToken;});
   });
 }
 // Graph-Fetch mit automatischer Wiederholung bei Drosselung (429) und kurzen Server-Fehlern (503/504).
 // Respektiert den Retry-After-Header; bis zu 5 Versuche mit Backoff.
 function gfetch(url,opts,tries){
   tries=tries||0;
   return fetch(url,opts).then(function(r){
     // 429/503/504 = klassische Drosselung; 403 ist bei OneNote oft ebenfalls Drosselung -> wiederholen (laengere Pause).
     if((r.status===429||r.status===503||r.status===504||r.status===403)&&tries<5){
       var ra=parseInt(r.headers.get("Retry-After")||"0",10);var base=(r.status===403)?4000:2000;var wait=(ra>0?ra*1000:Math.min(45000,base*(tries+1)));
       return new Promise(function(res){setTimeout(res,wait);}).then(function(){return gfetch(url,opts,tries+1);});
     }
     return r;
   });
 }
 function graphGet(token,url){return gfetch(url,{headers:{Authorization:"Bearer "+token}}).then(function(r){if(!r.ok)throw new Error("Graph "+r.status);return r.json();});}
 // Generischer Paginierer: alle Seiten einer Liste (@odata.nextLink) einsammeln und je Eintrag mappen.
 function graphPaged(token,url,map,acc){acc=acc||[];return graphGet(token,url).then(function(j){(j.value||[]).forEach(function(v){acc.push(map(v));});var nx=j["@odata.nextLink"];if(nx&&!_msStop)return graphPaged(token,nx,map,acc);return acc;});}
 // Alle Abschnitte (flach, inkl. Abschnittsgruppen, auch GETEILTE) mit Notizbuch-Zuordnung.
 function graphAllSections(token){
   return graphPaged(token,"https://graph.microsoft.com/v1.0/me/onenote/sections?$top=100&$select=id,displayName,pagesUrl&$expand=parentNotebook($select=id,displayName)",function(s){return {id:s.id,name:s.displayName||"",pagesUrl:s.pagesUrl||"",bookId:(s.parentNotebook&&s.parentNotebook.id)||("?"+(s.parentNotebook&&s.parentNotebook.displayName||s.id)),book:(s.parentNotebook&&s.parentNotebook.displayName)||"(ohne Notizbuch)"};});
 }
 // Aus den Abschnitten die Notizbuch-Liste ableiten (zeigt auch geteilte) -> [{id,name,count}].
 function notebooksFromSections(secs){
   var seen={},out=[];secs.forEach(function(s){var k=s.bookId;if(!seen[k]){seen[k]={id:k,name:s.book,count:0};out.push(seen[k]);}seen[k].count++;});
   out.sort(function(a,b){return a.name.localeCompare(b.name);});return out;
 }
 // Seiten eines Abschnitts -> [{id,title,section,book,contentUrl}]. Nutzt pagesUrl (wichtig fuer GETEILTE).
 function graphPagesOf(token,sec){
   var base=sec.pagesUrl||("https://graph.microsoft.com/v1.0/me/onenote/sections/"+sec.id+"/pages");
   var url=base+(base.indexOf("?")<0?"?":"&")+"$top=100&$select=id,title,contentUrl";
   return graphPaged(token,url,function(p){return {id:p.id,title:p.title||"",section:sec.name,book:sec.book,contentUrl:p.contentUrl||""};});
 }
 // Seiten der ausgewaehlten Abschnitte einsammeln (Abschnitt fuer Abschnitt -> zuverlaessig).
 function pagesFromSections(token,secs,onSec,log){
   var out=[];
   function nextSec(i){
     if(_msStop||i>=secs.length)return out;
     if(onSec)onSec(i,secs.length,secs[i]);
     return graphPagesOf(token,secs[i]).then(function(ps){ps.forEach(function(p){out.push(p);});return nextSec(i+1);}).catch(function(e){if(log)log.push("Seiten("+(secs[i]&&secs[i].name||"?")+"): "+String((e&&e.message)||e));return nextSec(i+1);});
   }
   return nextSec(0);
 }
 // Kuerzlich geoeffnete Notizbuecher (auch GETEILTE/persoenliche) -> [{name,url}].
 function graphRecentNotebooks(token){
   return graphGet(token,"https://graph.microsoft.com/v1.0/me/onenote/notebooks/getRecentNotebooks(includePersonalNotebooks=true)")
     .then(function(j){var seen={},out=[];(j.value||[]).forEach(function(r){var url=(r.links&&r.links.oneNoteWebUrl&&r.links.oneNoteWebUrl.href)||"";if(url&&!seen[url]){seen[url]=1;out.push({name:r.displayName||"(ohne Namen)",url:url});}});return out;});
 }
 // Notizbuch ueber seine Web-URL aufloesen (Zugriff auf geteilte) -> Notebook-Entitaet (mit id, sectionsUrl, sectionGroupsUrl).
 function graphNotebookFromUrl(token,webUrl){
   return fetch("https://graph.microsoft.com/v1.0/me/onenote/notebooks/getNotebookFromWebUrl",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({webUrl:webUrl})}).then(function(r){if(!r.ok)throw new Error("nbUrl "+r.status);return r.json();});
 }
 // Alle Abschnitte eines (auch geteilten) Notizbuchs, rekursiv inkl. Abschnittsgruppen, via dessen URLs.
 function nbSections(token,nb){
   var bookName=nb.displayName||"",bookId=nb.id||bookName,out=[];
   function sx(url){return graphPaged(token,url+(url.indexOf("?")<0?"?":"&")+"$select=id,displayName,pagesUrl",function(s){return {id:s.id,name:s.displayName||"",pagesUrl:s.pagesUrl||"",bookId:bookId,book:bookName};}).then(function(ss){ss.forEach(function(s){out.push(s);});});}
   function gx(url){return graphPaged(token,url+(url.indexOf("?")<0?"?":"&")+"$select=id,sectionsUrl,sectionGroupsUrl",function(g){return g;}).then(function(gs){return gs.reduce(function(p,g){return p.then(function(){return Promise.all([g.sectionsUrl?sx(g.sectionsUrl):0,g.sectionGroupsUrl?gx(g.sectionGroupsUrl):0]);});},Promise.resolve());});}
   return Promise.all([nb.sectionsUrl?sx(nb.sectionsUrl):0,nb.sectionGroupsUrl?gx(nb.sectionGroupsUrl):0]).then(function(){return out;});
 }
 // Abschnitte mehrerer Notizbuecher (per URL aufgeloest) einsammeln, mit Fortschritt + Diagnose-Protokoll.
 function sectionsFromBooks(token,books,onBook,log){
   var secs=[];
   return books.reduce(function(p,b,i){return p.then(function(){if(_msStop)return;if(onBook)onBook(i,books.length,b);
     return graphNotebookFromUrl(token,b.url).then(function(nb){nb.displayName=nb.displayName||b.name;return nbSections(token,nb);}).then(function(ss){if(log)log.push(b.name+": "+ss.length+" Abschn.");ss.forEach(function(s){secs.push(s);});}).catch(function(e){if(log)log.push(b.name+": FEHLER "+String((e&&e.message)||e));});
   });},Promise.resolve()).then(function(){return secs;});
 }
 // Notizbuchname -> ISO-Land (Fallback, wenn die KI kein Land erkennt).
 var NB_LAND={deutschland:"DE",polen:"PL","österreich":"AT",osterreich:"AT",schweiz:"CH",holland:"NL",niederlande:"NL",belgien:"BE",frankreich:"FR",italien:"IT",ungarn:"HU",griechenland:"GR",tschechien:"CZ",kroatien:"HR","rumänien":"RO",rumaenien:"RO",norwegen:"NO",finland:"FI",finnland:"FI",schweden:"SE",dänemark:"DK",daenemark:"DK",usa:"US",england:"GB",grossbritannien:"GB","großbritannien":"GB",spanien:"ES",portugal:"PT",slowenien:"SI",slowakei:"SK",bulgarien:"BG",serbien:"RS",türkei:"TR",tuerkei:"TR",afrika:"ZA",irland:"IE",litauen:"LT",lettland:"LV",estland:"EE"};
 function landFromBook(book){var k=String(book||"").toLowerCase();for(var key in NB_LAND){if(k.indexOf(key)>=0)return NB_LAND[key];}return "";}
 // Sites-Token (Sites.Read.All) NICHT-blockierend holen -> noetig fuer Bilder aus dem OneDrive der Kollegen.
 // Liefert null, wenn (noch) keine Admin-Freigabe erteilt wurde (Import laeuft dann ohne Bilder weiter).
 function msSitesToken(){
   // forceRefresh: gecachte Tokens stammen evtl. von VOR der Admin-Freigabe (ohne Sites-Scope) -> frisch holen.
   return ensureMsal().then(msalApp).then(function(app){var acc=app.getAllAccounts()[0];if(!acc)return null;return app.acquireTokenSilent({scopes:["Sites.Read.All"],account:acc,forceRefresh:true}).then(function(r){return r.accessToken;}).catch(function(){return null;});}).catch(function(){return null;});
 }
 /* ===== E-Mail-Anbindung (Microsoft 365 / Graph) ===== */
 var MS_MAIL_SCOPES=["Mail.Read","Mail.Send","User.Read"];
 // Mail-Token holen (eigenes Postfach lesen + Antworten senden). interactive=true -> Pop-up erlaubt (erstmalige Zustimmung).
 function msMailToken(interactive){
   return ensureMsal().then(msalApp).then(function(app){
     var acc=app.getAllAccounts()[0];
     var req={scopes:MS_MAIL_SCOPES,account:acc};
     return app.acquireTokenSilent(req).then(function(r){return r.accessToken;}).catch(function(){
       if(interactive)return app.acquireTokenPopup({scopes:MS_MAIL_SCOPES}).then(function(r){return r.accessToken;});
       return null;
     });
   });
 }
 function graphMe(token){return gfetch("https://graph.microsoft.com/v1.0/me?$select=mail,userPrincipalName,displayName",{headers:{Authorization:"Bearer "+token}}).then(function(r){if(!r.ok)throw new Error("me "+r.status);return r.json();}).then(function(j){return ((j.mail||j.userPrincipalName||"")+"").toLowerCase();});}
 // Letzte Nachrichten (Posteingang + Gesendet) holen, ab Datum sinceISO (optional). Bis ~maxN.
 function graphMessages(token,sinceISO,maxN){
   maxN=maxN||300;var out=[];
   var sel="id,subject,from,toRecipients,ccRecipients,receivedDateTime,sentDateTime,bodyPreview,isDraft,conversationId,webLink";
   var url="https://graph.microsoft.com/v1.0/me/messages?$top=50&$select="+sel+"&$orderby=receivedDateTime%20desc";
   if(sinceISO)url+="&$filter=receivedDateTime%20ge%20"+encodeURIComponent(sinceISO);
   function page(u){return gfetch(u,{headers:{Authorization:"Bearer "+token,Prefer:'outlook.body-content-type="text"'}}).then(function(r){if(!r.ok)throw new Error("msg "+r.status);return r.json();}).then(function(j){(j.value||[]).forEach(function(m){out.push(m);});var nx=j["@odata.nextLink"];if(nx&&out.length<maxN&&!_msStop)return page(nx);return out;});}
   return page(url);
 }
 // Antwort senden (Graph Mail.Send) -> liegt danach im "Gesendet"-Ordner. attach=[{name,dataUri}] optional.
 function graphSendMail(token,to,subject,bodyText,attach){
   var msg={message:{subject:subject,body:{contentType:"Text",content:bodyText},toRecipients:[{emailAddress:{address:to}}]},saveToSentItems:true};
   if(attach&&attach.length){
     msg.message.attachments=attach.map(function(f){
       var b64=String(f.dataUri||"").replace(/^data:[^,]*,/,"");
       return {"@odata.type":"#microsoft.graph.fileAttachment",name:f.name||"Anhang.pdf",contentType:f.contentType||"application/pdf",contentBytes:b64};
     });
   }
   return fetch("https://graph.microsoft.com/v1.0/me/sendMail",{method:"POST",headers:{Authorization:"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify(msg)}).then(function(r){if(!r.ok)throw new Error("send "+r.status);return true;});
 }
 // E-Mails aus dem eigenen Postfach abrufen und passenden Kontakten als Aktivitaet (mailin/mailout) zuordnen. Dedup ueber msgId.
 var MAIL_SINCE_KEY="amb_crm_mail_since";
 function importEmails(interactive){
   return msMailToken(interactive).then(function(tok){
     if(!tok)throw new Error("Kein Mail-Zugriff – bitte im Microsoft-Login der Berechtigung Mail.Read zustimmen.");
     return graphMe(tok).then(function(myEmail){
       var since=localStorage.getItem(MAIL_SINCE_KEY)||new Date(Date.now()-60*86400000).toISOString();
       return graphMessages(tok,since).then(function(msgs){
         var byEmail={};DB.contacts.forEach(function(c){if(c.mail)byEmail[String(c.mail).toLowerCase().trim()]=c;});
         var seenMsg={};DB.contacts.forEach(function(c){(c.activities||[]).forEach(function(a){if(a&&a.msgId)seenMsg[a.msgId]=1;});});
         var added=0,changed={};
         (msgs||[]).forEach(function(m){
           if(!m||m.isDraft)return;if(m.id&&seenMsg[m.id])return;
           var fromAddr=((m.from&&m.from.emailAddress&&m.from.emailAddress.address)||"").toLowerCase();
           var outgoing=(fromAddr===myEmail);var partner=null;
           if(outgoing){(m.toRecipients||[]).some(function(r){var a=((r.emailAddress&&r.emailAddress.address)||"").toLowerCase();if(byEmail[a]){partner=byEmail[a];return true;}return false;});}
           else{partner=byEmail[fromAddr];}
           if(!partner)return;
           var date=new Date(outgoing?(m.sentDateTime||m.receivedDateTime):m.receivedDateTime).getTime()||Date.now();
           var note=(m.subject?("Betreff: "+m.subject+"\n"):"")+((m.bodyPreview||"").trim());
           partner.activities=partner.activities||[];
           partner.activities.push({id:uid(),type:outgoing?"mailout":"mailin",date:date,note:note,by:(CUR&&CUR.n)||"",msgId:m.id||"",mailWeb:m.webLink||""});
           partner.activities.sort(function(x,y){return (x.date||0)-(y.date||0);});
           if(m.id)seenMsg[m.id]=1;changed[partner.id]=partner;added++;
         });
         Object.keys(changed).forEach(function(id){changed[id].updated=Date.now();saveContact(changed[id]);});
         try{localStorage.setItem(MAIL_SINCE_KEY,new Date(Date.now()-2*86400000).toISOString());}catch(e){} // 2 Tage Ueberlappung beim naechsten Mal
         return {scanned:(msgs||[]).length,added:added,contacts:Object.keys(changed).length};
       });
     });
   });
 }
 // Seiteninhalt (HTML) -> reiner Text + Bilder als {pre, full}. preAuthenticated=true.
 function graphPageContent(token,page){
   var base=(page&&page.contentUrl)||("https://graph.microsoft.com/v1.0/me/onenote/pages/"+((page&&page.id)||page)+"/content");
   var url=base+(base.indexOf("?")<0?"?":"&")+"preAuthenticated=true";
   return gfetch(url,{headers:{Authorization:"Bearer "+token}}).then(function(r){if(!r.ok)throw new Error("content "+r.status);return r.text();})
     .then(function(html){var d=document.createElement("div");d.innerHTML=html;var all=d.querySelectorAll("img"),imgs=[],sample="";all.forEach(function(im){var pre=im.getAttribute("src")||"",full=im.getAttribute("data-fullres-src")||im.getAttribute("data-render-src")||"";if(!full&&pre)full=pre;if(!pre&&full)pre=full;if(/^https?:\/\//.test(pre)||/^https?:\/\//.test(full)){imgs.push({pre:pre,full:full});if(!sample)sample=(full||pre);}});var txt=(d.innerText||d.textContent||"").replace(/\n{3,}/g,"\n\n").trim();return {text:txt,imgs:imgs,raw:all.length,sample:sample};});
 }
 // OneNote-Bild laden -> verkleinertes JPEG-DataURI. im={pre,full}.
 // publicAuth-Links verweigern fetch (400) -> rohe Ressourcen-URL (ohne ?publicAuth...) MIT Sites-Token zuerst,
 // danach <img crossOrigin> auf den preAuth-Link, zuletzt fetch-Varianten.
 function graphImage(token,sitesToken,im){
   var pre=(im&&im.pre)||im,full=(im&&im.full)||im;
   var raw=String(full||pre||"").split("?")[0]; // .../onenote/resources/{id}/content bzw. /$value
   // "siteCollections/..." ist keine gueltige Graph-Route fuer normale GETs -> auf "sites/..." umschreiben.
   var fixed=raw.replace("/v1.0/siteCollections/","/v1.0/sites/");
   function viaFetch(url,authTok){return gfetch(url,authTok?{headers:{Authorization:"Bearer "+authTok}}:{}).then(function(r){if(!r.ok)throw new Error("img "+r.status);return r.blob();}).then(function(b){if(!b||!b.size)throw new Error("leer");return new Promise(function(res,rej){var u=URL.createObjectURL(b);downscaleSrc(u,1200,function(d){URL.revokeObjectURL(u);if(d)res(d);else rej(new Error("decode"));});});});}
   function viaImg(url){return new Promise(function(res,rej){downscaleSrc(url,1200,function(d){d?res(d):rej(new Error("imgEl"));},true);});}
   // Jeden Schritt protokollieren -> Diagnose zeigt genau, welcher Weg woran scheitert.
   var steps=[];
   function tryStep(name,fn){return function(){return fn().catch(function(e){steps.push(name+":"+String((e&&e.message)||e).replace(/^img /,""));throw e;});};}
   var p=Promise.reject(new Error("start"));
   if(sitesToken&&fixed)p=p.catch(tryStep("fixSites",function(){return viaFetch(fixed,sitesToken);}));
   if(fixed)p=p.catch(tryStep("fixNotes",function(){return viaFetch(fixed,token);}));
   if(sitesToken&&raw&&raw!==fixed)p=p.catch(tryStep("rawSites",function(){return viaFetch(raw,sitesToken);}));
   p=p.catch(tryStep("imgEl",function(){return viaImg(pre);}));
   p=p.catch(tryStep("preOhne",function(){return viaFetch(pre,null);}));
   return p.catch(function(){throw new Error(steps.join(" / "));});
 }
 // Foto verkleinern (Längste Seite maxDim) und als JPEG-Data-URI zurückgeben -> kleine Payload.
 function downscaleImage(file,maxDim,cb){
   try{var img=new Image();var url=URL.createObjectURL(file);
     img.onload=function(){try{var w=img.width,h=img.height,s=Math.min(1,maxDim/Math.max(w,h||1));var cw=Math.max(1,Math.round(w*s)),ch=Math.max(1,Math.round(h*s));var cv=document.createElement("canvas");cv.width=cw;cv.height=ch;cv.getContext("2d").drawImage(img,0,0,cw,ch);URL.revokeObjectURL(url);cb(cv.toDataURL("image/jpeg",0.82));}catch(e){URL.revokeObjectURL(url);cb(null);}};
     img.onerror=function(){URL.revokeObjectURL(url);cb(null);};img.src=url;
   }catch(e){cb(null);}
 }

 /* --- Op-Warteschlange (für Offline/Server) --- */
 function queueRead(){try{return JSON.parse(localStorage.getItem(QKEY)||"[]");}catch(e){return [];}}
 // Cloud-Stand mit lokalen Daten zusammenführen: lokale Änderungen, die NEUER oder noch nicht synchronisiert sind,
 // gewinnen -> kein Zurückspringen von gerade gemachten Änderungen und kein Flackern beim 30s-Sync.
 function mergeCloud(list){
   var GRACE=15000,DELGRACE=45000,now=Date.now();
   function fresh(id){return (now-(_recentEdits[id]||0))<GRACE;} // gerade lokal bearbeitet?
   function justDeleted(id){return (now-(_recentDeletes[id]||0))<DELGRACE;} // gerade lokal geloescht?
   var pending={};queueRead().forEach(function(op){if(!op)return;if(op.op==="upsert"&&op.contact)pending[op.contact.id]=1;if(op.op==="delete"&&op.id)pending[op.id]=2;if(op.op==="bulk")(op.contacts||[]).forEach(function(c){if(c)pending[c.id]=1;});});
   var local={};(DB.contacts||[]).forEach(function(c){if(c)local[c.id]=c;});
   var out=[],seen={};
   (list||[]).forEach(function(cc){if(!cc)return;seen[cc.id]=1;if(pending[cc.id]===2||justDeleted(cc.id))return; /* lokal geloescht -> nicht zurueckholen */ var lc=local[cc.id];var keepLocal=lc&&(pending[cc.id]===1||fresh(cc.id)||(lc.updated||0)>=(cc.updated||0));if(!keepLocal&&lc&&lc.lat!=null&&cc.lat==null){cc.lat=lc.lat;cc.lon=lc.lon;} /* lokal ermittelte Koordinaten erhalten */ var chosen=keepLocal?lc:cc;
     // "Erledigt" ist klebrig: hat EINE Seite die Wiedervorlage (gleiches Fälligkeitsdatum) als erledigt markiert, bleibt sie erledigt -> kein Zurückspringen durch Uhren-Differenz zwischen Geräten.
     if(lc&&cc&&lc.followup&&cc.followup&&lc.followup.due===cc.followup.due&&(lc.followup.done||cc.followup.done)&&chosen.followup)chosen.followup.done=true;
     out.push(chosen);});
   // lokal angelegte/geänderte Kontakte, die (noch) nicht in der Cloud sind -> behalten, wenn ausstehend oder gerade bearbeitet
   (DB.contacts||[]).forEach(function(c){if(c&&!seen[c.id]&&(pending[c.id]===1||fresh(c.id)))out.push(c);});
   return out;
 }
 function queueWrite(q){try{localStorage.setItem(QKEY,JSON.stringify(q));}catch(e){}}
 function enqueue(op){var q=queueRead();q.push(op);queueWrite(q);}
 var _flushing=false,_flushAgain=false;
 function flush(){
   if(MODE==="local")return Promise.resolve();
   if(_flushing){_flushAgain=true;return Promise.resolve();} // keine parallele Synchronisation
   var q=queueRead();if(!q.length)return Promise.resolve();
   _flushing=true;
   function done(processed){
     // NUR die tatsaechlich gesendeten Ops vorne entfernen; waehrenddessen neu hinzugekommene bleiben erhalten (sonst Datenverlust!)
     if(processed>0){try{queueWrite(queueRead().slice(processed));}catch(e){}}
     _flushing=false;
     if(_flushAgain){_flushAgain=false;return flush();}
   }
   if(MODE==="server")return apiPost("batch",{ops:q}).then(function(res){if(res&&res.rev!=null)DB.rev=res.rev;done(q.length);},function(){done(0);});
   // cloud: Ops sequenziell an Supabase; bei Fehler Rest behalten und später erneut
   var i=0;
   function step(){
     if(i>=q.length)return Promise.resolve();
     var op=q[i],pr;
     if(op.op==="upsert")pr=sbUpsert([op.contact]);
     else if(op.op==="delete")pr=sbDelete(op.id);
     else if(op.op==="bulk")pr=op.replace?sbDeleteAll().then(function(){return sbUpsert(op.contacts||[]);}):sbUpsert(op.contacts||[]);
     else pr=Promise.resolve();
     return pr.then(function(){i++;return step();});
   }
   return step().then(function(){done(i);},function(){done(i);});
 }

 /* --- Mutationen: lokal optimistisch + (online) in die geteilte Quelle --- */
 function persist(){cacheSave();} /* nur lokaler Spiegel */
 var _recentEdits={}; // id -> Zeitpunkt der letzten lokalen Aenderung (Schutzfenster gegen Sync-Ruecksprung)
 function saveContact(c){if(c)_recentEdits[c.id]=Date.now();cacheSave();if(MODE!=="local"){enqueue({op:"upsert",contact:c});flush();}}
 var _recentDeletes={}; // id -> Loeschzeitpunkt (Schutzfenster, damit ein geloeschter Kontakt nicht durch Sync zurueckkommt)
 function removeContact(id){
   DB.contacts=DB.contacts.filter(function(x){return x.id!==id;});
   _recentDeletes[id]=Date.now();delete _recentEdits[id];
   cacheSave();
   if(MODE!=="local"){
     // ausstehende Speicherungen fuer diesen Kontakt aus der Warteschlange entfernen -> kein Wieder-Anlegen
     var q=queueRead().filter(function(op){if(!op)return false;if(op.op==="upsert"&&op.contact&&op.contact.id===id)return false;if(op.op==="bulk"&&op.contacts){op.contacts=op.contacts.filter(function(c){return c&&c.id!==id;});}return true;});
     queueWrite(q);
     enqueue({op:"delete",id:id});flush();
   }
 }
 function bulkSave(list,replace){cacheSave();if(MODE!=="local"){enqueue({op:"bulk",contacts:list,replace:!!replace});flush();}}

 /* --- Online-Sync --- */
 function pull(){
   if(MODE==="cloud")return sbGet().then(function(list){DB.contacts=mergeCloud(list);cacheSave();rerenderCurrent();});
   return apiGet().then(function(d){DB.contacts=d.contacts||[];DB.rev=d.rev||0;cacheSave();rerenderCurrent();});
 }
 function syncFromServer(){if(MODE==="local")return Promise.resolve();return flush().then(pull).catch(function(){});}
 // Backend erkennen: zuerst Cloud (Supabase), dann eigener PHP-Server, sonst lokal.
 function initBackend(){
   if(sbReady()){
     sbGet().then(function(list){
       MODE="cloud";setConn(true);
       if(!(list&&list.length)&&DB.contacts&&DB.contacts.length){enqueue({op:"bulk",contacts:DB.contacts,replace:false});}
       flush().then(sbGet).then(function(l){DB.contacts=mergeCloud(l);cacheSave();rerenderCurrent();}).catch(function(){});
     }).catch(function(){initPhp();});
   } else initPhp();
 }
 function initPhp(){
   apiGet().then(function(data){
     MODE="server";setConn(true);DB.rev=data.rev||0;
     if(!(data.contacts&&data.contacts.length)&&DB.contacts&&DB.contacts.length){enqueue({op:"bulk",contacts:DB.contacts,replace:false});}
     flush().then(function(){return apiGet();}).then(function(d){DB.contacts=d.contacts||[];DB.rev=d.rev||0;cacheSave();rerenderCurrent();}).catch(function(){});
   }).catch(function(){MODE="local";setConn(false);});
 }
 // hübsche Status-Symbole (Inline-SVG, currentColor) für die Verbindungsanzeige im Kopf
 var CONN_ICON={
   cloud:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 18a4 4 0 01-.5-7.97 5.5 5.5 0 0110.6-1.45A3.75 3.75 0 0117 18z"/><path d="M9.6 13.8l1.8 1.8 3.2-3.4"/></svg>',
   server:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="7" rx="1.5"/><rect x="3" y="13" width="18" height="7" rx="1.5"/><path d="M7 7.5h.01M7 16.5h.01"/></svg>',
   local:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="7" y="2.5" width="10" height="19" rx="2.5"/><path d="M11 18.5h2"/></svg>'
 };
 function setConn(ok){
   var el=document.getElementById("connState");
   var k=MODE==="cloud"?"cloud":(MODE==="server"?"server":"local");
   var lab=MODE==="cloud"?"Cloud":(MODE==="server"?"Server – geteilt":"Lokal – dieses Gerät");
   if(el){el.className="conn "+(ok?"on":"off");el.innerHTML=CONN_ICON[k]+"<span>"+lab+"</span>";el.title=ok?"Online verbunden – Daten werden für alle geteilt.":"Kein Online-Speicher verbunden. Daten nur auf diesem Gerät (Reiter „Daten“).";}
   var d=document.getElementById("connData");if(d)renderDataConn();
 }
 function rerenderCurrent(){
   updateBadge();
   if(typeof initFilters==="function")initFilters(); // Filter-Optionen nach Daten-Sync aktualisieren
   if(curView==="dashboard")renderDashboard();
   else if(curView==="list")renderList();
   else if(curView==="leads")renderLeads();
   else if(curView==="detail"&&curId&&byId(curId)){
     if(modal&&modal.classList.contains("open"))return;
     if(document.activeElement&&document.activeElement.closest&&document.activeElement.closest("#view-detail"))return;
     if((byId(curId).updated||0)===_detUpd)return; // unveraendert -> NICHT neu aufbauen (sonst blinkt die Karte beim 30s-Sync)
     openDetail(curId);
   }
   if(curView==="data")renderDataConn();
 }

 /* gespeicherte Angebote des Konfigurators lesen (read-only) */
 function loadOffers(){try{var o=JSON.parse(localStorage.getItem(CFG_KEY)||"{}");return o||{};}catch(e){return {};}}

 /* ---------- Helfer ---------- */
 function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c];});}
 function initials(n){n=(n||"").trim();if(!n)return "?";var p=n.split(/\s+/);return ((p[0][0]||"")+(p.length>1?p[p.length-1][0]:"")).toUpperCase();}
 function fullName(c){var n=[c.vorname,c.nachname].filter(Boolean).join(" ").trim();return n;}
 function displayName(c){return c.firma||fullName(c)||"(ohne Namen)";}
 // ---- Outlook/E-Mail (mailto) + Kalender (.ics) ----
 function mailGreeting(c){var nn=c.nachname||"",a=c.anrede||"";
   if(nn){if(/frau/i.test(a))return "Sehr geehrte Frau "+nn+",";if(/herr/i.test(a))return "Sehr geehrter Herr "+nn+",";return "Guten Tag "+nn+",";}
   return "Sehr geehrte Damen und Herren,";}
 function buildMailto(c){
   var who=(CUR&&CUR.n)?CUR.n:"";
   var sig="\n\nMit freundlichen Grüßen\n"+(who?who+"\n":"")+"Alzinger Maschinenbau";
   var body=mailGreeting(c)+"\n\n"+sig;
   return "mailto:"+encodeURIComponent(c.mail||"")+"?subject="+encodeURIComponent("Alzinger Maschinenbau – Sternsiebanlage Lepton 5100")+"&body="+encodeURIComponent(body);
 }
 function icsEsc(s){return String(s||"").replace(/\\/g,"\\\\").replace(/;/g,"\\;").replace(/,/g,"\\,").replace(/\r?\n/g,"\\n");}
 function icsDownload(c,fu){
   if(!fu||!fu.due)return;
   function z(n){return n<10?"0"+n:""+n;}
   function fmt(d){return d.getUTCFullYear()+z(d.getUTCMonth()+1)+z(d.getUTCDate())+"T"+z(d.getUTCHours())+z(d.getUTCMinutes())+z(d.getUTCSeconds())+"Z";}
   var dt=new Date(fu.due),who=displayName(c);
   var summ="Lepton: "+(fu.note||"Wiedervorlage")+" – "+who;
   var desc=["Kontakt: "+who,c.tel?("Tel: "+c.tel):"",c.mobil?("Mobil: "+c.mobil):"",c.mail?("E-Mail: "+c.mail):"",fu.note?("Notiz: "+fu.note):""].filter(Boolean).join("\n");
   var ics=["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Alzinger Maschinenbau//CRM//DE","CALSCALE:GREGORIAN","METHOD:PUBLISH","BEGIN:VEVENT","UID:amb-"+c.id+"-"+dt.getTime()+"@alzinger-maschinenbau.de","DTSTAMP:"+fmt(new Date()),"DTSTART:"+fmt(dt),"DTEND:"+fmt(new Date(dt.getTime()+1800000)),"SUMMARY:"+icsEsc(summ),"DESCRIPTION:"+icsEsc(desc),"BEGIN:VALARM","ACTION:DISPLAY","DESCRIPTION:"+icsEsc(summ),"TRIGGER:-PT30M","END:VALARM","END:VEVENT","END:VCALENDAR"].join("\r\n");
   var blob=new Blob([ics],{type:"text/calendar;charset=utf-8"}),url=URL.createObjectURL(blob);
   var a=document.createElement("a");a.href=url;a.download=(who.replace(/[^0-9A-Za-zÄÖÜäöüß]+/g,"_")||"Termin")+".ics";document.body.appendChild(a);a.click();a.remove();
   setTimeout(function(){URL.revokeObjectURL(url);},15000);
 }
 // Einzelne Firma per KI nachschlagen und fehlende Felder ergänzen (Straße, PLZ, Tel, GF …).
 // Überschreibt NICHTS – füllt nur leere Felder. Nutzt dieselbe KI-Suche wie die Lead-Suche.
 function enrichContactAI(c,btn){
   if(!aiReady()||!c||!c.firma)return;
   var old=btn?btn.innerHTML:"";if(btn){btn.disabled=true;btn.textContent="KI sucht Details … (~1–2 Min)";}
   function restore(){if(btn){btn.disabled=false;btn.innerHTML=old;}}
   var wo=[c.ort,landLabel(c.land)].filter(Boolean).join(", ")||c.land||"";
   apiAi(c.firma,wo||c.firma).then(function(leads){
     var nrm=function(s){return String(s||"").toLowerCase().replace(/[^a-z0-9]/g,"");};
     var target=nrm(c.firma),best=null;
     (leads||[]).forEach(function(l){if(best)return;var n=nrm(l.firma||l.name);if(n&&(n.indexOf(target)>=0||target.indexOf(n)>=0))best=l;});
     if(!best&&leads&&leads.length)best=leads[0];
     if(!best){restore();alert("Die KI hat zu „"+c.firma+"“ keine zusätzlichen Daten gefunden.");return;}
     var map={strasse:best.strasse,plz:best.plz,ort:best.ort,tel:best.tel,mail:best.email,web:best.web,gf:best.geschaeftsfuehrer,bl:best.betriebsleiter,menge:best.jahresmenge,sieb:best.siebtechnik,news:best.news};
     var changed=[];Object.keys(map).forEach(function(k){var v=map[k]&&String(map[k]).trim();if(v&&!String(c[k]||"").trim()){c[k]=v;changed.push(k);}});
     if(!changed.length){restore();alert("Keine neuen Angaben gefunden – die vorhandenen Felder bleiben unverändert.");return;}
     c.lat=null;c.lon=null; // Adresse geändert -> Standort beim nächsten Kartenaufruf neu bestimmen
     c.updated=Date.now();saveContact(c);openDetail(c.id);
   }).catch(function(e){restore();alert("KI-Abfrage fehlgeschlagen: "+String((e&&e.message)||e));});
 }
 function pad(n){return n<10?"0"+n:""+n;}
 function todayStr(){var d=new Date();return d.getFullYear()+"-"+pad(d.getMonth()+1)+"-"+pad(d.getDate());}
 function nowLocalInput(){var d=new Date();return d.getFullYear()+"-"+pad(d.getMonth()+1)+"-"+pad(d.getDate())+"T"+pad(d.getHours())+":"+pad(d.getMinutes());}
 function fmtDate(ts){if(!ts)return "";var d=new Date(ts);return pad(d.getDate())+"."+pad(d.getMonth()+1)+"."+d.getFullYear();}
 function fmtDateTime(ts){if(!ts)return "";var d=new Date(ts);return pad(d.getDate())+"."+pad(d.getMonth()+1)+"."+d.getFullYear()+" "+pad(d.getHours())+":"+pad(d.getMinutes());}
 function relDays(ts){var d=Math.round((startOfDay(ts)-startOfDay(Date.now()))/86400000);return d;}
 function startOfDay(ts){var d=new Date(ts);d.setHours(0,0,0,0);return d.getTime();}
 function dueClass(ts){var d=relDays(ts);if(d<0)return "over";if(d===0)return "today";return "soon";}
 function dueLabel(ts){var d=relDays(ts);if(d<0)return "überfällig ("+(-d)+"T)";if(d===0)return "heute";if(d===1)return "morgen";return "in "+d+" Tagen";}
 function lastActivityTs(c){var t=c.updated||c.created||0;(c.activities||[]).forEach(function(a){if(a.date>t)t=a.date;});return t;}

 /* ---------- Navigation ---------- */
 var curView="dashboard";
 function show(view){
   if(view==="data"&&!isAdmin())view="dashboard"; // Daten-Reiter nur fuer Admins
   curView=view;
   var vs=document.querySelectorAll(".view");for(var i=0;i<vs.length;i++)vs[i].classList.remove("active");
   var el=document.getElementById("view-"+view);if(el)el.classList.add("active");
   var nb=document.querySelectorAll("#nav button");for(i=0;i<nb.length;i++)nb[i].classList.toggle("active",nb[i].getAttribute("data-view")===view);
   window.scrollTo(0,0);
   document.getElementById("fab").style.display=(view==="detail"||view==="form")?"none":"flex";
 }
 document.getElementById("nav").addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;var v=b.getAttribute("data-view");if(v){if(v==="dashboard")renderDashboard();if(v==="list")renderList();if(v==="leads")renderLeads();if(v==="data")renderAuswertung();show(v);}});
 // Dashboard-Kacheln klickbar -> direkt in die passende Kontaktliste springen.
 document.getElementById("stats").addEventListener("click",function(e){
   var s=e.target.closest("[data-go]");if(!s)return;var go=s.getAttribute("data-go");
   function set(id,val){var el=document.getElementById(id);if(el)el.value=val;}
   set("q","");set("fBL","");set("fLand","");set("fOwner","");
   if(go==="due"){set("fStatus","");set("fSort","due");}
   else if(go==="all"){set("fStatus","");set("fSort","updated");}
   else{set("fStatus",go);set("fSort","updated");}
   renderList();show("list");
 });

 /* ---------- Übersicht ---------- */
 function dueFollowups(){var out=[];DB.contacts.forEach(function(c){if(c.followup&&!c.followup.done&&c.followup.due){out.push(c);}});out.sort(function(a,b){return a.followup.due-b.followup.due;});return out;}
 function overdueOrToday(){return dueFollowups().filter(function(c){return relDays(c.followup.due)<=0;});}

 function renderDashboard(){
   var name=(CUR&&CUR.n)?CUR.n.split(" ")[0]:"";
   document.getElementById("greet").textContent=name?("Servus, "+name+"!"):"Übersicht";
   var st={lead:0,interessent:0,angebot:0,kunde:0,haendler:0,verloren:0};
   DB.contacts.forEach(function(c){if(st[c.status]!=null)st[c.status]++;});
   var fu=dueFollowups(),od=overdueOrToday();
   var stats=document.getElementById("stats");
   stats.innerHTML=
     '<div class="stat'+(od.length?' accent':'')+'" data-go="due" style="cursor:pointer" title="Fällige Rückrufe anzeigen"><div class="n">'+od.length+'</div><div class="l">Rückrufe fällig</div></div>'+
     '<div class="stat" data-go="all" style="cursor:pointer" title="Alle Kontakte"><div class="n">'+DB.contacts.length+'</div><div class="l">Kontakte</div></div>'+
     '<div class="stat s-lead" data-go="lead" style="cursor:pointer" title="Offene Leads"><div class="n">'+(st.lead+st.interessent)+'</div><div class="l">Offene Leads</div></div>'+
     '<div class="stat s-angebot" data-go="angebot" style="cursor:pointer" title="Offene Angebote"><div class="n">'+st.angebot+'</div><div class="l">Angebote offen</div></div>'+
     '<div class="stat s-kunde" data-go="kunde" style="cursor:pointer" title="Kunden"><div class="n">'+st.kunde+'</div><div class="l">Kunden</div></div>'+
     '<div class="stat s-haendler" data-go="haendler" style="cursor:pointer" title="Händlerkontakte"><div class="n">'+st.haendler+'</div><div class="l">Händler</div></div>';
   // Wiedervorlagen
   document.getElementById("fuCnt").textContent=fu.length;
   var fl=document.getElementById("fuList");
   if(!fu.length){fl.innerHTML='<div style="font-size:13px;color:var(--faint);padding:6px 0">Keine offenen Wiedervorlagen. Sauber! 👍</div>';}
   else{fl.innerHTML=fu.slice(0,12).map(function(c){
     var d=c.followup;
     return '<div class="crow" data-id="'+c.id+'" style="margin-bottom:8px">'+
       '<div class="av av-'+esc(c.status||"lead")+'">'+esc(initials(displayName(c)))+'</div>'+
       '<div class="mid"><div class="nm">'+esc(displayName(c))+'</div>'+
       '<div class="meta">'+(d.note?'<span>'+esc(d.note)+'</span>':'<span>Wiedervorlage</span>')+(c.tel?'<span class="flag">'+esc(c.tel)+'</span>':'')+'</div></div>'+
       '<div class="right"><span class="due '+dueClass(d.due)+'">'+dueLabel(d.due)+'</span>'+
       (c.tel?'<a class="btn sm" href="tel:'+esc(c.tel)+'" onclick="event.stopPropagation()">Anrufen</a>':'')+
       '</div></div>';
   }).join("");}
   // letzte Aktivitäten
   var acts=[];
   DB.contacts.forEach(function(c){(c.activities||[]).forEach(function(a){acts.push({c:c,a:a});});});
   acts.sort(function(x,y){return y.a.date-x.a.date;});
   var rc=document.getElementById("recent");
   if(!acts.length){rc.innerHTML='<div style="font-size:13px;color:var(--faint);padding:6px 0">Noch keine Aktivitäten erfasst.</div>';}
   else{rc.innerHTML=acts.slice(0,10).map(function(o){
     return '<div class="crow" data-id="'+o.c.id+'" style="margin-bottom:8px;padding:11px 12px">'+
       '<div class="mid"><div class="nm" style="font-size:14px">'+esc(actLabel(o.a.type))+' · '+esc(displayName(o.c))+'</div>'+
       '<div class="meta"><span>'+fmtDateTime(o.a.date)+'</span>'+(o.a.by?'<span>'+esc(o.a.by)+'</span>':'')+(o.a.note?'<span>'+esc(o.a.note.slice(0,60))+'</span>':'')+'</div></div></div>';
   }).join("");}
   // Posteingang: eingegangene E-Mails (mailin), die noch nicht "gelesen" markiert sind, neueste zuerst
   var inbox=[];
   DB.contacts.forEach(function(c){(c.activities||[]).forEach(function(a){if(a.type==="mailin"&&!a.seen)inbox.push({c:c,a:a});});});
   inbox.sort(function(x,y){return y.a.date-x.a.date;});
   var ic=document.getElementById("inboxCard"),il=document.getElementById("inboxList");
   ic.style.display="";document.getElementById("inboxCnt").textContent=inbox.length;
   if(!inbox.length){
     il.innerHTML='<div style="font-size:13px;color:var(--faint);padding:6px 0">Noch keine eingegangenen E-Mails. Tippe oben auf <b>„E-Mails abrufen"</b>, um deine Outlook-Mails zu laden.</div>';
   } else {
     il.innerHTML=inbox.slice(0,15).map(function(o){
       var subj="",m=(o.a.note||"").match(/^Betreff:\s*(.+)$/m);if(m)subj=m[1].trim();
       var prev=(o.a.note||"").replace(/^Betreff:.*\n?/,"").trim().slice(0,80);
       return '<div class="crow" data-id="'+o.c.id+'" data-inboxact="'+o.a.id+'" style="margin-bottom:8px;padding:11px 12px">'+
         '<div class="av av-'+esc(o.c.status||"lead")+'">'+esc(initials(displayName(o.c)))+'</div>'+
         '<div class="mid"><div class="nm" style="font-size:14px">'+esc(displayName(o.c))+(subj?' · <span style="font-weight:600">'+esc(subj)+'</span>':'')+'</div>'+
         '<div class="meta"><span>'+fmtDateTime(o.a.date)+'</span>'+(prev?'<span>'+esc(prev)+'</span>':'')+'</div></div>'+
         '<div class="right"><button class="btn sm" data-inboxreply="'+o.c.id+'|'+o.a.id+'" title="Mit KI antworten">KI-Antwort</button>'+
         '<button class="btn sm ghost" data-inboxseen="'+o.c.id+'|'+o.a.id+'" title="Als gelesen markieren (aus Posteingang entfernen)">✓</button></div></div>';
     }).join("");
   }
   updateBadge();
 }
 function updateBadge(){var n=overdueOrToday().length;var b=document.getElementById("navBadge");if(n>0){b.textContent=n;b.classList.remove("hidden");}else b.classList.add("hidden");}

 /* ---------- Kontaktliste ---------- */
 function fillSelect(sel,opts,all){sel.innerHTML='<option value="">'+all+'</option>'+opts.map(function(o){return '<option value="'+o[0]+'">'+esc(o[1])+'</option>';}).join("");}
 // Vertriebler-Filter = internes Team (USERS ohne Händler, hd:1) + alle in den Kontakten vorkommenden Betreuer.
 function ownerOpts(){var seen={},out=[];USERS.forEach(function(u){if(u.n&&!u.hd&&!seen[u.n]){seen[u.n]=1;out.push([u.n,u.n]);}});DB.contacts.forEach(function(c){if(c.owner&&!seen[c.owner]){seen[c.owner]=1;out.push([c.owner,c.owner]);}});return out;}
 // Länder-Filter = bekannte Liste + alle in den Kontakten tatsächlich vorkommenden Codes
 function landOpts(){var seen={},out=[];LANDS.forEach(function(l){seen[l[0]]=1;out.push(l);});DB.contacts.forEach(function(c){var cc=(c.land||"").toUpperCase();if(cc&&!seen[cc]){seen[cc]=1;out.push([cc,landLabel(cc)]);}});return out;}
 // Bundesländer (DE). contactBundesland() nimmt das gesetzte Feld oder leitet es aus der Notiz ab
 // (z. B. importierte Leads haben das Bundesland in der Notiz) -> Bestandsdaten sind sofort filterbar.
 var BL=["Baden-Württemberg","Bayern","Berlin","Brandenburg","Bremen","Hamburg","Hessen","Mecklenburg-Vorpommern","Niedersachsen","Nordrhein-Westfalen","Rheinland-Pfalz","Saarland","Sachsen","Sachsen-Anhalt","Schleswig-Holstein","Thüringen"];
 var BLM=BL.slice().sort(function(a,b){return b.length-a.length;}); // längere zuerst (Sachsen-Anhalt vor Sachsen)
 function blFromText(t){t=String(t||"");for(var i=0;i<BLM.length;i++){if(t.indexOf(BLM[i])>=0)return BLM[i];}return "";}
 function contactBundesland(c){return (c&&c.bundesland)||blFromText(c&&c.notiz)||"";}
 function blOpts(){var seen={};DB.contacts.forEach(function(c){var b=contactBundesland(c);if(b)seen[b]=1;});return BL.filter(function(b){return seen[b];}).map(function(b){return [b,b];});}
 // Auswahl bewahren, damit initFilters() jederzeit erneut laufen kann (nach Import/Cloud-Sync).
 function refillSel(id,opts,all){var s=document.getElementById(id);if(!s)return;var cur=s.value;fillSelect(s,opts,all);if(cur)s.value=cur;}
 function initFilters(){
   refillSel("fStatus",STATUS,"Alle Status");
   refillSel("fLand",landOpts(),"Alle Länder");
   refillSel("fBL",blOpts(),"Alle Bundesländer");
   refillSel("fOwner",ownerOpts(),"Alle Vertriebler");
   refillSel("fLeadLand",landOpts(),"Alle Länder");
 }
 function matchQ(c,q){
   if(!q)return true;
   // Volltext: ALLE Felder + kompletter Verlauf (Aktivitaeten/Notizen) + Wiedervorlage
   var hay=[c.firma,c.firma2,c.anrede,c.vorname,c.nachname,c.strasse,c.plz,c.ort,contactBundesland(c),landLabel(c.land),c.tel,c.mobil,c.mail,c.web,c.ustid,c.quelle,c.owner,c.notiz,c.news,statusLabel(c.status)];
   (c.activities||[]).forEach(function(a){if(a){hay.push(a.note,a.offerNr,a.by,actLabel(a.type));}});
   if(c.followup&&c.followup.note)hay.push(c.followup.note);
   hay=hay.join(" ").toLowerCase();
   // mehrere Begriffe -> ALLE muessen vorkommen (UND-Suche)
   var terms=q.toLowerCase().split(/\s+/).filter(Boolean);
   for(var i=0;i<terms.length;i++){if(hay.indexOf(terms[i])<0)return false;}
   return true;
 }
 var _searchTerms=[];
 // Zeigt bei einem Suchtreffer, WO gefunden wurde (Textausschnitt + Quelle), wenn der Treffer nicht im sichtbaren Feld steht.
 function hitSnippet(c){
   if(!_searchTerms.length)return "";
   function find(text,label){if(!text)return null;var s=String(text),low=s.toLowerCase();for(var i=0;i<_searchTerms.length;i++){var idx=low.indexOf(_searchTerms[i]);if(idx>=0)return {text:s,idx:idx,len:_searchTerms[i].length,label:label};}return null;}
   function render(h){var s=h.text,start=Math.max(0,h.idx-28);var pre=(start>0?"…":"")+s.slice(start,h.idx);var hit=s.slice(h.idx,h.idx+h.len);var end=h.idx+h.len+44;var post=s.slice(h.idx+h.len,end)+((end<s.length)?"…":"");return '<div class="hit"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg><span>'+esc(pre)+'<b>'+esc(hit)+'</b>'+esc(post)+' <span class="hit-w">· '+esc(h.label)+'</span></span></div>';}
   var acts=(c.activities||[]).slice().sort(function(a,b){return (b.date||0)-(a.date||0);});
   for(var i=0;i<acts.length;i++){var h=find(acts[i].note,actLabel(acts[i].type)+" · "+fmtDate(acts[i].date));if(h)return render(h);}
   var fields=[[c.notiz,"Notiz"],[c.web,"Web"],[c.mail,"E-Mail"],[c.quelle,"Quelle"],[c.owner,"Betreuer"],[contactBundesland(c),"Bundesland"],[c.ustid,"USt-IdNr."],[c.followup&&c.followup.note,"Wiedervorlage"]];
   for(var j=0;j<fields.length;j++){var h2=find(fields[j][0],fields[j][1]);if(h2)return render(h2);}
   return ""; // Treffer steht in einem sichtbaren Feld (Firma/Ort/Tel) -> kein Extra-Hinweis noetig
 }
 function contactRow(c){
   var due=(c.followup&&!c.followup.done&&c.followup.due)?'<span class="due '+dueClass(c.followup.due)+'">'+dueLabel(c.followup.due)+'</span>':'';
   var sub=fullName(c);var loc=[c.strasse,[c.plz,c.ort].filter(Boolean).join(" ")].filter(Boolean).join(", ");
   return '<div class="crow" data-id="'+c.id+'">'+
     '<div class="av av-'+esc(c.status||"lead")+'">'+esc(initials(displayName(c)))+'</div>'+
     '<div class="mid"><div class="nm">'+esc(displayName(c))+'</div>'+
     '<div class="meta">'+
       (c.firma&&sub?'<span>'+esc(sub)+'</span>':'')+
       (c.land?'<span class="flag">'+esc(c.land)+'</span>':'')+
       (loc?'<span>'+esc(loc)+'</span>':'')+
       (c.tel?'<span>'+esc(c.tel)+'</span>':'')+
     '</div>'+hitSnippet(c)+'</div>'+
     '<div class="right"><span class="pill '+esc(c.status||"lead")+'">'+esc(statusLabel(c.status))+'</span>'+due+'</div>'+
   '</div>';
 }
 function renderList(){
   var q=document.getElementById("q").value.trim();
   _searchTerms=q?q.toLowerCase().split(/\s+/).filter(Boolean):[]; // fuer die Treffer-Anzeige in der Liste
   var fs=document.getElementById("fStatus").value,fl=document.getElementById("fLand").value,fbl=document.getElementById("fBL").value,fo=document.getElementById("fOwner").value,so=document.getElementById("fSort").value;
   var arr=DB.contacts.filter(function(c){return matchQ(c,q)&&(!fs||c.status===fs)&&(!fl||c.land===fl)&&(!fbl||contactBundesland(c)===fbl)&&(!fo||c.owner===fo);});
   arr.sort(function(a,b){
     if(so==="name")return displayName(a).localeCompare(displayName(b),"de");
     if(so==="created")return (b.created||0)-(a.created||0);
     if(so==="due"){var da=(a.followup&&!a.followup.done&&a.followup.due)||9e15,db=(b.followup&&!b.followup.done&&b.followup.due)||9e15;return da-db;}
     return lastActivityTs(b)-lastActivityTs(a);
   });
   document.getElementById("listSub").textContent=arr.length+" von "+DB.contacts.length+" Kontakten";
   lastListArr=arr;
   var el=document.getElementById("clist");
   if(!arr.length){el.innerHTML=emptyState(DB.contacts.length?"Keine Treffer für diese Filter.":"Noch keine Kontakte. Lege den ersten an (+ unten rechts).");}
   else el.innerHTML=arr.map(contactRow).join("");
   if(cMapOpen)showContactsMap();
 }
 function emptyState(msg){return '<div class="empty"><svg viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 00-4-4H7a4 4 0 00-4 4v2"/><circle cx="9.5" cy="8" r="3.5"/><path d="M19 8v6M22 11h-6"/></svg><div>'+esc(msg)+'</div></div>';}

 /* ---------- Kontakte-Karte (Standorte mit Fahnen-Markern) ---------- */
 var lastListArr=[],cMapOpen=false,_cmap=null,_cmarkers=null,_geoBusy=false;
 // SVG-Fahne (kein Emoji/PNG) -> rendert identisch auf Windows, Mac, iPhone.
 function flagIcon(L){return L.divIcon({className:"flag-mark",html:'<svg width="22" height="27" viewBox="0 0 22 27" style="filter:drop-shadow(0 1px 1.5px rgba(0,0,0,.45))"><line x1="3" y1="1" x2="3" y2="26" stroke="#2b2b2b" stroke-width="2.2"/><path d="M3 1.5 H19 L15 6.5 L19 11.5 H3 Z" fill="#c00000"/></svg>',iconSize:[22,27],iconAnchor:[3,26],popupAnchor:[8,-22]});}
 function addContactMarker(L,c){
   if(!_cmarkers||c.lat==null||c.lon==null)return;
   var loc=[c.plz,c.ort].filter(Boolean).join(" ");
   var gmq=(c.lat!=null&&c.lon!=null)?(c.lat+","+c.lon):encodeURIComponent([c.strasse,[c.plz,c.ort].filter(Boolean).join(" "),landLabel(c.land)].filter(Boolean).join(", "));
   var pop='<b>'+esc(displayName(c))+'</b>'+(loc?'<br>'+esc(loc):'')+(c.land?' ('+esc(c.land)+')':'')+
     '<div style="margin-top:7px;display:flex;gap:6px;flex-wrap:wrap">'+
       '<button data-cid="'+c.id+'" style="border:0;background:#c00000;color:#fff;border-radius:6px;padding:5px 9px;font:600 12px sans-serif;cursor:pointer">Öffnen</button>'+
       '<a href="https://www.google.com/maps?q='+gmq+'" target="_blank" rel="noopener" style="border:1px solid #c00000;color:#c00000;border-radius:6px;padding:5px 9px;font:600 12px sans-serif;text-decoration:none">In Google Maps</a>'+
     '</div>';
   L.marker([c.lat,c.lon],{icon:flagIcon(L)}).addTo(_cmarkers).bindPopup(pop);
 }
 // Nominatim-Abfrage mit Wiederholung bei Drosselung (429) / Netz-Aussetzern.
 function nomFetch(q,tries){
   tries=tries||0;
   return fetch("https://nominatim.openstreetmap.org/search?format=json&limit=1&accept-language=de&q="+encodeURIComponent(q),{headers:{"Accept":"application/json"}})
     .then(function(r){
       if((r.status===429||r.status===503)&&tries<3){return new Promise(function(res){setTimeout(res,1500*(tries+1));}).then(function(){return nomFetch(q,tries+1);});}
       if(!r.ok)throw new Error("nom "+r.status);return r.json();
     },function(e){if(tries<3){return new Promise(function(res){setTimeout(res,1500*(tries+1));}).then(function(){return nomFetch(q,tries+1);});}throw e;});
 }
 function geocodeContact(c){
   var land=landLabel(c.land);
   // Stufenweise: genaue Adresse -> PLZ+Ort+Land -> Ort+Land. Erhoeht die Trefferquote deutlich.
   var qs=[];
   [[c.strasse,[c.plz,c.ort].filter(Boolean).join(" "),land],[[c.plz,c.ort].filter(Boolean).join(" "),land],[c.ort,land]].forEach(function(p){var q=p.filter(Boolean).join(", ").trim();if(q&&qs.indexOf(q)<0)qs.push(q);});
   if(!qs.length)return Promise.reject();
   function tryQ(i){
     if(i>=qs.length)return Promise.reject();
     return nomFetch(qs[i])
       .then(function(a){if(a&&a.length)return {lat:parseFloat(a[0].lat),lon:parseFloat(a[0].lon)};return tryQ(i+1);})
       .catch(function(){return tryQ(i+1);});
   }
   return tryQ(0);
 }
 function geocodePending(L,list,i){
   if(i>=list.length||!cMapOpen){_geoBusy=false;return;}
   var c=list[i];
   geocodeContact(c).then(function(p){c.lat=p.lat;c.lon=p.lon;cacheSave();if(cMapOpen)addContactMarker(L,c);}).catch(function(){}).then(function(){setTimeout(function(){geocodePending(L,list,i+1);},600);});
 }
 function showContactsMap(){
   var div=document.getElementById("cMap");
   ensureLeaflet().then(function(L){
     if(!_cmap){_cmap=L.map(div).setView([47.5,9],5);addSat(L,_cmap);}
     if(_cmarkers)_cmarkers.remove();
     _cmarkers=L.layerGroup().addTo(_cmap);
     var bounds=[],pending=[];
     lastListArr.forEach(function(c){
       if(c.lat!=null&&c.lon!=null){addContactMarker(L,c);bounds.push([c.lat,c.lon]);}
       else if(c.ort||c.strasse||c.plz){pending.push(c);}
     });
     if(bounds.length)_cmap.fitBounds(bounds,{padding:[28,28],maxZoom:12});
     setTimeout(function(){try{_cmap.invalidateSize();}catch(e){}},130);
     if(pending.length&&!_geoBusy){_geoBusy=true;geocodePending(L,pending,0);}
   }).catch(function(){div.style.display="none";});
 }
 document.getElementById("mapToggle").onclick=function(){
   cMapOpen=!cMapOpen;
   document.getElementById("cMap").style.display=cMapOpen?"block":"none";
   document.getElementById("clist").style.display=cMapOpen?"none":"";
   this.classList.toggle("primary",cMapOpen);
   this.innerHTML=cMapOpen
     ?'<svg viewBox="0 0 24 24" style="width:15px;height:15px;stroke:currentColor;fill:none;stroke-width:1.7"><path d="M4 6h16M4 12h16M4 18h16"/></svg>Liste'
     :'<svg viewBox="0 0 24 24" style="width:15px;height:15px;stroke:currentColor;fill:none;stroke-width:1.7"><path d="M9 4L3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/></svg>Karte';
   if(cMapOpen)showContactsMap();
 };
 document.getElementById("cMap").addEventListener("click",function(e){var b=e.target.closest("[data-cid]");if(b)openDetail(b.getAttribute("data-cid"));});

 /* ---------- Leads ---------- */
 function renderLeads(){
   var q=document.getElementById("qLead").value.trim();var fl=document.getElementById("fLeadLand").value;
   var arr=DB.contacts.filter(function(c){return (c.status==="lead"||c.status==="interessent")&&matchQ(c,q)&&(!fl||c.land===fl);});
   arr.sort(function(a,b){return lastActivityTs(b)-lastActivityTs(a);});
   var el=document.getElementById("leadlist");
   if(!arr.length){el.innerHTML=emptyState("Keine offenen Leads. Oben im Internet suchen, manuell anlegen oder per CSV importieren (Reiter „Daten“).");return;}
   el.innerHTML=arr.map(contactRow).join("");
 }

 /* ---------- Online-Lead-Suche (OpenStreetMap – kostenlos, kein Server, nur online) ---------- */
 var lastQuery="", searchLand="DE", osmEls=[], osmLast={}, _aiErr="", _searchSrc="", _lastWas="", _lastWo="", _autoMore=0;
 function osmStatus(html){var e=document.getElementById("osmStatus");if(e)e.innerHTML=html;}
 function osmLoading(msg){osmStatus('<span class="spin"></span>'+msg);var m=document.getElementById("osmMap");if(m)m.style.display="none";var b=document.getElementById("osmResults");if(b)b.innerHTML='<div class="skel"></div><div class="skel" style="opacity:.7"></div><div class="skel" style="opacity:.45"></div>';}
 function osmClearResults(){var b=document.getElementById("osmResults");if(b)b.innerHTML="";var m=document.getElementById("osmMap");if(m)m.style.display="none";}
 function osmGeocode(place){
   var url="https://nominatim.openstreetmap.org/search?format=json&addressdetails=1&limit=1&accept-language=de&q="+encodeURIComponent(place);
   return fetch(url,{headers:{"Accept":"application/json"}}).then(function(r){if(!r.ok)throw new Error("geo");return r.json();}).then(function(a){if(!a||!a.length)throw new Error("noplace");return a[0];});
 }
 // Reverse-Geocoding: Koordinaten -> Land/Ort (fuer Anzeige bei der Umkreissuche).
 function osmReverse(lat,lon){
   return fetch("https://nominatim.openstreetmap.org/reverse?format=json&zoom=10&accept-language=de&lat="+lat+"&lon="+lon,{headers:{"Accept":"application/json"}})
     .then(function(r){if(!r.ok)throw new Error("rev");return r.json();})
     .then(function(j){var a=(j&&j.address)||{};return {cc:a.country_code||"",ort:a.city||a.town||a.village||a.municipality||a.county||a.state||""};});
 }
 function osmAreaRef(g){
   if(g.osm_type==="relation")return {area:3600000000+(+g.osm_id)};
   if(g.osm_type==="way")return {area:2400000000+(+g.osm_id)};
   return {around:[20000,g.lat,g.lon]};
 }
 // Begriff -> OSM-Filter. Schnelle TAG-Filter zuerst (laufen auch landesweit flott),
 // langsame Namens-Regex nur EINMAL gebündelt am Ende.
 function osmFilters(term){
   var t=(term||"").toLowerCase(),tags=[],names=[];
   if(/kompost|bio(m[uü]ll|abf|gut|ton)|gr[uü]n(gut|schnitt|abf)|gaerrest|gärrest/.test(t)){tags.push('nwr["industrial"="composting"]');tags.push('nwr["amenity"="recycling"]["recycling:organic"="yes"]');names.push("kompost");names.push("bioabfall");}
   if(/recycl|wertstoff|wertstoffhof/.test(t)){tags.push('nwr["amenity"="recycling"]["recycling_type"="centre"]');}
   if(/entsorg|abfall|müll|mull|deponie|landfill/.test(t)){tags.push('nwr["landuse"="landfill"]');tags.push('nwr["amenity"="waste_transfer_station"]');tags.push('nwr["amenity"="waste_disposal"]');names.push("entsorg");}
   if(/schrott|scrap|metall/.test(t)){tags.push('nwr["industrial"="scrap_yard"]');}
   if(/erden|substrat|humus|mutterboden|blumenerde/.test(t)){names.push("erden");names.push("substrat");names.push("humus");}
   if(/steinbruch|schotter|kies|sand|quarry|brech|baustoff/.test(t)){tags.push('nwr["landuse"="quarry"]');names.push("schotter");}
   if(/biogas|gärrest|garrest/.test(t)){names.push("biogas");}
   if(/garten|landschaft|galabau/.test(t)){tags.push('nwr["shop"="garden_centre"]');names.push("garten");names.push("landschaft");}
   if(/container/.test(t)){names.push("container");}
   if(!tags.length&&!names.length){var word=(t.replace(/[^a-zäöüß ]/g," ").trim().split(/\s+/)[0]||"");if(word.length>=3)names.push(word);}
   var f=tags.slice();
   if(names.length)f.push('nwr["name"~"'+names.join("|")+'",i]');
   return f.length?f:['nwr["name"~"x",i]'];
 }
 function osmBuildQuery(ref,filters){
   var lines=filters.map(function(fl){return ref.area?(fl+"(area.a);"):(fl+"(around:"+ref.around[0]+","+ref.around[1]+","+ref.around[2]+");");}).join("\n  ");
   return "[out:json][timeout:90];\n"+(ref.area?("area("+ref.area+")->.a;\n"):"")+"(\n  "+lines+"\n);\nout center 400;";
 }
 // Zwei Overpass-Server: bei Fehler/Überlast automatisch auf den zweiten ausweichen.
 var OVERPASS=["https://overpass-api.de/api/interpreter","https://overpass.kumi.systems/api/interpreter"];
 function osmOverpass(q,i){
   i=i||0;
   return fetch(OVERPASS[i],{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:"data="+encodeURIComponent(q)})
     .then(function(r){if(!r.ok)throw new Error("overpass "+r.status);return r.json();}).then(function(j){return j.elements||[];})
     .catch(function(e){if(i+1<OVERPASS.length)return osmOverpass(q,i+1);throw e;});
 }
 function osmAddr(t){return {strasse:[t["addr:street"],t["addr:housenumber"]].filter(Boolean).join(" "),plz:t["addr:postcode"]||"",ort:t["addr:city"]||t["addr:town"]||t["addr:village"]||t["addr:municipality"]||""};}
 // Robuster Dubletten-Schluessel: Umlaute, Rechtsformen (GmbH/AG/KG/Co …), Satzzeichen
 // und Leerzeichen werden vereinheitlicht -> "Kompost Bayern GmbH" == "kompost-bayern".
 function dnorm(s){var x=String(s||"").toLowerCase().replace(/ä/g,"ae").replace(/ö/g,"oe").replace(/ü/g,"ue").replace(/ß/g,"ss");
   x=x.replace(/[^a-z0-9]+/g," ");
   x=x.replace(/\b(gmbh|mbh|ag|kg|kgaa|ohg|ug|gbr|se|ek|ev|co|ltd|inc|llc)\b/g," ");
   return x.replace(/\s+/g," ").trim();}
 function dedupKey(firma,ort){return dnorm(firma)+"|"+dnorm(ort);}
 function osmExisting(){var s={};DB.contacts.forEach(function(c){if(c._osm)s[c._osm]=c.id;if(c.firma){s[((c.firma||"")+"|"+(c.ort||"")).toLowerCase()]=c.id;s["dk:"+dedupKey(c.firma,c.ort)]=c.id;}});return s;}
 function osmHave(ex,key,name,ort){return ex[key]||ex[((name||"")+"|"+(ort||"")).toLowerCase()]||ex["dk:"+dedupKey(name,ort)];}
 function osmToContact(el){
   var t=el.tags||{},a=osmAddr(t);var lat=el.lat||(el.center&&el.center.lat),lon=el.lon||(el.center&&el.center.lon);
   return {id:uid(),created:Date.now(),updated:Date.now(),status:"lead",
     firma:t.name||"",firma2:t.operator||"",anrede:"",vorname:"",nachname:"",
     lat:(lat!=null?+lat:null),lon:(lon!=null?+lon:null),
     strasse:a.strasse,plz:a.plz,ort:a.ort,land:(t._land||searchLand),
     tel:t["contact:phone"]||t.phone||"",mobil:"",mail:t["contact:email"]||t.email||"",
     web:t["contact:website"]||t.website||"",ustid:"",owner:(CUR&&CUR.n)||"",
     gf:t._gf||"",bl:t._bl||"",menge:t._menge||"",sieb:t._sieb||"",news:t._news||"",
     quelle:(el.type==="ai"?"KI-Suche: ":"Karten-Suche: ")+lastQuery+(t._quelle?(" – "+t._quelle):""),
     notiz:(t.operator?("Betreiber: "+t.operator):""),
     activities:[],_osm:(el.type+"/"+el.id)};
 }
 // KI-Treffer in dieselbe Element-Form bringen wie OSM (damit Karten/Übernahme identisch funktionieren)
 function aiSlug(o,i){var b=((o.firma||o.name||"")+"-"+(o.ort||"")).toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/(^-|-$)/g,"");return b||("lead-"+i);}
 function aiToEl(o,i){return {type:"ai",id:aiSlug(o,i),lat:(o.lat!=null?+o.lat:null),lon:(o.lon!=null?+o.lon:null),
   tags:{name:o.firma||o.name||"","addr:street":o.strasse||"","addr:postcode":o.plz||"","addr:city":o.ort||"","contact:phone":o.tel||"","contact:email":o.email||"",website:o.web||"",_land:(o.land||searchLand||"DE"),_quelle:o.quelle||"",_gf:o.geschaeftsfuehrer||"",_bl:o.betriebsleiter||"",_menge:o.jahresmenge||"",_sieb:o.siebtechnik||"",_news:o.news||""}};}
 function guessLand(wo){var t=(wo||"").toLowerCase();if(/schweiz|switzerland|\bch\b/.test(t))return "CH";if(/österreich|oesterreich|austria|\bat\b/.test(t))return "AT";if(/italien|italy|südtirol|suedtirol/.test(t))return "IT";if(/frankreich|france/.test(t))return "FR";if(/polen|poland/.test(t))return "PL";if(/niederlande|holland/.test(t))return "NL";return "DE";}
 function osmMake(key){var el=osmLast[key];if(!el)return null;
   // Dubletten-Schutz: gibt es den Kontakt schon, den vorhandenen zurueckgeben (NICHT neu anlegen).
   var t=el.tags||{},a=osmAddr(t),exist=osmHave(osmExisting(),key,t.name,a.ort);
   if(exist){var c0=byId(exist);if(c0)return c0;}
   var c=osmToContact(el);DB.contacts.push(c);return c;}
 function renderOsm(els){
   osmEls=els;osmLast={};els.forEach(function(el){osmLast[el.type+"/"+el.id]=el;});
   var box=document.getElementById("osmResults");
   if(!els.length){osmStatus('Keine Treffer für „'+esc(lastQuery)+'“. Anderen Begriff (z. B. „Recycling“, „Erden“) oder andere Region versuchen.');box.innerHTML="";return;}
   var ex=osmExisting(),anyNew=false;
   osmStatus(els.length+' Treffer'+(_searchSrc?(' <b>('+_searchSrc+')</b>'):'')+' für „'+esc(lastQuery)+'“ – prüfen und übernehmen:');
   box.innerHTML=els.map(function(el){
     var t=el.tags||{},a=osmAddr(t),loc=[a.plz,a.ort].filter(Boolean).join(" ");
     var key=el.type+"/"+el.id,have=osmHave(ex,key,t.name,a.ort);if(!have)anyNew=true;
     var web=t["contact:website"]||t.website;
     return '<div class="crow" style="cursor:pointer" data-rowkey="'+esc(key)+'" data-rowhave="'+esc(have||"")+'">'+
       '<div class="av" style="background:var(--gold)">'+esc(initials(t.name))+'</div>'+
       '<div class="mid"><div class="nm">'+esc(t.name)+'</div>'+
       '<div class="meta">'+(a.strasse?'<span>'+esc(a.strasse)+'</span>':'')+(loc?'<span>'+esc(loc)+'</span>':'')+
         ((t["contact:phone"]||t.phone)?'<span>'+esc(t["contact:phone"]||t.phone)+'</span>':'')+
         (web?'<span><a href="'+esc(/^https?:/.test(web)?web:"https://"+web)+'" target="_blank" rel="noopener" onclick="event.stopPropagation()">Web</a></span>':'')+
       '</div></div>'+
       '<div class="right">'+(have?'<button class="btn sm" data-openid="'+esc(have)+'">erfasst – öffnen</button>':'<button class="btn sm primary" data-osm="'+key+'">+ Lead</button>')+'</div>'+
     '</div>';
   }).join("")+(anyNew?'<button class="btn block" id="osmAddAll" style="margin-top:8px">Alle neuen als Leads übernehmen</button>':'')+
     (_searchSrc==="KI"?'<button class="btn block" id="osmMore" style="margin-top:8px;background:#fff;color:#c00000;border:1px solid #c00000">＋ Weitersuchen – weitere Firmen finden</button>':'');
   osmShowMap(els);
   geocodeOsmEls(els);
 }
 // KI-Treffer haben keine Koordinaten -> Adressen im Hintergrund geocoden (gedrosselt, max. 30),
 // damit sie nach und nach auf der Ergebnis-Karte erscheinen. Token bricht ab, wenn neu gesucht wird.
 var _geoTok=0;
 function geocodeOsmEls(els){
   _geoTok++;var tok=_geoTok;
   var pend=[];els.forEach(function(el){if((el.lat==null)&&el.tags&&el.tags.name)pend.push(el);});
   if(!pend.length)return;
   pend=pend.slice(0,30);var i=0;
   function next(){
     if(tok!==_geoTok||i>=pend.length)return;
     var el=pend[i++],t=el.tags||{},a=osmAddr(t);
     var q=[a.strasse,[a.plz,a.ort].filter(Boolean).join(" "),landLabel(t._land||searchLand)].filter(Boolean).join(", ");
     if(!q){setTimeout(next,30);return;}
     osmGeocode(q).then(function(g){if(tok!==_geoTok)return;if(g&&g.lat){el.lat=+g.lat;el.lon=+g.lon;osmShowMap(osmEls);}}).catch(function(){}).then(function(){setTimeout(next,1100);});
   }
   next();
 }
 // Weitersuchen: dieselbe KI-Suche erneut, aber die schon gefundenen Firmen ausschließen
 // und die neuen Treffer unten anhängen (max. 10 echte Firmen pro Suche).
 // Weitersuchen: dieselbe KI-Suche erneut, schon gefundene Firmen ausschließen und
 // die neuen Treffer anhängen. auto=true -> läuft selbsttätig mehrere Runden (wie eine
 // gründliche Recherche), bis _autoMore aufgebraucht ist oder nichts Neues mehr kommt.
 function aiMore(auto){
   if(_searchSrc!=="KI"||!_lastWas)return;
   var btn=document.getElementById("osmMore");
   if(btn){btn.disabled=true;btn.textContent=auto?("KI vertieft die Suche … ("+osmEls.length+" gefunden)"):"Sucht weitere Firmen … (~1–2 Min)";}
   var names=osmEls.map(function(el){return (el.tags&&el.tags.name)||"";}).filter(Boolean);
   var w2=_lastWas+" — WICHTIG: Finde NUR WEITERE, ANDERE echte Firmen. Bereits bekannt und NICHT erneut nennen: "+names.join("; ")+".";
   apiAi(w2,_lastWo).then(function(leads){
     var seen={};osmEls.forEach(function(el){seen[el.type+"/"+el.id]=1;seen["n:"+(((el.tags&&el.tags.name)||"").toLowerCase())]=1;});
     var add=[];leads.map(aiToEl).forEach(function(el){var k=el.type+"/"+el.id,nk="n:"+(((el.tags&&el.tags.name)||"").toLowerCase());if(seen[k]||seen[nk])return;seen[k]=1;seen[nk]=1;add.push(el);});
     if(!add.length){_autoMore=0;if(btn){btn.disabled=false;btn.textContent="Keine weiteren gefunden – erneut versuchen";}return;}
     renderOsm(osmEls.concat(add));
     if(auto&&_autoMore>0){_autoMore--;if(_autoMore>0)setTimeout(function(){aiMore(true);},400);}
   }).catch(function(e){_autoMore=0;if(btn){btn.disabled=false;btn.textContent="＋ Weitersuchen – weitere Firmen finden";}if(!auto)osmStatus('Weitersuche fehlgeschlagen: '+esc(String((e&&e.message)||e))+'. Bitte erneut versuchen.');});
 }
 /* ---------- Karte (Leaflet, lokal mitgeliefert; Kacheln von OSM, nur online) ---------- */
 var _leafletP=null,_map=null,_markers=null;
 function ensureLeaflet(){
   if(window.L)return Promise.resolve(window.L);
   if(_leafletP)return _leafletP;
   _leafletP=new Promise(function(res,rej){
     var s=document.createElement("script");s.src="vendor/leaflet.js";
     s.onload=function(){try{L.Icon.Default.mergeOptions({iconUrl:"vendor/images/marker-icon.png",iconRetinaUrl:"vendor/images/marker-icon-2x.png",shadowUrl:"vendor/images/marker-shadow.png"});}catch(e){}res(window.L);};
     s.onerror=function(){rej(new Error("leaflet"));};
     document.head.appendChild(s);
   });
   return _leafletP;
 }
 // Satelliten-/Luftbild-Kacheln (Esri World Imagery, kostenlos, ohne API-Schlüssel)
 // plus transparente Beschriftungen (Orte/Straßen), damit es lesbar bleibt – wie bei Google.
 function addSat(L,map){
   L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",{maxZoom:19,attribution:"Luftbild © Esri, Maxar, Earthstar Geographics"}).addTo(map);
   L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",{maxZoom:19,opacity:0.9}).addTo(map);
   return map;
 }
 // Stabile Satellitenkarte in der Kontakt-Detailansicht (Leaflet + Esri-Luftbild) statt flackerndem Google-iframe.
 var _detmap=null,_detUpd=null;
 function initDetailMap(c){
   var el=document.getElementById("detMap");if(!el)return;
   function draw(L,lat,lon){
     try{if(_detmap){_detmap.remove();_detmap=null;}}catch(e){}
     try{_detmap=L.map(el,{attributionControl:false}).setView([lat,lon],16);addSat(L,_detmap);L.marker([lat,lon],{icon:flagIcon(L)}).addTo(_detmap);
       setTimeout(function(){try{_detmap.invalidateSize();}catch(e){}},150);}catch(e){el.style.display="none";}
   }
   var ll=contactLatLon(c);
   ensureLeaflet().then(function(L){
     if(ll){draw(L,ll.lat,ll.lon);return;}
     geocodeContact(c).then(function(p){c.lat=p.lat;c.lon=p.lon;cacheSave();draw(L,p.lat,p.lon);}).catch(function(){el.style.display="none";});
   }).catch(function(){el.style.display="none";});
 }
 function osmShowMap(els){
   var mapDiv=document.getElementById("osmMap");
   var pts=(els||[]).filter(function(el){return el.lat||(el.center&&el.center.lat);});
   if(!pts.length){mapDiv.style.display="none";return;}
   mapDiv.style.display="block";
   ensureLeaflet().then(function(L){
     if(!_map){
       _map=L.map(mapDiv,{scrollWheelZoom:true});
       addSat(L,_map);
     }
     if(_markers)_markers.remove();
     _markers=L.layerGroup().addTo(_map);
     var bounds=[],ex=osmExisting();
     pts.forEach(function(el){
       var lat=el.lat||el.center.lat,lon=el.lon||el.center.lon,t=el.tags||{},a=osmAddr(t),key=el.type+"/"+el.id;
       var have=osmHave(ex,key,t.name,a.ort);
       var addr=esc([a.strasse,[a.plz,a.ort].filter(Boolean).join(" ")].filter(Boolean).join(", "));
       var btn=have?'<span style="color:#15803d;font:600 12px sans-serif">✓ schon Lead</span>':'<button class="lf-add" data-osm-map="'+key+'" style="margin-top:6px;border:0;background:#c00000;color:#fff;border-radius:6px;padding:6px 10px;font:600 12px sans-serif;cursor:pointer">+ Als Lead</button>';
       L.marker([lat,lon],{icon:flagIcon(L)}).addTo(_markers).bindPopup('<b>'+esc(t.name||"")+'</b>'+(addr?'<br>'+addr:'')+'<br>'+btn);
       bounds.push([lat,lon]);
     });
     if(bounds.length)_map.fitBounds(bounds,{padding:[28,28],maxZoom:13});
     setTimeout(function(){try{_map.invalidateSize();}catch(e){}},120);
   }).catch(function(){mapDiv.style.display="none";});
 }
 function osmRun(){
   var was=(document.getElementById("osmWas").value||"").trim(),wo=(document.getElementById("osmWo").value||"").trim();
   if(!was){osmStatus("Bitte eingeben, wonach gesucht werden soll (z. B. Kompostierung).");return;}
   if(!wo){osmStatus("Bitte eine Region angeben (z. B. Bayern oder eine Stadt).");return;}
   if(navigator.onLine===false){osmStatus("Keine Internetverbindung – die Lead-Suche funktioniert nur online.");return;}
   lastQuery=was+" in "+wo;
   osmLoading('Suche „'+esc(lastQuery)+'“ in der Karte …');
   osmGeocode(wo).then(function(g){
     var cc=(g.address&&g.address.country_code)||"";searchLand=cc?cc.toUpperCase():"DE";
     return osmOverpass(osmBuildQuery(osmAreaRef(g),osmFilters(was)));
   }).then(function(els){
     var seen={},out=[];els.forEach(function(el){var t=el.tags||{};if(!t.name)return;var k=el.type+"/"+el.id;if(seen[k])return;seen[k]=1;out.push(el);});
     _searchSrc="Karten-Suche";renderOsm(out);
   }).catch(function(e){
     osmClearResults();
     var m=String((e&&e.message)||e);
     // Wenn BEIDE unabhängigen Dienste (KI + Karten) am Netzwerk scheitern, ist es fast
     // sicher eine Firmen-Firewall / ein Browser-Schutz, der die Online-Suche blockiert.
     var netty=/Failed to fetch|NetworkError|Load failed|fetch resource/i.test(m+" "+_aiErr);
     if(netty){osmStatus('Die Online-Suche ist von diesem Rechner aus blockiert (vermutlich <b>Firmen-Firewall oder Browser-Schutz</b>) – auch die freie Karten-Suche wird abgewiesen. <b>Am Handy/Mobilfunk funktioniert die Suche.</b> Für den PC müsste die IT die Adressen <i>supabase.co</i>, <i>nominatim.openstreetmap.org</i> und <i>overpass-api.de</i> freigeben.');return;}
     var pre=_aiErr?("KI-Suche fehlgeschlagen: "+esc(_aiErr)+". Auch die Karten-Suche ist gerade nicht erreichbar. "):"";
     if(/noplace/.test(m))osmStatus(pre+'Region „'+esc(wo)+'“ nicht gefunden. Anders schreiben (z. B. „Bayern“, „München“).');
     else if(/overpass/.test(m))osmStatus(pre+"Suche fehlgeschlagen oder Region zu groß. Bitte enger eingrenzen (z. B. Stadt statt Bundesland) und erneut versuchen.");
     else osmStatus(pre||"Suche gerade nicht möglich (offline oder Kartendienst nicht erreichbar). Später erneut versuchen.");
   });
 }
 // Umkreissuche: GPS-Standort holen und Anlagen im gewaehlten Radius finden (praezise, OSM around:).
 function umkreisSearch(){
   var was=(document.getElementById("osmWas").value||"").trim()||"kompostierung";
   var km=parseInt((document.getElementById("osmRadius")||{}).value,10)||100;
   if(navigator.onLine===false){osmStatus("Keine Internetverbindung – die Umkreissuche funktioniert nur online.");return;}
   if(!navigator.geolocation){osmStatus("Dein Gerät unterstützt keine Standortbestimmung.");return;}
   _aiErr="";
   osmLoading("Standort wird ermittelt … (bitte Standort-Freigabe erlauben)");
   navigator.geolocation.getCurrentPosition(function(pos){
     var lat=pos.coords.latitude,lon=pos.coords.longitude;
     lastQuery=was+" im Umkreis "+km+" km";_lastWas=was;
     osmLoading('Standort gefunden – suche „'+esc(was)+'“ im Umkreis '+km+' km …');
     osmReverse(lat,lon).then(function(rg){return rg;},function(){return null;}).then(function(rg){
       var ort=(rg&&rg.ort)||"";if(rg&&rg.cc)searchLand=rg.cc.toUpperCase();
       if(ort)lastQuery=was+" im Umkreis "+km+" km um "+ort;
       // KI bevorzugt – findet auch Betriebe, die NICHT in OpenStreetMap stehen (z. B. Biomüll/Kompost).
       if(aiReady()){
         var wo=(ort||(lat.toFixed(3)+", "+lon.toFixed(3)))+" und Umgebung (Umkreis ca. "+km+" km)";_lastWo=wo;
         osmLoading('KI sucht „'+esc(was)+'“ im Umkreis '+km+' km um '+esc(ort||"deinen Standort")+' … <b>~1–2 Min</b>');
         aiSearchRetry(was,wo,1).then(function(leads){
           if(leads&&leads.length){_searchSrc="KI · Umkreis "+km+" km";renderOsm(leads.map(aiToEl));}
           else osmUmkreis(lat,lon,km,was);
         }).catch(function(e){_aiErr=String((e&&e.message)||e);osmUmkreis(lat,lon,km,was);});
       } else { osmUmkreis(lat,lon,km,was); }
     });
   },function(err){
     var c=err&&err.code;
     osmStatus(c===1?'Standort-Freigabe wurde abgelehnt. Bitte erlaube der Seite den Zugriff auf den Standort (Browser-/Handy-Einstellungen) und tippe erneut.':'Standort konnte nicht ermittelt werden. Bitte erneut versuchen (in Gebäuden ist GPS oft ungenau).');
   },{enableHighAccuracy:true,timeout:15000,maximumAge:60000});
 }
 // Umkreis ueber die kostenlose Karten-Suche (OSM around:) – Fallback, wenn keine KI / keine KI-Treffer.
 function osmUmkreis(lat,lon,km,was){
   osmLoading('Suche „'+esc(was)+'“ im Umkreis '+km+' km (Karten-Suche) …');
   osmOverpass(osmBuildQuery({around:[km*1000,lat,lon]},osmFilters(was))).then(function(els){
     var seen={},out=[];els.forEach(function(el){var t=el.tags||{};if(!t.name)return;var k=el.type+"/"+el.id;if(seen[k])return;seen[k]=1;out.push(el);});
     _searchSrc="Umkreis "+km+" km";renderOsm(out);
     if(!out.length)osmStatus('Keine Treffer im Umkreis '+km+' km'+(_aiErr?(' (KI: '+esc(_aiErr)+')'):'')+'. Größeren Radius wählen oder anderen Begriff (z. B. „Kompost", „Recycling", „Erden") versuchen.');
   }).catch(function(e){
     osmClearResults();var m=String((e&&e.message)||e);
     if(/Failed to fetch|NetworkError|Load failed|fetch resource/i.test(m))osmStatus('Die Online-Suche ist von diesem Gerät blockiert (Firewall/Browser-Schutz). Am Handy/Mobilfunk versuchen.');
     else if(/overpass/.test(m))osmStatus('Umkreissuche fehlgeschlagen (Kartendienst überlastet). Bitte erneut versuchen.');
     else osmStatus('Umkreissuche gerade nicht möglich. Später erneut versuchen.');
   });
 }
 // Haupt-Einstieg der Lead-Suche: KI (falls eingerichtet) zuerst, sonst/als Fallback OSM-Karten-Suche.
 function leadSearch(){
   var was=(document.getElementById("osmWas").value||"").trim(),wo=(document.getElementById("osmWo").value||"").trim();
   if(!was){osmStatus("Bitte eingeben, wonach gesucht werden soll (z. B. Kompostierung).");return;}
   if(!wo){osmStatus("Bitte eine Region angeben (z. B. Bayern oder eine Stadt).");return;}
   if(navigator.onLine===false){osmStatus("Keine Internetverbindung – die Lead-Suche funktioniert nur online.");return;}
   _aiErr="";
   if(!aiReady()){osmRun();return;}
   lastQuery=was+" in "+wo;searchLand=guessLand(wo);_lastWas=was;_lastWo=wo;_autoMore=0;
   osmLoading('KI durchsucht das Web nach „'+esc(lastQuery)+'“ … <b>gründliche Recherche – das dauert bis zu ~2 Minuten</b>. Danach ergänzt die KI automatisch weitere Firmen.');
   aiSearchRetry(was,wo,1).then(function(leads){
     if(!leads.length){osmClearResults();osmStatus('Die KI hat für „'+esc(lastQuery)+'“ keine Firmen gefunden. Tipp: anderen Begriff (z. B. „Kompostierung", „Recycling", „Erdenwerk") oder ein größeres Gebiet (z. B. „Bayern" statt nur einer Stadt) versuchen.');return;}
     _searchSrc="KI";renderOsm(leads.map(aiToEl));
     // Wie eine echte Recherche: automatisch noch bis zu 2 weitere Runden anhängen
     // (nur wenn die erste Runde "voll" war, also vermutlich mehr existiert).
     if(leads.length>=6){_autoMore=2;setTimeout(function(){aiMore(true);},500);}
   }).catch(function(e){
     // KI nicht erreichbar -> automatisch auf die kostenlose Karten-Suche zurückfallen.
     _aiErr=String((e&&e.message)||e);
     osmLoading('KI gerade nicht erreichbar ('+esc(_aiErr)+'). Wechsle zur kostenlosen Karten-Suche …');
     osmRun();
   });
 }
 // KI-Aufruf mit einer automatischen Wiederholung bei Netzwerkfehlern (z. B. Kaltstart
 // der Edge Function). Zeitüberschreitungen werden NICHT erneut versucht (zu langsam).
 function aiSearchRetry(was,wo,retries){
   var t0=Date.now();
   return apiAi(was,wo).catch(function(e){
     var msg=String((e&&e.message)||e),dt=Date.now()-t0;
     var netErr=/NetworkError|Failed to fetch|Load failed|networkerror|fetch resource/i.test(msg)&&!/Zeitüberschreitung/.test(msg);
     // Nur SCHNELLE Netzwerkfehler erneut versuchen (Kaltstart). Ein spätes Abbrechen
     // (> 20 s) ist meist ein Proxy-/Firewall-Timeout -> sofort zum Fallback, nicht warten.
     if(retries>0&&netErr&&dt<20000){return new Promise(function(res){setTimeout(res,2000);}).then(function(){return aiSearchRetry(was,wo,retries-1);});}
     throw e;
   });
 }
 // Ein "Suchen"-Knopf: Schalter "Umkreis" entscheidet -> Umkreissuche (GPS) oder normale Suche.
 function doLeadSearch(){var t=document.getElementById("osmNearTgl");if(t&&t.checked)umkreisSearch();else leadSearch();}
 document.getElementById("osmSearch").onclick=doLeadSearch;
 document.getElementById("osmWas").addEventListener("keydown",function(e){if(e.key==="Enter")doLeadSearch();});
 document.getElementById("osmWo").addEventListener("keydown",function(e){if(e.key==="Enter")doLeadSearch();});
 (function(){var t=document.getElementById("osmNearTgl");if(!t)return;t.addEventListener("change",function(){
   var on=t.checked;document.getElementById("osmRadius").disabled=!on;
   var wo=document.getElementById("osmWo");if(wo){wo.disabled=on;wo.style.opacity=on?"0.45":"";}
   document.getElementById("osmNearHint").textContent=on?"sucht um deinen Standort (GPS) – Radius wählen":"aus = im ganzen Land/Region suchen";
 });})();
 document.getElementById("osmResults").addEventListener("click",function(e){
   if(e.target.closest("a"))return; // Web-Links normal lassen
   if(e.target.id==="osmMore"){aiMore();return;}
   if(e.target.id==="osmAddAll"){var ex=osmExisting(),added=[],seen={};Object.keys(osmLast).forEach(function(k){var el=osmLast[k],t=el.tags||{},a=osmAddr(t);if(osmHave(ex,k,t.name,a.ort))return;var dk=dedupKey(t.name,a.ort);if(seen[dk])return;seen[dk]=1;var c=osmMake(k);if(c){added.push(c);ex["dk:"+dk]=c.id;}});if(added.length)bulkSave(added,false);renderOsm(osmEls);renderLeads();osmStatus(added.length+" neue Leads übernommen – sie stehen unten in deiner Lead-Liste.");return;}
   var o=e.target.closest("[data-openid]");if(o){openDetail(o.getAttribute("data-openid"));return;}
   // „+ Lead"-Button: schnell übernehmen (ohne Öffnen)
   var b=e.target.closest("[data-osm]");
   if(b){var c=osmMake(b.getAttribute("data-osm"));if(c)saveContact(c);b.outerHTML='<span class="pill" style="background:#e6f4ea;color:#15803d">✓ Lead</span>';renderLeads();return;}
   // Klick irgendwo auf die Zeile: erfasst -> öffnen; neu -> übernehmen und öffnen
   var row=e.target.closest(".crow[data-rowkey]");
   if(row){var have=row.getAttribute("data-rowhave");if(have){openDetail(have);return;}var c2=osmMake(row.getAttribute("data-rowkey"));if(c2){saveContact(c2);renderLeads();openDetail(c2.id);}}
 });
 // „+ Als Lead" aus einem Karten-Popup
 document.getElementById("osmMap").addEventListener("click",function(e){
   var b=e.target.closest("[data-osm-map]");if(!b)return;
   var c=osmMake(b.getAttribute("data-osm-map"));if(c){saveContact(c);b.outerHTML='<span style="color:#15803d;font:600 12px sans-serif">✓ Als Lead übernommen</span>';renderLeads();}
 });

 /* ---------- Klick auf Kontaktzeile ---------- */
 // mailin-Aktivität als "gelesen" markieren -> verschwindet aus dem Posteingang, bleibt aber im Kontaktverlauf.
 function markInboxSeen(cid,aid){var c=byId(cid);if(!c)return;var a=(c.activities||[]).filter(function(x){return x.id===aid;})[0];if(a&&!a.seen){a.seen=true;c.updated=Date.now();saveContact(c);}}
 document.body.addEventListener("click",function(e){
   if(e.target.closest("a"))return;
   var is=e.target.closest("[data-inboxseen]");
   if(is){e.preventDefault();e.stopPropagation();var sp=is.getAttribute("data-inboxseen").split("|");markInboxSeen(sp[0],sp[1]);renderDashboard();return;}
   var ir=e.target.closest("[data-inboxreply]");
   if(ir){e.preventDefault();e.stopPropagation();var parts=ir.getAttribute("data-inboxreply").split("|");markInboxSeen(parts[0],parts[1]);openDetail(parts[0]);setTimeout(function(){startMailReply(parts[1]);},60);return;}
   var row=e.target.closest(".crow");if(row&&row.getAttribute("data-id")){var ia=row.getAttribute("data-inboxact");if(ia)markInboxSeen(row.getAttribute("data-id"),ia);openDetail(row.getAttribute("data-id"));}
 });

 /* ---------- Detail ---------- */
 var curId=null;
 function offerLink(name){return "../index.html"; }
 // Kundendaten für den Konfigurator vorbereiten und dorthin springen.
 function offerPrefillFields(c){return {k_firma:c.firma||"",k_firma2:c.firma2||"",k_anrede:c.anrede||"",k_vor:c.vorname||"",k_nach:c.nachname||"",k_str:c.strasse||"",k_plz:c.plz||"",k_ort:c.ort||"",k_land:landLabel(c.land)||"",k_tel:c.tel||"",k_mail:c.mail||"",k_ustid:c.ustid||""};}
 function gotoConfigurator(c,withReturn){
   try{localStorage.setItem("amb_lepton_prefill",JSON.stringify({mode:"angebot",fields:offerPrefillFields(c),from:c.id,ts:Date.now()}));
     if(withReturn)localStorage.setItem("amb_lepton_offer_return",JSON.stringify({contactId:c.id,ts:Date.now()}));
     else try{localStorage.removeItem("amb_lepton_offer_return");}catch(_){}}catch(e){}
   location.href="../index.html";
 }
 function openDetail(id){
   var c=byId(id);if(!c)return;curId=id;_detUpd=(c.updated||0);
   var loc=[c.str,[c.plz,c.ort].filter(Boolean).join(" ")].filter(Boolean);
   var addr=[c.strasse,[c.plz,c.ort].filter(Boolean).join(" "),landLabel(c.land)].filter(Boolean).join(", ");
   var ll=contactLatLon(c);
   var notizClean=(c.notiz||"").replace(/^\s*Auf Karte:.*$/gim,"").trim();
   var acts=(c.activities||[]).slice().sort(function(a,b){return b.date-a.date;});
   var fu=c.followup&&!c.followup.done&&c.followup.due?c.followup:null;
   var html=''+
   '<button class="btn ghost sm" id="backBtn" style="margin-bottom:10px">← Zurück</button>'+
   '<div class="detail-head">'+
     '<div class="av av-'+esc(c.status||"lead")+'">'+esc(initials(displayName(c)))+'</div>'+
     '<div style="flex:1;min-width:0"><h2>'+esc(displayName(c))+'</h2>'+
       '<div class="who">'+esc([fullName(c),c.firma&&fullName(c)?"":""].filter(Boolean).join(""))+
         (fullName(c)&&c.firma?esc(fullName(c)):"")+(c.anrede?' · '+esc(c.anrede):'')+'</div>'+
     '</div>'+
     '<span class="pill '+esc(c.status||"lead")+'" style="align-self:flex-start">'+esc(statusLabel(c.status))+'</span>'+
   '</div>'+
   '<div class="quick">'+
     (c.tel?'<a class="btn sm primary" href="tel:'+esc(c.tel)+'"><svg viewBox="0 0 24 24"><path d="M5 4h4l2 5-3 2a13 13 0 006 6l2-3 5 2v4a2 2 0 01-2 2A17 17 0 013 6a2 2 0 012-2"/></svg>Anrufen</a>':'')+
     (c.mobil?'<a class="btn sm" href="tel:'+esc(c.mobil)+'">Mobil</a>':'')+
     (c.mail?'<a class="btn sm" id="mailBtn" href="mailto:'+esc(c.mail)+'" title="E-Mail in Outlook (vorausgefüllt)"><svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>E-Mail</a>':'')+
     '<button class="btn sm primary" id="offerBtn"><svg viewBox="0 0 24 24"><path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z"/><path d="M14 3v5h5"/></svg>Angebot erstellen</button>'+
     '<button class="btn sm" id="addActBtn"><svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>Aktivität</button>'+
     '<button class="btn sm" id="editBtn">Bearbeiten</button>'+
     '<button class="btn sm" id="photoBtn" title="Foto aufnehmen oder aus der Galerie hinzufügen"><svg viewBox="0 0 24 24"><path d="M3 7h4l2-2h6l2 2h4v12H3z"/><circle cx="12" cy="13" r="3.5"/></svg>Foto</button>'+
     '<input type="file" id="photoIn" accept="image/*" capture="environment" multiple style="display:none">'+
     (aiReady()&&c.firma?'<button class="btn sm" id="enrichBtn" title="Fehlende Daten (Straße, PLZ, Telefon, Ansprechpartner …) per KI nachschlagen"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>Per KI ergänzen</button>':'')+
   '</div>'+
   // Status-Schnellwechsel
   '<div class="fg" style="max-width:240px;margin:8px 0"><label>Status ändern</label><select class="field" id="dStatus">'+
     STATUS.map(function(s){return '<option value="'+s[0]+'"'+(c.status===s[0]?' selected':'')+'>'+esc(s[1])+'</option>';}).join("")+'</select></div>'+
   // Stammdaten
   '<dl class="kv">'+
     (c.firma2?'<dt>Zusatz</dt><dd>'+esc(c.firma2)+'</dd>':'')+
     (c.strasse?'<dt>Straße</dt><dd>'+esc(c.strasse)+'</dd>':'')+
     (c.plz?'<dt>Postleitzahl</dt><dd>'+esc(c.plz)+'</dd>':'')+
     (c.ort?'<dt>Ort</dt><dd>'+esc(c.ort)+'</dd>':'')+
     (c.land?'<dt>Land</dt><dd>'+esc(landLabel(c.land))+'</dd>':'')+
     (contactBundesland(c)?'<dt>Bundesland</dt><dd>'+esc(contactBundesland(c))+'</dd>':'')+
     (c.tel?'<dt>Telefon</dt><dd><a href="tel:'+esc(c.tel)+'">'+esc(c.tel)+'</a></dd>':'')+
     (c.mobil?'<dt>Mobil</dt><dd><a href="tel:'+esc(c.mobil)+'">'+esc(c.mobil)+'</a></dd>':'')+
     (c.mail?'<dt>E-Mail</dt><dd><a href="mailto:'+esc(c.mail)+'">'+esc(c.mail)+'</a></dd>':'')+
     (c.web?'<dt>Web</dt><dd><a href="'+esc(/^https?:/.test(c.web)?c.web:"https://"+c.web)+'" target="_blank" rel="noopener">'+esc(c.web)+'</a></dd>':'')+
     (c.ustid?'<dt>USt-IdNr.</dt><dd>'+esc(c.ustid)+'</dd>':'')+
     (c.gf?'<dt>Geschäftsf.</dt><dd>'+esc(c.gf)+'</dd>':'')+
     (c.bl?'<dt>Betriebsl.</dt><dd>'+esc(c.bl)+'</dd>':'')+
     (c.menge?'<dt>Jahresmenge</dt><dd>'+esc(c.menge)+'</dd>':'')+
     (c.sieb?'<dt>Siebtechnik</dt><dd>'+esc(c.sieb)+'</dd>':'')+
     (c.quelle?'<dt>Quelle</dt><dd>'+esc(c.quelle)+'</dd>':'')+
     (c.owner?'<dt>Betreuer</dt><dd>'+esc(c.owner)+'</dd>':'')+
   '</dl>'+
   (c.news?'<div class="card" style="background:#eef4ff;border-color:#cfe0ff"><div style="font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:#1d4ed8;margin-bottom:4px">News</div><div style="white-space:pre-wrap;font-size:14px">'+esc(c.news)+'</div></div>':'')+
   (notizClean?'<div class="card" style="background:var(--field)"><div style="white-space:pre-wrap;font-size:14px">'+esc(notizClean)+'</div></div>':'')+
   ((c.bilder&&c.bilder.length)?'<div class="card"><div style="font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-bottom:8px">Bilder ('+c.bilder.length+')</div><div style="display:flex;gap:8px;flex-wrap:wrap">'+c.bilder.map(function(b,i){return '<div style="position:relative"><img src="'+esc(b)+'" data-bild="'+i+'" title="Klick öffnet das Bild groß" style="width:150px;height:104px;object-fit:cover;border-radius:8px;border:1px solid var(--line);cursor:pointer"><button class="btn ghost" data-delbild="'+i+'" title="Dieses Bild entfernen" style="position:absolute;top:4px;right:4px;padding:2px 7px;background:rgba(0,0,0,.6);color:#fff;border:0;border-radius:6px;font-size:14px;line-height:1;cursor:pointer">×</button></div>';}).join("")+'</div></div>':'')+
   // Standort-Karte des Kontakts
   (function(){var mq=ll?(ll.lat+","+ll.lon):(addr||"");if(!mq)return "";var eq=encodeURIComponent(mq);
     return '<div style="margin:8px 0"><div id="detMap" title="Standort-Karte (Satellit)" style="width:100%;height:240px;border:1px solid var(--line);border-radius:12px;background:var(--field)"></div>'+
       '<div style="margin-top:6px"><a class="btn sm" href="https://www.google.com/maps?q='+eq+'&t=k" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" style="width:15px;height:15px;stroke:currentColor;fill:none;stroke-width:1.7"><path d="M12 21s-7-5.2-7-11a7 7 0 0114 0c0 5.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>In Google Maps öffnen</a></div></div>';})()+
   // Wiedervorlage
   '<div class="fu-box'+(fu?' active-fu':'')+'" id="fuBox">'+
     '<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px"><b style="font-size:13px">Wiedervorlage / Rückruf</b>'+
       (fu?'<span class="due '+dueClass(fu.due)+'">'+dueLabel(fu.due)+'</span>':'<span style="font-size:12px;color:var(--muted)">keine</span>')+'</div>'+
     (fu&&fu.note?'<div style="font-size:13px;margin-bottom:8px">'+esc(fu.note)+'</div>':'')+
     '<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">'+
       '<input class="field" type="date" id="fuDate" value="'+(fu?new Date(fu.due).toISOString().slice(0,10):"")+'" style="width:auto">'+
       '<input class="field" id="fuNote" placeholder="Notiz (optional)" value="'+(fu?esc(fu.note||""):"")+'" style="flex:1;min-width:140px">'+
       '<button class="btn sm" id="fuSet">Setzen</button>'+
       (fu?'<button class="btn sm" id="icsBtn" title="Termin in Outlook/Kalender übernehmen (.ics)"><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="17" rx="2"/><path d="M3 9h18M8 3v4M16 3v4"/></svg>In Kalender</button>':'')+
       (fu?'<button class="btn sm danger" id="fuDone">Erledigt</button>':'')+
     '</div>'+
   '</div>'+
   // Aktivitäten
   '<h3 style="font-family:var(--mono);font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:18px 0 10px">Verlauf / Lebenslauf ('+acts.length+')</h3>'+
   (acts.length?'<div class="tl">'+acts.map(actItem).join("")+'</div>':'<div style="font-size:13px;color:var(--muted);background:var(--field);border:1px dashed var(--line-strong);border-radius:12px;padding:14px;text-align:center">Hier entsteht der komplette Verlauf: <b>wann</b> war Kontakt, <b>wer</b>, Anrufe, E-Mails, <b>Angebote</b> (mit Nr./Betrag) und Notizen.<br><button class="btn sm primary" id="emptyAddAct" style="margin-top:10px">+ Erste Aktivität erfassen</button></div>')+
   '<div style="margin:22px 0 8px;display:flex;gap:8px;flex-wrap:wrap"><button class="btn danger sm" id="delBtn">Kontakt löschen</button></div>';
   var v=document.getElementById("view-detail");v.innerHTML=html;show("detail");
   initDetailMap(c); // stabile Leaflet-Satellitenkarte statt flackerndem Google-Rahmen
   // Fehlende Angebots-PDFs automatisch im Hintergrund erzeugen (ohne Klick).
   acts.forEach(function(a){if(a.type==="angebot"&&a.config&&!a.pdf)queuePdfGen(c.id,a.id,false);});
   document.getElementById("backBtn").onclick=function(){renderList();show("list");};
   document.getElementById("editBtn").onclick=function(){openForm(curId);};
   document.getElementById("addActBtn").onclick=function(){openActModal(curId);};
   var pBtn=document.getElementById("photoBtn"),pIn=document.getElementById("photoIn");
   if(pBtn&&pIn){pBtn.onclick=function(){pIn.click();};
     pIn.onchange=function(){var files=Array.prototype.slice.call(pIn.files||[]);if(!files.length)return;pBtn.disabled=true;var old=pBtn.innerHTML;pBtn.textContent="…";
       var uris=[],done=0;
       function finalize(){sbStoreImages(uris).then(function(urls){if(urls.length){if(!c.bilder)c.bilder=[];urls.forEach(function(u){c.bilder.push(u);});c.updated=Date.now();saveContact(c);}pBtn.disabled=false;pBtn.innerHTML=old;openDetail(curId);});}
       files.forEach(function(f){downscaleImage(f,1200,function(d){if(d)uris.push(d);if(++done===files.length)finalize();});});
     };
   }
   document.getElementById("offerBtn").onclick=function(){gotoConfigurator(c,false);};
   var enb=document.getElementById("enrichBtn");if(enb)enb.onclick=function(){enrichContactAI(c,this);};
   var eab=document.getElementById("emptyAddAct");if(eab)eab.onclick=function(){openActModal(curId);};
   document.getElementById("dStatus").onchange=function(){var cc=byId(curId)||c;cc.status=this.value;cc.updated=Date.now();saveContact(cc);openDetail(curId);};
   document.getElementById("fuSet").onclick=function(){var d=document.getElementById("fuDate").value;if(!d){alert("Bitte ein Datum wählen.");return;}var cc=byId(curId)||c;cc.followup={due:new Date(d+"T09:00").getTime(),note:document.getElementById("fuNote").value.trim(),done:false};cc.updated=Date.now();saveContact(cc);openDetail(curId);};
   var fd=document.getElementById("fuDone");if(fd)fd.onclick=function(){var cc=byId(curId)||c;if(cc.followup)cc.followup.done=true;cc.updated=Date.now();saveContact(cc);openDetail(curId);};
   var mb2=document.getElementById("mailBtn");if(mb2)mb2.href=buildMailto(c); // Outlook vorausgefüllt (Anrede + Signatur)
   var ib=document.getElementById("icsBtn");if(ib)ib.onclick=function(){icsDownload(c,c.followup);};
   document.getElementById("delBtn").onclick=function(){if(confirm("Diesen Kontakt mit gesamtem Verlauf endgültig löschen?")){removeContact(curId);renderList();show("list");}};
   var gb=document.getElementById("geoBtn");if(gb)gb.onclick=function(){var b=this;b.textContent="Suche Standort…";geocodeContact(c).then(function(p){c.lat=p.lat;c.lon=p.lon;c.updated=Date.now();saveContact(c);openDetail(curId);}).catch(function(){b.textContent="Standort nicht gefunden";});};
 }
 function contactLatLon(c){
   if(c.lat!=null&&c.lon!=null&&!isNaN(c.lat)&&!isNaN(c.lon))return {lat:+c.lat,lon:+c.lon};
   var m=(c.notiz||"").match(/mlat=([-0-9.]+)&mlon=([-0-9.]+)/);
   if(m)return {lat:+m[1],lon:+m[2]};
   return null;
 }
 var _detMap=null;
 function renderDetMap(ll){
   ensureLeaflet().then(function(L){
     var div=document.getElementById("detMap");if(!div)return;
     if(_detMap){try{_detMap.remove();}catch(e){}_detMap=null;}
     _detMap=L.map(div,{scrollWheelZoom:false}).setView([ll.lat,ll.lon],14);
     addSat(L,_detMap);
     L.marker([ll.lat,ll.lon],{icon:flagIcon(L)}).addTo(_detMap);
     setTimeout(function(){try{_detMap.invalidateSize();}catch(e){}},150);
   }).catch(function(){});
 }
 // PDF (data-URI) in neuem Tab öffnen – als Blob, da reine data-URIs oft blockiert werden.
 // Bild groß IN der App anzeigen (kein neues Fenster -> kein Problem in der installierten iPhone-App).
 function openImage(src){
   if(!src)return;
   var ov=document.getElementById("imgOverlay");
   if(!ov){ov=document.createElement("div");ov.id="imgOverlay";ov.style.cssText="position:fixed;inset:0;z-index:3000;background:rgba(12,13,15,.92);display:none;align-items:center;justify-content:center;padding:14px";ov.addEventListener("click",function(){ov.style.display="none";ov.innerHTML="";});document.body.appendChild(ov);}
   ov.innerHTML='<img src="'+esc(src)+'" alt="" style="max-width:100%;max-height:100%;border-radius:10px;box-shadow:0 8px 40px rgba(0,0,0,.5)"><div style="position:absolute;top:calc(14px + env(safe-area-inset-top));right:18px;color:#fff;font-size:28px;line-height:1">×</div>';
   ov.style.display="flex";
 }
 function openPdfUri(uri){
   try{
     var parts=String(uri).split(",");var meta=parts[0]||"";var b64=parts.slice(1).join(",");
     var bin=atob(b64);var len=bin.length;var arr=new Uint8Array(len);for(var i=0;i<len;i++)arr[i]=bin.charCodeAt(i);
     var mime=(meta.match(/data:([^;]+)/)||[,"application/pdf"])[1];
     var blob=new Blob([arr],{type:mime});var url=URL.createObjectURL(blob);
     var w=window.open(url,"_blank");if(!w)location.href=url;
     setTimeout(function(){URL.revokeObjectURL(url);},60000);
   }catch(e){try{window.open(uri,"_blank");}catch(_){}}
 }
 // ---- PDF im Hintergrund erzeugen (unsichtbarer Konfigurator-iFrame) ----
 // Bestehende Angebote (Konfig vorhanden, aber noch kein PDF) bekommen ihr PDF
 // automatisch, ohne dass man etwas anklicken oder die Seite verlassen muss.
 var _pdfQ=[], _pdfBusy=false, _pdfTried={}, _pdfActive={};
 function queuePdfGen(contactId,actId,force){
   var k=contactId+"/"+actId;
   if(force)delete _pdfTried[k];
   if(_pdfTried[k]||_pdfActive[k])return;
   _pdfTried[k]=1;_pdfQ.push({contactId:contactId,actId:actId});runPdfGen();
 }
 function runPdfGen(){
   if(_pdfBusy||!_pdfQ.length)return;
   var job=_pdfQ.shift();var c=byId(job.contactId);if(!c){return runPdfGen();}
   var a=(c.activities||[]).filter(function(x){return x.id===job.actId;})[0];
   if(!a||!a.config||a.pdf){return runPdfGen();}
   if(navigator.onLine===false){_pdfBusy=false;return;} // offline -> später erneut versuchen
   _pdfBusy=true;var k=job.contactId+"/"+job.actId;_pdfActive[k]=1;
   if(curId===job.contactId&&curView==="detail")openDetail(curId); // Label „wird erstellt …"
   try{localStorage.setItem("amb_lepton_loadoffer_data",JSON.stringify(a.config));
       localStorage.setItem("amb_lepton_offer_makepdf",JSON.stringify({contactId:job.contactId,actId:job.actId,iframe:true}));
   }catch(e){_pdfBusy=false;delete _pdfActive[k];return runPdfGen();}
   var ifr=document.createElement("iframe");ifr.setAttribute("aria-hidden","true");
   ifr.style.cssText="position:fixed;left:-10000px;top:0;width:980px;height:1400px;border:0;opacity:0;pointer-events:none";
   var fin=false;
   function done(){if(fin)return;fin=true;clearTimeout(tmr);window.removeEventListener("message",onMsg);try{ifr.remove();}catch(_){}delete _pdfActive[k];_pdfBusy=false;setTimeout(runPdfGen,150);}
   var tmr=setTimeout(done,90000);
   function onMsg(ev){
     var d=ev.data&&ev.data.ambOfferDone;if(!d||d.makepdfActId!==job.actId)return;
     if(d.pdf){var cc=byId(job.contactId);if(cc){var aa=(cc.activities||[]).filter(function(x){return x.id===job.actId;})[0];
       if(aa){aa.pdf=d.pdf;cacheSave();}}} /* PDF nur lokal speichern (aus Konfiguration jederzeit neu erzeugbar) -> ueberschreibt keine Aenderungen anderer Geraete */
     done();if(curId===job.contactId&&curView==="detail")openDetail(curId);
   }
   window.addEventListener("message",onMsg);
   ifr.src="../index.html";document.body.appendChild(ifr);
 }
 function actItem(a){
   var cls="t-"+a.type;
   var icon={anruf:'<path d="M5 4h4l2 5-3 2a13 13 0 006 6l2-3 5 2v4a2 2 0 01-2 2A17 17 0 013 6a2 2 0 012-2"/>',
     angebot:'<path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z"/>',
     mailout:'<path d="M3 7l9 6 9-6"/>',mailin:'<path d="M3 7l9 6 9-6"/>',
     besuch:'<path d="M12 21s-7-5.2-7-11a7 7 0 0114 0c0 5.8-7 11-7 11z"/>',notiz:'<path d="M5 7h14M5 12h14M5 17h9"/>'}[a.type]||'<circle cx="12" cy="12" r="6"/>';
   var offer="";
   var bits=[];
   if(a.offerNr)bits.push("Nr "+esc(a.offerNr));
   if(a.betrag)bits.push(esc(fmtEur(a.betrag)));
   if(a.offer)bits.push("Konfig: "+esc(a.offer));
   if(bits.length){var _osvg='<svg viewBox="0 0 24 24"><path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z"/><path d="M14 3v5h5"/></svg>';var openable=!!(a.config||a.offer);
     if(openable)offer='<a class="tl-offer" href="../index.html" data-actid="'+a.id+'"'+(a.offer?(' data-loadoffer="'+esc(a.offer)+'"'):'')+' title="Angebot im Konfigurator öffnen">'+_osvg+bits.join(" · ")+' ↗</a>';
     else offer='<span class="tl-offer" style="cursor:default">'+_osvg+bits.join(" · ")+'</span>';}
   var _psvg='<svg viewBox="0 0 24 24"><path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z"/><path d="M14 3v5h5"/></svg>';
   if(a.pdf){offer+='<button class="tl-offer" data-pdfact="'+a.id+'" title="Fertiges PDF ansehen (ohne Konfigurator)">'+_psvg+'PDF ansehen</button>';
     offer+='<button class="tl-offer" data-mailoffer="'+a.id+'" style="background:#eafaf0;color:#0a7d3a" title="Angebot als PDF per E-Mail senden"><svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>Per E-Mail senden</button>';}
   else if(a.config){
     if(_pdfActive[curId+"/"+a.id])offer+='<span class="tl-offer" style="cursor:default;opacity:.7">'+_psvg+'PDF wird erstellt …</span>';
     else offer+='<button class="tl-offer" data-makepdf="'+a.id+'" title="PDF jetzt erzeugen und hier ablegen">'+_psvg+'PDF erstellen</button>';
   }
   if(a.mailWeb)offer+='<a class="tl-offer" href="'+esc(a.mailWeb)+'" target="_blank" rel="noopener" style="background:#fff7e0;color:#8a6d00" title="Mail in Outlook öffnen"><svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>In Outlook</a>';
   if(a.type==="mailin")offer+='<button class="tl-offer" data-mailreply="'+a.id+'" style="background:#eafaf0;color:#0a7d3a" title="KI entwirft eine Antwort, du sendest sie"><svg viewBox="0 0 24 24"><path d="M12 3l2 5 5 2-5 2-2 5-2-5-5-2 5-2z"/></svg>KI-Antwort</button>';
   return '<div class="tl-item '+cls+'">'+
     '<div class="tl-dot"><svg viewBox="0 0 24 24">'+icon+'</svg></div>'+
     '<div class="tl-top"><span class="tl-type">'+esc(actLabel(a.type))+'</span>'+
       '<span class="tl-when">'+fmtDateTime(a.date)+'</span>'+(a.by?'<span class="tl-by">· '+esc(a.by)+'</span>':'')+
       '<button class="tl-del" data-act="'+a.id+'">löschen</button></div>'+
     (a.note?'<div class="tl-note">'+esc(a.note)+'</div>':'')+
     (a.noteImg?'<div class="tl-note"><img src="'+esc(a.noteImg)+'" data-actimg="'+a.id+'" title="Handschrift – Klick öffnet groß" style="max-width:100%;max-height:240px;border:1px solid var(--line);border-radius:8px;background:#fff;cursor:pointer;display:block"></div>':'')+offer+
   '</div>';
 }
 function fmtEur(v){var n=parseFloat(String(v).replace(/[^0-9.,-]/g,"").replace(/\./g,"").replace(",","."));if(isNaN(n))return String(v);return n.toLocaleString("de-DE")+" €";}
 // Aktivität löschen
 document.getElementById("view-detail").addEventListener("click",function(e){
   // Anrufstart merken (tel:-Link) -> nach Rueckkehr in die App kurz nachfragen. Waehlen NICHT verhindern.
   var tl=e.target.closest('a[href^="tel:"]');
   if(tl){pcWrite({cid:curId,ts:Date.now()});setTimeout(checkPendingCall,15000);}
   var db=e.target.closest("[data-delbild]");if(db){e.preventDefault();var dc=byId(curId);var di=parseInt(db.getAttribute("data-delbild"),10);if(dc&&dc.bilder&&dc.bilder[di]!=null&&confirm("Dieses Bild entfernen?")){dc.bilder.splice(di,1);if(!dc.bilder.length)delete dc.bilder;dc.updated=Date.now();saveContact(dc);openDetail(curId);}return;}
   var ai=e.target.closest("[data-actimg]");if(ai){e.preventDefault();var ac=byId(curId);var aid=ai.getAttribute("data-actimg");var aa=ac&&(ac.activities||[]).filter(function(x){return x.id===aid;})[0];if(aa&&aa.noteImg)openImage(aa.noteImg);return;}
   var ib=e.target.closest("[data-bild]");if(ib){e.preventDefault();var bc=byId(curId);var bi=parseInt(ib.getAttribute("data-bild"),10);if(bc&&bc.bilder&&bc.bilder[bi])openImage(bc.bilder[bi]);return;}
   var pb=e.target.closest("[data-pdfact]");if(pb){e.preventDefault();var pid=pb.getAttribute("data-pdfact");var pc=byId(curId);var pa=pc&&(pc.activities||[]).filter(function(x){return x.id===pid;})[0];if(pa&&pa.pdf)openPdfUri(pa.pdf);return;}
   var mb=e.target.closest("[data-makepdf]");if(mb){e.preventDefault();var mid=mb.getAttribute("data-makepdf");if(navigator.onLine===false){alert("Zum Erstellen des PDFs bitte einmal online gehen.");return;}queuePdfGen(curId,mid,true);return;}
   var mr=e.target.closest("[data-mailreply]");if(mr){e.preventDefault();startMailReply(mr.getAttribute("data-mailreply"));return;}
   var mo=e.target.closest("[data-mailoffer]");if(mo){e.preventDefault();startMailOffer(mo.getAttribute("data-mailoffer"));return;}
   var lo=e.target.closest("[data-actid]");if(lo){var aid=lo.getAttribute("data-actid");var cc=byId(curId);var act=cc&&(cc.activities||[]).filter(function(x){return x.id===aid;})[0];try{if(act&&act.config)localStorage.setItem("amb_lepton_loadoffer_data",JSON.stringify(act.config));else if(act&&act.offer)localStorage.setItem("amb_lepton_loadoffer",act.offer);}catch(_){}return;} // Link navigiert selbst zum Konfigurator
   var d=e.target.closest(".tl-del");if(!d)return;var aid=d.getAttribute("data-act");var c=byId(curId);if(!c)return;
   c.activities=(c.activities||[]).filter(function(x){return x.id!==aid;});c.updated=Date.now();saveContact(c);openDetail(curId);
 });

 /* ---------- Aktivität-Modal ---------- */
 var actType="anruf",actForId=null,_offerReturnState=null,_offerReturnPdf=null;
 var modal=document.getElementById("actModal");
 document.getElementById("actSeg").addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;actType=b.getAttribute("data-t");var bs=this.querySelectorAll("button");for(var i=0;i<bs.length;i++)bs[i].classList.toggle("on",bs[i]===b);toggleOfferField();});
 function toggleOfferField(){
   document.getElementById("actOfferWrap").style.display=(actType==="angebot")?"":"none";
   var mw=document.getElementById("actMailWrap");
   if(mw){
     var isMail=(actType==="mailout");
     mw.style.display=isMail?"":"none";
     if(isMail){
       var c=byId(actForId)||{};
       var to=document.getElementById("actMailTo");if(to&&!to.value)to.value=c.mail||"";
       var su=document.getElementById("actMailSubj");if(su&&!su.value)su.value=c.firma?("Ihre Anfrage – "+c.firma):"";
     }
   }
 }
 function openActModal(id){
   actForId=id;actType="anruf";_offerReturnState=null;_offerReturnPdf=null;
   var bs=document.querySelectorAll("#actSeg button");for(var i=0;i<bs.length;i++)bs[i].classList.toggle("on",bs[i].getAttribute("data-t")==="anruf");
   document.getElementById("actDate").value=nowLocalInput();
   document.getElementById("actNote").value="";
   document.getElementById("actOfferNr").value="";document.getElementById("actBetrag").value="";
   document.getElementById("actFu").checked=true;document.getElementById("actFuDays").value=7;
   var ms=document.getElementById("actMailSend");if(ms)ms.checked=false;
   var mf=document.getElementById("actMailFields");if(mf)mf.style.display="none";
   var mt=document.getElementById("actMailTo");if(mt)mt.value="";
   var msu=document.getElementById("actMailSubj");if(msu)msu.value="";
   var maw=document.getElementById("actMailAtt");if(maw)maw.style.display="none";
   _mailReplyCtx=null;_mailAttach=null;
   // Angebote aus Konfigurator füllen
   var offers=loadOffers();var sel=document.getElementById("actOffer");
   var names=Object.keys(offers).sort();
   sel.innerHTML='<option value="">— keines —</option>'+names.map(function(n){
     var o=offers[n]||{};var nr=(o.fields&&o.fields.m_nr)?(" · Nr "+o.fields.m_nr):"";
     return '<option value="'+esc(n)+'">'+esc(n)+esc(nr)+'</option>';
   }).join("");
   toggleOfferField();
   setNoteMode("text");_pad.inited=false;padClear();
   modal.classList.add("open");
 }
 /* ---- Notiz: Text  <->  echte Handschrift (Zeichenfeld) ---- */
 var noteMode="text";
 var _pad={canvas:null,ctx:null,drawing:false,ink:false,last:null,inited:false};
 function setNoteMode(m){
   noteMode=m;
   var ta=document.getElementById("actNote"),pw=document.getElementById("actPadWrap");
   if(ta)ta.style.display=(m==="text")?"":"none";
   if(pw)pw.style.display=(m==="draw")?"":"none";
   var bt=document.getElementById("noteModeText"),bd=document.getElementById("noteModeDraw");
   if(bt)bt.classList.toggle("on",m==="text");if(bd)bd.classList.toggle("on",m==="draw");
   if(m==="draw"&&!_pad.inited){setTimeout(function(){padInit();_pad.inited=true;},30);}
 }
 function padInit(){
   var cv=document.getElementById("actPad");if(!cv)return;_pad.canvas=cv;
   var r=cv.getBoundingClientRect();var dpr=window.devicePixelRatio||1;
   cv.width=Math.max(1,Math.round(r.width*dpr));cv.height=Math.max(1,Math.round(r.height*dpr));
   var ctx=cv.getContext("2d");ctx.scale(dpr,dpr);ctx.lineCap="round";ctx.lineJoin="round";ctx.strokeStyle="#16181a";ctx.lineWidth=2.4;
   _pad.ctx=ctx;_pad.ink=false;
   function pos(e){var b=cv.getBoundingClientRect();return {x:e.clientX-b.left,y:e.clientY-b.top};}
   cv.onpointerdown=function(e){e.preventDefault();try{cv.setPointerCapture(e.pointerId);}catch(_){}_pad.drawing=true;_pad.last=pos(e);};
   cv.onpointermove=function(e){if(!_pad.drawing)return;e.preventDefault();var p=pos(e);ctx.lineWidth=(e.pressure&&e.pressure>0)?(1.1+e.pressure*3.2):2.4;ctx.beginPath();ctx.moveTo(_pad.last.x,_pad.last.y);ctx.lineTo(p.x,p.y);ctx.stroke();_pad.last=p;_pad.ink=true;};
   cv.onpointerup=cv.onpointercancel=cv.onpointerleave=function(){_pad.drawing=false;};
 }
 function padClear(){if(_pad.ctx&&_pad.canvas){_pad.ctx.clearRect(0,0,_pad.canvas.width,_pad.canvas.height);}_pad.ink=false;}
 function padDataURL(){if(!_pad.canvas)return null;var s=_pad.canvas,o=document.createElement("canvas");o.width=s.width;o.height=s.height;var c=o.getContext("2d");c.fillStyle="#fff";c.fillRect(0,0,o.width,o.height);c.drawImage(s,0,0);return o.toDataURL("image/jpeg",0.85);}
 document.getElementById("noteModeText").onclick=function(){setNoteMode("text");};
 document.getElementById("noteModeDraw").onclick=function(){setNoteMode("draw");};
 document.getElementById("actPadClear").onclick=function(){padClear();};
 document.getElementById("actCancel").onclick=function(){modal.classList.remove("open");};
 document.getElementById("actCreateOffer").onclick=function(){var c=byId(actForId);if(c){modal.classList.remove("open");gotoConfigurator(c,true);}};
 // Mail senden an/aus -> Adress-/Betreff-Felder zeigen
 var _mailReplyCtx=null,_mailAttach=null;
 document.getElementById("actMailSend").onchange=function(){
   document.getElementById("actMailFields").style.display=this.checked?"":"none";
   if(this.checked){var c=byId(actForId)||{};var to=document.getElementById("actMailTo");if(to&&!to.value)to.value=c.mail||"";var su=document.getElementById("actMailSubj");if(su&&!su.value)su.value=c.firma?("Ihre Anfrage – "+c.firma):"";}
 };
 // KI-Antwortvorschlag -> entwirft Betreff + Text (nutzt ggf. die letzte eingegangene Mail als Kontext)
 document.getElementById("actMailAI").onclick=function(){
   var c=byId(actForId);if(!c)return;
   if(!aiReady()){alert("Bitte zuerst den KI-Schlüssel (CRM_SECRET) unter Daten eintragen.");return;}
   var btn=this;btn.disabled=true;var old=btn.innerHTML;btn.textContent="KI denkt…";
   // Kontext: letzte eingegangene Mail (falls per „KI-Antwort" gestartet) ODER aktueller Notiztext
   var ctx=_mailReplyCtx;
   var payload={firma:c.firma||"",name:displayName(c),subject:ctx?(ctx.subject||""):(document.getElementById("actMailSubj").value||""),text:ctx?(ctx.text||""):(document.getElementById("actNote").value||"(keine eingegangene Nachricht – formuliere eine freundliche Erstkontakt-/Nachfass-Mail)")};
   apiMailReply(payload).then(function(d){
     btn.disabled=false;btn.innerHTML=old;
     if(d&&d.error){alert("KI-Fehler: "+d.error);return;}
     if(!document.getElementById("actMailSend").checked){document.getElementById("actMailSend").checked=true;document.getElementById("actMailFields").style.display="";}
     if(d.subject)document.getElementById("actMailSubj").value=d.subject;
     setNoteMode("text");
     if(d.body)document.getElementById("actNote").value=d.body;
     var to=document.getElementById("actMailTo");if(to&&!to.value)to.value=c.mail||"";
   },function(e){btn.disabled=false;btn.innerHTML=old;alert("KI-Vorschlag fehlgeschlagen: "+(e&&e.message||e));});
 };
 // „KI-Antwort" auf eine eingegangene Mail -> Modal als „Mail raus" öffnen, Kontext setzen, KI-Vorschlag starten.
 function startMailReply(actId){
   var c=byId(curId);if(!c)return;
   var src=(c.activities||[]).filter(function(x){return x.id===actId;})[0];if(!src)return;
   if(!aiReady()){alert("Bitte zuerst den KI-Schlüssel (CRM_SECRET) unter Daten eintragen.");return;}
   openActModal(curId);
   // auf „Mail raus" umschalten
   actType="mailout";var bs=document.querySelectorAll("#actSeg button");for(var i=0;i<bs.length;i++)bs[i].classList.toggle("on",bs[i].getAttribute("data-t")==="mailout");
   toggleOfferField();
   document.getElementById("actMailSend").checked=true;document.getElementById("actMailFields").style.display="";
   document.getElementById("actMailTo").value=c.mail||"";
   var orig=src.note||"";var m=orig.match(/^Betreff:\s*(.+)$/m);
   document.getElementById("actMailSubj").value=m?("Re: "+m[1].trim()):(c.firma?("Re: "+c.firma):"Re:");
   _mailReplyCtx={subject:m?m[1].trim():"",text:orig};
   // KI gleich starten
   document.getElementById("actMailAI").click();
 }
 // „Angebot per E-Mail senden" -> Modal als „Mail raus" öffnen, das PDF anhängen, Standardtext vorbelegen.
 function startMailOffer(actId){
   var c=byId(curId);if(!c)return;
   var src=(c.activities||[]).filter(function(x){return x.id===actId;})[0];if(!src||!src.pdf){alert("Für dieses Angebot gibt es noch kein PDF. Bitte zuerst auf PDF erstellen tippen.");return;}
   openActModal(curId);
   actType="mailout";var bs=document.querySelectorAll("#actSeg button");for(var i=0;i<bs.length;i++)bs[i].classList.toggle("on",bs[i].getAttribute("data-t")==="mailout");
   toggleOfferField();
   document.getElementById("actMailSend").checked=true;document.getElementById("actMailFields").style.display="";
   document.getElementById("actMailTo").value=c.mail||"";
   var nr=src.offerNr?(" "+src.offerNr):"";
   document.getElementById("actMailSubj").value="Ihr Angebot – Sternsiebanlage Lepton 5100"+nr;
   var nm="Angebot_Lepton_5100"+(src.offerNr?("_"+String(src.offerNr).replace(/[^0-9A-Za-z-]/g,"")):"")+".pdf";
   _mailAttach=[{name:nm,dataUri:src.pdf,contentType:"application/pdf"}];
   var att=document.getElementById("actMailAtt");if(att){att.style.display="";document.getElementById("actMailAttName").textContent=nm+" (wird angehängt)";}
   var nt=document.getElementById("actNote");
   var anrede=c.nachname?("Sehr geehrte"+( (c.anrede||"").indexOf("Frau")>=0?" Frau ":(c.anrede||"").indexOf("Herr")>=0?"r Herr ":" Damen und Herren")):"Sehr geehrte Damen und Herren";
   var name=(c.anrede&&c.nachname)?(anrede+c.nachname):anrede;
   nt.value=name+",\n\nvielen Dank für Ihr Interesse an der Sternsiebanlage Lepton 5100. Im Anhang finden Sie unser Angebot.\n\nFür Rückfragen stehe ich Ihnen gerne zur Verfügung.\n\nMit freundlichen Grüßen\n"+((CUR&&CUR.n)||"")+"\nAlzinger Maschinenbau GmbH";
 }
 modal.addEventListener("click",function(e){if(e.target===modal)modal.classList.remove("open");});

 /* ---------- Anruf-Protokoll: tel:-Klick merken, nach Rueckkehr kurz nachfragen ----------
    Browser duerfen Anrufliste/Dauer nicht lesen -> halbautomatisch: Zeitpunkt + wer automatisch,
    Gespraechsnotiz per Kurz-Dialog. Pending ueberlebt App-Neustart (localStorage). */
 var PCKEY="amb_crm_pendingcall";
 function pcRead(){try{return JSON.parse(localStorage.getItem(PCKEY)||"null");}catch(e){return null;}}
 function pcWrite(o){try{if(o)localStorage.setItem(PCKEY,JSON.stringify(o));else localStorage.removeItem(PCKEY);}catch(e){}}
 var callBg=document.getElementById("callModal");
 function checkPendingCall(){
   if(callBg.classList.contains("open"))return;
   var p=pcRead();if(!p)return;
   var age=Date.now()-(p.ts||0);
   if(age<5000)return;                          // Waehlvorgang laeuft evtl. noch
   if(age>6*3600*1000){pcWrite(null);return;}   // aelter als 6h -> stillschweigend verwerfen
   var c=byId(p.cid);if(!c){pcWrite(null);return;}
   document.getElementById("callTitle").textContent="Anruf bei "+displayName(c)+" erfassen?";
   document.getElementById("callNote").value="";
   callBg.classList.add("open");
 }
 function pcFinish(note){
   var p=pcRead();pcWrite(null);callBg.classList.remove("open");
   if(note==null||!p)return;
   var c=byId(p.cid);if(!c)return;
   c.activities=c.activities||[];
   c.activities.push({id:uid(),type:"anruf",date:p.ts||Date.now(),note:note,by:(CUR&&CUR.n)||""});
   c.updated=Date.now();saveContact(c);
   if(curView==="detail"&&curId===c.id)openDetail(c.id);
 }
 document.getElementById("callSave").onclick=function(){pcFinish(document.getElementById("callNote").value.trim());};
 document.getElementById("callNoAnswer").onclick=function(){pcFinish("Nicht erreicht.");};
 document.getElementById("callDiscard").onclick=function(){pcFinish(null);};
 document.addEventListener("visibilitychange",function(){if(!document.hidden)setTimeout(checkPendingCall,400);});
 window.addEventListener("focus",function(){setTimeout(checkPendingCall,400);});

 // Rücksprung aus dem Konfigurator: Angebot wurde gespeichert -> Aktivität „Angebot gesendet" vorbereiten.
 function checkOfferReturn(){
   try{var d=localStorage.getItem("amb_lepton_offer_done");if(!d)return;localStorage.removeItem("amb_lepton_offer_done");
     var o=JSON.parse(d);if(!o||!o.contactId)return;var c=byId(o.contactId);if(!c)return;
     // Nachträglich erzeugtes PDF für ein bestehendes Angebot -> direkt an der Aktivität ablegen.
     if(o.makepdfActId){var ma=(c.activities||[]).filter(function(x){return x.id===o.makepdfActId;})[0];
       if(ma&&o.pdf){ma.pdf=o.pdf;c.updated=Date.now();saveContact(c);}
       openDetail(o.contactId);
       if(!o.pdf)setTimeout(function(){alert("Das PDF konnte nicht erzeugt werden. Bitte einmal online versuchen.");},100);
       return;}
     openDetail(o.contactId);openActModal(o.contactId);
     _offerReturnState=o.state||null; // volle Angebots-Konfiguration -> wird in der Aktivität gespeichert
     _offerReturnPdf=o.pdf||null;     // fertiges PDF (data-URI) -> ohne Konfigurator ansehbar
     actType="angebot";var bs=document.querySelectorAll("#actSeg button");for(var i=0;i<bs.length;i++)bs[i].classList.toggle("on",bs[i].getAttribute("data-t")==="angebot");
     toggleOfferField();
     var sel=document.getElementById("actOffer");if(sel){var has=false;for(var j=0;j<sel.options.length;j++)if(sel.options[j].value===o.name)has=true;if(!has){var op=document.createElement("option");op.value=o.name;op.textContent=o.name;sel.appendChild(op);}sel.value=o.name;}
     document.getElementById("actOfferNr").value=o.nr||"";
     document.getElementById("actBetrag").value=o.betrag?String(Math.round(o.betrag)):"";
     var nt=document.getElementById("actNote");if(nt&&!nt.value)nt.value="Angebot im Konfigurator erstellt: "+(o.name||"");
   }catch(e){}
 }
 document.getElementById("actSave").onclick=function(){
   var c=byId(actForId);if(!c)return;
   var sb=document.getElementById("actSave");
   var dv=document.getElementById("actDate").value;var ts=dv?new Date(dv).getTime():Date.now();
   var a={id:uid(),type:actType,date:ts,note:document.getElementById("actNote").value.trim(),by:(CUR&&CUR.n)||""};
   if(actType==="angebot"){var off=document.getElementById("actOffer").value;if(off)a.offer=off;var onr=document.getElementById("actOfferNr").value.trim();if(onr)a.offerNr=onr;var ab=document.getElementById("actBetrag").value.trim();if(ab)a.betrag=ab;
     // Wenn ein Konfigurator-Angebot gewählt wurde, Nr automatisch übernehmen
     var offs=loadOffers();if(off&&!a.offerNr){var o=offs[off];if(o&&o.fields&&o.fields.m_nr)a.offerNr=o.fields.m_nr;}
     // Volle Angebots-Konfiguration in der Aktivität ablegen -> liegt im CRM, geräteübergreifend.
     var cfg=_offerReturnState||(off&&offs[off])||null;if(cfg)a.config=cfg;
     if(_offerReturnPdf)a.pdf=_offerReturnPdf;}
   function finish(){
     c.activities=c.activities||[];c.activities.push(a);
     // Status automatisch hochstufen
     if(actType==="angebot"&&(c.status==="lead"||c.status==="interessent"))c.status="angebot";
     else if((actType==="anruf"||actType==="mailin"||actType==="besuch")&&c.status==="lead")c.status="interessent";
     // Automatische Wiedervorlage
     if(document.getElementById("actFu").checked){
       var days=parseInt(document.getElementById("actFuDays").value,10)||7;
       var due=startOfDay(ts+days*86400000)+9*3600000;
       var note=actType==="angebot"?"Angebot nachfassen":(actType==="anruf"?"Erneut anrufen":"Nachfassen");
       c.followup={due:due,note:note,done:false};
     }
     c.updated=Date.now();saveContact(c);sb.disabled=false;sb.textContent="Speichern";modal.classList.remove("open");openDetail(actForId);
   }
   // Mail raus + „jetzt senden" angehakt -> E-Mail über Microsoft 365 verschicken, dann als Aktivität ablegen.
   if(actType==="mailout"&&document.getElementById("actMailSend").checked){
     var to=(document.getElementById("actMailTo").value||"").trim();
     var subj=(document.getElementById("actMailSubj").value||"").trim();
     var bodyTxt=document.getElementById("actNote").value.trim();
     if(!to){alert("Bitte eine Empfänger-Adresse eintragen.");return;}
     if(!bodyTxt){alert("Bitte einen E-Mail-Text eingeben (das Notizfeld ist der Mailtext).");return;}
     sb.disabled=true;sb.textContent="Sende E-Mail…";
     msMailToken(true).then(function(tok){
       if(!tok)throw new Error("Kein Mail-Zugriff – bitte im Microsoft-Login der Berechtigung Mail.Send zustimmen.");
       return graphSendMail(tok,to,subj,bodyTxt,_mailAttach);
     }).then(function(){
       a.note=(subj?("Betreff: "+subj+"\n"):"")+bodyTxt;a.mailTo=to;a.mailSent=true;
       if(_mailAttach&&_mailAttach.length)a.mailAtt=_mailAttach[0].name;
       finish();
     },function(e){sb.disabled=false;sb.textContent="Speichern";alert("E-Mail konnte nicht gesendet werden: "+(e&&e.message||e)+"\n\nDie Aktivität wurde NICHT gespeichert.");});
     return;
   }
   // Handschrift-Notiz -> Bild in den Cloud-Speicher laden, URL an der Aktivität ablegen
   if(noteMode==="draw"&&_pad.ink){
     sb.disabled=true;sb.textContent="Speichere Handschrift…";
     sbUploadImage(padDataURL()).then(function(url){a.noteImg=url;},function(){a.noteImg=padDataURL();}).then(finish);
     return;
   }
   finish();
 };

 /* ---------- Formular (Neu/Bearbeiten) ---------- */
 function fInput(id,label,val,type,full,ph){return '<div class="fg'+(full?' full':'')+'"><label>'+label+'</label><input class="field" id="f_'+id+'" type="'+(type||"text")+'" value="'+esc(val||"")+'"'+(ph?' placeholder="'+esc(ph)+'"':'')+'></div>';}
 function openForm(id){
   var c=id?byId(id):null;var isNew=!c;c=c||{};
   var statusSel='<div class="fg"><label>Status</label><select class="field" id="f_status">'+STATUS.map(function(s){return '<option value="'+s[0]+'"'+((c.status||"lead")===s[0]?' selected':'')+'>'+esc(s[1])+'</option>';}).join("")+'</select></div>';
   var landSel='<div class="fg"><label>Land</label><select class="field" id="f_land">'+LANDS.map(function(l){return '<option value="'+l[0]+'"'+((c.land||"DE")===l[0]?' selected':'')+'>'+esc(l[1])+'</option>';}).join("")+'</select></div>';
   var blandSel='<div class="fg"><label>Bundesland</label><select class="field" id="f_bundesland"><option value="">—</option>'+BL.map(function(b){return '<option'+(contactBundesland(c)===b?' selected':'')+'>'+esc(b)+'</option>';}).join("")+'</select></div>';
   var ownerSel='<div class="fg"><label>Betreuer (Vertriebler)</label><select class="field" id="f_owner"><option value="">—</option>'+
     USERS.filter(function(u){return u.n&&!u.hd;}).map(function(u){var sel=(c.owner||(CUR&&CUR.n))===u.n?' selected':'';return '<option'+sel+'>'+esc(u.n)+'</option>';}).join("")+'</select></div>';
   var html=''+
   '<button class="btn ghost sm" id="fBack" style="margin-bottom:10px">← Zurück</button>'+
   '<h2 class="vh">'+(isNew?"Neuer Kontakt / Lead":"Kontakt bearbeiten")+'</h2>'+
   '<div class="sub">Pflicht ist nur ein Name (Firma oder Person).</div>'+
   (aiReady()?'<div style="margin:6px 0 14px;padding:12px;background:var(--field);border:1px dashed var(--line-strong);border-radius:12px">'+
     '<div style="display:flex;gap:8px;flex-wrap:wrap">'+
     '<button class="btn primary" id="fScan" type="button"><svg viewBox="0 0 24 24"><path d="M3 7a2 2 0 012-2h2l1.5-2h7L17 5h2a2 2 0 012 2v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><circle cx="12" cy="12.5" r="3.5"/></svg>Visitenkarte fotografieren</button>'+
     '<button class="btn" id="fScanGal" type="button"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>Aus Galerie laden</button>'+
     '</div>'+
     '<input type="file" id="fScanFile" accept="image/*" capture="environment" class="hidden">'+
     '<input type="file" id="fScanGalFile" accept="image/*" class="hidden">'+
     '<div id="fScanMsg" style="font-size:13px;color:var(--muted);margin-top:8px">Visitenkarte fotografieren oder ein vorhandenes Bild aus der Galerie laden – die KI füllt die Felder automatisch aus. Danach kurz prüfen und speichern.</div></div>':'')+
   '<div class="form-grid">'+
     fInput("firma","Firma",c.firma,"text",true)+
     fInput("firma2","Zusatz / Abteilung",c.firma2,"text",true)+
     fInput("anrede","Anrede / Titel",c.anrede)+
     '<div class="fg"></div>'+
     fInput("vorname","Vorname",c.vorname)+
     fInput("nachname","Nachname",c.nachname)+
     fInput("strasse","Straße &amp; Nr.",c.strasse,"text",true)+
     fInput("plz","PLZ",c.plz)+
     fInput("ort","Ort",c.ort)+
     blandSel+
     landSel+statusSel+
     fInput("tel","Telefon",c.tel,"tel")+
     fInput("mobil","Mobil",c.mobil,"tel")+
     fInput("mail","E-Mail",c.mail,"email")+
     fInput("web","Webseite",c.web)+
     fInput("ustid","USt-IdNr.",c.ustid)+
     fInput("gf","Geschäftsführer",c.gf)+
     fInput("bl","Betriebsleiter",c.bl)+
     fInput("menge","Jahresmenge (z. B. 30.000 t/Jahr)",c.menge)+
     '<div class="fg"><label>Siebtechnik</label><select class="field" id="f_sieb">'+
       ["","Sternsieb","Trommelsieb","Sonstige/unbekannt"].map(function(s){return '<option'+((c.sieb||"")===s?' selected':'')+'>'+esc(s)+'</option>';}).join("")+'</select></div>'+
     fInput("quelle","Quelle (Messe, Empfehlung…)",c.quelle)+
     ownerSel+
     '<div class="fg full"><label>News (aktuell)</label><textarea class="field" id="f_news" placeholder="z. B. Erweiterung 2026, neue Anlage…">'+esc(c.news||"")+'</textarea></div>'+
     '<div class="fg full"><label>Notizen</label><textarea class="field" id="f_notiz" placeholder="Bedarf, Maschinen, Besonderheiten…">'+esc(c.notiz||"")+'</textarea></div>'+
   '</div>'+
   '<div class="form-actions">'+
     '<button class="btn primary" id="fSave">Speichern</button>'+
     '<button class="btn ghost" id="fCancel">Abbrechen</button>'+
   '</div>';
   var v=document.getElementById("view-form");v.innerHTML=html;show("form");
   function done(){if(id){openDetail(id);}else{renderList();show("list");}}
   document.getElementById("fBack").onclick=done;
   document.getElementById("fCancel").onclick=done;
   // Visitenkarten-Scan: Foto ODER Galerie-Bild -> KI -> Formularfelder füllen (nur leere überschreiben).
   var _scanBtn=document.getElementById("fScan");
   if(_scanBtn){
     var _scanGal=document.getElementById("fScanGal");
     function processScan(f){
       if(!f)return;
       var msg=document.getElementById("fScanMsg");msg.style.color="var(--muted)";msg.textContent="Bild wird ausgewertet … (ein paar Sekunden)";_scanBtn.disabled=true;if(_scanGal)_scanGal.disabled=true;
       function endBtns(){_scanBtn.disabled=false;if(_scanGal)_scanGal.disabled=false;}
       downscaleImage(f,1600,function(uri){
         if(!uri){msg.textContent="Bild konnte nicht gelesen werden – bitte erneut versuchen.";endBtns();return;}
         apiCardScan(uri).then(function(card){
           var setF=function(k,val){var el=document.getElementById("f_"+k);if(el&&val&&String(val).trim())el.value=String(val).trim();};
           ["firma","anrede","vorname","nachname","strasse","plz","ort","tel","mobil","mail","web","ustid"].forEach(function(k){setF(k,card[k]);});
           if(card.position)setF("firma2",card.position);
           if(card.land){var ls=document.getElementById("f_land");if(ls){var code=String(card.land).toUpperCase().slice(0,2);for(var i=0;i<ls.options.length;i++)if(ls.options[i].value===code){ls.value=code;break;}}}
           if(card.plz&&(card.land||"").toUpperCase().slice(0,2)==="DE"){var pe=document.getElementById("f_plz");if(pe&&/^\d{1,4}$/.test(pe.value)){while(pe.value.length<5)pe.value="0"+pe.value;}}
           var any=["firma","vorname","nachname","mail","tel","mobil"].some(function(k){return card[k]&&String(card[k]).trim();});
           msg.style.color=any?"#15803d":"var(--muted)";
           msg.textContent=any?"✓ Übernommen – bitte prüfen, ggf. ergänzen und speichern.":"Auf dem Bild konnten keine Daten erkannt werden. Schärfer/näher und erneut versuchen.";
           endBtns();
         }).catch(function(err){msg.style.color="#b91c1c";msg.textContent="Scan fehlgeschlagen: "+String((err&&err.message)||err)+(/scan 404/.test(String(err&&err.message))?" (KI-Funktion noch nicht eingerichtet – Reiter Daten)":"");endBtns();});
       });
     }
     _scanBtn.onclick=function(){document.getElementById("fScanFile").click();};
     document.getElementById("fScanFile").onchange=function(e){var f=e.target.files&&e.target.files[0];e.target.value="";processScan(f);};
     if(_scanGal){
       _scanGal.onclick=function(){document.getElementById("fScanGalFile").click();};
       document.getElementById("fScanGalFile").onchange=function(e){var f=e.target.files&&e.target.files[0];e.target.value="";processScan(f);};
     }
   }
   document.getElementById("fSave").onclick=function(){
     function g(k){var e=document.getElementById("f_"+k);return e?e.value.trim():"";}
     var rec=c.id?c:{id:uid(),created:Date.now(),activities:[]};
     ["firma","firma2","anrede","vorname","nachname","strasse","plz","ort","bundesland","land","status","tel","mobil","mail","web","ustid","gf","bl","menge","sieb","news","quelle","owner","notiz"].forEach(function(k){rec[k]=g(k);});
     if(!rec.firma&&!rec.vorname&&!rec.nachname){alert("Bitte mindestens eine Firma oder einen Namen angeben.");return;}
     rec.updated=Date.now();
     if(!c.id)DB.contacts.push(rec);
     saveContact(rec);openDetail(rec.id);
   };
 }

 /* ---------- FAB ---------- */
 document.getElementById("fab").onclick=function(){openForm(null);};

 /* ---------- Suche/Filter Listener ---------- */
 ["q"].forEach(function(id){document.getElementById(id).addEventListener("input",renderList);});
 ["fStatus","fLand","fBL","fOwner","fSort"].forEach(function(id){document.getElementById(id).addEventListener("change",renderList);});
 document.getElementById("qLead").addEventListener("input",renderLeads);
 document.getElementById("fLeadLand").addEventListener("change",renderLeads);

 /* ---------- Daten: Export/Import ---------- */
 document.getElementById("expBtn").onclick=function(){
   var blob=new Blob([JSON.stringify(DB,null,2)],{type:"application/json"});
   var a=document.createElement("a");a.href=URL.createObjectURL(blob);
   a.download="amb-crm-"+todayStr()+".json";a.click();setTimeout(function(){URL.revokeObjectURL(a.href);},2000);
 };
 document.getElementById("impBtn").onclick=function(){document.getElementById("impFile").click();};
 document.getElementById("impFile").onchange=function(e){
   var f=e.target.files[0];if(!f)return;var rd=new FileReader();
   rd.onload=function(){try{var inc=JSON.parse(rd.result);var list=inc.contacts||inc;if(!Array.isArray(list))throw 0;
     var mode=confirm("Importierte Kontakte ZUSAMMENFÜHREN (OK) oder bestehende ERSETZEN (Abbrechen)?");
     if(mode){var have={};DB.contacts.forEach(function(c){have[c.id]=c;});var added=[];list.forEach(function(c){if(c.id&&have[c.id]){}else{if(!c.id)c.id=uid();if(!c.activities)c.activities=[];DB.contacts.push(c);added.push(c);}});bulkSave(added,false);}
     else{DB.contacts=list.map(function(c){if(!c.id)c.id=uid();if(!c.activities)c.activities=[];return c;});bulkSave(DB.contacts,true);}
     alert("Import abgeschlossen: "+list.length+" Kontakte verarbeitet.");renderList();renderDashboard();show("list");
   }catch(err){alert("Datei konnte nicht gelesen werden (kein gültiges CRM-JSON).");}};
   rd.readAsText(f);e.target.value="";
 };
 // CSV
 document.getElementById("csvBtn").onclick=function(){document.getElementById("csvFile").click();};
 document.getElementById("csvFile").onchange=function(e){var f=e.target.files[0];if(!f)return;var rd=new FileReader();rd.onload=function(){var n=importCSV(rd.result);alert(n+" Leads importiert.");initFilters();renderList();renderDashboard();show("list");};rd.readAsText(f);e.target.value="";};
 // OneNote/Notiz -> Kontakt + Verlauf per KI
 var NOTE_ATYPES={anruf:1,mailout:1,mailin:1,besuch:1,angebot:1,notiz:1};
 function noteDateTs(s){s=String(s||"").trim();var m=s.match(/^(\d{4})-(\d{2})-(\d{2})/);if(m){var d=new Date(+m[1],+m[2]-1,+m[3],9,0,0);if(!isNaN(d))return d.getTime();}var d2=new Date(s);return isNaN(d2)?Date.now():d2.getTime();}
 // Bild aus Data-/Blob-URL verkleinern (für eingefügte/angehängte Bilder).
 function downscaleSrc(src,maxDim,cb,cors){
   try{var img=new Image();if(cors)img.crossOrigin="anonymous";img.onload=function(){try{var w=img.width,h=img.height,s=Math.min(1,maxDim/Math.max(w,h||1));var cw=Math.max(1,Math.round(w*s)),ch=Math.max(1,Math.round(h*s));var cv=document.createElement("canvas");cv.width=cw;cv.height=ch;cv.getContext("2d").drawImage(img,0,0,cw,ch);cb(cv.toDataURL("image/jpeg",0.8));}catch(e){cb(null);}};img.onerror=function(){cb(null);};img.src=src;}catch(e){cb(null);}
 }
 // Bilder einsammeln: aus dem eingefügten Inhalt (img) + aus der Datei-Auswahl. Max 6.
 function gatherNoteImages(cb){
   var tasks=[],ne=document.getElementById("noteIn");
   if(ne){var imgs=ne.querySelectorAll("img");for(var i=0;i<imgs.length&&tasks.length<6;i++){var s=imgs[i].src||"";if(/^data:image\//i.test(s)||/^blob:/i.test(s))tasks.push({t:"src",v:s});}}
   var fi=document.getElementById("noteImgs");if(fi&&fi.files)for(var j=0;j<fi.files.length&&tasks.length<6;j++)tasks.push({t:"file",v:fi.files[j]});
   if(!tasks.length){cb([]);return;}
   var out=[],done=0;function fin(){done++;if(done>=tasks.length)cb(out.filter(Boolean));}
   tasks.forEach(function(tk){if(tk.t==="file")downscaleImage(tk.v,1400,function(u){if(u&&u.length<2500000)out.push(u);fin();});else downscaleSrc(tk.v,1400,function(u){if(u&&u.length<2500000)out.push(u);fin();});});
 }
 (function(){var nb=document.getElementById("noteBtn");if(!nb)return;
   var ne=document.getElementById("noteIn"),imgBtn=document.getElementById("noteImgBtn"),imgIn=document.getElementById("noteImgs"),clr=document.getElementById("noteClear"),msg=document.getElementById("noteMsg");
   function imgCount(){var n=0;if(ne)n+=ne.querySelectorAll("img").length;if(imgIn&&imgIn.files)n+=imgIn.files.length;return n;}
   function setMsg(){var n=imgCount();msg.style.color="var(--muted)";msg.textContent=n?(n+" Bild(er) erkannt"):"";}
   if(imgBtn)imgBtn.onclick=function(){imgIn.click();};
   if(imgIn)imgIn.onchange=function(){setMsg();};
   if(ne)ne.addEventListener("input",setMsg);
   if(clr)clr.onclick=function(){if(ne)ne.innerHTML="";if(imgIn)imgIn.value="";msg.textContent="";};
   nb.onclick=function(){
     var txt=(ne?(ne.innerText||ne.textContent||""):"").trim();
     if(!txt){msg.style.color="var(--muted)";msg.textContent="Bitte zuerst eine OneNote-Seite einfügen.";return;}
     if(!aiReady()){msg.style.color="#b91c1c";msg.textContent="KI ist nicht eingerichtet (Reiter Daten → KI-Schlüssel).";return;}
     msg.style.color="var(--muted)";msg.textContent="KI wertet die Notiz aus … (ein paar Sekunden)";nb.disabled=true;
     gatherNoteImages(function(bilder){
       apiNoteScan(txt).then(function(res){
         var c=res.contact||{};var rec={id:uid(),created:Date.now(),updated:Date.now(),status:"lead",land:(String(c.land||"DE").toUpperCase().slice(0,2)||"DE"),activities:[],owner:(CUR&&CUR.n)||""};
         ["firma","anrede","vorname","nachname","strasse","plz","ort","bundesland","tel","mobil","mail","web","ustid"].forEach(function(k){var v=c[k]&&String(c[k]).trim();if(v)rec[k]=v;});
         if(c.position)rec.firma2=c.position;
         if(rec.plz&&rec.land==="DE"&&/^\d{1,4}$/.test(rec.plz)){while(rec.plz.length<5)rec.plz="0"+rec.plz;}
         (res.activities||[]).forEach(function(a){var ty=(a&&a.type||"notiz");if(!NOTE_ATYPES[ty])ty="notiz";rec.activities.push({id:uid(),type:ty,date:noteDateTs(a&&a.date),note:(a&&a.note)||"",by:(CUR&&CUR.n)||""});});
         rec.activities.sort(function(x,y){return (x.date||0)-(y.date||0);});
         if(bilder&&bilder.length)rec.bilder=bilder;
         if(!rec.firma&&!rec.nachname){msg.style.color="#b91c1c";msg.textContent="Konnte keine Firma/Person erkennen. Bitte mehr Text einfügen.";nb.disabled=false;return;}
         DB.contacts.push(rec);saveContact(rec);
         if(ne)ne.innerHTML="";if(imgIn)imgIn.value="";nb.disabled=false;msg.textContent="";
         openDetail(rec.id);
       }).catch(function(err){msg.style.color="#b91c1c";msg.textContent="Auswertung fehlgeschlagen: "+String((err&&err.message)||err);nb.disabled=false;});
     });
   };
 })();
 /* ===== OneNote-Massenimport: Login -> Notizbuch-Auswahl -> Schleife ===== */
 (function(){
   var btn=document.getElementById("msBtn");if(!btn)return;
   var stopBtn=document.getElementById("msStop"),prog=document.getElementById("msProg"),bar=document.getElementById("msBar"),msg=document.getElementById("msMsg");
   var booksBox=document.getElementById("msBooks"),bookList=document.getElementById("msBookList"),goBtn=document.getElementById("msGo");
   var _token=null,_books=[],_sections=[],_mode="recent";
   function setBar(done,total){bar.style.width=(total?Math.round(done/total*100):0)+"%";}
   function say(t,col){prog.style.display="block";msg.style.color=col||"var(--muted)";msg.innerHTML=t;}
   stopBtn.onclick=function(){_msStop=true;say("Wird gestoppt …");};
   function renderBooks(){
     // Pro Notizbuch (= Land): Haken + Dropdown, welcher Vertriebler die Kontakte betreut (Standard: eingeloggter Nutzer).
     var team=USERS.filter(function(u){return u.n&&!u.hd;});
     bookList.innerHTML=_books.map(function(n,i){
       var cnt=(n.count!=null)?(' <span style="color:var(--muted)">('+n.count+' Abschnitte)</span>'):"";
       var opts=team.map(function(u){var sel=((CUR&&CUR.n)===u.n)?' selected':'';return '<option'+sel+'>'+esc(u.n)+'</option>';}).join("");
       return '<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">'+
         '<label style="flex:1;min-width:160px;display:flex;align-items:center;gap:8px;font-size:14px;cursor:pointer"><input type="checkbox" class="msBk" data-i="'+i+'" checked> '+esc(n.name)+cnt+'</label>'+
         '<select class="field msOwn" data-i="'+i+'" title="Welcher Vertriebler betreut dieses Land?" style="width:auto;padding:4px 8px;font-size:13px">'+opts+'</select></div>';
     }).join("");
     booksBox.style.display="block";prog.style.display="none";btn.textContent="Erneut anmelden";
   }
   // 1) Login -> kuerzlich geoeffnete Notizbuecher (auch geteilte); Fallback: eigene Abschnitte
   btn.onclick=function(){
     if(!aiReady()){say("Bitte zuerst die KI einrichten (Reiter Daten → KI-Schlüssel).","#b91c1c");return;}
     _msStop=false;btn.disabled=true;booksBox.style.display="none";setBar(0,1);say("Anmeldung bei Microsoft … (Pop-up bestätigen)");
     msToken().then(function(t){_token=t;say("Angemeldet. Lese Notizbücher (auch geteilte) …");return graphRecentNotebooks(t).catch(function(){return [];});})
       .then(function(recents){
         if(recents&&recents.length){_mode="recent";_books=recents.slice().sort(function(a,b){return a.name.localeCompare(b.name);});btn.disabled=false;renderBooks();return;}
         // Fallback: nur eigene Notizbuecher ueber die Abschnitte
         return graphAllSections(_token).then(function(secs){_mode="sections";_sections=secs;btn.disabled=false;
           if(!secs.length){say("Keine Notizbücher gefunden. Bitte im Microsoft-Pop-up der Berechtigung Notes.Read.All zustimmen.","#b91c1c");return;}
           _books=notebooksFromSections(secs);renderBooks();});
       })
       .catch(function(e){btn.disabled=false;loginErr(e);});
   };
   document.getElementById("msAll").onclick=function(){bookList.querySelectorAll(".msBk").forEach(function(c){c.checked=true;});};
   document.getElementById("msNone").onclick=function(){bookList.querySelectorAll(".msBk").forEach(function(c){c.checked=false;});};
   // 2) Import der gewaehlten Notizbuecher
   goBtn.onclick=function(){
     var chosen=[],names=[],ownerByBook={};
     bookList.querySelectorAll(".msBk").forEach(function(c){if(c.checked){var i=+c.getAttribute("data-i"),b=_books[i];chosen.push(b);names.push(b.name);var os=bookList.querySelector('.msOwn[data-i="'+i+'"]');ownerByBook[b.name]=(os&&os.value)||((CUR&&CUR.n)||"");}});
     if(!names.length){say("Bitte mindestens ein Notizbuch auswählen.","#b91c1c");return;}
     _msStop=false;goBtn.disabled=true;btn.disabled=true;stopBtn.classList.remove("hidden");setBar(0,1);
     say("Öffne "+names.length+" Notizbuch(ern) … ("+esc(names.join(", "))+")");
     var added=[],fail=0,skip=0,token=_token,pages=[],dbg=[],imgFound=0,imgLoaded=0,imgRaw=0,imgSample="",imgAdded=0,sitesToken=null,savedUpto=0;
     msSitesToken().then(function(st){sitesToken=st;}); // nicht-blockierend: Bilder aus OneDrive der Kollegen (falls Admin-Freigabe da)
     // Bilder einer Seite laden (max 4) -> [dataURIs]; aktualisiert die Zaehler.
     function loadImgs(pc){
       imgRaw+=(pc.raw||0);if(!imgSample&&pc.sample)imgSample=pc.sample;
       var iu=(pc.imgs||[]).slice(0,4),bl=[];imgFound+=iu.length;
       return iu.reduce(function(pr,u){return pr.then(function(){return graphImage(token,sitesToken,u).then(function(d){if(d&&d.length<2500000){bl.push(d);imgLoaded++;}}).catch(function(e){if(dbg.length<8)dbg.push("Bild: "+String((e&&e.message)||e));});});},Promise.resolve()).then(function(){return sbStoreImages(bl);}); // -> URLs (Storage), Data-URI nur als Fallback
     }
     // Abschnitte der Auswahl ermitteln (recent: per URL aufloesen; sections: aus Cache filtern)
     var secsP;
     if(_mode==="recent"){secsP=sectionsFromBooks(token,chosen,function(bi,bt,b){say("Öffne Notizbuch "+(bi+1)+" / "+bt+": <b>"+esc(b.name)+"</b> …");},dbg);}
     else{var sel={};chosen.forEach(function(b){sel[b.id]=1;});secsP=Promise.resolve(_sections.filter(function(s){return sel[s.bookId];}));}
     secsP.then(function(secs){
       if(!secs.length){throw new Error("Diagnose – keine Abschnitte: "+(dbg.length?dbg.join(" | "):"(kein Protokoll)"));}
       say(secs.length+" Abschnitte – lese Seiten …");
       return pagesFromSections(token,secs,function(si,st,sec){if(si%5===0)say("Abschnitte werden gelesen … "+(si+1)+" / "+st+" &nbsp; <b>"+esc(sec.book||"")+"</b>");},dbg);})
       .then(function(ps){pages=ps;if(!pages.length){throw new Error("Diagnose – 0 Seiten bei Abschnitten: "+(dbg.length?dbg.join(" | "):"(kein Protokoll)"));}say(pages.length+" Seiten gefunden – Verarbeitung startet …");
         var ex=osmExisting();
         function nextPage(i,att){
           att=att||0;
           if(_msStop||i>=pages.length){return finish();}
           var p=pages[i];setBar(i,pages.length);say("Seite "+(i+1)+" / "+pages.length+": <b>"+esc(p.title||"(ohne Titel)")+"</b> <span style=\"color:var(--muted)\">("+esc(p.book||"")+(p.section?(" › "+esc(p.section)):"")+")</span>"+(att?" <span style=\"color:#b45309\">· Wiederholung "+att+"</span>":"")+" &nbsp; ✓ "+added.length+" angelegt, "+skip+" vorhanden, "+fail+" Fehler");
           graphPageContent(token,p).then(function(pc){
             var text=(p.title?(p.title+"\n"):"")+(p.book?("Land/Notizbuch: "+p.book+"\n"):"")+(p.section?("Region/Bundesland: "+p.section+"\n"):"")+pc.text;
             if(!text.trim()){skip++;return null;}
             return apiNoteScan(text).then(function(res){
               var c=res.contact||{};
               // Schutz: liefert die KI (z. B. wegen Drosselung) GAR keine Daten, KEINEN leeren Kontakt anlegen -> Fehler -> Wiederholung.
               var kiHas=(c&&Object.keys(c).some(function(k){return String(c[k]||"").trim();}))||(res.activities&&res.activities.length);
               if(!kiHas)throw new Error("KI lieferte keine Daten (Drosselung?)");
               var fa=String(c.firma||"").trim()||String(p.title||"").trim();
               var dk="dk:"+dedupKey(fa,c.ort);
               if(ex[dk]){ // schon vorhanden -> kein Duplikat; fehlende Bilder/Betreuer nachtragen
                 var exC=byId(ex[dk]),chg=false;
                 if(exC&&!exC.owner&&ownerByBook[p.book]){exC.owner=ownerByBook[p.book];chg=true;}
                 if(exC&&!(exC.bilder&&exC.bilder.length)&&pc.imgs&&pc.imgs.length){
                   return loadImgs(pc).then(function(bl){if(bl.length){exC.bilder=bl;imgAdded++;chg=true;}if(chg){exC.updated=Date.now();saveContact(exC);}skip++;});
                 }
                 if(chg){exC.updated=Date.now();saveContact(exC);}
                 skip++;return null;
               }
               return loadImgs(pc).then(function(bilder){
                 // Land: zuerst aus der ADRESSE (KI), Notizbuchname nur als Fallback (z. B. Muenchner Kontakt im Afrika-Buch -> DE).
                 var lf=landFromBook(p.book),ki=String(c.land||"").toUpperCase().slice(0,2);
                 var rec={id:uid(),created:Date.now(),updated:Date.now(),status:"lead",land:(ki||lf||"DE"),activities:[],owner:ownerByBook[p.book]||((CUR&&CUR.n)||"")};
                 rec.firma=fa;["anrede","vorname","nachname","strasse","plz","ort","bundesland","tel","mobil","mail","web","ustid"].forEach(function(k){var v=c[k]&&String(c[k]).trim();if(v)rec[k]=v;});
                 // Abschnittsname nur uebernehmen, wenn er ein ECHTES Bundesland ist (in Auslands-Notizbuechern ist der Abschnitt oft der Kundenname).
                 if(!rec.bundesland&&p.section&&blFromText(p.section))rec.bundesland=blFromText(p.section);
                 if(c.position)rec.firma2=c.position;
                 if(rec.plz&&rec.land==="DE"&&/^\d{1,4}$/.test(rec.plz)){while(rec.plz.length<5)rec.plz="0"+rec.plz;}
                 (res.activities||[]).forEach(function(a){var ty=(a&&a.type||"notiz");if(!NOTE_ATYPES[ty])ty="notiz";rec.activities.push({id:uid(),type:ty,date:noteDateTs(a&&a.date),note:(a&&a.note)||"",by:(CUR&&CUR.n)||""});});
                 rec.activities.sort(function(x,y){return (x.date||0)-(y.date||0);});
                 if(bilder.length)rec.bilder=bilder;
                 rec.quelle="OneNote-Import"+(p.book?(" ("+p.book+")"):"");
                 DB.contacts.push(rec);added.push(rec);ex[dk]=rec.id;
                 if(added.length-savedUpto>=8){bulkSave(added.slice(savedUpto),false);savedUpto=added.length;} // nur die NEUEN sichern (nicht kumulativ)
               });
             });
           }).then(function(){setTimeout(function(){nextPage(i+1,0);},150);},function(){
             // Fehler (oft kurzzeitige Drosselung 429/Überlastung) -> bis zu 3x mit zunehmender Wartezeit wiederholen
             if(!_msStop&&att<3){setTimeout(function(){nextPage(i,att+1);},1500*(att+1));}
             else{fail++;setTimeout(function(){nextPage(i+1,0);},150);}
           });
         }
         function finish(){
           setBar(1,1);
           if(added.length>savedUpto){bulkSave(added.slice(savedUpto),false);savedUpto=added.length;}
           initFilters();renderDashboard();
           goBtn.disabled=false;btn.disabled=false;stopBtn.classList.add("hidden");
           var imgInfo=" · Bilder "+imgLoaded+"/"+imgFound+(imgAdded?(" ("+imgAdded+" nachgetragen)"):"");
           say((_msStop?"Gestoppt. ":"Fertig! ")+"<b>"+added.length+"</b> Kontakte angelegt"+(skip?(", "+skip+" bereits vorhanden/übersprungen"):"")+(fail?(", "+fail+" Fehler"):"")+imgInfo+".","#15803d");
           // Bild-Diagnose als kopierbarer Kasten, falls nicht alle Bilder geladen wurden.
           if(imgLoaded<imgFound||(imgRaw&&!imgFound)){
             var diag="BILD-DIAGNOSE  img-Tags="+imgRaw+"  erkannt="+imgFound+"  geladen="+imgLoaded+"  Sites-Zugriff="+(sitesToken?"ja":"NEIN (Admin-Freigabe fehlt)")+"\nBeispiel-URL: "+(imgSample||"(keine)")+"\nFehler: "+(dbg.length?dbg.slice(0,4).join("  |  "):"(keine)");
             msg.innerHTML+='<div style="margin-top:8px"><div style="font-size:12px;color:#b91c1c;margin-bottom:4px">⚠ Bilder kamen nicht alle an – bitte diesen Kasten abfotografieren/kopieren und mir schicken:</div><textarea readonly style="width:100%;height:84px;font-family:var(--mono);font-size:11px;border:1px solid var(--line);border-radius:8px;padding:6px;background:#fff" onclick="this.select()">'+esc(diag)+'</textarea></div>';
           }
         }
         nextPage(0);
       })
       .catch(function(e){goBtn.disabled=false;btn.disabled=false;stopBtn.classList.add("hidden");say("Import fehlgeschlagen: "+esc(String((e&&e.message)||e)),"#b91c1c");});
   };
   function loginErr(e){var m=String((e&&e.message)||e);
     if(/popup|user_cancelled|interaction/i.test(m))say("Anmeldung abgebrochen. Bitte erneut versuchen und das Microsoft-Fenster bestätigen.","#b91c1c");
     else if(/consent|AADSTS65001|permission/i.test(m))say("Berechtigung fehlt: Im Microsoft-Login der Leseberechtigung Notes.Read zustimmen (ggf. muss der Admin zustimmen).","#b91c1c");
     else say("Anmeldung fehlgeschlagen: "+esc(m),"#b91c1c");
   }
 })();
 var CSV_COLS={firma:"firma",company:"firma",zusatz:"firma2",anrede:"anrede",vorname:"vorname",firstname:"vorname",nachname:"nachname",lastname:"nachname",name:"nachname",strasse:"strasse","straße":"strasse",street:"strasse",plz:"plz",zip:"plz",ort:"ort",city:"ort",land:"land",country:"land",bundesland:"bundesland",state:"bundesland",region:"bundesland",tel:"tel",telefon:"tel",phone:"tel",mobil:"mobil",mobile:"mobil",mail:"mail",email:"mail","e-mail":"mail",web:"web",website:"web",url:"web",ustid:"ustid",vat:"ustid",quelle:"quelle",source:"quelle",notiz:"notiz",note:"notiz",notes:"notiz",status:"status"};
 function splitCSVLine(line,sep){var out=[],cur="",q=false;for(var i=0;i<line.length;i++){var ch=line[i];if(q){if(ch==='"'){if(line[i+1]==='"'){cur+='"';i++;}else q=false;}else cur+=ch;}else{if(ch==='"')q=true;else if(ch===sep){out.push(cur);cur="";}else cur+=ch;}}out.push(cur);return out;}
 function importCSV(text){
   text=text.replace(/^﻿/,"");var lines=text.split(/\r?\n/).filter(function(l){return l.trim();});if(lines.length<2)return 0;
   var sep=(lines[0].split(";").length>lines[0].split(",").length)?";":",";
   var head=splitCSVLine(lines[0],sep).map(function(h){return CSV_COLS[h.trim().toLowerCase()]||null;});
   var n=0,added=[];
   for(var r=1;r<lines.length;r++){var cells=splitCSVLine(lines[r],sep);var rec={id:uid(),created:Date.now(),updated:Date.now(),status:"lead",land:"DE",activities:[]};var has=false;
     for(var c=0;c<head.length;c++){if(head[c]&&cells[c]!=null){var val=cells[c].trim();if(val){rec[head[c]]=val;has=true;}}}
     if(!has)continue;if(rec.land)rec.land=rec.land.toUpperCase().slice(0,2)||"DE";if(!findStatus(rec.status))rec.status="lead";
     // PLZ-Reparatur: DE-Postleitzahlen mit verlorener führender Null (Excel-Zahl) auf 5 Stellen auffüllen.
     if(rec.plz&&rec.land==="DE"&&/^\d{1,4}$/.test(rec.plz)){while(rec.plz.length<5)rec.plz="0"+rec.plz;}
     DB.contacts.push(rec);added.push(rec);n++;}
   bulkSave(added,false);return n;
 }
 function findStatus(s){for(var i=0;i<STATUS.length;i++)if(STATUS[i][0]===s)return true;return false;}
 (function(){var tpl="firma;anrede;vorname;nachname;strasse;plz;ort;bundesland;land;tel;mobil;mail;web;quelle;notiz\n"+
   "Mustermann GmbH;Herr;Max;Mustermann;Industriestr. 1;80331;München;Bayern;DE;+49 89 123456;;info@mustermann.de;mustermann.de;Messe Bauma;Interesse Lepton 5100\n";
   document.getElementById("csvTpl").href="data:text/csv;charset=utf-8,"+encodeURIComponent(tpl);})();
 document.getElementById("wipeBtn").onclick=function(){if(confirm("Wirklich ALLE CRM-Daten auf diesem Gerät löschen? Das kann nicht rückgängig gemacht werden.")){if(confirm("Sicher? Letzte Warnung.")){DB={contacts:[]};bulkSave([],true);renderDashboard();renderList();show("dashboard");}}};
 // Leere Import-Kontakte finden: OneNote-Quelle, KEINE Adresse/Kontaktdaten/Person, KEIN Verlauf, KEINE Bilder.
 function isEmptyImport(c){
   if(!/^OneNote-Import/.test(String(c.quelle||"")))return false;
   var hasInfo=c.strasse||c.plz||c.ort||c.tel||c.mobil||c.mail||c.web||c.vorname||c.nachname||c.ustid||c.firma2;
   var hasAct=(c.activities||[]).length, hasImg=(c.bilder||[]).length;
   return !hasInfo&&!hasAct&&!hasImg;
 }
 document.getElementById("cleanEmptyBtn").onclick=function(){
   var leer=DB.contacts.filter(isEmptyImport),msg=document.getElementById("cleanEmptyMsg");
   if(!leer.length){msg.style.color="var(--pos)";msg.textContent="Keine leeren Import-Kontakte gefunden. ✓";return;}
   if(!confirm(leer.length+" leere Import-Kontakte (nur Firmenname, sonst nichts) endgültig entfernen?"))return;
   var ids={};leer.forEach(function(c){ids[c.id]=1;});
   DB.contacts=DB.contacts.filter(function(c){return !ids[c.id];});
   cacheSave();if(MODE!=="local"){leer.forEach(function(c){enqueue({op:"delete",id:c.id});});flush();}
   msg.style.color="var(--pos)";msg.textContent=leer.length+" entfernt. ✓";
   initFilters();renderDashboard();
 };
 // Migration: alle eingebetteten (base64) Bilder in den Cloud-Speicher auslagern und durch URLs ersetzen.
 document.getElementById("migImgBtn").onclick=function(){
   var btn=this,msg=document.getElementById("migImgMsg");
   if(!(SB&&SB.url&&SB.key)){msg.style.color="#b91c1c";msg.textContent="Erst mit der Cloud verbinden.";return;}
   var todo=DB.contacts.filter(function(c){return (c.bilder||[]).some(function(b){return !isStored(b);});});
   if(!todo.length){msg.style.color="var(--pos)";msg.textContent="Alle Bilder liegen bereits im Cloud-Speicher. ✓";return;}
   if(!confirm("Bilder von "+todo.length+" Kontakt(en) in den Cloud-Speicher auslagern? (einmalig, kann etwas dauern)"))return;
   btn.disabled=true;var done=0,changed=0,failPrev=false;
   function nextC(i){
     if(i>=todo.length){btn.disabled=false;bulkSave([],false);initFilters();renderDashboard();msg.style.color=failPrev?"#b45309":"var(--pos)";msg.textContent=changed+" Kontakt(e) ausgelagert"+(failPrev?" – einige Bilder blieben eingebettet (Bucket angelegt?)":"")+". ✓";return;}
     var c=todo[i];done++;msg.style.color="var(--muted)";msg.textContent="Lade hoch … "+done+" / "+todo.length;
     sbStoreImages(c.bilder||[]).then(function(urls){
       var ok=urls.every(isStored);if(!ok)failPrev=true;
       if(JSON.stringify(urls)!==JSON.stringify(c.bilder)){c.bilder=urls;c.updated=Date.now();saveContact(c);changed++;}
       setTimeout(function(){nextC(i+1);},60);
     });
   }
   nextC(0);
 };

 /* ---------- Vertriebler-Auswertung (Aktivitäten je Person) ---------- */
 var EVAL_TYPES=[["anruf","Anrufe"],["mailout","Mail raus"],["mailin","Mail rein"],["besuch","Besuche"],["angebot","Angebote"],["notiz","Notizen"]];
 function evalFrom(){
   var v=(document.getElementById("evalRange")||{}).value||"all";var now=new Date();
   if(v==="all")return 0;
   if(v==="month")return new Date(now.getFullYear(),now.getMonth(),1).getTime();
   if(v==="year")return new Date(now.getFullYear(),0,1).getTime();
   return Date.now()-parseInt(v,10)*86400000;
 }
 function renderAuswertung(){
   var body=document.getElementById("evalBody");if(!body)return;
   var from=evalFrom();
   var who={}; // name -> {anruf,mailout,...,total,betrag,kunden}
   function row(n){if(!who[n])who[n]={total:0,betrag:0,kunden:0};return who[n];}
   USERS.forEach(function(u){if(u.n&&!u.hd)row(u.n);}); // Team immer zeigen (auch mit 0)
   DB.contacts.forEach(function(c){
     if(c.owner)row(c.owner).kunden++;
     (c.activities||[]).forEach(function(a){
       if(from&&(a.date||0)<from)return;
       var n=a.by||"(ohne Name)";var r=row(n);var t=(a&&a.type)||"notiz";
       r[t]=(r[t]||0)+1;r.total++;
       if(t==="angebot"&&a.betrag){var b=parseFloat(String(a.betrag).replace(/[^0-9.,-]/g,"").replace(/\./g,"").replace(",","."));if(!isNaN(b))r.betrag+=b;}
     });
   });
   var names=Object.keys(who).sort(function(a,b){return who[b].total-who[a].total||a.localeCompare(b);});
   var tot={total:0,betrag:0,kunden:0};EVAL_TYPES.forEach(function(t){tot[t[0]]=0;});
   names.forEach(function(n){var r=who[n];tot.total+=r.total;tot.betrag+=r.betrag;tot.kunden+=r.kunden;EVAL_TYPES.forEach(function(t){tot[t[0]]+=(r[t[0]]||0);});});
   var th='<th style="text-align:left;padding:7px 8px;font-size:12px;color:var(--muted);font-weight:600">Vertriebler</th>'+
     EVAL_TYPES.map(function(t){return '<th style="padding:7px 8px;font-size:12px;color:var(--muted);font-weight:600;text-align:right">'+t[1]+'</th>';}).join("")+
     '<th style="padding:7px 8px;font-size:12px;color:var(--muted);font-weight:700;text-align:right">Gesamt</th>'+
     '<th style="padding:7px 8px;font-size:12px;color:var(--muted);font-weight:600;text-align:right">Angebote €</th>'+
     '<th style="padding:7px 8px;font-size:12px;color:var(--muted);font-weight:600;text-align:right">Kunden</th>';
   function cells(n,r,bold){var s=bold?"font-weight:700;":"";
     return '<td style="padding:7px 8px;'+s+'">'+esc(n)+'</td>'+
       EVAL_TYPES.map(function(t){var v=r[t[0]]||0;return '<td style="padding:7px 8px;text-align:right;'+s+(v?'':'color:var(--faint)')+'">'+v+'</td>';}).join("")+
       '<td style="padding:7px 8px;text-align:right;font-weight:700;'+s+'">'+r.total+'</td>'+
       '<td style="padding:7px 8px;text-align:right;'+s+(r.betrag?'':'color:var(--faint)')+'">'+(r.betrag?fmtEur(Math.round(r.betrag)):"–")+'</td>'+
       '<td style="padding:7px 8px;text-align:right;'+s+(r.kunden?'':'color:var(--faint)')+'">'+(r.kunden||0)+'</td>';}
   var rows=names.map(function(n){return '<tr style="border-top:1px solid var(--line)">'+cells(n,who[n],false)+'</tr>';}).join("");
   var totRow='<tr style="border-top:2px solid var(--line-strong);background:var(--field)">'+cells("Gesamt",tot,true)+'</tr>';
   body.innerHTML='<table style="width:100%;border-collapse:collapse;font-size:14px;min-width:560px"><thead><tr>'+th+'</tr></thead><tbody>'+rows+totRow+'</tbody></table>'+
     '<div style="font-size:12px;color:var(--muted);margin-top:8px">Zählt Aktivitäten nach <b>wer sie erfasst hat</b> im gewählten Zeitraum. „Kunden" = aktuell betreute Kontakte.</div>';
 }
 /* ---------- Daten-Reiter: Verbindungsstatus + Cloud-Konfiguration ---------- */
 function renderDataConn(){
   var body=document.getElementById("connDataBody");if(!body)return;
   var q=queueRead().length;
   if(MODE==="cloud"){
     body.innerHTML='<div style="font-size:14px;color:var(--pos);font-weight:700">✓ Mit der Cloud-Datenbank verbunden – Daten online &amp; für alle geteilt.</div>'+
       '<div style="font-size:12px;color:var(--muted);margin-top:4px">'+DB.contacts.length+' Kontakte'+(q?(' · '+q+' Änderung(en) werden übertragen'):' · alles synchron')+'</div>';
   } else if(MODE==="server"){
     body.innerHTML='<div style="font-size:14px;color:var(--pos);font-weight:700">✓ Mit dem Server verbunden – Daten werden für alle geteilt.</div>'+
       '<div style="font-size:12px;color:var(--muted);margin-top:4px">'+DB.contacts.length+' Kontakte · Stand '+(DB.rev||0)+(q?(' · '+q+' Änderung(en) warten auf Übertragung'):' · alles synchron')+'</div>';
   } else {
     body.innerHTML='<div style="font-size:14px;font-weight:700">Lokaler Modus – Daten nur auf diesem Gerät.</div>'+
       '<div style="font-size:12px;color:var(--muted);margin-top:4px">Für <b>online &amp; geteilt</b> unten eine kostenlose Cloud-Datenbank verbinden – oder einen eigenen PHP-Server nutzen. Sonst Austausch per Export/Import.'+(q?(' ('+q+' lokale Änderung(en) bereit zur Übertragung.)'):'')+'</div>';
   }
   var ti=document.getElementById("tokenInp");if(ti&&document.activeElement!==ti)ti.value=TOKEN;
   var su=document.getElementById("sbUrl"),sk=document.getElementById("sbKey");
   if(su&&document.activeElement!==su)su.value=(SB&&SB.url)||"";
   if(sk&&document.activeElement!==sk)sk.value=(SB&&SB.key)||"";
   var ai=document.getElementById("aiSecret");if(ai&&document.activeElement!==ai)ai.value=AISECRET||"";
   var aiSt=document.getElementById("aiState");
   if(aiSt){aiSt.textContent=aiReady()?"✓ KI-Suche aktiv":(SB&&SB.url&&SB.key?"Schlüssel fehlt – KI-Suche aus":"erst Cloud-Datenbank verbinden");aiSt.style.color=aiReady()?"var(--pos)":"var(--muted)";}
 }
 document.getElementById("evalRange").onchange=renderAuswertung;
 document.getElementById("reconnBtn").onclick=function(){var b=this;b.textContent="Prüfe…";initBackend();setTimeout(function(){b.textContent="Verbindung prüfen";renderDataConn();},900);};
 // Einrichtungs-Link erzeugen: bettet Cloud-Zugang (+ KI-Schluessel) ein -> Kollege klickt, ist verbunden, muss nur einloggen.
 document.getElementById("setupLinkBtn").onclick=function(){
   if(!(SB&&SB.url&&SB.key)){alert("Erst mit der Cloud-Datenbank verbinden, dann den Link erzeugen.");return;}
   var payload=btoa(unescape(encodeURIComponent(JSON.stringify({u:SB.url,k:SB.key,c:AISECRET||""})))).replace(/\+/g,"-").replace(/\//g,"_").replace(/=+$/,"");
   var link=location.origin+location.pathname.replace(/[^/]*$/,"")+"#s="+payload;
   var done=function(ok){var b=document.getElementById("setupLinkBtn");b.textContent=ok?"✓ Link kopiert – nur intern teilen!":"Kopieren fehlgeschlagen";setTimeout(function(){b.innerHTML="🔗 Einrichtungs-Link für Vertriebler";},2500);};
   if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(link).then(function(){done(true);},function(){prompt("Diesen Link NUR INTERN teilen:",link);});}
   else{prompt("Diesen Link NUR INTERN teilen:",link);}
 };
 document.getElementById("tokenSave").onclick=function(){TOKEN=document.getElementById("tokenInp").value.trim();try{localStorage.setItem(TKEY,TOKEN);}catch(e){}initBackend();setTimeout(renderDataConn,700);};
 document.getElementById("sbConnect").onclick=function(){
   var url=document.getElementById("sbUrl").value.trim(),key=document.getElementById("sbKey").value.trim();
   if(!/^https?:\/\//.test(url)||!key){alert("Bitte Project-URL (https://…supabase.co) und den anon-Key eingeben.");return;}
   SB={url:url,key:key};try{localStorage.setItem(SBKEY,JSON.stringify(SB));}catch(e){}
   var b=this;b.textContent="Verbinde…";
   sbGet().then(function(){initBackend();setTimeout(function(){b.textContent="Verbinden";renderDataConn();},600);})
     .catch(function(){b.textContent="Verbinden";alert("Verbindung fehlgeschlagen. Bitte URL/Key prüfen und sicherstellen, dass die Tabelle contacts samt Zugriffsregel angelegt ist (siehe Anleitung).");renderDataConn();});
 };
 document.getElementById("sbDisconnect").onclick=function(){SB=null;try{localStorage.removeItem(SBKEY);}catch(e){}MODE="local";setConn(false);renderDataConn();};
 document.getElementById("sbHelp").onclick=function(e){e.preventDefault();document.getElementById("sbHelpBox").classList.toggle("hidden");};
 document.getElementById("aiSave").onclick=function(){AISECRET=document.getElementById("aiSecret").value.trim();try{localStorage.setItem(AIKEY,AISECRET);}catch(e){}renderDataConn();};

 /* ---------- Erinnerungen (Browser-Benachrichtigungen) ---------- */
 var NKEY="amb_crm_notified";
 function notifiedSet(){try{return JSON.parse(localStorage.getItem(NKEY)||"{}");}catch(e){return {};}}
 function setNotified(o){try{localStorage.setItem(NKEY,JSON.stringify(o));}catch(e){}}
 function refreshNotifBtn(){var b=document.getElementById("notifBtn");var card=document.getElementById("notifCard");
   if(!("Notification" in window)){card.querySelector("p").textContent="Dieser Browser unterstützt keine Benachrichtigungen. Fällige Rückrufe siehst du oben in der Liste.";b.style.display="none";return;}
   if(Notification.permission==="granted"){b.textContent="Erinnerungen sind aktiv ✓";b.disabled=true;b.style.opacity=.7;}
   else if(Notification.permission==="denied"){b.textContent="Im Browser blockiert";b.disabled=true;}
 }
 document.getElementById("notifBtn").onclick=function(){if(!("Notification" in window))return;Notification.requestPermission().then(function(){refreshNotifBtn();checkReminders();});};
 function checkReminders(){
   if(!("Notification" in window)||Notification.permission!=="granted")return;
   var seen=notifiedSet();var today=todayStr();
   overdueOrToday().forEach(function(c){
     var key=c.id+"|"+today+"|"+(c.followup.due);
     if(seen[key])return;seen[key]=1;
     try{var n=new Notification("Rückruf fällig: "+displayName(c),{body:(c.followup.note||"Wiedervorlage")+(c.tel?" · "+c.tel:""),tag:"crm-"+c.id,icon:"icon-192.png"});
       n.onclick=function(){window.focus();openDetail(c.id);n.close();};}catch(e){}
   });
   setNotified(seen);
 }

 /* ---------- Start ---------- */
 var booted=false;
 var APP_VER="v117";
 function boot(){
   if(booted)return;booted=true;
   try{document.getElementById("appVer").textContent=APP_VER;}catch(_){}
   initFilters();renderDashboard();renderList();show("dashboard");
   refreshNotifBtn();renderDataConn();
   initBackend();                // Cloud/Server erkennen + geteilte Daten laden (sonst lokal)
   checkOfferReturn();           // aus dem Konfigurator zurückgekommen? Angebot-Aktivität vorbereiten.
   setTimeout(checkPendingCall,1500); // offener Anruf von vorhin? -> kurz nachfragen
   checkReminders();
   setInterval(function(){syncFromServer();checkReminders();if(curView==="dashboard")updateBadge();},30*1000);
   document.addEventListener("visibilitychange",function(){if(!document.hidden){syncFromServer();checkReminders();}});
   window.addEventListener("online",function(){if(MODE==="local")initBackend();else syncFromServer();});
 }

 if("serviceWorker" in navigator){window.addEventListener("load",function(){navigator.serviceWorker.register("sw.js").catch(function(){});});}

 // Auto-Login: jetzt sind alle Konstanten/Funktionen definiert -> sicher boot() auslösen.
 try{var existing=findUser(localStorage.getItem(AKEY));if(existing)pass(existing);}catch(e){}
})();
</script>
</body>
</html>
'''

# Manifest + Service-Worker (eigenständig, Scope /vertrieb/)
MANIFEST = {
  "name": "Alzinger Vertrieb / CRM",
  "short_name": "Vertrieb CRM",
  "description": "CRM für den Alzinger-Vertrieb: Kontakte, Leads, Aktivitäten (Anruf/Angebot) und Wiedervorlagen – offline.",
  "lang": "de",
  "start_url": ".",
  "scope": ".",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#16181a",
  "theme_color": "#c00000",
  "icons": [
    {"src":"icon-192.png","sizes":"192x192","type":"image/png","purpose":"any maskable"},
    {"src":"icon-512.png","sizes":"512x512","type":"image/png","purpose":"any maskable"}
  ]
}

SW = r'''// Eigener Service-Worker der eigenständigen Vertriebs-/CRM-Seite (Scope /vertrieb/).
// Komplett getrennt von Konfigurator & Ersatzteilkatalog – eigener Cache "vertrieb-".
const CACHE="vertrieb-v117";
const ASSETS=["./","./index.html","./manifest.webmanifest","./icon-192.png","./icon-512.png","./icon-32.png","./favicon.ico",
  "./vendor/leaflet.js","./vendor/leaflet.css","./vendor/msal-browser.min.js",
  "./vendor/images/marker-icon.png","./vendor/images/marker-icon-2x.png","./vendor/images/marker-shadow.png"];

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
  if(req.url.indexOf("tile.openstreetmap")>=0||req.url.indexOf("arcgisonline")>=0)return; // Karten-/Satellitenkacheln nicht cachen (Browser-Cache reicht)
  if(req.url.indexOf("supabase.co")>=0)return;          // Cloud-DB immer live, nie cachen
  if(req.url.indexOf("login.microsoftonline.com")>=0||req.url.indexOf("graph.microsoft.com")>=0||req.url.indexOf("msauth.net")>=0)return; // Microsoft 365 / OneNote-Import: immer live, nie cachen/abfangen
  const isHTML=req.mode==="navigate"||(req.headers.get("accept")||"").includes("text/html");
  if(isHTML){
    // cache:"reload" -> HTML IMMER frisch vom Netz holen (umgeht den HTTP-Cache des Browsers, kein "alte Version"-Problem mehr)
    e.respondWith(
      fetch(req,{cache:"reload"}).then(resp=>{
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
'''

# Zentrales, dateibasiertes PHP-Backend (geteilte Daten im Firmennetz).
# Eine Datei, keine Datenbank. Liegt neben index.html und wird von der App
# automatisch erkannt (sonst läuft die App im lokalen Modus weiter).
API_PHP = r'''<?php
/* Zentrale Datenhaltung für das Alzinger Vertriebs-CRM (geteilt).
   - Single-File, dateibasiert: Daten in ./data/crm.json (kein DB-Server nötig).
   - Drop-in: diese Datei + index.html etc. in einen Web-Ordner mit PHP legen
     (IIS+PHP, Apache, nginx+php-fpm, Synology/QNAP …) und im Browser aufrufen.
   - Der Ordner ./data muss vom Webserver beschreibbar sein.
   Optionaler Zugriffsschutz: $TOKEN setzen und denselben Wert in der App
   (Reiter „Daten“ → Zugriffsschutz) hinterlegen. */

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

$TOKEN = '';   // leer = kein Schutz. Sonst geheimer Wert, identisch in der App.

if ($TOKEN !== '') {
  $sent = isset($_SERVER['HTTP_X_CRM_TOKEN']) ? $_SERVER['HTTP_X_CRM_TOKEN']
        : (isset($_GET['token']) ? $_GET['token'] : '');
  if (!hash_equals($TOKEN, (string)$sent)) {
    http_response_code(401); echo json_encode(array('error'=>'unauthorized')); exit;
  }
}

$DIR  = __DIR__ . '/data';
$FILE = $DIR . '/crm.json';
if (!is_dir($DIR)) @mkdir($DIR, 0775, true);

function read_db($FILE){
  if (!file_exists($FILE)) return array('rev'=>0,'contacts'=>array());
  $d = json_decode((string)file_get_contents($FILE), true);
  if (!is_array($d)) $d = array();
  if (!isset($d['contacts']) || !is_array($d['contacts'])) $d['contacts'] = array();
  if (!isset($d['rev'])) $d['rev'] = 0;
  return $d;
}
function write_db($FILE,$d){
  $tmp = $FILE . '.tmp';
  file_put_contents($tmp, json_encode($d, JSON_UNESCAPED_UNICODE|JSON_PRETTY_PRINT));
  @rename($tmp, $FILE);
}
function reindex($db){ $i=array(); foreach($db['contacts'] as $k=>$c){ if(isset($c['id'])) $i[$c['id']]=$k; } return $i; }

$action = isset($_GET['action']) ? $_GET['action'] : '';
$method = $_SERVER['REQUEST_METHOD'];

if ($method === 'GET' && ($action === 'all' || $action === '')) {
  echo json_encode(read_db($FILE), JSON_UNESCAPED_UNICODE); exit;
}

if ($method === 'POST' && $action === 'batch') {
  $body = json_decode((string)file_get_contents('php://input'), true);
  $ops  = (isset($body['ops']) && is_array($body['ops'])) ? $body['ops'] : array();

  $lf = fopen($FILE.'.lock','c');                 // exklusive Sperre über Lesen-Ändern-Schreiben
  if ($lf) flock($lf, LOCK_EX);
  $db  = read_db($FILE);
  $idx = reindex($db);
  foreach ($ops as $op) {
    $type = isset($op['op']) ? $op['op'] : '';
    if ($type === 'upsert' && isset($op['contact']['id'])) {
      $c = $op['contact']; $id = $c['id'];
      if (isset($idx[$id])) $db['contacts'][$idx[$id]] = $c;
      else { $idx[$id] = count($db['contacts']); $db['contacts'][] = $c; }
    } else if ($type === 'delete' && isset($op['id'])) {
      $id = $op['id'];
      if (isset($idx[$id])) { array_splice($db['contacts'], $idx[$id], 1); $idx = reindex($db); }
    } else if ($type === 'bulk') {
      $list = (isset($op['contacts']) && is_array($op['contacts'])) ? $op['contacts'] : array();
      if (!empty($op['replace'])) { $db['contacts'] = $list; $idx = reindex($db); }
      else {
        foreach ($list as $c) {
          if (!isset($c['id'])) continue; $id = $c['id'];
          if (isset($idx[$id])) $db['contacts'][$idx[$id]] = $c;
          else { $idx[$id] = count($db['contacts']); $db['contacts'][] = $c; }
        }
      }
    }
  }
  $db['rev'] = intval($db['rev']) + 1;
  write_db($FILE, $db);
  if ($lf) { flock($lf, LOCK_UN); fclose($lf); }
  echo json_encode(array('ok'=>true,'rev'=>$db['rev'],'count'=>count($db['contacts']))); exit;
}

http_response_code(400);
echo json_encode(array('error'=>'bad request'));
'''

# Schützt den Datenordner zusätzlich gegen direkten Web-Zugriff (Apache).
HTACCESS_DATA = "Require all denied\nDeny from all\n"

# ---- Ausgabe schreiben ----
out=TPL
out=out.replace("%%RED%%",RED).replace("%%RED2%%",RED2)
out=out.replace("%%LOGOL%%",LOGO_L).replace("%%LOGOD%%",LOGO_D)
out=out.replace("%%USERS%%",USERS_JS)

for tok in ["%%RED%%","%%RED2%%","%%LOGOL%%","%%LOGOD%%","%%USERS%%"]:
    assert tok not in out, "Token übrig: "+tok
for need in ['id="gateForm"','id="clist"','id="actModal"','renderDashboard','amb_lepton_crm','amb_lepton_configs','checkReminders','initBackend','api.php','id="connState"','id="osmSearch"','overpass-api.de','osmToContact','id="osmMap"','ensureLeaflet','arcgisonline','addSat','id="sbUrl"','sbUpsert','supabase.co','id="cMap"','showContactsMap','id="actBetrag"','flagIcon','id="detMap"','contactLatLon','leadSearch','apiAi','aiPost','id="aiSecret"','/functions/v1/']:
    assert need in out, "Pflicht-Markierung fehlt: "+need
# Leaflet (Karten-Bibliothek) muss lokal vorhanden sein (Laufzeit-Abhängigkeit der Standort-Karte)
for vf in ["leaflet.js","leaflet.css","images/marker-icon.png","images/marker-shadow.png","msal-browser.min.js"]:
    assert os.path.exists(os.path.join(OUTDIR,"vendor",vf)), "vendor fehlt: vertrieb/vendor/"+vf

open(os.path.join(OUTDIR,"index.html"),"w",encoding="utf8").write(out)
open(os.path.join(OUTDIR,"manifest.webmanifest"),"w",encoding="utf8").write(json.dumps(MANIFEST,ensure_ascii=False,indent=2))
open(os.path.join(OUTDIR,"sw.js"),"w",encoding="utf8").write(SW)
open(os.path.join(OUTDIR,"api.php"),"w",encoding="utf8").write(API_PHP)
# Datenordner anlegen + gegen direkten Web-Zugriff schützen (Apache). Inhalt nicht eingecheckt.
DATA_DIR=os.path.join(OUTDIR,"data"); os.makedirs(DATA_DIR,exist_ok=True)
open(os.path.join(DATA_DIR,".htaccess"),"w",encoding="utf8").write(HTACCESS_DATA)
# Icons aus dem Wurzelverzeichnis übernehmen (gleiche Marke)
for ic in ["icon-192.png","icon-512.png"]:
    src=os.path.join(ROOT,ic)
    if os.path.exists(src): shutil.copyfile(src,os.path.join(OUTDIR,ic))

print("vertrieb/index.html erzeugt – bytes",len(out.encode("utf8")))
print("vertrieb/manifest.webmanifest, sw.js, api.php, data/.htaccess, Icons geschrieben")
