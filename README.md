# Alzinger Lepton 5100 – Angebots-Konfigurator

Installierbare, offline-fähige Web-App zum Erstellen von **Angebot**, **Kaufvertrag**
und **Gebrauchtmaschinen-Angebot** für die mobile Sternsiebanlage Lepton 5100.

## Struktur
```
index.html            ← Konfigurator-App (generiert – nicht direkt bearbeiten)
ersatzteile.html      ← Ersatzteilkatalog mit 3D-Ansicht (generiert, EIGENE Seite/URL)
manifest.webmanifest  ← App-Definition (Name, Icon, Farben)
sw.js                 ← Service-Worker (Offline, beide Seiten)
icon-192/512.png      ← App-Symbol
build/
  build.py                 ← Generator: erzeugt index.html (Konfigurator)
  catalog.json             ← Maschinen-Optionen + Preise  (HIER pflegen)
  assets.b64.json          ← Bilder/Logos (base64, selten geändert)
  build_ersatzteile.py     ← Generator: erzeugt ersatzteile.html
  spareparts.json          ← Ersatzteile + Preise  (HIER pflegen)
  i18n_ersatzteile.json    ← Übersetzungen der Ersatzteil-Seite (DE/EN/PL/FR)
  glbgen.py                ← erzeugt 3D-Platzhaltermodelle (GLB)
  modelviewer.min.js       ← 3D-Viewer-Library (offline eingebettet)
  models_cad/              ← HIER STEP/GLB/SEV-Dateien ablegen (→ 3D im Katalog)
CLAUDE.md             ← Projektleitfaden für Claude Code
```

## Bauen
```
python3 build/build.py               # schreibt index.html (Konfigurator)
python3 build/build_ersatzteile.py   # schreibt ersatzteile.html (Ersatzteilkatalog)
```
Für die **STEP→3D-Konvertierung** zusätzlich einmalig: `pip install cascadio`.
(Ohne STEP-Dateien baut die Seite auch ohne dieses Paket – mit Platzhaltermodellen.)

## Ersatzteilkatalog – eigene Seite
`ersatzteile.html` ist **unabhängig** vom Konfigurator (eigene URL,
`…/ersatzteile.html`) und taucht **nicht** in Angebot/Kaufvertrag auf.
Bauteile lassen sich in 3D drehen, in den **Warenkorb** legen und als
Anfrage **drucken** oder **per E-Mail** an Alzinger senden.
Eigene CAD-Daten: Dateien in `build/models_cad/` ablegen (Details siehe
`build/models_cad/README.md`) und neu bauen.

## Lokal testen
```
python3 -m http.server      # dann http://localhost:8000 öffnen
```
Service-Worker & Speichern/Laden brauchen `http(s)://` (nicht per Doppelklick `file://`).

## Veröffentlichen (GitHub Pages)
Settings → Pages → Branch `main`, Ordner `/root` → Save.
Konfigurator: `https://DEIN-NAME.github.io/lepton-konfigurator/`
Ersatzteilkatalog: `https://DEIN-NAME.github.io/lepton-konfigurator/ersatzteile.html`

## Auf dem Handy installieren
iPhone (Safari): Teilen → „Zum Home-Bildschirm". Android (Chrome): Menü → „App installieren".
