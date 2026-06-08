import os, json
HERE=os.path.dirname(os.path.abspath(__file__))
A=json.load(open(os.path.join(HERE,"assets.b64.json"),encoding="utf8"))
IMG=A["IMG"]; BANNERS=A["BANNERS"]; HERO=A["HERO"]; LOGO_L=A["LOGO_L"]; LOGO_D=A["LOGO_D"]; RED=A["RED"]; RED2=A["RED2"]
CATS=json.load(open(os.path.join(HERE,"catalog.json"),encoding="utf8"))
I18N_RAW=json.load(open(os.path.join(HERE,"i18n.json"),encoding="utf8"))

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
.tb-right{display:flex;align-items:center;gap:12px}
.langsel{display:inline-flex;gap:2px;background:rgba(255,255,255,.16);border-radius:8px;padding:3px}
.langsel button{background:none;border:0;color:#fff;font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:.04em;padding:5px 7px;border-radius:6px;cursor:pointer;opacity:.72;transition:.12s}
.langsel button:hover{opacity:1}
.langsel button.active{background:#fff;color:var(--red);opacity:1}
.tb-burger{background:none;border:0;cursor:pointer;padding:4px;display:inline-flex}
.menu{position:absolute;top:100%;right:14px;margin-top:8px;width:268px;max-height:84vh;background:#fff;border-radius:12px;box-shadow:0 18px 44px rgba(0,0,0,.28);overflow:hidden auto;display:none;z-index:90}
.menu.open{display:block}
.menu .mh{background:var(--ink);color:#fff;font-family:var(--mono);font-size:10px;letter-spacing:.18em;text-transform:uppercase;padding:12px 16px}
.menu>button{display:flex;width:100%;align-items:center;justify-content:space-between;gap:10px;background:#fff;border:0;border-top:1px solid var(--line);padding:14px 16px;font-family:var(--sans);font-size:15px;font-weight:600;color:var(--ink);cursor:pointer;text-align:left}
.menu>button:hover{background:#faf7f7}
.menu>button.active{color:var(--red)}
.menu>button .dot{width:9px;height:9px;border-radius:50%;border:2px solid var(--line-strong);flex-shrink:0}
.menu>button.active .dot{background:var(--red);border-color:var(--red)}
.menu>button .lab small{display:block;font-weight:400;font-size:11px;color:var(--muted);margin-top:1px}
.menu .mssec{padding:11px 14px;border-top:1px solid var(--line)}
.menu .mssec select{width:100%;font-family:var(--sans);font-size:13px;border:1px solid var(--line-strong);background:var(--field);border-radius:8px;padding:9px 10px;color:var(--ink);outline:none}
.menu .msbtns{display:flex;gap:6px;margin-top:8px}
.menu .msbtns button{flex:1;font-family:var(--mono);font-size:10px;letter-spacing:.04em;text-transform:uppercase;font-weight:600;padding:9px 4px;border:1px solid var(--line-strong);background:#fff;color:var(--ink);border-radius:7px;cursor:pointer}
.menu .msbtns button:hover{border-color:var(--ink)}
.hero{position:relative;min-height:330px;background-image:linear-gradient(90deg,rgba(16,17,19,.86) 0%,rgba(16,17,19,.55) 55%,rgba(16,17,19,.25) 100%),url("%%HERO%%");background-size:cover;background-position:center;color:#fff;display:flex;align-items:flex-end}
.hero-in{max-width:1120px;margin:0 auto;width:100%;padding:42px 20px 40px}
.hero .kick{font-family:var(--mono);font-size:11px;letter-spacing:.24em;text-transform:uppercase;color:#ff9d8c;font-weight:500}
.hero h1{font-size:clamp(28px,6vw,46px);font-weight:800;letter-spacing:-.02em;line-height:1.04;margin-top:12px}
.hero .hsub{font-family:var(--mono);font-size:12.5px;letter-spacing:.16em;text-transform:uppercase;color:#e7e5e0;margin-top:14px;font-weight:500}
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
.pcard.disabled{opacity:.42;filter:grayscale(.7);pointer-events:none}
.pcard.noimg .pbody{padding-top:38px}.pcard.noimg{min-height:118px}
.pcard .pimg{height:160px;background-size:contain;background-repeat:no-repeat;background-position:center;background-color:#fff}
.pcard .pbody{padding:13px 14px 14px;display:flex;flex-direction:column;gap:5px;flex:1}
.pcard .pname{font-size:13.5px;font-weight:600;line-height:1.3}
.pcard .pdesc{font-size:11.5px;color:var(--muted);line-height:1.4;flex:1}
.pspecs{display:flex;flex-direction:column;gap:3px}
.pcard .pspecs{margin-top:7px}
.pspecs .pr2{display:flex;justify-content:space-between;gap:10px;font-size:11px;line-height:1.3}
.pspecs .pk{color:var(--faint);white-space:nowrap}
.pspecs .pv{color:var(--ink);font-family:var(--mono);font-size:10.5px;text-align:right}
.pspecs .pf{color:var(--muted);font-size:11px;line-height:1.35;padding-left:11px;position:relative}
.pspecs .pf::before{content:"·";position:absolute;left:2px;color:var(--gold);font-weight:700}
.catbanner .cbinfo{text-align:left;max-width:560px;margin:12px auto 2px}
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
#doc{background:#fff;border:1px solid var(--line-strong);border-radius:6px;max-width:860px;margin:0 auto 140px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.08)}
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
.lines .ln{display:flex;justify-content:space-between;gap:14px;padding:5px 0;font-size:12.5px;border-bottom:1px solid var(--line-strong);align-items:center}
.lines .lt{display:flex;align-items:center;gap:13px;min-width:0}
.lines .th{width:104px;height:70px;border-radius:5px;object-fit:contain;background:#fff;flex-shrink:0;border:1px solid var(--line-strong)}
.lines .th.th-x{border:0;background:transparent}
.lines .n .a{font-family:var(--mono);font-size:9.5px;color:var(--faint)}
.lines .p{font-family:var(--mono);font-weight:500;white-space:nowrap}
.totals{margin-top:18px;border-top:2px solid var(--ink);padding-top:12px}
.totals .row{display:flex;justify-content:space-between;gap:14px;font-size:13px;padding:4px 0}
.totals .row .v{font-family:var(--mono);white-space:nowrap;flex-shrink:0}
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
body.mode-gebraucht .hero .hsub{display:none}
@media (max-width:680px){#doc .pad{padding:26px 22px}.machine .specs{columns:1}.terms,.sig2{grid-template-columns:1fr}.gdata{grid-template-columns:1fr}.dmeta{text-align:left}}
@media print{@page{margin:0}body{background:#fff}body *{visibility:hidden}#doc,#doc *{visibility:visible;-webkit-print-color-adjust:exact;print-color-adjust:exact}#doc{position:absolute;left:0;top:0;width:100%;max-width:none;margin:0;border:0;box-shadow:none;border-radius:0}#doc .pad{padding:13mm 14mm}.noprint{display:none!important}.machine,.lines .grp,.lines .ln,.totals .row.gross,.sign,.sig2,.vp .party{break-inside:avoid}}
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
</style>
</head>
<body>
<div id="gate" class="noprint">
  <div class="gc">
    <img class="gl" src="%%LOGOD%%" alt="Alzinger">
    <div class="gh">Anmeldung</div>
    <div class="gs">Lepton 5100 Konfigurator</div>
    <form id="gateForm" autocomplete="on">
      <input id="gu" name="username" placeholder="Benutzername" autocomplete="username" autocapitalize="none" autocorrect="off" spellcheck="false">
      <input id="gp" name="password" type="password" placeholder="Passwort" autocomplete="current-password">
      <button type="submit">Anmelden</button>
      <div class="ge" id="gerr"></div>
    </form>
  </div>
</div>
<script>
(function(){
 function sha256(ascii){function r(v,a){return (v>>>a)|(v<<(32-a));}var mp=Math.pow,mw=mp(2,32),res="",words=[],bl=ascii.length*8;var hash=sha256.h=sha256.h||[],k=sha256.k=sha256.k||[],pc=k.length,ic={},i,j;for(var c=2;pc<64;c++){if(!ic[c]){for(i=0;i<313;i+=c)ic[i]=c;hash[pc]=(mp(c,.5)*mw)|0;k[pc++]=(mp(c,1/3)*mw)|0;}}ascii+="\x80";while(ascii.length%64-56)ascii+="\x00";for(i=0;i<ascii.length;i++){j=ascii.charCodeAt(i);if(j>>8)return;words[i>>2]|=j<<((3-i)%4)*8;}words[words.length]=((bl/mw)|0);words[words.length]=bl;for(j=0;j<words.length;){var w=words.slice(j,j+=16),oh=hash;hash=hash.slice(0,8);for(i=0;i<64;i++){var w15=w[i-15],w2=w[i-2],a=hash[0],e=hash[4],t1=hash[7]+(r(e,6)^r(e,11)^r(e,25))+((e&hash[5])^((~e)&hash[6]))+k[i]+(w[i]=i<16?w[i]:(w[i-16]+(r(w15,7)^r(w15,18)^(w15>>>3))+w[i-7]+(r(w2,17)^r(w2,19)^(w2>>>10)))|0),t2=(r(a,2)^r(a,13)^r(a,22))+((a&hash[1])^(a&hash[2])^(hash[1]&hash[2]));hash=[(t1+t2)|0].concat(hash);hash[4]=(hash[4]+t1)|0;}for(i=0;i<8;i++)hash[i]=(hash[i]+oh[i])|0;}for(i=0;i<8;i++){for(j=3;j+1;j--){var b=(hash[i]>>(j*8))&255;res+=((b<16)?0:"")+b.toString(16);}}return res;}
 var USERS=[{h:"2a0e88896d2303027849314ab026e16a096c8234cc0bb3b4eb9ffe5e1fbfd324",n:""},{h:"378b467d56232e509fc568bfc3849a9d1fb40c6a248a35d755cb9db1053c33bf",n:"Johannes Rudel"},{h:"2c5ce471a6a1e91a47b4a357064cdab49fbc11e76982da2371b15c0c6608b80f",n:"Tobias Ermel"},{h:"50b9f421b5a362836fbb38ba11d8d59b76c287ef29d6c445df771a0c8f1116df",n:"Richard Alzinger",tel:"+49 170 3336025",mail:"richard@alzinger-maschinenbau.de"},{h:"9833d8644a16501b9eab7a849a294b8b209e32db63366041b50bbfa0107da4d3",n:"Adam Domaradzki"},{h:"0ad1350f32d0d469d4c044cb1ad38b4964763caf497112c76bfc462a81ccda9b",n:"Łukasz Zdziennicki"}];
 var AKEY="amb_lepton_auth",UKEY="amb_lepton_user";
 var gate=document.getElementById("gate");
 function pass(){gate.classList.add("hidden");}
 function findUser(hash){for(var i=0;i<USERS.length;i++)if(USERS[i].h===hash)return USERS[i];return null;}
 function setIf(id,val){if(!val)return false;var e=document.getElementById(id);if(e&&!e.value){e.value=val;return true;}return false;}
 function fillFields(o){if(!o)return;var ch=false;ch=setIf("m_verk",o.n)||ch;ch=setIf("m_vtel",o.tel)||ch;ch=setIf("m_vmail",o.mail)||ch;if(ch){var mv=document.getElementById("m_verk");if(mv){try{mv.dispatchEvent(new Event("input",{bubbles:true}));}catch(_){}}}}
 try{if(findUser(localStorage.getItem(AKEY)))pass();}catch(e){}
 document.getElementById("gateForm").addEventListener("submit",function(ev){ev.preventDefault();
  var u=(document.getElementById("gu").value||"").trim().toLowerCase(),p=(document.getElementById("gp").value||"");
  var hit=findUser(sha256(u+":"+p));
  if(hit){try{localStorage.setItem(AKEY,hit.h);localStorage.setItem(UKEY,JSON.stringify({n:hit.n||"",tel:hit.tel||"",mail:hit.mail||""}));}catch(_){}document.getElementById("gerr").textContent="";pass();fillFields(hit);}
  else{document.getElementById("gerr").textContent="Benutzername oder Passwort falsch.";var gp=document.getElementById("gp");gp.value="";gp.focus();}
 });
})();
</script>
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
      <div class="tb-right">
        <div class="langsel" id="langsel" aria-label="Sprache / Language">
          <button type="button" data-lang="de">DE</button>
          <button type="button" data-lang="en">EN</button>
          <button type="button" data-lang="pl">PL</button>
          <button type="button" data-lang="fr">FR</button>
        </div>
        <button class="tb-burger" id="burger" aria-label="Menü"><svg viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>
      </div>
    </div>
    <div class="menu" id="menu">
      <div class="mh" data-i18n="menu_choose">Dokument wählen</div>
      <button data-mode="angebot"><span class="lab"><span data-i18n="mode_angebot">Angebot</span><small data-i18n="mode_angebot_sub">Unverbindliches Angebot</small></span><span class="dot"></span></button>
      <button data-mode="kaufvertrag"><span class="lab"><span data-i18n="mode_kaufvertrag">Kaufvertrag</span><small data-i18n="mode_kaufvertrag_sub">Verbindlicher Kaufvertrag</small></span><span class="dot"></span></button>
      <button data-mode="gebraucht"><span class="lab"><span data-i18n="mode_gebraucht">Gebrauchtmaschine</span><small data-i18n="mode_gebraucht_sub">Angebot Gebrauchtmaschine</small></span><span class="dot"></span></button>
      <div class="mh" data-i18n="menu_saved">Gespeicherte Dokumente</div>
      <div class="mssec">
        <select id="savedList"><option value="">—</option></select>
        <div class="msbtns"><button id="loadBtn" data-i18n="btn_load">Laden</button><button id="saveBtn" data-i18n="btn_save">Speichern</button><button id="delBtn" data-i18n="btn_delete">Löschen</button></div>
      </div>
    </div>
  </div>
</header>
<section class="hero noprint">
  <div class="hero-in">
    <h1 id="heroTitle">Angebot erstellen</h1>
    <div class="hsub" data-i18n="hero_sub">Mobile Sternsiebanlage LEPTON 5100 · Serie 2026</div>
    <button class="cta" data-i18n="cta" onclick="document.getElementById('main').scrollIntoView({behavior:'smooth'})">Zur Konfiguration ↓</button>
  </div>
</section>
<div class="wrap noprint" id="main">
  <div class="modebar"><span data-i18n="active_mode">Aktiver Modus:</span> <span class="pill" id="modePill">Angebot</span></div>
  <div class="section">
    <div class="kick2" data-i18n="s1_kick">01 · Dokumentdaten</div>
    <h2 id="h2meta">Angebot &amp; Verkäufer</h2>
    <div class="card"><div class="grid">
      <div class="fld"><label id="lblNr">Angebotsnummer</label><input id="m_nr" data-i18n-ph="ph_nr" placeholder="z. B. ANG-2026-001"></div>
      <div class="fld"><label data-i18n="lbl_datum">Datum</label><input id="m_datum"></div>
      <div class="fld"><label data-i18n="lbl_ort">Ort</label><input id="m_ort" placeholder="Schierling"></div>
      <div class="fld"><label data-i18n="lbl_verk">Verkäufer</label><input id="m_verk" data-i18n-ph="ph_verk" placeholder="Name Verkäufer"></div>
      <div class="fld"><label data-i18n="lbl_vtel">Telefon Verkäufer</label><input id="m_vtel" data-i18n-ph="ph_optional" placeholder="optional"></div>
      <div class="fld"><label data-i18n="lbl_vmail">E-Mail Verkäufer</label><input id="m_vmail" data-i18n-ph="ph_optional" placeholder="optional"></div>
      <div id="gebrauchtFields" class="grid" style="grid-column:1/-1;display:none">
        <div class="subnote" data-i18n="g_subnote">Angaben Gebrauchtmaschine</div>
        <div class="fld"><label data-i18n="lbl_g_jahr">Baujahr</label><input id="g_jahr" data-i18n-ph="ph_g_jahr" placeholder="z. B. 2021"></div>
        <div class="fld"><label data-i18n="lbl_g_std">Betriebsstunden</label><input id="g_std" data-i18n-ph="ph_g_std" placeholder="z. B. 1.850 h"></div>
        <div class="fld"><label data-i18n="lbl_g_sn">Maschinen-/Serien-Nr.</label><input id="g_sn" data-i18n-ph="ph_optional" placeholder="optional"></div>
        <div class="fld wide"><label data-i18n="lbl_g_zustand">Zustand</label><input id="g_zustand" data-i18n-ph="ph_g_zustand" placeholder="z. B. sehr guter, gepflegter Zustand"></div>
      </div>
    </div></div>
  </div>
  <div class="section">
    <div class="kick2" data-i18n="s2_kick">02 · Kunde</div>
    <h2 data-i18n="h2_customer">Rechnungsanschrift &amp; Ansprechpartner</h2>
    <div class="card"><div class="grid">
      <div class="fld"><label data-i18n="lbl_firma">Firmenname</label><input id="k_firma"></div>
      <div class="fld"><label data-i18n="lbl_firma2">Firmenname Zusatz</label><input id="k_firma2" data-i18n-ph="ph_optional" placeholder="optional"></div>
      <div class="fld"><label data-i18n="lbl_anrede">Anrede</label><select id="k_anrede"><option value="Herr" data-i18n="opt_herr">Herr</option><option value="Frau" data-i18n="opt_frau">Frau</option><option value="">—</option></select></div>
      <div class="fld"><label data-i18n="lbl_vor">Vorname</label><input id="k_vor"></div>
      <div class="fld"><label data-i18n="lbl_nach">Nachname</label><input id="k_nach"></div>
      <div class="fld"><label data-i18n="lbl_str">Straße</label><input id="k_str"></div>
      <div class="fld"><label data-i18n="lbl_plz">PLZ</label><input id="k_plz"></div>
      <div class="fld"><label data-i18n="lbl_ort">Ort</label><input id="k_ort"></div>
      <div class="fld"><label data-i18n="lbl_land">Land</label><input id="k_land" data-i18n-ph="ph_land" placeholder="z. B. Polen"></div>
      <div class="fld"><label data-i18n="lbl_tel">Telefon</label><input id="k_tel" data-i18n-ph="ph_optional" placeholder="optional"></div>
      <div class="fld"><label data-i18n="lbl_mail">E-Mail</label><input id="k_mail" data-i18n-ph="ph_optional" placeholder="optional"></div>
      <div class="fld"><label data-i18n="lbl_ustid">USt-IdNr.</label><input id="k_ustid" data-i18n-ph="ph_optional" placeholder="optional"></div>
    </div></div>
  </div>
  <div class="section">
    <div class="kick2" data-i18n="s3_kick">03 · Konfiguration</div>
    <h2 data-i18n="h2_config">Maschine &amp; Ausstattung</h2>
    <div class="basis"><div class="bimg" id="basisImg"></div>
      <div class="btx"><span class="tag" data-i18n="base_tag">Basismaschine · enthalten</span><div class="t">Lepton 5100</div><div class="a"><span data-i18n="art_no">Art.-Nr.</span> 5000379</div><div class="d" data-i18n="base_desc">Mobiler Scheibenseparator · Bunker 8 m³ · Siebdeck 1 (3–38°) · 4 E-Motoren</div><div class="p" id="basisPrice">340.300 €</div></div>
    </div>
    <div id="catalog"></div>
  </div>
  <div class="section">
    <div class="kick2" data-i18n="s4_kick">04 · Konditionen</div>
    <h2 data-i18n="h2_terms">Steuer, Liefer- &amp; Zahlungsbedingungen</h2>
    <div class="card"><div class="grid">
      <div class="fld"><label data-i18n="lbl_tax">Steuer</label><select id="t_tax">
        <option value="ausfuhr" data-i18n="tax_ausfuhr">Steuerfreie Ausfuhrlieferung (Drittland, § 4 Abs. 1 Nr. 1 a UStG)</option>
        <option value="ig" data-i18n="tax_ig">Steuerfreie innergemeinschaftliche Lieferung (EU, § 4 Abs. 1 Nr. 1 b UStG)</option>
        <option value="mwst" data-i18n="tax_mwst">19 % USt. (Inland Deutschland)</option>
      </select></div>
      <div class="fld wide" id="gPreisWrap" style="display:none"><label data-i18n="lbl_gpreis">Verkaufspreis Gebrauchtmaschine (netto, €)</label><input id="g_preis" inputmode="decimal" data-i18n-ph="ph_gpreis" placeholder="z. B. 185.000"></div>
      <div class="fld wide"><label data-i18n="lbl_liefer">Lieferbedingung</label><input id="t_liefer"></div>
      <div class="fld"><label data-i18n="lbl_termin">Liefertermin</label><input id="t_termin" data-i18n-ph="ph_termin" placeholder="z. B. KW 40 / 2026"></div>
      <div class="fld wide"><label data-i18n="lbl_zahlung">Zahlungsbedingungen</label><textarea id="t_zahlung"></textarea></div>
      <div class="fld wide"><label data-i18n="lbl_gewahr">Gewährleistung</label><textarea id="t_gewahr"></textarea></div>
      <div class="fld wide"><label data-i18n="lbl_sonder">Sonderabsprachen</label><textarea id="t_sonder" data-i18n-ph="ph_optional" placeholder="optional"></textarea></div>
    </div></div>
  </div>
  <div class="pvbar"><span class="t" id="pvTitle">Angebot — Vorschau</span>
    <div><button class="btn g" id="resetBtn" data-i18n="btn_reset">Zurücksetzen</button> <button class="btn p" id="pdfBtn" data-i18n="btn_pdf">Als PDF speichern</button> <button class="btn s" id="printBtn">Angebot drucken</button></div>
  </div>
</div>
<div id="doc"></div>
<div class="bar noprint">
  <div class="str"><span style="background:var(--red)"></span><span style="background:var(--slate)"></span><span style="background:#fff"></span><span style="background:var(--gold)"></span></div>
  <div class="in">
    <div class="sums">
      <div class="b"><span class="k" data-i18n="bar_options">Optionen</span><span class="vv" id="sumOpt">0</span></div>
      <div class="b"><span class="k" data-i18n="bar_net">Netto gesamt</span><span class="vv big" id="sumNet">340.300 €</span></div>
      <div class="b"><span class="k" id="sumTaxLabel">Gesamt</span><span class="vv cr" id="sumGross">340.300 €</span></div>
    </div>
    <button class="btn p" id="printBtn2" data-i18n="btn_print">Drucken</button>
  </div>
</div>
<script>
const IMG=%%IMG%%; const BANNERS=%%BANNERS%%; const CATS=%%CATS%%;
const I18N=%%I18N%%; const SPEC=%%SPEC%%;
const ASSET={LOGO_L:"%%LOGOL%%",LOGO_D:"%%LOGOD%%"};
const BASE={name:"Basismaschine Lepton 5100",art:"5000379",price:340300};
const LOCALE={de:"de-DE",en:"en-GB",pl:"pl-PL",fr:"fr-FR"};
const LKEY="amb_lepton_lang";
var lang="de";
(function(){
 "use strict";
 var optById={},catById={},confMap={}; CATS.forEach(function(c){c.opts.forEach(function(o){optById[o.id]=o;catById[o.id]=c;});});
 CATS.forEach(function(c){c.opts.forEach(function(o){if(o.conf)o.conf.forEach(function(id){(confMap[o.id]=confMap[o.id]||{})[id]=true;(confMap[id]=confMap[id]||{})[o.id]=true;});});});
 function clearConflicts(id){var m=confMap[id];if(!m)return;for(var cid in m){if(state.chosen[cid])state.chosen[cid]=false;var o=optById[cid];if(o&&o.ex&&state.excl[o.ex]===cid)state.excl[o.ex]="";var cat=catById[cid];if(cat&&cat.ex&&state.excl[cat.ex]===cid)state.excl[cat.ex]="";var card=document.querySelector('.pcard[data-id="'+cid+'"]');if(card){var cb=card.querySelector('input[type=checkbox]');if(cb)cb.checked=false;card.classList.remove("on");}}}
 var state={chosen:{},excl:{sd1:"",sd2:"",fg:"",vd:"",gk:""},mode:"angebot"};
 var IDS=["m_nr","m_datum","m_ort","m_verk","m_vtel","m_vmail","k_firma","k_firma2","k_anrede","k_vor","k_nach","k_str","k_plz","k_ort","k_land","k_tel","k_mail","k_ustid","t_tax","t_rabatt","t_liefer","t_termin","t_zahlung","t_gewahr","t_sonder","g_jahr","g_std","g_sn","g_zustand","g_preis"];
 var DEF_FIELDS=[["t_liefer","def_liefer"],["t_zahlung","def_zahlung"],["t_gewahr","def_gewahr"]];
 function t(k){var L=I18N[lang]||I18N.de;return (L&&L[k]!=null)?L[k]:((I18N.de[k]!=null)?I18N.de[k]:k);}
 function tf(k,o){var s=t(k);for(var p in o){s=s.split("{"+p+"}").join(o[p]);}return s;}
 function optName(o){return o["name_"+lang]||o.name;}
 function optDesc(o){return o["desc_"+lang]||o.desc||"";}
 function catH(c){return c["h_"+lang]||c.h;}
 function parseNum(s){s=String(s||"").trim().replace(/\s/g,"");if(/^\d{1,3}(\.\d{3})+$/.test(s))s=s.replace(/\./g,"");s=s.replace(",",".");var x=parseFloat(s);return isNaN(x)?0:x;}
 function money(x){var dd=Number.isInteger(x)?0:2;return x.toLocaleString(LOCALE[lang]||"de-DE",{minimumFractionDigits:dd,maximumFractionDigits:2})+" €";}
 function esc(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
 function v(id){var e=document.getElementById(id);return e?(e.value||"").trim():"";}
 function imgDiv(o){return (o.img&&IMG[o.img])?'<div class="pimg" style="background-image:url('+IMG[o.img]+')"></div>':'';}
 function specRows(s){return s.map(function(r){return r[1]?'<div class="pr2"><span class="pk">'+esc(r[0])+'</span><span class="pv">'+esc(r[1])+'</span></div>':'<div class="pf">'+esc(r[0])+'</div>';}).join('');}
 function specsHTML(o){var s=o["specs_"+lang]||o.specs;if(!s||!s.length)return '';return '<div class="pspecs">'+specRows(s)+'</div>';}
 function cbanner(c){var bn=BANNERS[c.h],cs=c["cspecs_"+lang]||c.cspecs;if(!bn&&!cs)return '';return '<div class="catbanner">'+(bn?'<img src="'+bn+'" alt="">':'')+(cs&&cs.length?'<div class="pspecs cbinfo">'+specRows(cs)+'</div>':'')+'</div>';}
 function cardInner(o){return '<div class="ck"></div>'+imgDiv(o)+'<div class="pbody"><div class="pname">'+esc(optName(o))+'</div><div class="pdesc">'+esc(optDesc(o))+'</div>'+specsHTML(o)+'<div class="pfoot"><span class="part">'+(o.art?t("art_prefix")+esc(o.art):'')+'</span><span class="pprice">'+(o.price===0?t("incl_short"):money(o.price))+'</span></div></div>';}
 function buildCatalog(){
  var html="";
  CATS.forEach(function(c){
   var hasEx=c.ex||c.opts.some(function(o){return o.ex;});
   html+='<div class="catblk"><div class="ch">'+esc(catH(c))+(hasEx?' <span style="color:#9a9aa0;font-weight:500;text-transform:none;letter-spacing:0">'+t("cat_deselect")+'</span>':'')+'</div>'+cbanner(c)+'<div class="cards">';
   c.opts.forEach(function(o){
    var grp=c.ex||o.ex;
    if(grp){ html+='<div class="pcard radio'+(o.img?'':' noimg')+'" data-group="'+grp+'" data-id="'+o.id+'">'+cardInner(o)+'</div>'; }
    else { html+='<label class="pcard'+(o.img?'':' noimg')+'" data-id="'+o.id+'">'+cardInner(o)+'<input type="checkbox" data-id="'+o.id+'" hidden></label>'; }
   });
   html+='</div></div>';
  });
  document.getElementById("catalog").innerHTML=html;
  document.querySelectorAll('.pcard input[type=checkbox]').forEach(function(cb){cb.addEventListener("change",function(){var id=cb.getAttribute("data-id");state.chosen[id]=cb.checked;cb.closest(".pcard").classList.toggle("on",cb.checked);if(cb.checked)clearConflicts(id);render();});});
  document.querySelectorAll('.pcard.radio').forEach(function(card){card.addEventListener("click",function(){var g=card.getAttribute("data-group"),id=card.getAttribute("data-id");state.excl[g]=(state.excl[g]===id)?"":id;document.querySelectorAll('.pcard.radio[data-group="'+g+'"]').forEach(function(c2){c2.classList.toggle("on",c2.getAttribute("data-id")===state.excl[g]);});if(state.excl[g]===id)clearConflicts(id);render();});});
 }
 function syncCards(){
  document.querySelectorAll('.pcard input[type=checkbox]').forEach(function(cb){var on=!!state.chosen[cb.getAttribute("data-id")];cb.checked=on;cb.closest(".pcard").classList.toggle("on",on);});
  document.querySelectorAll('.pcard.radio').forEach(function(c){var g=c.getAttribute("data-group");c.classList.toggle("on",c.getAttribute("data-id")===state.excl[g]);});
 }
 function selectedList(){
  var out=[];
  CATS.forEach(function(c){var items=[];
   if(c.ex){var id=state.excl[c.ex];if(id&&optById[id]){var o=optById[id];items.push({name:catH(c)+": "+optName(o),art:o.art,price:o.price,img:o.img});}}
   else{c.opts.forEach(function(o){
     if(o.ex){if(state.excl[o.ex]===o.id)items.push({name:optName(o),art:o.art,price:o.price,img:o.img});}
     else if(state.chosen[o.id])items.push({name:optName(o),art:o.art,price:o.price,img:o.img});
   });}
   if(items.length)out.push({grp:catH(c),items:items});});
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
 function taxNote(tx){if(tx==="ausfuhr")return t("taxnote_ausfuhr");if(tx==="ig")return t("taxnote_ig");return t("taxnote_mwst");}
 function pers(){return [v("k_anrede"),v("k_vor"),v("k_nach")].filter(Boolean).join(" ");}
 function kaeuferLines(){
  var a=[];
  if(v("k_firma"))a.push("<b>"+esc(v("k_firma"))+"</b>");
  if(v("k_firma2"))a.push(esc(v("k_firma2")));
  if(pers())a.push((v("k_firma")?t("attn"):"")+esc(pers()));
  if(v("k_str"))a.push(esc(v("k_str")));
  var po=[v("k_plz"),v("k_ort")].filter(Boolean).join(" ");if(po)a.push(esc(po));
  if(v("k_land"))a.push(esc(v("k_land")));
  return a;
 }
 function docHead(label){
  var nr=v("m_nr"),datum=v("m_datum"),ort=v("m_ort"),meta="";
  if(nr)meta+=(label||"Nr.")+' <b>'+esc(nr)+'</b><br>';
  if(datum)meta+=esc(ort?ort+", ":"")+'<b>'+esc(datum)+'</b>';else if(ort)meta+=esc(ort);
  return '<div class="dtop"><div class="dfirm"><img class="dlogo" src="'+ASSET.LOGO_D+'"><div class="fnm">Maschinenbau GmbH</div>Am Gewerbering 14 · D-84069 Schierling<br>www.alzinger-recyclingtechnik.com</div><div class="dmeta">'+(meta||"&nbsp;")+'</div></div>';
 }
 function addrBlock(){
  var a=kaeuferLines();
  if(v("k_ustid"))a.push('<span style="color:#9a9aa0;font-size:11px">'+t("lbl_ustid")+' '+esc(v("k_ustid"))+'</span>');
  return '<div class="addr"><span class="s">'+t("addr_to")+'</span>'+(a.length?a.join("<br>"):'<span style="color:#9a9aa0">'+t("addr_placeholder")+'</span>')+'</div>';
 }
 function salutS(){var anr=v("k_anrede"),nach=v("k_nach");if(anr==="Herr"&&nach)return tf("salut_herr",{n:esc(nach)});if(anr==="Frau"&&nach)return tf("salut_frau",{n:esc(nach)});return t("salut_generic");}
 function salutation(){return '<div class="salut"><p>'+salutS()+'</p><p>'+t("salut_body")+'</p></div>';}
 function machineSpec(label,showPrice){
  var specs=SPEC[lang]||SPEC.de;
  var sp=specs.map(function(x){return '<div>'+esc(x)+'</div>';}).join("");
  return '<div class="machine"><div class="mh"><span class="nm">'+t("machine_base")+' <span class="art2">(5000379)</span>'+(label?' · <span style="color:#ffd2cf">'+esc(label)+'</span>':'')+'</span>'+(showPrice===false?'':'<span class="pr">'+money(BASE.price)+'</span>')+'</div><div class="specs">'+sp+'</div></div>';
 }
 function linesHTML(sel,grpLabel,showPrices){
  var lh='<div class="lines"><div class="grp dark">'+esc(grpLabel)+'</div>';
  sel.forEach(function(g){lh+='<div class="grp">'+esc(g.grp)+'</div>';
   g.items.forEach(function(it){var th=(it.img&&IMG[it.img])?'<img class="th" src="'+IMG[it.img]+'" alt="">':'<i class="th th-x"></i>';
    lh+='<div class="ln"><span class="lt">'+th+'<span class="n">'+esc(it.name)+(it.art?' <span class="a">('+it.art+')</span>':'')+'</span></span>'+(showPrices===false?'':'<span class="p">'+(it.price===0?t("incl_long"):money(it.price))+'</span>')+'</div>';});});
  if(!sel.length)lh+='<div style="font-size:12px;color:#9a9aa0;padding:8px 0">'+t("no_options")+'</div>';
  return lh+'</div>';
 }
 function totalsHTML(r,netLabel){
  var th='<div class="totals"><div class="row"><span>'+t("machine_base")+'</span><span class="v">'+money(BASE.price)+'</span></div><div class="row"><span>'+tf("totals_options",{n:r.count})+'</span><span class="v">'+money(r.net-BASE.price)+'</span></div>';
  if(r.rab>0)th+='<div class="row"><span>'+t("totals_subtotal")+'</span><span class="v">'+money(r.net)+'</span></div><div class="row"><span>'+t("totals_discount")+'</span><span class="v">−'+money(r.rab)+'</span></div>';
  th+='<div class="row net"><span>'+esc(netLabel)+'</span><span class="v">'+money(r.na)+'</span></div>';
  if(r.tax==="mwst")th+='<div class="row"><span>'+t("totals_vat")+'</span><span class="v">'+money(r.ust)+'</span></div><div class="row gross"><span>'+t("totals_gross")+'</span><span class="v">'+money(r.gross)+'</span></div>';
  return th+'<div class="taxnote">'+taxNote(r.tax)+'</div></div>';
 }
 function totalsGebraucht(r){
  if(r.na===0)return '<div class="totals"><div class="row net"><span>'+t("sell_net")+'</span><span class="v" style="color:#9a9aa0">'+t("price_manual")+'</span></div></div>';
  var th='<div class="totals"><div class="row net"><span>'+t("sell_net")+'</span><span class="v">'+money(r.na)+'</span></div>';
  if(r.tax==="mwst")th+='<div class="row"><span>'+t("totals_vat")+'</span><span class="v">'+money(r.ust)+'</span></div><div class="row gross"><span>'+t("totals_gross")+'</span><span class="v">'+money(r.gross)+'</span></div>';
  return th+'<div class="taxnote">'+taxNote(r.tax)+'</div></div>';
 }
 function termsHTML(){
  var liefer=v("t_liefer"),termin=v("t_termin"),lieferTxt=liefer+(termin?"\n"+t("terms_delivery_date")+termin:""),sonder=v("t_sonder"),tb='<div class="terms">';
  if(sonder)tb+='<div style="grid-column:1/-1"><div class="h">'+t("lbl_sonder")+'</div><div class="x">'+esc(sonder)+'</div></div>';
  tb+='<div><div class="h">'+t("lbl_gewahr")+'</div><div class="x">'+esc(v("t_gewahr"))+'</div></div>';
  tb+='<div><div class="h">'+t("terms_delivery")+'</div><div class="x">'+esc(lieferTxt)+'</div></div>';
  tb+='<div style="grid-column:1/-1"><div class="h">'+t("lbl_zahlung")+'</div><div class="x">'+esc(v("t_zahlung"))+'</div></div>';
  return tb+'</div>';
 }
 function legalBlock(tax){return '<div class="legal">'+tf("legal",{tax:taxNote(tax)})+'</div>';}
 function signSingle(){var sh='<div class="sign"><div class="g">'+t("sign_offer")+'<br>'+t("sign_regards")+'</div><div class="nm">'+esc(v("m_verk"))+'</div><div>Alzinger Maschinenbau GmbH</div>';if(v("m_vtel"))sh+='<div style="color:#5e6166">'+t("sign_phone")+esc(v("m_vtel"))+'</div>';if(v("m_vmail"))sh+='<div style="color:#5e6166">'+t("sign_email")+esc(v("m_vmail"))+'</div>';return sh+'</div>';}
 function signTwo(){return '<div class="sig2"><div class="sigbox"><div class="sl"></div>'+t("sign_seller_line")+'<br><b>'+esc(v("m_verk"))+'</b> · Alzinger Maschinenbau GmbH</div><div class="sigbox"><div class="sl"></div>'+t("sign_buyer_line")+(pers()?'<br><b>'+esc(pers())+'</b>':'')+'</div></div>';}
 function gdataBlock(){
  var items=[[t("lbl_g_jahr"),v("g_jahr")],[t("lbl_g_std"),v("g_std")],[t("gdata_sn"),v("g_sn")],[t("lbl_g_zustand"),v("g_zustand")]].filter(function(x){return x[1];});
  if(!items.length)return '';
  return '<div class="sec-h">'+t("gdata_title")+'</div><div class="gdata">'+items.map(function(x){return '<div class="gx"><div class="gk">'+esc(x[0])+'</div><div class="gv">'+esc(x[1])+'</div></div>';}).join("")+'</div>';
 }
 function renderAngebot(r){return docHead(t("docnr_angebot"))+addrBlock()+'<div class="dtitle">'+t("doc_angebot_title")+'<span class="u"></span><span class="sub">'+esc(t("hero_sub"))+'</span></div>'+salutation()+machineSpec("",true)+linesHTML(r.sel,t("opts_selected"),true)+totalsHTML(r,t("net_angebot"))+termsHTML()+legalBlock(r.tax)+signSingle();}
 function renderGebraucht(r){return docHead(t("docnr_angebot"))+addrBlock()+'<div class="dtitle">'+t("doc_gebraucht_title")+'<span class="u"></span></div><div class="salut"><p>'+salutS()+'</p><p>'+t("gebraucht_body")+'</p></div>'+gdataBlock()+machineSpec(t("machine_used_label"),false)+linesHTML(r.sel,t("equipment"),false)+totalsGebraucht(r)+termsHTML()+legalBlock(r.tax)+signSingle();}
 function renderKaufvertrag(r){
  var k=kaeuferLines(); if(v("k_ustid"))k.push('<span style="color:#9a9aa0;font-size:11px">'+t("lbl_ustid")+' '+esc(v("k_ustid"))+'</span>');
  var vp='<div class="sec-h">'+t("kv_partners")+'</div><div class="vp"><div class="party"><div>Alzinger Maschinenbau GmbH<br>Am Gewerbering 14<br>DE 84069 Schierling<br>'+t("kv_repby")+esc(v("m_verk")||"—")+'</div><div class="role">'+t("role_seller")+'</div></div><div class="amp">'+t("kv_and")+'</div><div class="party"><div>'+(k.length?k.join("<br>"):t("buyer_placeholder"))+'<br>'+t("kv_repby")+esc(pers()||"—")+'</div><div class="role">'+t("role_buyer")+'</div></div></div><p class="ptxt">'+t("kv_intro")+'</p>';
  return docHead(t("docnr_vertrag"))+'<div class="dtitle">'+t("doc_vertrag_title")+'<span class="u"></span><span class="sub">'+esc(t("hero_sub"))+'</span></div>'+vp+'<div class="sec-h">'+t("kv_subject")+'</div><p class="ptxt">'+t("kv_subject_text")+'</p>'+machineSpec("",true)+linesHTML(r.sel,t("equipment"),true)+totalsHTML(r,t("net_kaufvertrag"))+termsHTML()+legalBlock(r.tax)+signTwo();
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
 function isActive(id){var o=optById[id];if(!o)return false;var c=catById[id];if(o.ex)return state.excl[o.ex]===id;if(c&&c.ex)return state.excl[c.ex]===id;return !!state.chosen[id];}
 function updateAvailability(){
  var blocked={};
  CATS.forEach(function(c){c.opts.forEach(function(o){
   if(isActive(o.id)&&confMap[o.id]){for(var k in confMap[o.id])blocked[k]=true;}
  });});
  CATS.forEach(function(c){c.opts.forEach(function(o){
   var off=(o.req&&!isActive(o.req))||!!blocked[o.id];
   var card=document.querySelector('.pcard[data-id="'+o.id+'"]');
   if(card)card.classList.toggle("disabled",off);
   if(off){
    if(state.chosen[o.id]){state.chosen[o.id]=false;if(card){var cb=card.querySelector('input[type=checkbox]');if(cb)cb.checked=false;}}
    if(o.ex&&state.excl[o.ex]===o.id)state.excl[o.ex]="";
    var cat=catById[o.id];if(cat&&cat.ex&&state.excl[cat.ex]===o.id)state.excl[cat.ex]="";
    if(card)card.classList.remove("on");
   }
  });});
 }
 function render(){
  updateAvailability();
  var r=compute();var dash=(r.gebraucht&&r.na===0);
  document.getElementById("sumOpt").textContent=r.count;
  document.getElementById("sumNet").textContent=dash?"—":money(r.na);
  document.getElementById("sumTaxLabel").textContent=r.tax==="mwst"?t("bar_brutto"):t("bar_total_net");
  document.getElementById("sumGross").textContent=dash?"—":money(r.gross);
  var bp=document.getElementById("basisPrice");if(bp)bp.textContent=money(BASE.price);
  renderDoc(r);
 }
 function applyMode(m){
  state.mode=m;
  var doc=t("pill_"+m);
  document.getElementById("heroTitle").textContent=t("title_"+m);
  document.getElementById("modePill").textContent=doc;
  document.getElementById("gebrauchtFields").style.display=(m==="gebraucht")?"grid":"none";
  document.body.classList.toggle("mode-gebraucht",m==="gebraucht");
  document.getElementById("gPreisWrap").style.display=(m==="gebraucht")?"":"none";
  document.getElementById("h2meta").textContent=t("h2_"+m);
  document.getElementById("lblNr").textContent=(m==="kaufvertrag")?t("lbl_nr_vertrag"):t("lbl_nr_angebot");
  document.getElementById("pvTitle").textContent=tf("pv_title",{doc:doc});
  document.getElementById("printBtn").textContent=tf("btn_print_doc",{doc:doc});
  document.querySelectorAll("#menu button").forEach(function(b){b.classList.toggle("active",b.getAttribute("data-mode")===m);});
  document.getElementById("menu").classList.remove("open");
  render();
 }
 function isDefaultVal(id,val){var key=null;DEF_FIELDS.forEach(function(p){if(p[0]===id)key=p[1];});if(!key)return false;for(var lg in I18N){if(I18N[lg][key]===val)return true;}return false;}
 function applyDefaults(){
  DEF_FIELDS.forEach(function(p){var e=document.getElementById(p[0]);if(!e)return;var cur=e.value;if(cur===""||isDefaultVal(p[0],cur))e.value=t(p[1]);});
  var d=document.getElementById("m_datum");
  if(d&&(d.value===""||d.value===d.getAttribute("data-auto"))){var nv=new Date().toLocaleDateString(LOCALE[lang]||"de-DE",{day:"2-digit",month:"2-digit",year:"numeric"});d.value=nv;d.setAttribute("data-auto",nv);}
 }
 function applyLang(){
  document.documentElement.lang=lang;
  document.querySelectorAll("[data-i18n]").forEach(function(el){el.textContent=t(el.getAttribute("data-i18n"));});
  document.querySelectorAll("[data-i18n-ph]").forEach(function(el){el.setAttribute("placeholder",t(el.getAttribute("data-i18n-ph")));});
  document.querySelectorAll("#langsel button").forEach(function(b){b.classList.toggle("active",b.getAttribute("data-lang")===lang);});
 }
 function setLang(l){
  if(!I18N[l])return;
  lang=l;
  try{localStorage.setItem(LKEY,l);}catch(e){}
  applyDefaults();
  applyLang();
  buildCatalog();syncCards();
  refreshSaved();
  applyMode(state.mode);
 }
 function resetAll(){
  state.chosen={};state.excl={sd1:"",sd2:"",fg:"",vd:"",gk:""};
  document.querySelectorAll('.pcard input[type=checkbox]').forEach(function(cb){cb.checked=false;});
  document.querySelectorAll('.pcard').forEach(function(c){c.classList.remove("on");});
  ["t_rabatt","g_jahr","g_std","g_sn","g_zustand","g_preis"].forEach(function(id){var e=document.getElementById(id);if(e)e.value="";});
  render();
 }
 var SKEY="amb_lepton_configs";
 function loadAll(){try{return JSON.parse(localStorage.getItem(SKEY)||"{}");}catch(e){return {};}}
 function saveAll(o){try{localStorage.setItem(SKEY,JSON.stringify(o));return true;}catch(e){return false;}}
 function gatherState(){var f={};IDS.forEach(function(id){var e=document.getElementById(id);if(e)f[id]=e.value;});return {mode:state.mode,chosen:state.chosen,excl:state.excl,fields:f,ts:Date.now()};}
 function applyState(s){if(!s)return;var f=s.fields||{};IDS.forEach(function(id){var e=document.getElementById(id);if(e&&f[id]!==undefined)e.value=f[id];});state.chosen=s.chosen||{};state.excl=s.excl||{sd1:"",sd2:"",fg:"",vd:"",gk:""};syncCards();applyMode(s.mode||"angebot");}
 function suggestName(){var who=[v("k_firma"),v("k_nach")].filter(Boolean).join(" ");return t("pill_"+state.mode)+(who?" "+who:"")+(v("m_nr")?" ("+v("m_nr")+")":"");}
 function refreshSaved(){var sel=document.getElementById("savedList");if(!sel)return;var o=loadAll(),names=Object.keys(o).sort();var cur=sel.value;sel.innerHTML='<option value="">'+(names.length?tf("saved_count",{n:names.length}):t("saved_none"))+'</option>'+names.map(function(n){return '<option value="'+esc(n)+'">'+esc(n)+'</option>';}).join("");if(cur)sel.value=cur;}
 function doSave(){var name=window.prompt(t("prompt_save_name"),suggestName());if(name===null)return;name=name.trim();if(!name)return;var o=loadAll();o[name]=gatherState();if(!saveAll(o)){window.alert(t("alert_save_fail"));return;}refreshSaved();document.getElementById("savedList").value=name;}
 function doLoad(){var n=document.getElementById("savedList").value;if(!n)return;var o=loadAll();if(o[n])applyState(o[n]);}
 function doDelete(){var n=document.getElementById("savedList").value;if(!n)return;if(!window.confirm(tf("confirm_delete",{n:n})))return;var o=loadAll();delete o[n];saveAll(o);refreshSaved();}
 function docFilename(){var who=v("k_firma")||pers()||"",nr=v("m_nr")||"";var parts=[t("pill_"+state.mode),who,nr].filter(Boolean);var name=parts.join(" ").replace(/[\/\\:*?"<>|#]/g,"").trim().replace(/\s+/g,"_");return name||t("pill_"+state.mode);}
 var _origTitle=document.title;
 function doPrint(){document.title=docFilename();window.print();}
 window.addEventListener("afterprint",function(){document.title=_origTitle;});
 var _pdfLoading=false;
 function loadPdfLib(cb,err){
  if(window.jspdf&&window.html2canvas){cb();return;}
  var s=document.createElement("script");s.src="pdfvendor.js";
  s.onload=function(){cb();};s.onerror=function(){if(err)err();};
  document.head.appendChild(s);
 }
 function findBreak(ctx,w,from,minY){
  var H=from-minY;if(H<=0)return from;
  var data=ctx.getImageData(0,minY,w,H).data;
  for(var yy=H-1;yy>0;yy--){var off=yy*w*4,white=true;for(var x=0;x<w;x+=24){var i=off+x*4;if(data[i]<248||data[i+1]<248||data[i+2]<248){white=false;break;}}if(white)return minY+yy;}
  return from;
 }
 function doPdf(){
  var btn=document.getElementById("pdfBtn"),old=btn?btn.textContent:"";if(btn){btn.disabled=true;btn.textContent="…";}
  function fin(){if(btn){btn.disabled=false;btn.textContent=old;}}
  function fail(){fin();window.alert("PDF konnte nicht erstellt werden. Bitte einmal online öffnen und erneut versuchen.");}
  loadPdfLib(function(){
   try{
    var src=document.getElementById("doc");
    var holder=document.createElement("div");holder.style.cssText="position:fixed;left:-10000px;top:0;width:880px;background:#fff";
    var clone=src.cloneNode(true);clone.style.cssText="width:880px;max-width:none;margin:0;border:0;box-shadow:none;border-radius:0;overflow:visible";
    holder.appendChild(clone);document.body.appendChild(holder);
    window.html2canvas(clone,{scale:2,backgroundColor:"#ffffff",useCORS:true,logging:false}).then(function(canvas){
     holder.remove();
     var jsPDF=window.jspdf.jsPDF,pdf=new jsPDF({orientation:"p",unit:"mm",format:"a4"});
     var pw=pdf.internal.pageSize.getWidth(),ph=pdf.internal.pageSize.getHeight();
     var mT=10,mB=10,contentMM=ph-mT-mB;
     var cw=canvas.width,chT=canvas.height,pxmm=cw/pw,pagePx=Math.floor(contentMM*pxmm),ctx=canvas.getContext("2d");
     var y=0,first=true;
     while(y<chT){
      var sliceH=Math.min(pagePx,chT-y);
      if(y+sliceH<chT){var bp=findBreak(ctx,cw,y+sliceH,y+Math.floor(sliceH*0.55));if(bp>y+10)sliceH=bp-y;}
      var tmp=document.createElement("canvas");tmp.width=cw;tmp.height=sliceH;tmp.getContext("2d").drawImage(canvas,0,y,cw,sliceH,0,0,cw,sliceH);
      var img=tmp.toDataURL("image/jpeg",0.92);
      if(!first)pdf.addPage();
      pdf.addImage(img,"JPEG",0,mT,pw,sliceH/pxmm);
      first=false;y+=sliceH;
     }
     pdf.save(docFilename()+".pdf");fin();
    }).catch(function(){try{holder.remove();}catch(_){}fail();});
   }catch(e){fail();}
  },fail);
 }
 function init(){
  try{var sl=localStorage.getItem(LKEY);if(sl&&I18N[sl])lang=sl;}catch(e){}
  document.getElementById("tbLogo").src=ASSET.LOGO_L;
  try{var raw=localStorage.getItem("amb_lepton_user");if(raw){var ou;try{ou=JSON.parse(raw);}catch(_){ou={n:raw};}if(ou){var mv=document.getElementById("m_verk");if(mv&&!mv.value&&ou.n)mv.value=ou.n;var vt=document.getElementById("m_vtel");if(vt&&!vt.value&&ou.tel)vt.value=ou.tel;var vm=document.getElementById("m_vmail");if(vm&&!vm.value&&ou.mail)vm.value=ou.mail;}}}catch(e){}
  if(IMG["image3"])document.getElementById("basisImg").style.backgroundImage="url("+IMG["image3"]+")";
  buildCatalog();
  IDS.forEach(function(id){var e=document.getElementById(id);if(e){e.addEventListener("input",render);e.addEventListener("change",render);}});
  document.getElementById("burger").addEventListener("click",function(e){e.stopPropagation();document.getElementById("menu").classList.toggle("open");});
  document.querySelectorAll("#menu button").forEach(function(b){b.addEventListener("click",function(){applyMode(b.getAttribute("data-mode"));});});
  document.querySelectorAll("#langsel button").forEach(function(b){b.addEventListener("click",function(){setLang(b.getAttribute("data-lang"));});});
  document.addEventListener("click",function(e){var m=document.getElementById("menu");if(m.classList.contains("open")&&!m.contains(e.target)&&e.target.id!=="burger")m.classList.remove("open");});
  document.getElementById("resetBtn").addEventListener("click",resetAll);
  var _pb=document.getElementById("pdfBtn");if(_pb)_pb.addEventListener("click",doPdf);
  ["printBtn","printBtn2"].forEach(function(id){var b=document.getElementById(id);if(b)b.addEventListener("click",doPrint);});
  applyDefaults();
  applyLang();
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

# ---- i18n vorbereiten: lang-major Dicts + Katalog-Übersetzungen einmischen ----
LANGS=["de","en","pl","fr"]
ui=I18N_RAW["ui"]; spec=I18N_RAW["spec"]; chs=I18N_RAW["cat_headers"]; cops=I18N_RAW["cat_opts"]
I18N={lg:{k:ui[k][lg] for k in ui} for lg in LANGS}
SPEC={lg:[row[lg] for row in spec] for lg in LANGS}
for c in CATS:
    tr=chs.get(c["h"],{})
    for lg in ["en","pl","fr"]:
        if lg in tr: c["h_"+lg]=tr[lg]
    for o in c["opts"]:
        ot=cops.get(o["id"],{})
        if "name" in ot:
            for lg in ["en","pl","fr"]:
                if lg in ot["name"]: o["name_"+lg]=ot["name"][lg]
        if "desc" in ot:
            for lg in ["en","pl","fr"]:
                if lg in ot["desc"]: o["desc_"+lg]=ot["desc"][lg]

out=TPL
out=out.replace("%%IMG%%",json.dumps(IMG))
out=out.replace("%%BANNERS%%",json.dumps(BANNERS,ensure_ascii=False))
out=out.replace("%%CATS%%",json.dumps(CATS,ensure_ascii=False))
out=out.replace("%%I18N%%",json.dumps(I18N,ensure_ascii=False))
out=out.replace("%%SPEC%%",json.dumps(SPEC,ensure_ascii=False))
out=out.replace("%%HERO%%",HERO)
out=out.replace("%%LOGOL%%",LOGO_L)
out=out.replace("%%LOGOD%%",LOGO_D)
out=out.replace("%%RED%%",RED).replace("%%RED2%%",RED2)
for tok in ["%%IMG%%","%%BANNERS%%","%%CATS%%","%%I18N%%","%%SPEC%%","%%HERO%%","%%LOGOL%%","%%LOGOD%%","%%RED%%","%%RED2%%"]:
    assert tok not in out, "Token uebrig: "+tok
for need in ['id="burger"','id="menu"','id="heroTitle"','id="langsel"','renderKaufvertrag','renderGebraucht','data-mode="gebraucht"','data-lang="pl"','id="tbLogo"','function setLang']:
    assert need in out, "fehlt: "+need
p=os.path.join(HERE,"..","index.html")
open(p,"w",encoding="utf8").write(out)
print("index.html erzeugt – bytes",len(out.encode("utf8")))
