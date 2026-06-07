# CAD-/3D-Dateien hier ablegen

Lege hier deine Dateien der Lepton 5100 ab. Beim Build
(`python3 build/build_ersatzteile.py`) werden sie automatisch verarbeitet
und als `models/<name>.glb` ausgelagert (die Seite lädt sie bei Bedarf nach).

> Dateien in diesem Ordner sind **lokal** (per `.gitignore` nicht eingecheckt) –
> eingecheckt wird nur das Ergebnis in `models/`.

## Unterstützte Formate
| Endung            | Ergebnis                  | Hinweis |
|-------------------|---------------------------|---------|
| `.step` / `.stp`  | **3D-Modell** (GLB)       | wird via OpenCASCADE konvertiert |
| `.glb` / `.gltf`  | **3D-Modell**             | direkt eingebettet |
| `.sev`            | **2D-Vorschaubild**       | Solid Edge – nur das eingebettete Vorschaubild (kein 3D möglich) |

> **Solid Edge:** `.sev` enthält keine offen lesbare Geometrie. Für echtes 3D
> in Solid Edge per **Speichern unter → STEP (*.stp)** oder **glTF/GLB** exportieren.

## Artikelnummer & Bezeichnung – automatisch
Werden übernommen aus:
1. der `PRODUCT(...)`-Angabe **in** der STEP-Datei (Art.-Nr. = 1. Feld,
   Bezeichnung = 2. Feld), sonst
2. dem **Dateinamen** `ARTNR Bezeichnung.ext`
   (Trenner Leerzeichen, `_` oder `-`), z. B. `5100-100 Sternscheibe.step`.

## Feinjustierung
Preise, Beschreibung und Kategorie in `build/spareparts.json` pflegen und mit
`"model": "5100-100.step"` (3D) bzw. `"img": "Bunker"` (Vorschau) referenzieren.
Nicht referenzierte Dateien erscheinen automatisch unter „Aus CAD importiert".
