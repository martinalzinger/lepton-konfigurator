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

## Ersatzteilkatalog (komplett eigenständiger Ordner `ersatzteile/`)
**Vollständig getrennt** vom Konfigurator: eigener Ordner/URL (`…/ersatzteile/`),
**eigener Service-Worker** (`ersatzteile/sw.js`, Scope `/ersatzteile/`, Cache-
Namespace `ersatzteile-`), **eigenes Manifest/Icons** – teilt **keine Datei** mit
dem Konfigurator. Kein Bezug zu Angebot/Kaufvertrag/Gebraucht. 3D-Ansicht je
Bauteil, **Warenkorb**, Versand als **Druck-/PDF-Anfrage** oder **mailto** an
`martin@alzinger-maschinenbau.de`.

**Wichtig – 3D-Modelle ausgelagert:** Die GLBs werden **nicht** in die HTML
eingebettet, sondern als `ersatzteile/models/*.glb` daneben geschrieben und im
Browser **bei Bedarf nachgeladen** (Klick auf „3D ansehen"; der eigene Service-
Worker cacht sie offline). So bleibt die HTML klein (~0,2 MB), auch bei großen
Baugruppen. `ersatzteile/models/` (inkl. Platzhalter `proc-*.glb`) und
`ersatzteile/vendor/` werden vom Build erzeugt/gepflegt und sind eingecheckt.

Quelle/Build:
- `build/build_ersatzteile.py` – Template (`TPL`) + Generator → schreibt
  `ersatzteile/index.html` und `ersatzteile/models/*.glb`.
  Aufruf: `python3 build/build_ersatzteile.py`.
- `build/spareparts.json` – Ersatzteile (Kategorien, Art.-Nr., Preise, `model`/`img`).
- `build/i18n_ersatzteile.json` – UI-Texte der Seite als `key:{de,en,pl,fr}`.
- `build/glbgen.py` – erzeugt 3D-**Platzhaltermodelle** (GLB), Schlüssel z. B.
  `scheibe|welle|lager|ritzel|trommel|keilriemen|abstreifer|gehaeuse`.
- `ersatzteile/vendor/*.js` – three.js (Core + GLTFLoader + OrbitControls +
  BufferGeometryUtils), offline; `three` per `<script type="importmap">`, die Loader
  werden **dynamisch bei Bedarf** importiert. Treibt den **interaktiven 3D-Explorer**
  (Bauteile picken, ein-/ausblenden, einzeln bestellen).
- `build/assets_spareparts.b64.json` – optionale eingebettete Vorschaubilder.

**3D-Explorer:** Beim Klick auf „3D ansehen" lädt der Viewer das GLB nach und
listet alle **Einzelteile** der Baugruppe (gruppiert nach Artikelnummer, Instanz-
Suffixe wie `_24`/`_oa_3`/`_v8.00` werden in `normPart()` entfernt). Teile lassen
sich anklicken (im Modell oder in der Liste), per Auge-Symbol ein-/ausblenden und
einzeln in den Warenkorb legen (Registry `amb_lepton_subparts`).

Eigene CAD-Daten → `build/models_cad/` ablegen (lokal; per `.gitignore` nicht
eingecheckt), dann neu bauen. Ergebnis landet als `ersatzteile/models/<safe>.glb`:
- `.step`/`.stp` → nach GLB konvertiert (via `cascadio`/OpenCASCADE; `pip install cascadio`,
  Tessellierung `tol_linear=0.5`). Art.-Nr./Bezeichnung aus `PRODUCT(...)` bzw. Dateiname.
- `.glb`/`.gltf` → nach `ersatzteile/models/` kopiert.
- `.sev` (Solid Edge) → nur eingebettetes **Vorschaubild** (kein 3D möglich;
  für echtes 3D in Solid Edge als STEP/glTF exportieren).
Im `spareparts.json` per `"model":"<safe>.glb"` referenzieren (Dateiname in
`ersatzteile/models/`); nicht referenzierte Modelle landen automatisch unter
„Aus CAD importiert".

`spareparts.json` ändern → **immer** `python3 build/build_ersatzteile.py` neu bauen.

## Vertriebs-CRM (eigenständiger Ordner `vertrieb/`)
**Vollständig getrennt** vom Konfigurator und vom Ersatzteilkatalog: eigener
Ordner/URL (`…/vertrieb/`), **eigener Service-Worker** (`vertrieb/sw.js`, Scope
`/vertrieb/`, Cache-Namespace `vertrieb-`), **eigenes Manifest/Icons**. Funktioniert
**online wie offline** (PWA, installierbar) – dasselbe Modell wie der Konfigurator.

