import os, json
HERE=os.path.dirname(os.path.abspath(__file__))
A=json.load(open(os.path.join(HERE,"assets.b64.json"),encoding="utf8"))
IMG=A["IMG"]; BANNERS=A["BANNERS"]; HERO=A["HERO"]; LOGO_L=A["LOGO_L"]; LOGO_D=A["LOGO_D"]; RED=A["RED"]; RED2=A["RED2"]
CATS=json.load(open(os.path.join(HERE,"catalog.json"),encoding="utf8"))

TPL = r'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Alzinger · Lepton 5100 Konfigurator</title>
<meta name="theme-color" content="#c00000">
<link rel="manifest" href="manifest.webmanifest">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Lepton Konfigurator">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
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
.topbar-in{max-width:1120px;margin:0 auto;padding:14px 20px 12px;position:relative}
.tb-logo img{height:34px;display:block;margin:2px auto 0}
.tb-div{height:1px;background:rgba(255,255,255,.45);margin:12px 0}
.tb-row{display:flex;align-items:center;justify-content:space-between}
.tb-icons{display:flex;gap:20px}
.tb-icons a{color:#fff;display:inline-flex}
.tb-icons svg,.tb-burger svg{width:26px;height:26px;stroke:#fff;fill:none;stroke-width:1.7}
.tb-burger{background:none;border:0;cursor:pointer;padding:4px;display:inline-flex}
.menu{position:absolute;top:100%;right:14px;margin-top:8px;width:268px;background:#fff;border-radius:12px;box-shadow:0 18px 44px rgba(0,0,0,.28);overflow:hidden;display:none;z-index:90}
.menu.open{display:block}
.menu .mh{background:var(--ink);color:#fff;font-family:var(--mono);font-size:10px;letter-spacing:.18em;text-transform:uppercase;padding:12px 16px}
.menu button{display:flex;width:100%;align-items:center;justify-content:space-between;gap:10px;background:#fff;border:0;border-top:1px solid var(--line);padding:14px 16px;font-family:var(--sans);font-size:15px;font-weight:600;color:var(--ink);cursor:pointer;text-align:left}
.menu button:hover{background:#faf7f7}
.menu button.active{color:var(--red)}
.menu button .dot{width:9px;height:9px;border-radius:50%;border:2px solid var(--line-strong);flex-shrink:0}
.menu button.active .dot{background:var(--red);border-color:var(--red)}
.menu button .lab small{display:block;font-weight:400;font-size:11px;color:var(--muted);margin-top:1px}
.hero{position:relative;min-height:330px;background-image:linear-gradient(90deg,rgba(16,17,19,.86) 0%,rgba(16,17,19,.55) 55%,rgba(16,17,19,.25) 100%),url("%%HERO%%");background-size:cover;background-position:center;color:#fff;display:flex;align-items:flex-end}
.hero-in{max-width:1120px;margin:0 auto;width:100%;padding:42px 20px 40px}
.hero .kick{font-family:var(--mono);font-size:11px;letter-spacing:.24em;text-transform:uppercase;color:#ff9d8c;font-weight:500}
.hero h1{font-size:clamp(28px,6vw,46px);font-weight:800;letter-spacing:-.02em;line-height:1.04;margin-top:12px}
.hero .hsub{font-size:14px;color:#d6d4cf;margin-top:8px}
.hero .cta{display:inline-flex;align-items:center;gap:10px;margin-top:20px;background:var(--red);color:#fff;border:0;border-radius:8px;padding:13px 20px;font-family:var(--mono);font-size:12px;letter-spacing:.06em;text-transform:uppercase;font-weight:600;cursor:pointer}
.hero .cta:hover{background:var(--red2)}
.wrap{max-width:1120px;margin:0 auto;padding:30px 20px 150px}
.modebar{display:inline-flex;align-items:center;gap:9px;background:#fff;border:1px solid var(--line);border-radius:30px;padding:7px 15px 7px 9px;font-size:13px;margin-bottom:8px}
.modebar .pill{background:var(--red);color:#fff;font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;padding:4px 10px;border-radius:20px;font-weight:600}
.section{margin-top:30px}
.kick2{font-family:var(--mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--red);font-weight:600}
.section>h2{font-size:21px;font-weight:700;letter-spacing:-.01em;margin:8px 0 16px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.fld{display:flex;flex-direction:column;gap:6px}
.fld label{font-size:12.5px;color:var(--muted);font-weight:600}
.fld input,.fld select,.fld textarea{font-family:var(--sans);font-size:14px;border:1px solid var(--line-strong);background:var(--field);border-radius:8px;padding:10px 12px;color:var(--ink);width:100%;outline:none;transition:.15s}
.fld textarea{font-size:13px;line-height:1.5;resize:vertical;min-height:66px}
.fld :focus{border-color:var(--red);box-shadow:0 0 0 3px var(--red-soft);background:#fffdfc}
.fld.wide{grid-column:1/-1}
.subnote{font-family:var(--mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--gold);margin:2px 0 8px;grid-column:1/-1}
.basis{display:flex;gap:18px;background:var(--ink);color:#fff;border-radius:12px;overflow:hidden;flex-wrap:wrap;align-items:stretch}
.basis .bimg{flex:1;min-width:220px;min-height:170px;background-size:cover;background-position:center}
.basis .btx{flex:1.3;min-width:260px;padding:20px 22px;display:flex;flex-direction:column;justify-content:center}
.basis .tag{font-family:var(--mono);font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;background:var(--gold);color:#16181a;padding:3px 8px;border-radius:4px;font-weight:600;align-self:flex-start}
.basis .t{font-weight:800;font-size:20px;margin-top:11px}
.basis .a{font-family:var(--mono);font-size:11px;color:#b7b5ac;margin-top:4px}
.basis .d{font-size:12.5px;color:#cfcdc6;margin-top:10px;line-height:1.5}
.basis .p{font-family:var(--mono);font-weight:600;font-size:23px;margin-top:14px}
.catblk{margin-top:18px}
.catblk>.ch{font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--slate);font-weight:600;display:flex;align-items:center;gap:9px;margin:0 2px 10px}
.catblk>.ch::before{content:"";width:5px;height:14px;background:var(--gold);border-radius:1px}
.catbanner{background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px;margin-bottom:14px;text-align:center}
.catbanner img{max-width:100%;max-height:260px;width:auto;height:auto;display:inline-block}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(212px,1fr));gap:13px}
.pcard{position:relative;background:var(--surface);border:1.5px solid var(--line);border-radius:12px;overflow:hidden;cursor:pointer;transition:.14s;display:flex;flex-direction:column}
.pcard:hover{border-color:var(--line-strong);transform:translateY(-2px);box-shadow:0 8px 22px rgba(0,0,0,.07)}
.pcard.on{border-color:var(--red);box-shadow:0 0 0 3px var(--red-soft)}
.pcard.noimg .pbody{padding-top:38px}.pcard.noimg{min-height:118px}
.pcard .pimg{height:160px;background-size:contain;background-repeat:no-repeat;background-position:center;background-color:#f3f2ee}
.pcard .pbody{padding:13px 14px 14px;display:flex;flex-direction:column;gap:5px;flex:1}
.pcard .pname{font-size:13.5px;font-weight:600;line-height:1.3}
.pcard .pdesc{font-size:11.5px;color:var(--muted);line-height:1.4;flex:1}
.pcard .pfoot{display:flex;justify-content:space-between;align-items:center;margin-top:4px;gap:8px}
.pcard .part{font-family:var(--mono);font-size:10px;color:var(--faint)}
.pcard .pprice{font-family:var(--mono);font-weight:600;font-size:13.5px;color:var(--red);white-space:nowrap}
.pcard .ck{position:absolute;top:10px;right:10px;width:26px;height:26px;border-radius:50%;background:rgba(22,24,26,.5);border:1.5px solid rgba(255,255,255,.7);transition:.14s;z-index:2}
.pcard.on .ck{background:var(--red);border-color:var(--red)}
.pcard.on .ck::after{content:"";position:absolute;left:9px;top:5px;width:5px;height:11px;border:solid #fff;border-width:0 2px 2px 0;transform:rotate(45deg)}
.bar{position:fixed;left:0;right:0;bottom:0;background:var(--ink);color:#fff;z-index:60;box-shadow:0 -6px 24px rgba(0,0,0,.2)}
.bar .str{display:flex;height:4px}.bar .str span{flex:1}
.bar .in{max-width:1120px;margin:0 auto;padding:11px 20px;display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap}
.bar .sums{display:flex;gap:24px;flex-wrap:wrap;align-items:baseline}
.bar .b{display:flex;flex-direction:column;gap:1px}
.bar .k{font-family:var(--mono);font-size:9px;letter-spacing:.12em;text-transform:uppercase;color:#a9a69c}
.bar .vv{font-family:var(--mono);font-weight:600;font-size:17px}.bar .vv.big{font-size:22px}.bar .vv.cr{color:#ff8d7a}
.btn{font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;padding:12px 17px;border:0;border-radius:8px;cursor:pointer;font-weight:600;transition:.15s}
.btn.p{background:var(--red);color:#fff}.btn.p:hover{background:var(--red2)}
.btn.g{background:transparent;color:#cfcdc4;border:1px solid #45474a}.btn.g:hover{border-color:#fff;color:#fff}
.pvbar{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin:34px 0 14px}
.pvbar .t{font-family:var(--mono);font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:600}
.savebar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:30px 0 0}.savebar select{flex:1;min-width:170px;font-family:var(--sans);font-size:13px;border:1px solid var(--line-strong);background:var(--field);border-radius:8px;padding:9px 11px;color:var(--ink);outline:none}.btn.s{background:#fff;border:1px solid var(--line-strong);color:var(--ink)}.btn.s:hover{border-color:var(--ink)}
#doc{background:#fff;border:1px solid var(--line-strong);border-radius:6px;max-width:860px;margin:0 auto;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.08)}
#doc .topstr{display:flex;height:6px}#doc .topstr span{flex:1}
#doc .pad{padding:42px 46px 38px}
.dtop{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;flex-wrap:wrap}
.dfirm{font-size:11.5px;color:var(--muted);line-height:1.5}
.dfirm .dlogo{height:30px;display:block;margin-bottom:3px}
.dfirm .fnm{font-weight:800;font-size:13px;color:var(--ink)}
.dmeta{text-align:right;font-family:var(--mono);font-size:11.5px;color:var(--muted);line-height:1.7}
.dmeta b{color:var(--ink)}
.addr{margin-top:28px;font-size:13px;line-height:1.55}
.addr .s{font-family:var(--mono);font-size:9px;letter-spacing:.18em;text-transform:uppercase;color:var(--faint);display:block;margin-bottom:5px}
.dtitle{margin-top:28px;font-size:25px;font-weight:800;letter-spacing:-.01em}
.dtitle .u{display:block;width:56px;height:4px;background:var(--red);border-radius:2px;margin-top:9px}
.dtitle .sub{font-family:var(--mono);font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--red);margin-top:11px;font-weight:600}
.ptxt{font-size:13px;line-height:1.6;margin-top:14px}
.salut{margin-top:20px;font-size:13.5px;line-height:1.6}.salut p{margin-bottom:10px}
.sec-h{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--red);font-weight:600;margin-top:26px;padding-bottom:6px;border-bottom:2px solid var(--ink)}
.vp{margin-top:14px}
.vp .party{display:flex;justify-content:space-between;gap:14px;background:#faf9f6;border:1px solid var(--line);border-radius:8px;padding:13px 15px;font-size:12.5px;line-height:1.55}
.vp .role{font-family:var(--mono);font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--red);font-weight:600;align-self:flex-start;white-space:nowrap}
.vp .amp{text-align:center;font-size:12px;color:var(--muted);margin:7px 0}
.gdata{margin-top:14px;display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.gdata .gx{background:#faf9f6;border:1px solid var(--line);border-radius:8px;padding:10px 13px}
.gdata .gk{font-family:var(--mono);font-size:9px;letter-spacing:.12em;text-transform:uppercase;color:var(--faint)}
.gdata .gv{font-weight:600;font-size:14px;margin-top:3px}
.machine{margin-top:18px;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.machine .mh{background:var(--ink);color:#fff;padding:13px 16px;display:flex;justify-content:space-between;gap:12px;align-items:baseline;flex-wrap:wrap}
.machine .mh .nm{font-weight:700;font-size:14.5px}.machine .mh .art2{font-family:var(--mono);font-size:11px;color:#b7b5ac}
.machine .mh .pr{font-family:var(--mono);font-weight:600;font-size:15px}
.machine .specs{padding:13px 18px;columns:2;column-gap:30px;font-size:11.5px;color:var(--muted);line-height:1.7}
.machine .specs div{break-inside:avoid;padding-left:11px;position:relative}
.machine .specs div::before{content:"·";position:absolute;left:0;color:var(--gold);font-weight:700}
.lines{margin-top:18px}
.lines .grp{font-family:var(--mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--slate);font-weight:600;margin:14px 0 6px;padding-bottom:4px;border-bottom:1px solid var(--line)}
.lines .grp.dark{color:var(--ink);border-color:var(--ink)}
.lines .ln{display:flex;justify-content:space-between;gap:14px;padding:6px 0;font-size:12.5px;border-bottom:1px dotted var(--line);align-items:center}
.lines .lt{display:flex;align-items:center;gap:11px;min-width:0}
.lines .th{width:60px;height:42px;border-radius:4px;background-size:contain;background-repeat:no-repeat;background-position:center;background-color:#fff;flex-shrink:0;border:1px solid var(--line)}
.lines .n .a{font-family:var(--mono);font-size:9.5px;color:var(--faint)}
.lines .p{font-family:var(--mono);font-weight:500;white-space:nowrap}
.totals{margin-top:18px;border-top:2px solid var(--ink);padding-top:12px}
.totals .row{display:flex;justify-content:space-between;gap:14px;font-size:13px;padding:4px 0}
.totals .row .v{font-family:var(--mono)}
.totals .row.net{font-size:15px;font-weight:700}.totals .row.net .v{color:var(--red);font-size:16px}
.totals .row.gross{background:var(--ink);color:#fff;margin:8px -10px 0;padding:11px 10px;border-radius:6px;font-weight:700}.totals .row.gross .v{color:#fff;font-size:16px}
.taxnote{font-size:11px;color:var(--muted);margin-top:8px;font-style:italic}
.terms{margin-top:24px;display:grid;grid-template-columns:1fr 1fr;gap:18px}
.terms .h{font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--red);font-weight:600;margin-bottom:6px}
.terms .x{font-size:11.5px;color:#33332f;line-height:1.55;white-space:pre-line}
.legal{margin-top:24px;padding-top:14px;border-top:1px solid var(--line);font-size:10.5px;color:var(--muted);line-height:1.6}
.sign{margin-top:22px;font-size:12.5px;line-height:1.6}.sign .g{margin-bottom:18px}.sign .nm{font-weight:700}
.sig2{margin-top:30px;display:grid;grid-template-columns:1fr 1fr;gap:30px}
.sig2 .sigbox{font-size:11.5px;color:var(--muted)}
.sig2 .sl{border-top:1px solid var(--ink);margin-bottom:6px;height:34px}
.sig2 .sigbox b{color:var(--ink)}
#doc .dfoot{display:flex;height:6px}#doc .dfoot span{flex:1}
body.mode-gebraucht .pcard .pprice,body.mode-gebraucht .basis .p{display:none}
@media (max-width:680px){#doc .pad{padding:26px 22px}.machine .specs{columns:1}.terms,.sig2{grid-template-columns:1fr}.gdata{grid-template-columns:1fr}.dmeta{text-align:left}}
@media print{@page{margin:13mm}body{background:#fff}body *{visibility:hidden}#doc,#doc *{visibility:visible}#doc{position:absolute;left:0;top:0;width:100%;max-width:none;border:0;box-shadow:none;border-radius:0}#doc .pad{padding:0}.noprint{display:none!important}.machine,.lines .grp,.lines .ln,.totals .row.gross,.sign,.sig2,.vp .party{break-inside:avoid}}
</style>
</head>
<body>
<header class="topbar noprint">
  <div class="topbar-in">
    <div class="tb-logo"><img src="" id="tbLogo" alt="Alzinger"></div>
    <div class="tb-div"></div>
    <div class="tb-row">
      <div class="tb-icons">
        <a href="mailto:martin@alzinger-maschinenbau.de" aria-label="E-Mail"><svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg></a>
        <a href="tel:+4917031285 33" aria-label="Telefon"><svg viewBox="0 0 24 24"><path d="M5 4h4l2 5-3 2a13 13 0 006 6l2-3 5 2v4a2 2 0 01-2 2A17 17 0 013 6a2 2 0 012-2"/></svg></a>
        <a href="https://alzinger-recyclingtechnik.com" target="_blank" rel="noopener" aria-label="Website"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 010 18M12 3a14 14 0 000 18"/></svg></a>
      </div>
      <button class="tb-burger" id="burger" aria-label="Menü"><svg viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>
    </div>
    <div class="menu" id="menu">
      <div class="mh">Dokument wählen</div>
      <button data-mode="angebot"><span class="lab">Angebot<small>Unverbindliches Angebot</small></span><span class="dot"></span></button>
      <button data-mode="kaufvertrag"><span class="lab">Kaufvertrag<small>Verbindlicher Kaufvertrag</small></span><span class="dot"></span></button>
      <button data-mode="gebraucht"><span class="lab">Gebrauchtmaschine<small>Angebot Gebrauchtmaschine</small></span><span class="dot"></span></button>
    </div>
  </div>
</header>
<section class="hero noprint">
  <div class="hero-in">
    <h1 id="heroTitle">Angebot erstellen</h1>
    <button class="cta" onclick="document.getElementById('main').scrollIntoView({behavior:'smooth'})">Zur Konfiguration ↓</button>
  </div>
</section>
<div class="wrap noprint" id="main">
  <div class="modebar">Aktiver Modus: <span class="pill" id="modePill">Angebot</span></div>
  <div class="section">
    <div class="kick2">01 · Dokumentdaten</div>
    <h2 id="h2meta">Angebot &amp; Verkäufer</h2>
    <div class="card"><div class="grid">
      <div class="fld"><label id="lblNr">Angebotsnummer</label><input id="m_nr" placeholder="z. B. ANG-2026-001"></div>
      <div class="fld"><label>Datum</label><input id="m_datum"></div>
      <div class="fld"><label>Ort</label><input id="m_ort" placeholder="Schierling"></div>
      <div class="fld"><label>Verkäufer</label><input id="m_verk" value="Łukasz Zdziennicki"></div>
      <div class="fld"><label>Telefon Verkäufer</label><input id="m_vtel" placeholder="optional"></div>
      <div class="fld"><label>E-Mail Verkäufer</label><input id="m_vmail" placeholder="optional"></div>
      <div id="gebrauchtFields" class="grid" style="grid-column:1/-1;display:none">
        <div class="subnote">Angaben Gebrauchtmaschine</div>
        <div class="fld"><label>Baujahr</label><input id="g_jahr" placeholder="z. B. 2021"></div>
        <div class="fld"><label>Betriebsstunden</label><input id="g_std" placeholder="z. B. 1.850 h"></div>
        <div class="fld"><label>Maschinen-/Serien-Nr.</label><input id="g_sn" placeholder="optional"></div>
        <div class="fld wide"><label>Zustand</label><input id="g_zustand" placeholder="z. B. sehr guter, gepflegter Zustand"></div>
      </div>
    </div></div>
  </div>
  <div class="section">
    <div class="kick2">02 · Kunde</div>
    <h2>Rechnungsanschrift &amp; Ansprechpartner</h2>
    <div class="card"><div class="grid">
      <div class="fld"><label>Firmenname</label><input id="k_firma"></div>
      <div class="fld"><label>Firmenname Zusatz</label><input id="k_firma2" placeholder="optional"></div>
      <div class="fld"><label>Anrede</label><select id="k_anrede"><option>Herr</option><option>Frau</option><option value="">—</option></select></div>
      <div class="fld"><label>Vorname</label><input id="k_vor"></div>
      <div class="fld"><label>Nachname</label><input id="k_nach"></div>
      <div class="fld"><label>Straße</label><input id="k_str"></div>
      <div class="fld"><label>PLZ</label><input id="k_plz"></div>
      <div class="fld"><label>Ort</label><input id="k_ort"></div>
      <div class="fld"><label>Land</label><input id="k_land" placeholder="z. B. Polen"></div>
      <div class="fld"><label>Telefon</label><input id="k_tel" placeholder="optional"></div>
      <div class="fld"><label>E-Mail</label><input id="k_mail" placeholder="optional"></div>
      <div class="fld"><label>USt-IdNr.</label><input id="k_ustid" placeholder="optional"></div>
    </div></div>
  </div>
  <div class="section">
    <div class="kick2">03 · Konfiguration</div>
    <h2>Maschine &amp; Ausstattung</h2>
    <div class="basis"><div class="bimg" id="basisImg"></div>
      <div class="btx"><span class="tag">Basismaschine · enthalten</span><div class="t">Lepton 5100</div><div class="a">Art.-Nr. 5000379</div><div class="d">Mobiler Scheibenseparator · Bunker 8 m³ · Siebdeck 1 (3–38°) · 4 E-Motoren</div><div class="p">340.300 €</div></div>
    </div>
    <div id="catalog"></div>
  </div>
  <div class="section">
    <div class="kick2">04 · Konditionen</div>
    <h2>Steuer, Liefer- &amp; Zahlungsbedingungen</h2>
    <div class="card"><div class="grid">
      <div class="fld"><label>Steuer</label><select id="t_tax">
        <option value="ausfuhr">Steuerfreie Ausfuhrlieferung (Drittland, § 4 Abs. 1 Nr. 1 a UStG)</option>
        <option value="ig">Steuerfreie innergemeinschaftliche Lieferung (EU, § 4 Abs. 1 Nr. 1 b UStG)</option>
        <option value="mwst">19 % USt. (Inland Deutschland)</option>
      </select></div>
      <div class="fld" id="rabattWrap"><label>Rabatt (netto, €)</label><input id="t_rabatt" inputmode="decimal" placeholder="0"></div>
      <div class="fld wide" id="gPreisWrap" style="display:none"><label>Verkaufspreis Gebrauchtmaschine (netto, €)</label><input id="g_preis" inputmode="decimal" placeholder="z. B. 185.000"></div>
      <div class="fld wide"><label>Lieferbedingung</label><input id="t_liefer" value="FCA Schierling Germany (Incoterms 2010)"></div>
      <div class="fld"><label>Liefertermin</label><input id="t_termin" placeholder="z. B. KW 40 / 2026"></div>
      <div class="fld wide"><label>Zahlungsbedingungen</label><textarea id="t_zahlung">30% Anzahlung bei Auftragserteilung
Restbetrag bei Versandbereitschaft
Die gesamte noch ausstehende Summe ist bei früherer Lieferung vor Auslieferung fällig.</textarea></div>
      <div class="fld wide"><label>Gewährleistung</label><textarea id="t_gewahr">1 Jahr ab Auslieferung, nicht auf Verschleißteile
Schäden, die durch Nichtbeachtung der Betriebsanleitung entstehen, sind von jeder Gewährleistung ausgeschlossen.</textarea></div>
      <div class="fld wide"><label>Sonderabsprachen</label><textarea id="t_sonder" placeholder="optional"></textarea></div>
    </div></div>
  </div>
  <div class="savebar"><select id="savedList"><option value="">— Gespeicherte Dokumente —</option></select><button class="btn s" id="loadBtn">Laden</button><button class="btn s" id="saveBtn">Speichern</button><button class="btn s" id="delBtn">Löschen</button></div>
  <div class="pvbar"><span class="t" id="pvTitle">Angebot — Vorschau</span>
    <div><button class="btn g" id="resetBtn">Zurücksetzen</button> <button class="btn p" id="printBtn" onclick="window.print()">Angebot drucken</button></div>
  </div>
</div>
<div id="doc"></div>
<div class="bar noprint">
  <div class="str"><span style="background:var(--red)"></span><span style="background:var(--slate)"></span><span style="background:#fff"></span><span style="background:var(--gold)"></span></div>
  <div class="in">
    <div class="sums">
      <div class="b"><span class="k">Optionen</span><span class="vv" id="sumOpt">0</span></div>
      <div class="b"><span class="k">Netto gesamt</span><span class="vv big" id="sumNet">340.300 €</span></div>
      <div class="b"><span class="k" id="sumTaxLabel">Gesamt</span><span class="vv cr" id="sumGross">340.300 €</span></div>
    </div>
    <button class="btn p" onclick="window.print()">Drucken</button>
  </div>
</div>
<script>
const IMG=%%IMG%%; const BANNERS=%%BANNERS%%; const CATS=%%CATS%%;
const ASSET={LOGO_L:"%%LOGOL%%",LOGO_D:"%%LOGOD%%"};
const BASE={name:"Basismaschine Lepton 5100",art:"5000379",price:340300};
const TITLES={angebot:"Angebot erstellen",kaufvertrag:"Kaufvertrag erstellen",gebraucht:"Gebrauchtmaschine – Angebot"};
const PILLS={angebot:"Angebot",kaufvertrag:"Kaufvertrag",gebraucht:"Gebrauchtmaschine"};
(function(){
 "use strict";
 var optById={}; CATS.forEach(function(c){c.opts.forEach(function(o){optById[o.id]=o;});});
 var state={chosen:{},excl:{sd1:"",sd2:""},mode:"angebot"};
 var IDS=["m_nr","m_datum","m_ort","m_verk","m_vtel","m_vmail","k_firma","k_firma2","k_anrede","k_vor","k_nach","k_str","k_plz","k_ort","k_land","k_tel","k_mail","k_ustid","t_tax","t_rabatt","t_liefer","t_termin","t_zahlung","t_gewahr","t_sonder","g_jahr","g_std","g_sn","g_zustand","g_preis"];
 function parseNum(s){s=String(s||"").trim().replace(/\s/g,"");if(/^\d{1,3}(\.\d{3})+$/.test(s))s=s.replace(/\./g,"");s=s.replace(",",".");var x=parseFloat(s);return isNaN(x)?0:x;}
 function money(x){var dd=Number.isInteger(x)?0:2;return x.toLocaleString("de-DE",{minimumFractionDigits:dd,maximumFractionDigits:2})+" \u20ac";}
 function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
 function v(id){var e=document.getElementById(id);return e?(e.value||"").trim():"";}
 function imgDiv(o){return (o.img&&IMG[o.img])?'<div class="pimg" style="background-image:url('+IMG[o.img]+')"></div>':'';}
 function cardInner(o){return '<div class="ck"></div>'+imgDiv(o)+'<div class="pbody"><div class="pname">'+esc(o.name)+'</div><div class="pdesc">'+esc(o.desc||"")+'</div><div class="pfoot"><span class="part">Art. '+o.art+'</span><span class="pprice">'+(o.price===0?"inkl.":money(o.price))+'</span></div></div>';}
 function buildCatalog(){
  var html="";
  CATS.forEach(function(c){
   html+='<div class="catblk"><div class="ch">'+esc(c.h)+(c.ex?' <span style="color:#9a9aa0;font-weight:500;text-transform:none;letter-spacing:0">\u00b7 erneut tippen zum Abw\u00e4hlen</span>':'')+'</div>'+(BANNERS[c.h]?'<div class="catbanner"><img src="'+BANNERS[c.h]+'" alt=""></div>':'')+'<div class="cards">';
   if(c.ex){ c.opts.forEach(function(o){html+='<div class="pcard radio'+(o.img?'':' noimg')+'" data-group="'+c.ex+'" data-id="'+o.id+'">'+cardInner(o)+'</div>';}); }
   else { c.opts.forEach(function(o){html+='<label class="pcard'+(o.img?'':' noimg')+'" data-id="'+o.id+'">'+cardInner(o)+'<input type="checkbox" data-id="'+o.id+'" hidden></label>';}); }
   html+='</div></div>';
  });
  document.getElementById("catalog").innerHTML=html;
  document.querySelectorAll('.pcard input[type=checkbox]').forEach(function(cb){cb.addEventListener("change",function(){state.chosen[cb.getAttribute("data-id")]=cb.checked;cb.closest(".pcard").classList.toggle("on",cb.checked);render();});});
  document.querySelectorAll('.pcard.radio').forEach(function(card){card.addEventListener("click",function(){var g=card.getAttribute("data-group"),id=card.getAttribute("data-id");state.excl[g]=(state.excl[g]===id)?"":id;document.querySelectorAll('.pcard.radio[data-group="'+g+'"]').forEach(function(c2){c2.classList.toggle("on",c2.getAttribute("data-id")===state.excl[g]);});render();});});
 }
 function selectedList(){
  var out=[];
  CATS.forEach(function(c){var items=[];
   if(c.ex){var id=state.excl[c.ex];if(id&&optById[id]){var o=optById[id];items.push({name:c.h+": "+o.name,art:o.art,price:o.price,img:o.img});}}
   else{c.opts.forEach(function(o){if(state.chosen[o.id])items.push({name:o.name,art:o.art,price:o.price,img:o.img});});}
   if(items.length)out.push({grp:c.h,items:items});});
  return out;
 }
 function compute(){
  var sel=selectedList(),count=0;sel.forEach(function(g){g.items.forEach(function(){count++;});});
  var tax=v("t_tax");
  if(state.mode==="gebraucht"){var gp=parseNum(v("g_preis")),ug=tax==="mwst"?gp*0.19:0;return {gebraucht:true,net:gp,count:count,rab:0,na:gp,tax:tax,ust:ug,gross:gp+ug,sel:sel};}
  var net=BASE.price;sel.forEach(function(g){g.items.forEach(function(it){net+=it.price;});});
  var rab=parseNum(v("t_rabatt"));if(rab>net)rab=net;var na=net-rab;
  var ust=tax==="mwst"?na*0.19:0;
  return {gebraucht:false,net:net,count:count,rab:rab,na:na,tax:tax,ust:ust,gross:na+ust,sel:sel};
 }
 function taxNote(t){if(t==="ausfuhr")return "Bei obiger Lieferung handelt es sich um eine steuerfreie Ausfuhrlieferung gem. \u00a7 4 Abs. 1 Nr. 1 a UStG.";if(t==="ig")return "Steuerfreie innergemeinschaftliche Lieferung gem. \u00a7 4 Abs. 1 Nr. 1 b UStG. Die USt-IdNr. des Erwerbers ist anzugeben.";return "Alle Preise verstehen sich zzgl. der gesetzlichen Umsatzsteuer (19 %).";}
 function pers(){return [v("k_anrede"),v("k_vor"),v("k_nach")].filter(Boolean).join(" ");}
 function kaeuferLines(){
  var a=[];
  if(v("k_firma"))a.push("<b>"+esc(v("k_firma"))+"</b>");
  if(v("k_firma2"))a.push(esc(v("k_firma2")));
  if(pers())a.push((v("k_firma")?"z. Hd. ":"")+esc(pers()));
  if(v("k_str"))a.push(esc(v("k_str")));
  var po=[v("k_plz"),v("k_ort")].filter(Boolean).join(" ");if(po)a.push(esc(po));
  if(v("k_land"))a.push(esc(v("k_land")));
  return a;
 }
 function docHead(label){
  var nr=v("m_nr"),datum=v("m_datum"),ort=v("m_ort"),meta="";
  if(nr)meta+=(label||"Nr.")+' <b>'+esc(nr)+'</b><br>';
  if(datum)meta+=esc(ort?ort+", ":"")+'<b>'+esc(datum)+'</b>';else if(ort)meta+=esc(ort);
  return '<div class="dtop"><div class="dfirm"><img class="dlogo" src="'+ASSET.LOGO_D+'"><div class="fnm">Maschinenbau GmbH</div>Am Gewerbering 14 \u00b7 D-84069 Schierling<br>www.alzinger-recyclingtechnik.com</div><div class="dmeta">'+(meta||"&nbsp;")+'</div></div>';
 }
 function addrBlock(){
  var a=kaeuferLines();
  if(v("k_ustid"))a.push('<span style="color:#9a9aa0;font-size:11px">USt-IdNr. '+esc(v("k_ustid"))+'</span>');
  return '<div class="addr"><span class="s">An</span>'+(a.length?a.join("<br>"):'<span style="color:#9a9aa0">\u2014 Kundenadresse \u2014</span>')+'</div>';
 }
 function salutation(){
  var anr=v("k_anrede"),nach=v("k_nach"),s;
  if(anr==="Herr"&&nach)s="Sehr geehrter Herr "+esc(nach)+",";else if(anr==="Frau"&&nach)s="Sehr geehrte Frau "+esc(nach)+",";else s="Sehr geehrte Damen und Herren,";
  return '<div class="salut"><p>'+s+'</p><p>wir bedanken uns herzlich f\u00fcr Ihr Interesse an unserem Produkt und unterbreiten Ihnen gerne \u2013 freibleibend \u2013 das nachfolgende Angebot.</p></div>';
 }
 function machineSpec(label,showPrice){
  return '<div class="machine"><div class="mh"><span class="nm">Basismaschine Lepton 5100 <span class="art2">(5000379)</span>'+(label?' \u00b7 <span style="color:#ffd2cf">'+label+'</span>':'')+'</span>'+(showPrice===false?'':'<span class="pr">'+money(BASE.price)+'</span>')+'</div><div class="specs"><div>Grundrahmen</div><div>Bunker 8 m\u00b3 mit beidseitiger Bef\u00fcllung</div><div>Siebdeck 1 mit Neigungsverstellung 3\u201338\u00b0</div><div>Siebdeck 1: 4 Elektromotoren, reversierbar</div><div>Elektrischer Antrieb aller B\u00e4nder</div><div>Siebdeck 1 Band quer: 910 mm, 2 m/s</div><div>Feinkornband 1: 1550 mm, 1,4 m/s</div><div>Feinkornband 2: 800 mm, 1,1 m/s</div><div>Feinkornband 3: 800 mm, 1,9 m/s</div><div>Ohne Siebwalzen \u00b7 Bunker ohne Vordosierung</div></div></div>';
 }
 function linesHTML(sel,grpLabel,showPrices){
  var lh='<div class="lines"><div class="grp dark">'+grpLabel+'</div>';
  sel.forEach(function(g){lh+='<div class="grp">'+esc(g.grp)+'</div>';
   g.items.forEach(function(it){var th=(it.img&&IMG[it.img])?'<i class="th" style="background-image:url('+IMG[it.img]+')"></i>':'';
    lh+='<div class="ln"><span class="lt">'+th+'<span class="n">'+esc(it.name)+' <span class="a">('+it.art+')</span></span></span>'+(showPrices===false?'':'<span class="p">'+(it.price===0?"inklusive":money(it.price))+'</span>')+'</div>';});});
  if(!sel.length)lh+='<div style="font-size:12px;color:#9a9aa0;padding:8px 0">Noch keine Optionen gew\u00e4hlt \u2013 die Basismaschine ist enthalten.</div>';
  return lh+'</div>';
 }
 function totalsHTML(r,netLabel){
  var th='<div class="totals"><div class="row"><span>Basismaschine Lepton 5100</span><span class="v">'+money(BASE.price)+'</span></div><div class="row"><span>Optionen / Ausstattung ('+r.count+')</span><span class="v">'+money(r.net-BASE.price)+'</span></div>';
  if(r.rab>0)th+='<div class="row"><span>Zwischensumme netto</span><span class="v">'+money(r.net)+'</span></div><div class="row"><span>abzgl. Rabatt</span><span class="v">\u2212'+money(r.rab)+'</span></div>';
  th+='<div class="row net"><span>'+netLabel+'</span><span class="v">'+money(r.na)+'</span></div>';
  if(r.tax==="mwst")th+='<div class="row"><span>zzgl. 19 % USt.</span><span class="v">'+money(r.ust)+'</span></div><div class="row gross"><span>Gesamtbetrag (brutto)</span><span class="v">'+money(r.gross)+'</span></div>';
  return th+'<div class="taxnote">'+taxNote(r.tax)+'</div></div>';
 }
 function totalsGebraucht(r){
  if(r.na===0)return '<div class="totals"><div class="row net"><span>Verkaufspreis (netto)</span><span class="v" style="color:#9a9aa0">\u2014 Preis manuell eingeben \u2014</span></div></div>';
  var th='<div class="totals"><div class="row net"><span>Verkaufspreis (netto)</span><span class="v">'+money(r.na)+'</span></div>';
  if(r.tax==="mwst")th+='<div class="row"><span>zzgl. 19 % USt.</span><span class="v">'+money(r.ust)+'</span></div><div class="row gross"><span>Gesamtbetrag (brutto)</span><span class="v">'+money(r.gross)+'</span></div>';
  return th+'<div class="taxnote">'+taxNote(r.tax)+'</div></div>';
 }
 function termsHTML(){
  var liefer=v("t_liefer"),termin=v("t_termin"),lieferTxt=liefer+(termin?"\nLiefertermin: "+termin:""),sonder=v("t_sonder"),tb='<div class="terms">';
  if(sonder)tb+='<div style="grid-column:1/-1"><div class="h">Sonderabsprachen</div><div class="x">'+esc(sonder)+'</div></div>';
  tb+='<div><div class="h">Gew\u00e4hrleistung</div><div class="x">'+esc(v("t_gewahr"))+'</div></div>';
  tb+='<div><div class="h">Lieferbedingungen</div><div class="x">'+esc(lieferTxt)+'</div></div>';
  tb+='<div style="grid-column:1/-1"><div class="h">Zahlungsbedingungen</div><div class="x">'+esc(v("t_zahlung"))+'</div></div>';
  return tb+'</div>';
 }
 function legalBlock(tax){return '<div class="legal">Dieses Dokument ist freibleibend und unverbindlich. '+taxNote(tax)+' Es gelten die Allgemeinen Gesch\u00e4ftsbedingungen der Alzinger Maschinenbau GmbH, die der K\u00e4ufer anerkennt. Die AGB sind unter www.alzinger-recyclingtechnik.com einsehbar.</div>';}
 function signSingle(){var sh='<div class="sign"><div class="g">Gerne stehen wir Ihnen f\u00fcr weitere Fragen zur Verf\u00fcgung.<br>Mit freundlichen Gr\u00fc\u00dfen</div><div class="nm">'+esc(v("m_verk"))+'</div><div>Alzinger Maschinenbau GmbH</div>';if(v("m_vtel"))sh+='<div style="color:#5e6166">Telefon: '+esc(v("m_vtel"))+'</div>';if(v("m_vmail"))sh+='<div style="color:#5e6166">E-Mail: '+esc(v("m_vmail"))+'</div>';return sh+'</div>';}
 function signTwo(){return '<div class="sig2"><div class="sigbox"><div class="sl"></div>Ort, Datum \u00b7 Unterschrift Verk\u00e4ufer<br><b>'+esc(v("m_verk"))+'</b> \u00b7 Alzinger Maschinenbau GmbH</div><div class="sigbox"><div class="sl"></div>Ort, Datum \u00b7 Unterschrift K\u00e4ufer'+(pers()?'<br><b>'+esc(pers())+'</b>':'')+'</div></div>';}
 function gdataBlock(){
  var items=[["Baujahr",v("g_jahr")],["Betriebsstunden",v("g_std")],["Maschinen-Nr.",v("g_sn")],["Zustand",v("g_zustand")]].filter(function(x){return x[1];});
  if(!items.length)return '';
  return '<div class="sec-h">Maschinendaten</div><div class="gdata">'+items.map(function(x){return '<div class="gx"><div class="gk">'+x[0]+'</div><div class="gv">'+esc(x[1])+'</div></div>';}).join("")+'</div>';
 }
 function renderAngebot(r){return docHead("Angebot-Nr.")+addrBlock()+'<div class="dtitle">ANGEBOT<span class="u"></span><span class="sub">Mobile Sternsiebanlage LEPTON 5100 · Serie 2026</span></div>'+salutation()+machineSpec("",true)+linesHTML(r.sel,"Ausgew\u00e4hlte Optionen",true)+totalsHTML(r,"Gesamtkaufpreis (netto) inkl. aller gew\u00e4hlten Ausstattungsvarianten")+termsHTML()+legalBlock(r.tax)+signSingle();}
 function renderGebraucht(r){var anr=v("k_anrede"),nach=v("k_nach"),s=(anr==="Herr"&&nach)?"Sehr geehrter Herr "+esc(nach)+",":((anr==="Frau"&&nach)?"Sehr geehrte Frau "+esc(nach)+",":"Sehr geehrte Damen und Herren,");return docHead("Angebot-Nr.")+addrBlock()+'<div class="dtitle">ANGEBOT \u2013 GEBRAUCHTMASCHINE<span class="u"></span></div><div class="salut"><p>'+s+'</p><p>gerne unterbreiten wir Ihnen \u2013 freibleibend \u2013 das nachfolgende Angebot \u00fcber die unten beschriebene <b>Gebrauchtmaschine</b>.</p></div>'+gdataBlock()+machineSpec("Gebrauchtmaschine",false)+linesHTML(r.sel,"Ausstattung",false)+totalsGebraucht(r)+termsHTML()+legalBlock(r.tax)+signSingle();}
 function renderKaufvertrag(r){
  var k=kaeuferLines(); if(v("k_ustid"))k.push('<span style="color:#9a9aa0;font-size:11px">USt-IdNr. '+esc(v("k_ustid"))+'</span>');
  var vp='<div class="sec-h">Vertragspartner</div><div class="vp"><div class="party"><div>Alzinger Maschinenbau GmbH<br>Am Gewerbering 14<br>DE 84069 Schierling<br>vertreten durch '+esc(v("m_verk")||"\u2014")+'</div><div class="role">Verk\u00e4ufer</div></div><div class="amp">und</div><div class="party"><div>'+(k.length?k.join("<br>"):"\u2014 K\u00e4ufer \u2014")+'<br>vertreten durch '+esc(pers()||"\u2014")+'</div><div class="role">K\u00e4ufer</div></div></div><p class="ptxt">Die Parteien schlie\u00dfen folgenden Vertrag \u00fcber den Kauf einer Neumaschine.</p>';
  return docHead("Vertrag-Nr.")+'<div class="dtitle">KAUFVERTRAG<span class="u"></span><span class="sub">Mobile Sternsiebanlage LEPTON 5100 · Serie 2026</span></div>'+vp+'<div class="sec-h">Gegenstand des Vertrages</div><p class="ptxt">Der Verk\u00e4ufer verkauft und der K\u00e4ufer kauft zu den nachfolgenden Bedingungen folgende konfigurierte Neumaschine:</p>'+machineSpec("",true)+linesHTML(r.sel,"Ausstattung",true)+totalsHTML(r,"Kaufpreis (netto)")+termsHTML()+legalBlock(r.tax)+signTwo();
 }
 function renderDoc(r){
  var inner;
  if(state.mode==="kaufvertrag")inner=renderKaufvertrag(r);
  else if(state.mode==="gebraucht")inner=renderGebraucht(r);
  else inner=renderAngebot(r);
  var stripe='<div class="topstr"><span style="background:var(--red)"></span><span style="background:var(--slate)"></span><span style="background:#fff"></span><span style="background:var(--gold)"></span></div>';
  var foot='<div class="dfoot"><span style="background:var(--red)"></span><span style="background:var(--slate)"></span><span style="background:#fff"></span><span style="background:var(--gold)"></span></div>';
  document.getElementById("doc").innerHTML=stripe+'<div class="pad">'+inner+'</div>'+foot;
 }
 function render(){
  var r=compute();var dash=(r.gebraucht&&r.na===0);
  document.getElementById("sumOpt").textContent=r.count;
  document.getElementById("sumNet").textContent=dash?"\u2014":money(r.na);
  document.getElementById("sumTaxLabel").textContent=r.tax==="mwst"?"Brutto":"Gesamt netto";
  document.getElementById("sumGross").textContent=dash?"\u2014":money(r.gross);
  renderDoc(r);
 }
 function applyMode(m){
  state.mode=m;
  document.getElementById("heroTitle").textContent=TITLES[m];
  document.getElementById("modePill").textContent=PILLS[m];
  document.getElementById("gebrauchtFields").style.display=(m==="gebraucht")?"grid":"none";
  document.body.classList.toggle("mode-gebraucht",m==="gebraucht");
  document.getElementById("rabattWrap").style.display=(m==="gebraucht")?"none":"";
  document.getElementById("gPreisWrap").style.display=(m==="gebraucht")?"":"none";
  var isV=(m==="kaufvertrag");
  document.getElementById("h2meta").textContent=isV?"Kaufvertrag & Verk\u00e4ufer":(m==="gebraucht"?"Gebrauchtmaschine & Verk\u00e4ufer":"Angebot & Verk\u00e4ufer");
  document.getElementById("lblNr").textContent=isV?"Vertragsnummer":"Angebotsnummer";
  document.getElementById("pvTitle").textContent=PILLS[m]+" \u2014 Vorschau";
  document.getElementById("printBtn").textContent=PILLS[m]+" drucken";
  document.querySelectorAll("#menu button").forEach(function(b){b.classList.toggle("active",b.getAttribute("data-mode")===m);});
  document.getElementById("menu").classList.remove("open");
  render();
 }
 function resetAll(){
  state.chosen={};state.excl={sd1:"",sd2:""};
  document.querySelectorAll('.pcard input[type=checkbox]').forEach(function(cb){cb.checked=false;});
  document.querySelectorAll('.pcard').forEach(function(c){c.classList.remove("on");});
  ["t_rabatt","g_jahr","g_std","g_sn","g_zustand","g_preis"].forEach(function(id){var e=document.getElementById(id);if(e)e.value="";});
  render();
 }
 var SKEY="amb_lepton_configs";
 function loadAll(){try{return JSON.parse(localStorage.getItem(SKEY)||"{}");}catch(e){return {};}}
 function saveAll(o){try{localStorage.setItem(SKEY,JSON.stringify(o));return true;}catch(e){return false;}}
 function gatherState(){var f={};IDS.forEach(function(id){var e=document.getElementById(id);if(e)f[id]=e.value;});return {mode:state.mode,chosen:state.chosen,excl:state.excl,fields:f,ts:Date.now()};}
 function applyState(s){if(!s)return;var f=s.fields||{};IDS.forEach(function(id){var e=document.getElementById(id);if(e&&f[id]!==undefined)e.value=f[id];});state.chosen=s.chosen||{};state.excl=s.excl||{sd1:"",sd2:""};document.querySelectorAll('.pcard input[type=checkbox]').forEach(function(cb){var on=!!state.chosen[cb.getAttribute("data-id")];cb.checked=on;cb.closest(".pcard").classList.toggle("on",on);});document.querySelectorAll('.pcard.radio').forEach(function(c){var g=c.getAttribute("data-group");c.classList.toggle("on",c.getAttribute("data-id")===state.excl[g]);});applyMode(s.mode||"angebot");}
 function suggestName(){var who=[v("k_firma"),v("k_nach")].filter(Boolean).join(" ");return PILLS[state.mode]+(who?" "+who:"")+(v("m_nr")?" ("+v("m_nr")+")":"");}
 function refreshSaved(){var sel=document.getElementById("savedList");if(!sel)return;var o=loadAll(),names=Object.keys(o).sort();sel.innerHTML='<option value="">'+(names.length?"\u2014 Gespeichert ("+names.length+") \u2014":"\u2014 noch nichts gespeichert \u2014")+'</option>'+names.map(function(n){return '<option value="'+esc(n)+'">'+esc(n)+'</option>';}).join("");}
 function doSave(){var name=window.prompt("Name f\u00fcr dieses Dokument:",suggestName());if(name===null)return;name=name.trim();if(!name)return;var o=loadAll();o[name]=gatherState();if(!saveAll(o)){window.alert("Speichern hier nicht m\u00f6glich \u2013 in der ver\u00f6ffentlichten App (eigene Adresse) funktioniert es dauerhaft.");return;}refreshSaved();document.getElementById("savedList").value=name;}
 function doLoad(){var n=document.getElementById("savedList").value;if(!n)return;var o=loadAll();if(o[n])applyState(o[n]);}
 function doDelete(){var n=document.getElementById("savedList").value;if(!n)return;if(!window.confirm('"'+n+'" l\u00f6schen?'))return;var o=loadAll();delete o[n];saveAll(o);refreshSaved();}
 function init(){
  document.getElementById("tbLogo").src=ASSET.LOGO_L;
  if(IMG["image3"])document.getElementById("basisImg").style.backgroundImage="url("+IMG["image3"]+")";
  var dt=new Date();document.getElementById("m_datum").value=dt.toLocaleDateString("de-DE",{day:"2-digit",month:"2-digit",year:"numeric"});
  buildCatalog();
  IDS.forEach(function(id){var e=document.getElementById(id);if(e){e.addEventListener("input",render);e.addEventListener("change",render);}});
  document.getElementById("burger").addEventListener("click",function(e){e.stopPropagation();document.getElementById("menu").classList.toggle("open");});
  document.querySelectorAll("#menu button").forEach(function(b){b.addEventListener("click",function(){applyMode(b.getAttribute("data-mode"));});});
  document.addEventListener("click",function(e){var m=document.getElementById("menu");if(m.classList.contains("open")&&!m.contains(e.target)&&e.target.id!=="burger")m.classList.remove("open");});
  document.getElementById("resetBtn").addEventListener("click",resetAll);
  applyMode("angebot");
  refreshSaved();
  var _sb=document.getElementById("saveBtn");if(_sb)_sb.addEventListener("click",doSave);
  var _lb=document.getElementById("loadBtn");if(_lb)_lb.addEventListener("click",doLoad);
  var _db=document.getElementById("delBtn");if(_db)_db.addEventListener("click",doDelete);
  var _sl=document.getElementById("savedList");if(_sl)_sl.addEventListener("change",doLoad);
 }
 init();
})();
if("serviceWorker" in navigator){window.addEventListener("load",function(){navigator.serviceWorker.register("sw.js").catch(function(){});});}
</script>
</body>
</html>
'''

out=TPL
out=out.replace("%%IMG%%",json.dumps(IMG))
out=out.replace("%%BANNERS%%",json.dumps(BANNERS,ensure_ascii=False))
out=out.replace("%%CATS%%",json.dumps(CATS,ensure_ascii=False))
out=out.replace("%%HERO%%",HERO)
out=out.replace("%%LOGOL%%",LOGO_L)
out=out.replace("%%LOGOD%%",LOGO_D)
out=out.replace("%%RED%%",RED).replace("%%RED2%%",RED2)
for tok in ["%%IMG%%","%%BANNERS%%","%%CATS%%","%%HERO%%","%%LOGOL%%","%%LOGOD%%","%%RED%%","%%RED2%%"]:
    assert tok not in out, "Token uebrig: "+tok
for need in ['id="burger"','id="menu"','id="heroTitle"','renderKaufvertrag','renderGebraucht','data-mode="gebraucht"','id="tbLogo"']:
    assert need in out, "fehlt: "+need
p=os.path.join(HERE,"..","index.html")
open(p,"w",encoding="utf8").write(out)
print("index.html erzeugt – bytes",len(out.encode("utf8")))
