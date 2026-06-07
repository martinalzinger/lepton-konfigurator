# Alzinger Lepton 5100 – Angebots-Konfigurator

Installierbare, offline-fähige Web-App zum Erstellen von **Angebot**, **Kaufvertrag**
und **Gebrauchtmaschinen-Angebot** für die mobile Sternsiebanlage Lepton 5100.

## Struktur
```
index.html            ← Konfigurator-App (generiert – nicht direkt bearbeiten)
ersatzteile.html      ← Ersatzteilkatalog mit 3D-Ansicht (generiert, EIGENE Seite/URL)
models/               ← 3D-Modelle (.glb), werden bei Bedarf nachgeladen (generiert)
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
  models_cad/              ← HIER STEP/GLB/SEV ablegen (→ wird zu models/*.glb; lokal, nicht eingecheckt)
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

Die 3D-Modelle sind **nicht** in die HTML eingebettet, sondern liegen als
`models/*.glb` daneben und werden erst beim Klick auf „3D ansehen" **nachgeladen**
(der Service-Worker cacht sie offline). Dadurch bleibt `ersatzteile.html` klein
(~1 MB) – auch bei großen Baugruppen.

Eigene CAD-Daten: Dateien in `build/models_cad/` ablegen (Details siehe
`build/models_cad/README.md`) und neu bauen – STEP wird automatisch nach
`models/*.glb` konvertiert (`pip install cascadio`).

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
