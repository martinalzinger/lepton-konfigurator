# CLAUDE.md

Leitfaden für die Arbeit an diesem Repository mit Claude Code.

## Was ist das?
Eine **einseitige, offline-fähige PWA** (eine HTML-Datei) für Alzinger Maschinenbau.
Vertrieb konfiguriert die Sternsiebanlage **Lepton 5100** und erzeugt daraus ein
druckfertiges Dokument. Drei Modi, umschaltbar über das Hamburger-Menü oben rechts:
- **Angebot** – unverbindliches Angebot (volle Preiskalkulation)
- **Kaufvertrag** – verbindlicher Vertrag (Vertragspartner, zwei Unterschriften)
- **Gebrauchtmaschine** – Angebot ohne Einzelpreise, mit **manuellem Verkaufspreis**

## Sprache & Marke
- UI und Dokumente sind **deutsch**. Antworten/Commits bevorzugt deutsch.
- Markenrot **#c00000**. Schriften: Manrope (Text) + IBM Plex Mono (Zahlen/Labels).

## Architektur – WICHTIG
`index.html` ist **generiert** und darf **nicht direkt bearbeitet** werden
(Änderungen gehen beim nächsten Build verloren). Quelle ist:

- `build/build.py` – enthält das komplette HTML/CSS/JS-Template (Variable `TPL`)
  und ersetzt Platzhalter `%%…%%` mit Daten/Bildern.
- `build/catalog.json` – die **Maschinen-Optionen** (Kategorien, Preise, Art.-Nr.).
- `build/assets.b64.json` – Bilder, Banner und Logos als base64 (selten geändert).

Build (keine externen Pakete nötig, nur Python 3):
```
python3 build/build.py        # schreibt ./index.html
```
Nach jeder Änderung an Template oder Daten neu bauen.

