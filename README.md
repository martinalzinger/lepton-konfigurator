# Alzinger Lepton 5100 – Angebots-Konfigurator

Installierbare, offline-fähige Web-App zum Erstellen von **Angebot**, **Kaufvertrag**
und **Gebrauchtmaschinen-Angebot** für die mobile Sternsiebanlage Lepton 5100.

## Struktur
```
index.html            ← die App (generiert – nicht direkt bearbeiten)
manifest.webmanifest  ← App-Definition (Name, Icon, Farben)
sw.js                 ← Service-Worker (Offline)
icon-192/512.png      ← App-Symbol
build/
  build.py            ← Generator: erzeugt index.html
  catalog.json        ← Maschinen-Optionen + Preise  (HIER pflegen)
  assets.b64.json     ← Bilder/Logos (base64, selten geändert)
CLAUDE.md             ← Projektleitfaden für Claude Code
```

## Bauen
```
python3 build/build.py      # schreibt index.html (nur Python 3 nötig, keine Pakete)
```

## Lokal testen
```
python3 -m http.server      # dann http://localhost:8000 öffnen
```
Service-Worker & Speichern/Laden brauchen `http(s)://` (nicht per Doppelklick `file://`).

## Veröffentlichen (GitHub Pages)
Settings → Pages → Branch `main`, Ordner `/root` → Save.
App läuft unter `https://DEIN-NAME.github.io/lepton-konfigurator/`.

## Auf dem Handy installieren
iPhone (Safari): Teilen → „Zum Home-Bildschirm". Android (Chrome): Menü → „App installieren".
