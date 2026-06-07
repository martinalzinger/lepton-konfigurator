# Alzinger Lepton 5100 – Angebots-Konfigurator

Installierbare, offline-fähige Web-App zum Erstellen von **Angebot**, **Kaufvertrag**
und **Gebrauchtmaschinen-Angebot** für die mobile Sternsiebanlage Lepton 5100.

## Struktur
```
index.html            ← Konfigurator-App (generiert – nicht direkt bearbeiten)
manifest.webmanifest  ← App-Definition Konfigurator
sw.js                 ← Service-Worker Konfigurator (NUR index.html)
icon-192/512.png      ← App-Symbol Konfigurator
ersatzteile/          ← KOMPLETT EIGENSTÄNDIGE Ersatzteil-App (eigene URL /ersatzteile/)
  index.html          ←   3D-Explorer-Katalog (generiert)
  sw.js               ←   eigener Service-Worker (Scope /ersatzteile/)
  manifest.webmanifest←   eigene App-Definition ("Ersatzteile")
  icon-192/512.png    ←   eigene App-Symbole
  models/             ←   3D-Modelle (.glb), bei Bedarf nachgeladen (generiert)
  vendor/             ←   three.js (3D-Viewer, offline)
build/
  build.py                 ← Generator: erzeugt index.html (Konfigurator)
  catalog.json             ← Maschinen-Optionen + Preise  (HIER pflegen)
  assets.b64.json          ← Bilder/Logos (base64, selten geändert)
  build_ersatzteile.py     ← Generator: erzeugt ersatzteile/index.html + ersatzteile/models/
  spareparts.json          ← Ersatzteile + Preise  (HIER pflegen)
  i18n_ersatzteile.json    ← Übersetzungen der Ersatzteil-Seite (DE/EN/PL/FR)
  glbgen.py                ← erzeugt 3D-Platzhaltermodelle (GLB)
  models_cad/              ← HIER STEP/GLB/SEV ablegen (→ ersatzteile/models/*.glb; lokal, nicht eingecheckt)
CLAUDE.md             ← Projektleitfaden für Claude Code
```

## Bauen
```
python3 build/build.py               # schreibt index.html (Konfigurator)
python3 build/build_ersatzteile.py   # schreibt ersatzteile/index.html (Ersatzteilkatalog)
```
Für die **STEP→3D-Konvertierung** zusätzlich einmalig: `pip install cascadio`.
(Ohne STEP-Dateien baut die Seite auch ohne dieses Paket – mit Platzhaltermodellen.)

## Ersatzteilkatalog – eigene Seite
Der Ersatzteilkatalog ist **komplett eigenständig** im Ordner `ersatzteile/`
(eigene URL `…/ersatzteile/`, eigener Service-Worker, eigenes Manifest/Icons) und
teilt **keine Datei** mit dem Konfigurator; er taucht **nicht** in Angebot/Kaufvertrag auf.
Bauteile lassen sich in 3D drehen, in den **Warenkorb** legen und als
Anfrage **drucken** oder **per E-Mail** an Alzinger senden.

**3D-Explorer:** Bei Baugruppen kann man in das 3D-Modell hineingehen,
**einzelne Bauteile anklicken, ein-/ausblenden** und jedes Teil mit seiner
Artikelnummer **einzeln in den Warenkorb** legen.

Die 3D-Modelle sind **nicht** in die HTML eingebettet, sondern liegen als
`ersatzteile/models/*.glb` daneben und werden erst beim Klick auf „3D ansehen"
**nachgeladen** (der eigene Service-Worker cacht sie offline). Dadurch bleibt
`ersatzteile/index.html` klein (~0,2 MB) – auch bei großen Baugruppen.

Eigene CAD-Daten: Dateien in `build/models_cad/` ablegen (Details siehe
`build/models_cad/README.md`) und neu bauen – STEP wird automatisch nach
`ersatzteile/models/*.glb` konvertiert (`pip install cascadio`).

## Lokal testen
```
python3 -m http.server      # dann http://localhost:8000 öffnen
```
Service-Worker & Speichern/Laden brauchen `http(s)://` (nicht per Doppelklick `file://`).

## Veröffentlichen (GitHub Pages)
Settings → Pages → Branch `main`, Ordner `/root` → Save.
Konfigurator: `https://DEIN-NAME.github.io/lepton-konfigurator/`
Ersatzteilkatalog: `https://DEIN-NAME.github.io/lepton-konfigurator/ersatzteile/`

## Auf dem Handy installieren
iPhone (Safari): Teilen → „Zum Home-Bildschirm". Android (Chrome): Menü → „App installieren".