Lokal testen: `python3 -m http.server`, dann http://localhost:8000
(Service-Worker/Storage brauchen http(s), nicht file://).

## Daten pflegen (häufigster Fall)
Preise/Optionen ändern oder ergänzen → `build/catalog.json` bearbeiten, dann bauen.
Eine Option sieht so aus:
```json
{ "id":"5001173", "art":"5001173", "name":"Genset Perkins",
  "desc":"…", "price":19800, "img":"image4" }
```
- `id` muss eindeutig sein. `img` verweist auf einen Schlüssel in `assets.b64.json`
  (oder `null` für eine Karte ohne Bild).
- Kategorien mit Feld `"ex":"sd1"` sind **Exklusiv-Gruppen** (Siebteilung):
  nur eine Auswahl, erneutes Tippen wählt ab.
- Der Preis der Basismaschine (340.300 €, Art. 5000379) steht direkt in
  `build/build.py` (Konstante `BASE` sowie der Basis-Block im HTML).

## Sprachen (DE/EN/PL/FR)
Umschalter oben rechts in der roten Leiste. Alle Texte liegen in `build/i18n.json`:
- `ui` – Oberflächen-/Dokument-/Rechtstexte als `key: {de,en,pl,fr}`.
  Platzhalter `{n}`, `{doc}`, `{tax}` werden im JS (`tf()`) ersetzt.
- `spec` – die 10 Zeilen der Maschinen-Grundspezifikation (4 Sprachen).
- `cat_headers` / `cat_opts` – Katalog-Übersetzungen (Kategorien per Überschrift,
  Optionen per `id`); build.py mischt sie als `h_en/_pl/_fr` bzw.
  `name_en…`/`desc_en…` in `CATS`. Fehlt eine Übersetzung → Fallback Deutsch.
- Im HTML markieren `data-i18n="key"` (Textinhalt) und `data-i18n-ph="key"`
  (Placeholder) übersetzbare Stellen; `applyLang()` füllt sie.
**Neue Katalog-Option** braucht daher auch einen Eintrag unter `cat_opts` in
`i18n.json` (sonst erscheint sie in allen Sprachen deutsch).

## Wichtige Stellen im Code (build.py → TPL → JavaScript)
- `compute()` – Summen; im Gebraucht-Modus = manueller Preis (`g_preis`).
- `renderAngebot() / renderKaufvertrag() / renderGebraucht()` – die drei Dokumente.
  `renderDoc()` schaltet anhand `state.mode` um.
- `machineSpec(label, showPrice)` / `linesHTML(sel, label, showPrices)` –
  Positionsliste; im Gebraucht-Modus mit `showPrice=false`.
- `applyMode(m)` – Moduswechsel: Titel, Felder, `body.mode-gebraucht`-Klasse
  (blendet Preise per CSS aus), Druck-Label.
- `gatherState/applyState` + `doSave/doLoad/doDelete` – **Speichern/Laden**
  der Dokumente via `localStorage` (Schlüssel `amb_lepton_configs`).
- Druck: `window.print()`, gedruckt wird nur `#doc` (Print-CSS am Ende von `TPL`).

## Konventionen
- Alles bleibt **in einer Datei** (index.html), keine Build-Toolchain, kein Framework.
- Kein externer Netzzugriff zur Laufzeit außer Google-Fonts-Link.
- Keine Browser-Storage-Annahmen außerhalb `try/catch` (App muss auch ohne laufen).

## Typische Aufgaben
- *Preis/Option ändern*: `build/catalog.json` → `python3 build/build.py`.
- *Neues Feld im Dokument*: Eingabefeld im HTML-Teil von `TPL` ergänzen, `id`
  in die Liste `IDS` aufnehmen (für Speichern + Auto-Render), im passenden
  `render…()` ausgeben, bauen.
- *PDF-Export statt Druckdialog*: in `TPL` eine Print-/PDF-Funktion ergänzen
  (z. B. Browser-Druck nach PDF) – Layout `#doc` ist bereits druckoptimiert.
- *App-Icon neu*: aus dem Logo erzeugen und `icon-192/512.png` ersetzen.

## Ersatzteilkatalog (eigene Seite `ersatzteile.html`)
**Unabhängig** vom Konfigurator: eigene Datei/URL (`…/ersatzteile.html`), kein
Bezug zu Angebot/Kaufvertrag/Gebraucht. 3D-Ansicht je Bauteil, **Warenkorb**,
Versand als **Druck-/PDF-Anfrage** oder **mailto** an `martin@alzinger-maschinenbau.de`.

Quelle/Build:
- `build/build_ersatzteile.py` – Template (`TPL`) + Generator → schreibt `ersatzteile.html`.
  Aufruf: `python3 build/build_ersatzteile.py`.
- `build/spareparts.json` – Ersatzteile (Kategorien, Art.-Nr., Preise, `model`/`img`).
- `build/i18n_ersatzteile.json` – UI-Texte der Seite als `key:{de,en,pl,fr}`.
- `build/glbgen.py` – erzeugt 3D-**Platzhaltermodelle** (GLB), Schlüssel z. B.
  `scheibe|welle|lager|ritzel|trommel|keilriemen|abstreifer|gehaeuse`.
- `build/modelviewer.min.js` – Google `<model-viewer>` (offline eingebettet via `%%MV%%`).
- `build/assets_spareparts.b64.json` – zusätzliche Bilder (z. B. Bunker-Vorschau).

Eigene CAD-Daten → `build/models_cad/` ablegen, dann neu bauen:
- `.step`/`.stp` → 3D-Modell (via `cascadio`/OpenCASCADE; `pip install cascadio`).
  Art.-Nr./Bezeichnung werden aus `PRODUCT(...)` bzw. Dateiname übernommen.
- `.glb`/`.gltf` → direkt eingebettet.
- `.sev` (Solid Edge) → nur eingebettetes **Vorschaubild** (kein 3D möglich;
  für echtes 3D in Solid Edge als STEP/glTF exportieren).
Im `spareparts.json` per `"model":"datei.step"` bzw. `"img":"name"` referenzieren;
nicht referenzierte Dateien landen automatisch unter „Aus CAD importiert".

`spareparts.json` ändern → **immer** `python3 build/build_ersatzteile.py` neu bauen.

## Deploy
GitHub Pages aus dem Branch `main` (Ordner `/root`). `index.html` und
`ersatzteile.html` liegen im Wurzelverzeichnis, daher ist kein Build-Schritt auf
dem Server nötig.