Zweck: Vertrieb verwaltet **Adressen/Kontakte & Leads** (DE/CH/AT/…), erfasst pro
Kontakt einen **Verlauf** (Anruf, E-Mail raus/rein, Angebot gesendet, Besuch, Notiz –
jeweils mit **wer/wann**) und setzt **Wiedervorlagen/Rückruf-Erinnerungen**. Fällige
Rückrufe erscheinen im Dashboard und als **Browser-Benachrichtigung** (Notifications API).

**Zwei Betriebsarten – automatisch erkannt:**
- **Lokal** (Standard, z. B. GitHub Pages): Daten pro Gerät im `localStorage`
  (`amb_lepton_crm`). Übertragung per **Export/Import (JSON)**, Leads per **CSV-Import**.
- **Server / geteilt**: Liegt der Ordner auf einem Server **mit PHP**, nutzt die App
  automatisch das mitgelieferte Backend `vertrieb/api.php` → **eine zentrale,
  geteilte Datendatei** `vertrieb/data/crm.json` für das ganze Team. Die App pingt
  beim Start `api.php`; ist es da → Server-Modus (Anzeige „● Server – geteilt"),
  sonst lokal. Status/Umschaltung im Reiter **Daten**.

`api.php` ist ein **einzelnes, dateibasiertes** Backend (keine DB): `GET ?action=all`
liefert `{rev,contacts}`, `POST ?action=batch` wendet **Ops** (`upsert`/`delete`/`bulk`)
unter `flock`-Sperre an. Schreibvorgänge laufen **pro Kontakt** (nicht ganze DB) →
gleichzeitiges Arbeiten ist sicher. Offline gemachte Änderungen landen in einer
**Warteschlange** (`amb_lepton_crm_queue`) und werden bei nächster Verbindung
nachgereicht → funktioniert **online wie offline**. Optionaler Zugriffsschutz per
`$TOKEN` in `api.php` (gleicher Wert in der App unter Daten → Zugriffsschutz).
Die Datendatei `vertrieb/data/crm.json` ist **nicht eingecheckt** (`.gitignore`);
`vertrieb/data/.htaccess` sperrt den direkten Web-Zugriff (Apache).

(Automatische Internet-Lead-Suche und automatisches E-Mail-Beantworten brauchen
zusätzliche Server-Dienste und sind bewusst **nicht** enthalten.)

**Verknüpfung zum Konfigurator** (gleicher Origin → gemeinsamer `localStorage`):
- Anmeldung wird geteilt (`amb_lepton_auth`/`amb_lepton_user`, gleiche `USERS`-Liste
  wie in `build.py`) → das CRM kennt den eingeloggten Vertriebler („wer hat Kontakt").
- Beim Erfassen einer **„Angebot gesendet"**-Aktivität kann ein im Konfigurator
  gespeichertes Angebot (`amb_lepton_configs`) verknüpft werden (read-only).

Quelle/Build:
- `build/build_vertrieb.py` – komplettes Template (`TPL`) + Manifest + SW + PHP-API.
  Schreibt `vertrieb/index.html`, `vertrieb/manifest.webmanifest`, `vertrieb/sw.js`,
  `vertrieb/api.php`, `vertrieb/data/.htaccess` und kopiert die Icons.
  Aufruf: `python3 build/build_vertrieb.py`. Keine externen Pakete.
  Der SW cacht `api.php` **nie** (dynamisch, immer ans Netz).
- Marke/Optik wie der Rest (Rot `#c00000`, Manrope + IBM Plex Mono); nutzt `LOGO_*`,
  `RED*` aus `build/assets.b64.json`.
- UI ist **deutsch** (interne App; keine i18n-Datei).

## Deploy
GitHub Pages aus dem Branch `main` (Ordner `/root`). Konfigurator = `index.html`
im Wurzelverzeichnis; Ersatzteilkatalog = Ordner `ersatzteile/` (eigene URL
`…/ersatzteile/`); Vertriebs-CRM = Ordner `vertrieb/` (eigene URL `…/vertrieb/`).
Kein Build-Schritt auf dem Server nötig.

**Geteiltes CRM auf eigenem Server:** Den Ordner `vertrieb/` auf einen Webserver
**mit PHP** legen (IIS+PHP, Apache, nginx+php-fpm, NAS) und `…/vertrieb/` aufrufen;
`vertrieb/data/` muss für den Webserver beschreibbar sein. Dann teilen sich alle
Vertriebler automatisch denselben Datenstand. Auf GitHub Pages (kein PHP) läuft die
App weiter im lokalen Modus.
