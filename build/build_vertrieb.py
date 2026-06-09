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
USERS_JS='[{h:"2a0e88896d2303027849314ab026e16a096c8234cc0bb3b4eb9ffe5e1fbfd324",n:""},{h:"378b467d56232e509fc568bfc3849a9d1fb40c6a248a35d755cb9db1053c33bf",n:"Johannes Rudel"},{h:"2c5ce471a6a1e91a47b4a357064cdab49fbc11e76982da2371b15c0c6608b80f",n:"Tobias Ermel"},{h:"50b9f421b5a362836fbb38ba11d8d59b76c287ef29d6c445df771a0c8f1116df",n:"Richard Alzinger",tel:"+49 170 3336025",mail:"richard@alzinger-maschinenbau.de"},{h:"9833d8644a16501b9eab7a849a294b8b209e32db63366041b50bbfa0107da4d3",n:"Adam Domaradzki"},{h:"0ad1350f32d0d469d4c044cb1ad38b4964763caf497112c76bfc462a81ccda9b",n:"Łukasz Zdziennicki"},{h:"6dce472c58a319f6b55518c7ddcb0e438cdc50c1566ff46ec420a12289df2980",n:"Martin Alzinger",tel:"+49 170 3128533",mail:"martin@alzinger-maschinenbau.de"}]'

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
.topbar-in{max-width:1120px;margin:0 auto;padding:12px 16px calc(12px + env(safe-area-inset-top)) 16px;padding-top:max(12px,env(safe-area-inset-top))}
.tb-row{display:flex;align-items:center;justify-content:space-between;gap:12px}
.tb-brand{display:flex;flex-direction:column;align-items:flex-start;gap:3px;min-width:0}
.tb-brand img{height:30px;display:block}
.tb-sub{font-family:var(--mono);font-size:10px;letter-spacing:.22em;text-transform:uppercase;color:#fff;opacity:.95;font-weight:600;margin-top:10px}
.conn{font-family:var(--mono);font-size:9.5px;letter-spacing:.02em;white-space:nowrap}
.conn.on{color:#bbf7d0}.conn.off{color:rgba(255,255,255,.72)}
.tb-user{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:600}
.tb-user .av{width:30px;height:30px;border-radius:50%;background:rgba(255,255,255,.18);display:inline-flex;align-items:center;justify-content:center;font-family:var(--mono);font-size:12px;font-weight:600}
.tb-user button{background:none;border:0;color:rgba(255,255,255,.85);font-size:11px;cursor:pointer;text-decoration:underline;text-underline-offset:2px}

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
.crow .right{flex:0 0 auto;display:flex;flex-direction:column;align-items:flex-end;gap:6px}

.pill{font-family:var(--mono);font-size:10px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;padding:3px 8px;border-radius:20px;white-space:nowrap}
.pill.lead{background:#eef1f4;color:var(--slate)}
.pill.interessent{background:#fff3e0;color:var(--warn)}
.pill.angebot{background:#e7f0ff;color:#1d4ed8}
.pill.kunde{background:#e6f4ea;color:var(--pos)}
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
.form-actions{display:flex;gap:8px;margin-top:18px;flex-wrap:wrap}

/* Detail */
.detail-head{display:flex;gap:14px;align-items:flex-start;margin-bottom:6px}
.detail-head .av{width:52px;height:52px;border-radius:12px;background:var(--ink);color:#fff;display:flex;align-items:center;justify-content:center;font-family:var(--mono);font-weight:600;font-size:18px;flex:0 0 auto}
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
        <span class="tb-sub">CRM System</span>
        <span id="connState" class="conn off" title="">● Lokal – dieses Gerät</span>
      </div>
      <div class="tb-user">
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
    <h2 class="vh" id="greet">Übersicht</h2>
    <div class="sub" id="greetSub">Dein Vertriebs-Cockpit</div>

    <div class="stats" id="stats"></div>

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
      <input class="search" id="q" placeholder="Suchen: Firma, Name, Ort, Telefon, E-Mail…">
    </div>
    <div class="toolbar">
      <select class="filter" id="fStatus"><option value="">Alle Status</option></select>
      <select class="filter" id="fLand"><option value="">Alle Länder</option></select>
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
    <div class="sub">Server-Verbindung, Sichern, Übertragen und Importieren.</div>
    <div class="card" id="connData">
      <h3>Geteilte Daten / Server</h3>
      <div id="connDataBody"></div>
      <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
        <button class="btn sm" id="reconnBtn" type="button">Verbindung prüfen</button>
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
      <h3>Verknüpfung</h3>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <a class="btn" href="../index.html"><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="14" rx="2"/><path d="M7 20h10"/></svg>Lepton Konfigurator</a>
        <a class="btn" href="../ersatzteile/"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 00-.1-1l2-1.6-2-3.4-2.4 1a7 7 0 00-1.7-1l-.3-2.5H10l-.3 2.5a7 7 0 00-1.7 1l-2.4-1-2 3.4 2 1.6a7 7 0 000 2l-2 1.6 2 3.4 2.4-1a7 7 0 001.7 1l.3 2.5h3.8l.3-2.5a7 7 0 001.7-1l2.4 1 2-3.4-2-1.6c.07-.33.1-.66.1-1z"/></svg>Ersatzteilkatalog</a>
      </div>
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
    Alzinger Maschinenbau · Vertrieb / CRM — PWA, online wie offline.<br>
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
    <div class="fg" style="margin-bottom:6px">
      <label>Notiz</label>
      <textarea class="field" id="actNote" placeholder="Worum ging es? Ergebnis, Vereinbarung…"></textarea>
    </div>
    <label class="chk"><input type="checkbox" id="actFu" checked> Wiedervorlage anlegen in
      <input type="number" id="actFuDays" value="7" min="1" max="180" style="width:58px;border:1px solid var(--line-strong);border-radius:7px;padding:4px 6px;text-align:center"> Tagen</label>
    <div class="form-actions">
      <button class="btn primary block" id="actSave" type="button">Speichern</button>
      <button class="btn ghost block" id="actCancel" type="button">Abbrechen</button>
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
 var gate=document.getElementById("gate");
 function setUser(u){CUR=u||{n:""};try{localStorage.setItem(UKEY,JSON.stringify({n:u.n||"",tel:u.tel||"",mail:u.mail||""}));}catch(_){}
   var un=document.getElementById("uName");if(un)un.textContent=u.n||"Vertrieb";
   var av=document.getElementById("uAv");if(av){av.textContent=initials(u.n||"?");av.title=u.n||"";}}
 function pass(u){setUser(u);gate.classList.add("hidden");boot();}
 // Auto-Login wird am ENDE der IIFE ausgelöst (erst dann sind alle Daten/Funktionen definiert).
 document.getElementById("gateForm").addEventListener("submit",function(ev){ev.preventDefault();
  var u=(document.getElementById("gu").value||"").trim().toLowerCase(),p=(document.getElementById("gp").value||"");
  var hit=findUser(sha256(u+":"+p));
  if(hit){try{localStorage.setItem(AKEY,hit.h);}catch(_){}document.getElementById("gerr").textContent="";pass(hit);}
  else{document.getElementById("gerr").textContent="Benutzername oder Passwort falsch.";var gp=document.getElementById("gp");gp.value="";gp.focus();}
 });
 document.getElementById("logoutBtn").addEventListener("click",function(){try{localStorage.removeItem(AKEY);}catch(_){}location.reload();});

 /* ---------- Konstanten ---------- */
 var KEY="amb_lepton_crm";
 var CFG_KEY="amb_lepton_configs"; // gespeicherte Angebote des Konfigurators (gleicher Origin)
 var STATUS=[["lead","Lead"],["interessent","Interessent"],["angebot","Angebot offen"],["kunde","Kunde"],["verloren","Verloren"]];
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
 function cacheRead(){try{var o=JSON.parse(localStorage.getItem(KEY)||"{}");if(!o.contacts)o.contacts=[];return o;}catch(e){return {contacts:[]};}}
 function cacheSave(){try{localStorage.setItem(KEY,JSON.stringify(DB));}catch(e){}}
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
 function sbUpsert(list){if(!list||!list.length)return Promise.resolve();var body=list.map(function(c){return {id:c.id,data:c};});return fetch(sbBase(),{method:"POST",headers:sbHeaders({"Prefer":"resolution=merge-duplicates,return=minimal"}),body:JSON.stringify(body)}).then(function(r){if(!r.ok)throw new Error("sb "+r.status);});}
 function sbDelete(id){return fetch(sbBase()+"?id=eq."+encodeURIComponent(id),{method:"DELETE",headers:sbHeaders({"Prefer":"return=minimal"})}).then(function(r){if(!r.ok)throw new Error("sb "+r.status);});}
 function sbDeleteAll(){return fetch(sbBase()+"?id=neq.__none__",{method:"DELETE",headers:sbHeaders({"Prefer":"return=minimal"})}).then(function(r){if(!r.ok)throw new Error("sb "+r.status);});}

 /* --- KI-Lead-Suche über Supabase Edge Function "lead-ai" (Claude + Web-Suche) --- */
 function aiReady(){return !!(SB&&SB.url&&SB.key&&AISECRET);}
 function aiPost(name,was,wo){
   var ctl=("AbortController" in window)?new AbortController():null;
   var to=ctl?setTimeout(function(){try{ctl.abort();}catch(_){}},120000):0;
   var done=function(){if(to)clearTimeout(to);};
   return fetch(SB.url.replace(/\/+$/,"")+"/functions/v1/"+name,{method:"POST",headers:{"Authorization":"Bearer "+SB.key,"apikey":SB.key,"Content-Type":"application/json","x-crm-secret":AISECRET},body:JSON.stringify({was:was,wo:wo}),signal:ctl?ctl.signal:undefined})
     .then(function(r){if(!r.ok)return r.json().catch(function(){return {};}).then(function(e){var err=new Error("ai "+r.status+(e&&e.error?(": "+e.error):""));err.status=r.status;throw err;});return r.json();})
     .then(function(d){done();return d;},function(e){done();if(e&&(e.name==="AbortError"||/abort/i.test(String(e&&e.message)))){var er=new Error("Zeitüberschreitung – die KI-Suche hat zu lange gebraucht. Bitte Region enger fassen und erneut versuchen.");er.status=0;throw er;}throw e;});
 }
 function apiAi(was,wo){
   // Edge-Function-Name kann „lead-ai" oder „lead-ai-" sein -> bei 404 die zweite Variante versuchen.
   return aiPost("lead-ai",was,wo).catch(function(e){if(e&&e.status===404)return aiPost("lead-ai-",was,wo);throw e;})
     .then(function(d){return (d.leads||[]).filter(function(x){return x&&(x.firma||x.name);});});
 }

 /* --- Op-Warteschlange (für Offline/Server) --- */
 function queueRead(){try{return JSON.parse(localStorage.getItem(QKEY)||"[]");}catch(e){return [];}}
 function queueWrite(q){try{localStorage.setItem(QKEY,JSON.stringify(q));}catch(e){}}
 function enqueue(op){var q=queueRead();q.push(op);queueWrite(q);}
 function flush(){
   if(MODE==="local")return Promise.resolve();
   var q=queueRead();if(!q.length)return Promise.resolve();
   if(MODE==="server")return apiPost("batch",{ops:q}).then(function(res){queueWrite([]);if(res&&res.rev!=null)DB.rev=res.rev;}).catch(function(){/* offline: behalten */});
   // cloud: Ops sequenziell an Supabase; bei Fehler Rest behalten und später erneut
   var i=0;
   function step(){
     if(i>=q.length){queueWrite([]);return Promise.resolve();}
     var op=q[i],pr;
     if(op.op==="upsert")pr=sbUpsert([op.contact]);
     else if(op.op==="delete")pr=sbDelete(op.id);
     else if(op.op==="bulk")pr=op.replace?sbDeleteAll().then(function(){return sbUpsert(op.contacts||[]);}):sbUpsert(op.contacts||[]);
     else pr=Promise.resolve();
     return pr.then(function(){i++;return step();});
   }
   return step().catch(function(){if(i>0)queueWrite(q.slice(i));});
 }

 /* --- Mutationen: lokal optimistisch + (online) in die geteilte Quelle --- */
 function persist(){cacheSave();} /* nur lokaler Spiegel */
 function saveContact(c){cacheSave();if(MODE!=="local"){enqueue({op:"upsert",contact:c});flush();}}
 function removeContact(id){DB.contacts=DB.contacts.filter(function(x){return x.id!==id;});cacheSave();if(MODE!=="local"){enqueue({op:"delete",id:id});flush();}}
 function bulkSave(list,replace){cacheSave();if(MODE!=="local"){enqueue({op:"bulk",contacts:list,replace:!!replace});flush();}}

 /* --- Online-Sync --- */
 function pull(){
   if(MODE==="cloud")return sbGet().then(function(list){DB.contacts=list||[];cacheSave();rerenderCurrent();});
   return apiGet().then(function(d){DB.contacts=d.contacts||[];DB.rev=d.rev||0;cacheSave();rerenderCurrent();});
 }
 function syncFromServer(){if(MODE==="local")return;flush().then(pull).catch(function(){});}
 // Backend erkennen: zuerst Cloud (Supabase), dann eigener PHP-Server, sonst lokal.
 function initBackend(){
   if(sbReady()){
     sbGet().then(function(list){
       MODE="cloud";setConn(true);
       if(!(list&&list.length)&&DB.contacts&&DB.contacts.length){enqueue({op:"bulk",contacts:DB.contacts,replace:false});}
       flush().then(sbGet).then(function(l){DB.contacts=l||[];cacheSave();rerenderCurrent();}).catch(function(){});
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
 function setConn(ok){
   var el=document.getElementById("connState");
   var lab=MODE==="cloud"?"● Cloud – geteilt":(MODE==="server"?"● Server – geteilt":"● Lokal – dieses Gerät");
   if(el){el.className="conn "+(ok?"on":"off");el.textContent=lab;el.title=ok?"Online verbunden – Daten werden für alle geteilt.":"Kein Online-Speicher verbunden. Daten nur auf diesem Gerät (Reiter „Daten“).";}
   var d=document.getElementById("connData");if(d)renderDataConn();
 }
 function rerenderCurrent(){
   updateBadge();
   if(curView==="dashboard")renderDashboard();
   else if(curView==="list")renderList();
   else if(curView==="leads")renderLeads();
   else if(curView==="detail"&&curId&&byId(curId)){
     if(modal&&modal.classList.contains("open"))return;
     if(document.activeElement&&document.activeElement.closest&&document.activeElement.closest("#view-detail"))return;
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
   curView=view;
   var vs=document.querySelectorAll(".view");for(var i=0;i<vs.length;i++)vs[i].classList.remove("active");
   var el=document.getElementById("view-"+view);if(el)el.classList.add("active");
   var nb=document.querySelectorAll("#nav button");for(i=0;i<nb.length;i++)nb[i].classList.toggle("active",nb[i].getAttribute("data-view")===view);
   window.scrollTo(0,0);
   document.getElementById("fab").style.display=(view==="detail"||view==="form")?"none":"flex";
 }
 document.getElementById("nav").addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;var v=b.getAttribute("data-view");if(v){if(v==="dashboard")renderDashboard();if(v==="list")renderList();if(v==="leads")renderLeads();show(v);}});

 /* ---------- Übersicht ---------- */
 function dueFollowups(){var out=[];DB.contacts.forEach(function(c){if(c.followup&&!c.followup.done&&c.followup.due){out.push(c);}});out.sort(function(a,b){return a.followup.due-b.followup.due;});return out;}
 function overdueOrToday(){return dueFollowups().filter(function(c){return relDays(c.followup.due)<=0;});}

 function renderDashboard(){
   var name=(CUR&&CUR.n)?CUR.n.split(" ")[0]:"";
   document.getElementById("greet").textContent=name?("Servus, "+name+"!"):"Übersicht";
   var st={lead:0,interessent:0,angebot:0,kunde:0,verloren:0};
   DB.contacts.forEach(function(c){if(st[c.status]!=null)st[c.status]++;});
   var fu=dueFollowups(),od=overdueOrToday();
   var stats=document.getElementById("stats");
   stats.innerHTML=
     '<div class="stat'+(od.length?' accent':'')+'"><div class="n">'+od.length+'</div><div class="l">Rückrufe fällig</div></div>'+
     '<div class="stat"><div class="n">'+DB.contacts.length+'</div><div class="l">Kontakte</div></div>'+
     '<div class="stat"><div class="n">'+(st.lead+st.interessent)+'</div><div class="l">Offene Leads</div></div>'+
     '<div class="stat"><div class="n">'+st.angebot+'</div><div class="l">Angebote offen</div></div>'+
     '<div class="stat"><div class="n">'+st.kunde+'</div><div class="l">Kunden</div></div>';
   // Wiedervorlagen
   document.getElementById("fuCnt").textContent=fu.length;
   var fl=document.getElementById("fuList");
   if(!fu.length){fl.innerHTML='<div style="font-size:13px;color:var(--faint);padding:6px 0">Keine offenen Wiedervorlagen. Sauber! 👍</div>';}
   else{fl.innerHTML=fu.slice(0,12).map(function(c){
     var d=c.followup;
     return '<div class="crow" data-id="'+c.id+'" style="margin-bottom:8px">'+
       '<div class="av">'+esc(initials(displayName(c)))+'</div>'+
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
   updateBadge();
 }
 function updateBadge(){var n=overdueOrToday().length;var b=document.getElementById("navBadge");if(n>0){b.textContent=n;b.classList.remove("hidden");}else b.classList.add("hidden");}

 /* ---------- Kontaktliste ---------- */
 function fillSelect(sel,opts,all){sel.innerHTML='<option value="">'+all+'</option>'+opts.map(function(o){return '<option value="'+o[0]+'">'+esc(o[1])+'</option>';}).join("");}
 function ownerOpts(){var seen={},out=[];DB.contacts.forEach(function(c){if(c.owner&&!seen[c.owner]){seen[c.owner]=1;out.push([c.owner,c.owner]);}});return out;}
 // Länder-Filter = bekannte Liste + alle in den Kontakten tatsächlich vorkommenden Codes
 function landOpts(){var seen={},out=[];LANDS.forEach(function(l){seen[l[0]]=1;out.push(l);});DB.contacts.forEach(function(c){var cc=(c.land||"").toUpperCase();if(cc&&!seen[cc]){seen[cc]=1;out.push([cc,landLabel(cc)]);}});return out;}
 function initFilters(){
   fillSelect(document.getElementById("fStatus"),STATUS,"Alle Status");
   fillSelect(document.getElementById("fLand"),landOpts(),"Alle Länder");
   fillSelect(document.getElementById("fOwner"),ownerOpts(),"Alle Vertriebler");
   fillSelect(document.getElementById("fLeadLand"),landOpts(),"Alle Länder");
 }
 function matchQ(c,q){if(!q)return true;q=q.toLowerCase();var hay=[c.firma,c.firma2,c.vorname,c.nachname,c.ort,c.plz,c.tel,c.mobil,c.mail,c.quelle,c.notiz].join(" ").toLowerCase();return hay.indexOf(q)>=0;}
 function contactRow(c){
   var due=(c.followup&&!c.followup.done&&c.followup.due)?'<span class="due '+dueClass(c.followup.due)+'">'+dueLabel(c.followup.due)+'</span>':'';
   var sub=fullName(c);var loc=[c.plz,c.ort].filter(Boolean).join(" ");
   return '<div class="crow" data-id="'+c.id+'">'+
     '<div class="av">'+esc(initials(displayName(c)))+'</div>'+
     '<div class="mid"><div class="nm">'+esc(displayName(c))+'</div>'+
     '<div class="meta">'+
       (c.firma&&sub?'<span>'+esc(sub)+'</span>':'')+
       (c.land?'<span class="flag">'+esc(c.land)+'</span>':'')+
       (loc?'<span>'+esc(loc)+'</span>':'')+
       (c.tel?'<span>'+esc(c.tel)+'</span>':'')+
     '</div></div>'+
     '<div class="right"><span class="pill '+esc(c.status||"lead")+'">'+esc(statusLabel(c.status))+'</span>'+due+'</div>'+
   '</div>';
 }
 function renderList(){
   var q=document.getElementById("q").value.trim();
   var fs=document.getElementById("fStatus").value,fl=document.getElementById("fLand").value,fo=document.getElementById("fOwner").value,so=document.getElementById("fSort").value;
   var arr=DB.contacts.filter(function(c){return matchQ(c,q)&&(!fs||c.status===fs)&&(!fl||c.land===fl)&&(!fo||c.owner===fo);});
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
 function flagIcon(L){return L.divIcon({className:"flag-mark",html:'<div style="font-size:22px;line-height:1;filter:drop-shadow(0 1px 1px rgba(0,0,0,.45))">🚩</div>',iconSize:[24,24],iconAnchor:[3,22],popupAnchor:[8,-20]});}
 function addContactMarker(L,c){
   if(!_cmarkers||c.lat==null||c.lon==null)return;
   var loc=[c.plz,c.ort].filter(Boolean).join(" ");
   var pop='<b>'+esc(displayName(c))+'</b>'+(loc?'<br>'+esc(loc):'')+(c.land?' ('+esc(c.land)+')':'')+
     '<br><button data-cid="'+c.id+'" style="margin-top:6px;border:0;background:#c00000;color:#fff;border-radius:6px;padding:5px 9px;font:600 12px sans-serif;cursor:pointer">Öffnen</button>';
   L.marker([c.lat,c.lon],{icon:flagIcon(L)}).addTo(_cmarkers).bindPopup(pop);
 }
 function geocodeContact(c){
   var parts=[c.strasse,[c.plz,c.ort].filter(Boolean).join(" "),landLabel(c.land)].filter(Boolean);
   if(!parts.length)return Promise.reject();
   return fetch("https://nominatim.openstreetmap.org/search?format=json&limit=1&accept-language=de&q="+encodeURIComponent(parts.join(", ")))
     .then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(a){if(!a||!a.length)throw 0;return {lat:parseFloat(a[0].lat),lon:parseFloat(a[0].lon)};});
 }
 function geocodePending(L,list,i){
   if(i>=list.length||!cMapOpen){_geoBusy=false;return;}
   var c=list[i];
   geocodeContact(c).then(function(p){c.lat=p.lat;c.lon=p.lon;saveContact(c);if(cMapOpen)addContactMarker(L,c);}).catch(function(){}).then(function(){setTimeout(function(){geocodePending(L,list,i+1);},600);});
 }
 function showContactsMap(){
   var div=document.getElementById("cMap");
   ensureLeaflet().then(function(L){
     if(!_cmap){_cmap=L.map(div).setView([47.5,9],5);L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19,attribution:"© OpenStreetMap-Mitwirkende"}).addTo(_cmap);}
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
 var lastQuery="", searchLand="DE", osmEls=[], osmLast={}, _aiErr="", _searchSrc="", _lastWas="", _lastWo="";
 function osmStatus(html){var e=document.getElementById("osmStatus");if(e)e.innerHTML=html;}
 function osmLoading(msg){osmStatus('<span class="spin"></span>'+msg);var m=document.getElementById("osmMap");if(m)m.style.display="none";var b=document.getElementById("osmResults");if(b)b.innerHTML='<div class="skel"></div><div class="skel" style="opacity:.7"></div><div class="skel" style="opacity:.45"></div>';}
 function osmClearResults(){var b=document.getElementById("osmResults");if(b)b.innerHTML="";var m=document.getElementById("osmMap");if(m)m.style.display="none";}
 function osmGeocode(place){
   var url="https://nominatim.openstreetmap.org/search?format=json&addressdetails=1&limit=1&accept-language=de&q="+encodeURIComponent(place);
   return fetch(url,{headers:{"Accept":"application/json"}}).then(function(r){if(!r.ok)throw new Error("geo");return r.json();}).then(function(a){if(!a||!a.length)throw new Error("noplace");return a[0];});
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
   if(/kompost/.test(t)){tags.push('nwr["industrial"="composting"]');tags.push('nwr["amenity"="recycling"]["recycling:organic"="yes"]');names.push("kompost");}
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
 function osmExisting(){var s={};DB.contacts.forEach(function(c){if(c._osm)s[c._osm]=c.id;if(c.firma)s[((c.firma||"")+"|"+(c.ort||"")).toLowerCase()]=c.id;});return s;}
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
 function osmMake(key){var el=osmLast[key];if(!el)return null;var c=osmToContact(el);DB.contacts.push(c);return c;}
 function renderOsm(els){
   osmEls=els;osmLast={};els.forEach(function(el){osmLast[el.type+"/"+el.id]=el;});
   var box=document.getElementById("osmResults");
   if(!els.length){osmStatus('Keine Treffer für „'+esc(lastQuery)+'“. Anderen Begriff (z. B. „Recycling“, „Erden“) oder andere Region versuchen.');box.innerHTML="";return;}
   var ex=osmExisting(),anyNew=false;
   osmStatus(els.length+' Treffer'+(_searchSrc?(' <b>('+_searchSrc+')</b>'):'')+' für „'+esc(lastQuery)+'“ – prüfen und übernehmen:');
   box.innerHTML=els.map(function(el){
     var t=el.tags||{},a=osmAddr(t),loc=[a.plz,a.ort].filter(Boolean).join(" ");
     var key=el.type+"/"+el.id,have=ex[key]||ex[((t.name||"")+"|"+(a.ort||"")).toLowerCase()];if(!have)anyNew=true;
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
 }
 // Weitersuchen: dieselbe KI-Suche erneut, aber die schon gefundenen Firmen ausschließen
 // und die neuen Treffer unten anhängen (max. 10 echte Firmen pro Suche).
 function aiMore(){
   if(_searchSrc!=="KI"||!_lastWas)return;
   var btn=document.getElementById("osmMore");if(btn){btn.disabled=true;btn.textContent="Sucht weitere Firmen … (~1–2 Min)";}
   var names=osmEls.map(function(el){return (el.tags&&el.tags.name)||"";}).filter(Boolean);
   var w2=_lastWas+" — WICHTIG: Finde NUR WEITERE, ANDERE echte Firmen. Bereits bekannt und NICHT erneut nennen: "+names.join("; ")+".";
   apiAi(w2,_lastWo).then(function(leads){
     var seen={};osmEls.forEach(function(el){seen[el.type+"/"+el.id]=1;seen["n:"+(((el.tags&&el.tags.name)||"").toLowerCase())]=1;});
     var add=[];leads.map(aiToEl).forEach(function(el){var k=el.type+"/"+el.id,nk="n:"+(((el.tags&&el.tags.name)||"").toLowerCase());if(seen[k]||seen[nk])return;seen[k]=1;seen[nk]=1;add.push(el);});
     if(!add.length){if(btn){btn.disabled=false;btn.textContent="Keine weiteren gefunden – erneut versuchen";}return;}
     renderOsm(osmEls.concat(add));
   }).catch(function(e){if(btn){btn.disabled=false;btn.textContent="＋ Weitersuchen – weitere Firmen finden";}osmStatus('Weitersuche fehlgeschlagen: '+esc(String((e&&e.message)||e))+'. Bitte erneut versuchen.');});
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
 function osmShowMap(els){
   var mapDiv=document.getElementById("osmMap");
   var pts=(els||[]).filter(function(el){return el.lat||(el.center&&el.center.lat);});
   if(!pts.length){mapDiv.style.display="none";return;}
   mapDiv.style.display="block";
   ensureLeaflet().then(function(L){
     if(!_map){
       _map=L.map(mapDiv,{scrollWheelZoom:true});
       L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19,attribution:"© OpenStreetMap-Mitwirkende"}).addTo(_map);
     }
     if(_markers)_markers.remove();
     _markers=L.layerGroup().addTo(_map);
     var bounds=[],ex=osmExisting();
     pts.forEach(function(el){
       var lat=el.lat||el.center.lat,lon=el.lon||el.center.lon,t=el.tags||{},a=osmAddr(t),key=el.type+"/"+el.id;
       var have=ex[key]||ex[((t.name||"")+"|"+(a.ort||"")).toLowerCase()];
       var addr=esc([a.strasse,[a.plz,a.ort].filter(Boolean).join(" ")].filter(Boolean).join(", "));
       var btn=have?'<span style="color:#15803d;font:600 12px sans-serif">✓ schon Lead</span>':'<button class="lf-add" data-osm-map="'+key+'" style="margin-top:6px;border:0;background:#c00000;color:#fff;border-radius:6px;padding:6px 10px;font:600 12px sans-serif;cursor:pointer">+ Als Lead</button>';
       L.marker([lat,lon]).addTo(_markers).bindPopup('<b>'+esc(t.name||"")+'</b>'+(addr?'<br>'+addr:'')+'<br>'+btn);
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
     var pre=_aiErr?("KI-Suche fehlgeschlagen: "+esc(_aiErr)+". Auch die Karten-Suche ist gerade nicht erreichbar. "):"";
     if(/noplace/.test(m))osmStatus(pre+'Region „'+esc(wo)+'“ nicht gefunden. Anders schreiben (z. B. „Bayern“, „München“).');
     else if(/overpass/.test(m))osmStatus(pre+"Suche fehlgeschlagen oder Region zu groß. Bitte enger eingrenzen (z. B. Stadt statt Bundesland) und erneut versuchen.");
     else osmStatus(pre||"Suche gerade nicht möglich (offline oder Kartendienst nicht erreichbar). Später erneut versuchen.");
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
   lastQuery=was+" in "+wo;searchLand=guessLand(wo);_lastWas=was;_lastWo=wo;
   osmLoading('KI durchsucht das Web nach „'+esc(lastQuery)+'“ … <b>gründliche Recherche – das dauert bis zu ~2 Minuten</b>, bitte warten.');
   apiAi(was,wo).then(function(leads){
     if(!leads.length){osmClearResults();osmStatus('Die KI hat für „'+esc(lastQuery)+'“ keine Firmen gefunden. Tipp: anderen Begriff (z. B. „Kompostierung", „Recycling", „Erdenwerk") oder ein größeres Gebiet (z. B. „Bayern" statt nur einer Stadt) versuchen.');return;}
     _searchSrc="KI";renderOsm(leads.map(aiToEl));
   }).catch(function(e){osmClearResults();osmStatus('KI-Suche fehlgeschlagen: '+esc(String((e&&e.message)||e))+'. Bitte erneut versuchen.');});
 }
 document.getElementById("osmSearch").onclick=leadSearch;
 document.getElementById("osmWas").addEventListener("keydown",function(e){if(e.key==="Enter")leadSearch();});
 document.getElementById("osmWo").addEventListener("keydown",function(e){if(e.key==="Enter")leadSearch();});
 document.getElementById("osmResults").addEventListener("click",function(e){
   if(e.target.closest("a"))return; // Web-Links normal lassen
   if(e.target.id==="osmMore"){aiMore();return;}
   if(e.target.id==="osmAddAll"){var ex=osmExisting(),added=[];Object.keys(osmLast).forEach(function(k){var el=osmLast[k],t=el.tags||{},a=osmAddr(t);if(ex[k]||ex[((t.name||"")+"|"+(a.ort||"")).toLowerCase()])return;var c=osmMake(k);if(c)added.push(c);});if(added.length)bulkSave(added,false);renderOsm(osmEls);renderLeads();osmStatus(added.length+" neue Leads übernommen – sie stehen unten in deiner Lead-Liste.");return;}
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
 document.body.addEventListener("click",function(e){
   if(e.target.closest("a"))return;
   var row=e.target.closest(".crow");if(row&&row.getAttribute("data-id")){openDetail(row.getAttribute("data-id"));}
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
   var c=byId(id);if(!c)return;curId=id;
   var loc=[c.str,[c.plz,c.ort].filter(Boolean).join(" ")].filter(Boolean);
   var addr=[c.strasse,[c.plz,c.ort].filter(Boolean).join(" "),landLabel(c.land)].filter(Boolean).join(", ");
   var ll=contactLatLon(c);
   var notizClean=(c.notiz||"").replace(/^\s*Auf Karte:.*$/gim,"").trim();
   var acts=(c.activities||[]).slice().sort(function(a,b){return b.date-a.date;});
   var fu=c.followup&&!c.followup.done&&c.followup.due?c.followup:null;
   var html=''+
   '<button class="btn ghost sm" id="backBtn" style="margin-bottom:10px">← Zurück</button>'+
   '<div class="detail-head">'+
     '<div class="av">'+esc(initials(displayName(c)))+'</div>'+
     '<div style="flex:1;min-width:0"><h2>'+esc(displayName(c))+'</h2>'+
       '<div class="who">'+esc([fullName(c),c.firma&&fullName(c)?"":""].filter(Boolean).join(""))+
         (fullName(c)&&c.firma?esc(fullName(c)):"")+(c.anrede?' · '+esc(c.anrede):'')+'</div>'+
     '</div>'+
     '<span class="pill '+esc(c.status||"lead")+'" style="align-self:flex-start">'+esc(statusLabel(c.status))+'</span>'+
   '</div>'+
   '<div class="quick">'+
     (c.tel?'<a class="btn sm primary" href="tel:'+esc(c.tel)+'"><svg viewBox="0 0 24 24"><path d="M5 4h4l2 5-3 2a13 13 0 006 6l2-3 5 2v4a2 2 0 01-2 2A17 17 0 013 6a2 2 0 012-2"/></svg>Anrufen</a>':'')+
     (c.mobil?'<a class="btn sm" href="tel:'+esc(c.mobil)+'">Mobil</a>':'')+
     (c.mail?'<a class="btn sm" href="mailto:'+esc(c.mail)+'"><svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>E-Mail</a>':'')+
     '<button class="btn sm primary" id="offerBtn"><svg viewBox="0 0 24 24"><path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z"/><path d="M14 3v5h5"/></svg>Angebot erstellen</button>'+
     '<button class="btn sm" id="addActBtn"><svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>Aktivität</button>'+
     '<button class="btn sm" id="editBtn">Bearbeiten</button>'+
   '</div>'+
   // Status-Schnellwechsel
   '<div class="fg" style="max-width:240px;margin:8px 0"><label>Status ändern</label><select class="field" id="dStatus">'+
     STATUS.map(function(s){return '<option value="'+s[0]+'"'+(c.status===s[0]?' selected':'')+'>'+esc(s[1])+'</option>';}).join("")+'</select></div>'+
   // Stammdaten
   '<dl class="kv">'+
     (c.firma2?'<dt>Zusatz</dt><dd>'+esc(c.firma2)+'</dd>':'')+
     (addr?'<dt>Adresse</dt><dd>'+esc(addr)+'</dd>':'')+
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
   // Standort-Karte des Kontakts
   (function(){var mq=ll?(ll.lat+","+ll.lon):(addr||"");if(!mq)return "";var eq=encodeURIComponent(mq);
     return '<div style="margin:8px 0"><iframe id="detMap" title="Standort-Karte" src="https://maps.google.com/maps?q='+eq+'&z=14&output=embed" style="width:100%;height:220px;border:0;border-radius:12px" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>'+
       '<div style="margin-top:6px"><a class="btn sm" href="https://www.google.com/maps?q='+eq+'" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" style="width:15px;height:15px;stroke:currentColor;fill:none;stroke-width:1.7"><path d="M12 21s-7-5.2-7-11a7 7 0 0114 0c0 5.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>In Google Maps öffnen</a></div></div>';})()+
   // Wiedervorlage
   '<div class="fu-box'+(fu?' active-fu':'')+'" id="fuBox">'+
     '<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px"><b style="font-size:13px">Wiedervorlage / Rückruf</b>'+
       (fu?'<span class="due '+dueClass(fu.due)+'">'+dueLabel(fu.due)+'</span>':'<span style="font-size:12px;color:var(--muted)">keine</span>')+'</div>'+
     (fu&&fu.note?'<div style="font-size:13px;margin-bottom:8px">'+esc(fu.note)+'</div>':'')+
     '<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">'+
       '<input class="field" type="date" id="fuDate" value="'+(fu?new Date(fu.due).toISOString().slice(0,10):"")+'" style="width:auto">'+
       '<input class="field" id="fuNote" placeholder="Notiz (optional)" value="'+(fu?esc(fu.note||""):"")+'" style="flex:1;min-width:140px">'+
       '<button class="btn sm" id="fuSet">Setzen</button>'+
       (fu?'<button class="btn sm danger" id="fuDone">Erledigt</button>':'')+
     '</div>'+
   '</div>'+
   // Aktivitäten
   '<h3 style="font-family:var(--mono);font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:18px 0 10px">Verlauf / Lebenslauf ('+acts.length+')</h3>'+
   (acts.length?'<div class="tl">'+acts.map(actItem).join("")+'</div>':'<div style="font-size:13px;color:var(--muted);background:var(--field);border:1px dashed var(--line-strong);border-radius:12px;padding:14px;text-align:center">Hier entsteht der komplette Verlauf: <b>wann</b> war Kontakt, <b>wer</b>, Anrufe, E-Mails, <b>Angebote</b> (mit Nr./Betrag) und Notizen.<br><button class="btn sm primary" id="emptyAddAct" style="margin-top:10px">+ Erste Aktivität erfassen</button></div>')+
   '<div style="margin:22px 0 8px;display:flex;gap:8px;flex-wrap:wrap"><button class="btn danger sm" id="delBtn">Kontakt löschen</button></div>';
   var v=document.getElementById("view-detail");v.innerHTML=html;show("detail");
   document.getElementById("backBtn").onclick=function(){renderList();show("list");};
   document.getElementById("editBtn").onclick=function(){openForm(curId);};
   document.getElementById("addActBtn").onclick=function(){openActModal(curId);};
   document.getElementById("offerBtn").onclick=function(){gotoConfigurator(c,false);};
   var eab=document.getElementById("emptyAddAct");if(eab)eab.onclick=function(){openActModal(curId);};
   document.getElementById("dStatus").onchange=function(){c.status=this.value;c.updated=Date.now();saveContact(c);openDetail(curId);};
   document.getElementById("fuSet").onclick=function(){var d=document.getElementById("fuDate").value;if(!d){alert("Bitte ein Datum wählen.");return;}c.followup={due:new Date(d+"T09:00").getTime(),note:document.getElementById("fuNote").value.trim(),done:false};c.updated=Date.now();saveContact(c);openDetail(curId);};
   var fd=document.getElementById("fuDone");if(fd)fd.onclick=function(){if(c.followup)c.followup.done=true;c.updated=Date.now();saveContact(c);openDetail(curId);};
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
     L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19,attribution:"© OpenStreetMap-Mitwirkende"}).addTo(_detMap);
     L.marker([ll.lat,ll.lon],{icon:flagIcon(L)}).addTo(_detMap);
     setTimeout(function(){try{_detMap.invalidateSize();}catch(e){}},150);
   }).catch(function(){});
 }
 // PDF (data-URI) in neuem Tab öffnen – als Blob, da reine data-URIs oft blockiert werden.
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
   if(a.pdf){var _psvg='<svg viewBox="0 0 24 24"><path d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8z"/><path d="M14 3v5h5"/></svg>';offer+='<button class="tl-offer" data-pdfact="'+a.id+'" title="Fertiges PDF ansehen (ohne Konfigurator)">'+_psvg+'PDF ansehen</button>';}
   return '<div class="tl-item '+cls+'">'+
     '<div class="tl-dot"><svg viewBox="0 0 24 24">'+icon+'</svg></div>'+
     '<div class="tl-top"><span class="tl-type">'+esc(actLabel(a.type))+'</span>'+
       '<span class="tl-when">'+fmtDateTime(a.date)+'</span>'+(a.by?'<span class="tl-by">· '+esc(a.by)+'</span>':'')+
       '<button class="tl-del" data-act="'+a.id+'">löschen</button></div>'+
     (a.note?'<div class="tl-note">'+esc(a.note)+'</div>':'')+offer+
   '</div>';
 }
 function fmtEur(v){var n=parseFloat(String(v).replace(/[^0-9.,-]/g,"").replace(/\./g,"").replace(",","."));if(isNaN(n))return String(v);return n.toLocaleString("de-DE")+" €";}
 // Aktivität löschen
 document.getElementById("view-detail").addEventListener("click",function(e){
   var pb=e.target.closest("[data-pdfact]");if(pb){e.preventDefault();var pid=pb.getAttribute("data-pdfact");var pc=byId(curId);var pa=pc&&(pc.activities||[]).filter(function(x){return x.id===pid;})[0];if(pa&&pa.pdf)openPdfUri(pa.pdf);return;}
   var lo=e.target.closest("[data-actid]");if(lo){var aid=lo.getAttribute("data-actid");var cc=byId(curId);var act=cc&&(cc.activities||[]).filter(function(x){return x.id===aid;})[0];try{if(act&&act.config)localStorage.setItem("amb_lepton_loadoffer_data",JSON.stringify(act.config));else if(act&&act.offer)localStorage.setItem("amb_lepton_loadoffer",act.offer);}catch(_){}return;} // Link navigiert selbst zum Konfigurator
   var d=e.target.closest(".tl-del");if(!d)return;var aid=d.getAttribute("data-act");var c=byId(curId);if(!c)return;
   c.activities=(c.activities||[]).filter(function(x){return x.id!==aid;});c.updated=Date.now();saveContact(c);openDetail(curId);
 });

 /* ---------- Aktivität-Modal ---------- */
 var actType="anruf",actForId=null,_offerReturnState=null,_offerReturnPdf=null;
 var modal=document.getElementById("actModal");
 document.getElementById("actSeg").addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;actType=b.getAttribute("data-t");var bs=this.querySelectorAll("button");for(var i=0;i<bs.length;i++)bs[i].classList.toggle("on",bs[i]===b);toggleOfferField();});
 function toggleOfferField(){document.getElementById("actOfferWrap").style.display=(actType==="angebot")?"":"none";}
 function openActModal(id){
   actForId=id;actType="anruf";_offerReturnState=null;_offerReturnPdf=null;
   var bs=document.querySelectorAll("#actSeg button");for(var i=0;i<bs.length;i++)bs[i].classList.toggle("on",bs[i].getAttribute("data-t")==="anruf");
   document.getElementById("actDate").value=nowLocalInput();
   document.getElementById("actNote").value="";
   document.getElementById("actOfferNr").value="";document.getElementById("actBetrag").value="";
   document.getElementById("actFu").checked=true;document.getElementById("actFuDays").value=7;
   // Angebote aus Konfigurator füllen
   var offers=loadOffers();var sel=document.getElementById("actOffer");
   var names=Object.keys(offers).sort();
   sel.innerHTML='<option value="">— keines —</option>'+names.map(function(n){
     var o=offers[n]||{};var nr=(o.fields&&o.fields.m_nr)?(" · Nr "+o.fields.m_nr):"";
     return '<option value="'+esc(n)+'">'+esc(n)+esc(nr)+'</option>';
   }).join("");
   toggleOfferField();
   modal.classList.add("open");
 }
 document.getElementById("actCancel").onclick=function(){modal.classList.remove("open");};
 document.getElementById("actCreateOffer").onclick=function(){var c=byId(actForId);if(c){modal.classList.remove("open");gotoConfigurator(c,true);}};
 modal.addEventListener("click",function(e){if(e.target===modal)modal.classList.remove("open");});
 // Rücksprung aus dem Konfigurator: Angebot wurde gespeichert -> Aktivität „Angebot gesendet" vorbereiten.
 function checkOfferReturn(){
   try{var d=localStorage.getItem("amb_lepton_offer_done");if(!d)return;localStorage.removeItem("amb_lepton_offer_done");
     var o=JSON.parse(d);if(!o||!o.contactId)return;var c=byId(o.contactId);if(!c)return;
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
   var dv=document.getElementById("actDate").value;var ts=dv?new Date(dv).getTime():Date.now();
   var a={id:uid(),type:actType,date:ts,note:document.getElementById("actNote").value.trim(),by:(CUR&&CUR.n)||""};
   if(actType==="angebot"){var off=document.getElementById("actOffer").value;if(off)a.offer=off;var onr=document.getElementById("actOfferNr").value.trim();if(onr)a.offerNr=onr;var ab=document.getElementById("actBetrag").value.trim();if(ab)a.betrag=ab;
     // Wenn ein Konfigurator-Angebot gewählt wurde, Nr automatisch übernehmen
     var offs=loadOffers();if(off&&!a.offerNr){var o=offs[off];if(o&&o.fields&&o.fields.m_nr)a.offerNr=o.fields.m_nr;}
     // Volle Angebots-Konfiguration in der Aktivität ablegen -> liegt im CRM, geräteübergreifend.
     var cfg=_offerReturnState||(off&&offs[off])||null;if(cfg)a.config=cfg;
     if(_offerReturnPdf)a.pdf=_offerReturnPdf;}
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
   c.updated=Date.now();saveContact(c);modal.classList.remove("open");openDetail(actForId);
 };

 /* ---------- Formular (Neu/Bearbeiten) ---------- */
 function fInput(id,label,val,type,full,ph){return '<div class="fg'+(full?' full':'')+'"><label>'+label+'</label><input class="field" id="f_'+id+'" type="'+(type||"text")+'" value="'+esc(val||"")+'"'+(ph?' placeholder="'+esc(ph)+'"':'')+'></div>';}
 function openForm(id){
   var c=id?byId(id):null;var isNew=!c;c=c||{};
   var statusSel='<div class="fg"><label>Status</label><select class="field" id="f_status">'+STATUS.map(function(s){return '<option value="'+s[0]+'"'+((c.status||"lead")===s[0]?' selected':'')+'>'+esc(s[1])+'</option>';}).join("")+'</select></div>';
   var landSel='<div class="fg"><label>Land</label><select class="field" id="f_land">'+LANDS.map(function(l){return '<option value="'+l[0]+'"'+((c.land||"DE")===l[0]?' selected':'')+'>'+esc(l[1])+'</option>';}).join("")+'</select></div>';
   var ownerSel='<div class="fg"><label>Betreuer (Vertriebler)</label><select class="field" id="f_owner"><option value="">—</option>'+
     USERS.filter(function(u){return u.n;}).map(function(u){var sel=(c.owner||(CUR&&CUR.n))===u.n?' selected':'';return '<option'+sel+'>'+esc(u.n)+'</option>';}).join("")+'</select></div>';
   var html=''+
   '<button class="btn ghost sm" id="fBack" style="margin-bottom:10px">← Zurück</button>'+
   '<h2 class="vh">'+(isNew?"Neuer Kontakt / Lead":"Kontakt bearbeiten")+'</h2>'+
   '<div class="sub">Pflicht ist nur ein Name (Firma oder Person).</div>'+
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
   document.getElementById("fSave").onclick=function(){
     function g(k){var e=document.getElementById("f_"+k);return e?e.value.trim():"";}
     var rec=c.id?c:{id:uid(),created:Date.now(),activities:[]};
     ["firma","firma2","anrede","vorname","nachname","strasse","plz","ort","land","status","tel","mobil","mail","web","ustid","gf","bl","menge","sieb","news","quelle","owner","notiz"].forEach(function(k){rec[k]=g(k);});
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
 ["fStatus","fLand","fOwner","fSort"].forEach(function(id){document.getElementById(id).addEventListener("change",renderList);});
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
 document.getElementById("csvFile").onchange=function(e){var f=e.target.files[0];if(!f)return;var rd=new FileReader();rd.onload=function(){var n=importCSV(rd.result);alert(n+" Leads importiert.");renderList();renderDashboard();show("list");};rd.readAsText(f);e.target.value="";};
 var CSV_COLS={firma:"firma",company:"firma",zusatz:"firma2",anrede:"anrede",vorname:"vorname",firstname:"vorname",nachname:"nachname",lastname:"nachname",name:"nachname",strasse:"strasse","straße":"strasse",street:"strasse",plz:"plz",zip:"plz",ort:"ort",city:"ort",land:"land",country:"land",tel:"tel",telefon:"tel",phone:"tel",mobil:"mobil",mobile:"mobil",mail:"mail",email:"mail","e-mail":"mail",web:"web",website:"web",url:"web",ustid:"ustid",vat:"ustid",quelle:"quelle",source:"quelle",notiz:"notiz",note:"notiz",notes:"notiz",status:"status"};
 function splitCSVLine(line,sep){var out=[],cur="",q=false;for(var i=0;i<line.length;i++){var ch=line[i];if(q){if(ch==='"'){if(line[i+1]==='"'){cur+='"';i++;}else q=false;}else cur+=ch;}else{if(ch==='"')q=true;else if(ch===sep){out.push(cur);cur="";}else cur+=ch;}}out.push(cur);return out;}
 function importCSV(text){
   text=text.replace(/^﻿/,"");var lines=text.split(/\r?\n/).filter(function(l){return l.trim();});if(lines.length<2)return 0;
   var sep=(lines[0].split(";").length>lines[0].split(",").length)?";":",";
   var head=splitCSVLine(lines[0],sep).map(function(h){return CSV_COLS[h.trim().toLowerCase()]||null;});
   var n=0,added=[];
   for(var r=1;r<lines.length;r++){var cells=splitCSVLine(lines[r],sep);var rec={id:uid(),created:Date.now(),updated:Date.now(),status:"lead",land:"DE",activities:[]};var has=false;
     for(var c=0;c<head.length;c++){if(head[c]&&cells[c]!=null){var val=cells[c].trim();if(val){rec[head[c]]=val;has=true;}}}
     if(!has)continue;if(rec.land)rec.land=rec.land.toUpperCase().slice(0,2)||"DE";if(!findStatus(rec.status))rec.status="lead";
     DB.contacts.push(rec);added.push(rec);n++;}
   bulkSave(added,false);return n;
 }
 function findStatus(s){for(var i=0;i<STATUS.length;i++)if(STATUS[i][0]===s)return true;return false;}
 (function(){var tpl="firma;anrede;vorname;nachname;strasse;plz;ort;land;tel;mobil;mail;web;quelle;notiz\n"+
   "Mustermann GmbH;Herr;Max;Mustermann;Industriestr. 1;80331;München;DE;+49 89 123456;;info@mustermann.de;mustermann.de;Messe Bauma;Interesse Lepton 5100\n";
   document.getElementById("csvTpl").href="data:text/csv;charset=utf-8,"+encodeURIComponent(tpl);})();
 document.getElementById("wipeBtn").onclick=function(){if(confirm("Wirklich ALLE CRM-Daten auf diesem Gerät löschen? Das kann nicht rückgängig gemacht werden.")){if(confirm("Sicher? Letzte Warnung.")){DB={contacts:[]};bulkSave([],true);renderDashboard();renderList();show("dashboard");}}};

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
 document.getElementById("reconnBtn").onclick=function(){var b=this;b.textContent="Prüfe…";initBackend();setTimeout(function(){b.textContent="Verbindung prüfen";renderDataConn();},900);};
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
 function boot(){
   if(booted)return;booted=true;
   initFilters();renderDashboard();renderList();show("dashboard");
   refreshNotifBtn();renderDataConn();
   initBackend();                // Cloud/Server erkennen + geteilte Daten laden (sonst lokal)
   checkOfferReturn();           // aus dem Konfigurator zurückgekommen? Angebot-Aktivität vorbereiten.
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
const CACHE="vertrieb-v9";
const ASSETS=["./","./index.html","./manifest.webmanifest","./icon-192.png","./icon-512.png",
  "./vendor/leaflet.js","./vendor/leaflet.css",
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
  if(req.url.indexOf("tile.openstreetmap")>=0)return;  // Karten-Kacheln nicht cachen (Browser-Cache reicht)
  if(req.url.indexOf("supabase.co")>=0)return;          // Cloud-DB immer live, nie cachen
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
for need in ['id="gateForm"','id="clist"','id="actModal"','renderDashboard','amb_lepton_crm','amb_lepton_configs','checkReminders','initBackend','api.php','id="connState"','id="osmSearch"','overpass-api.de','osmToContact','id="osmMap"','ensureLeaflet','tile.openstreetmap','id="sbUrl"','sbUpsert','supabase.co','id="cMap"','showContactsMap','id="actBetrag"','flagIcon','id="detMap"','contactLatLon','leadSearch','apiAi','aiPost','id="aiSecret"','/functions/v1/']:
    assert need in out, "Pflicht-Markierung fehlt: "+need
# Leaflet (Karten-Bibliothek) muss lokal vorhanden sein (Laufzeit-Abhängigkeit der Standort-Karte)
for vf in ["leaflet.js","leaflet.css","images/marker-icon.png","images/marker-shadow.png"]:
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
