#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STEP -> GLB Konverter (Fenster-Programm) fuer den Alzinger Lepton-Ersatzteilkatalog.

Bedienung: STEP-Datei waehlen -> "Umwandeln" -> die fertige .glb liegt daneben.
Die GLB behaelt die Bauteile + PDM-/Artikelnummern (fuer den 3D-Explorer).

Voraussetzung: Python 3 (Windows: python.org, beim Setup "Add python.exe to PATH" anhaken).
Beim ersten Start installiert sich die Umwandel-Bibliothek (cascadio) automatisch.
"""

import sys, os, struct, threading, subprocess, traceback

# ---- benoetigte Pakete sicherstellen (einmalig, beim ersten Start) ----
def ensure(pkg, importname=None):
    try:
        __import__(importname or pkg); return True, ""
    except ImportError:
        try:
            out = subprocess.run([sys.executable, "-m", "pip", "install", pkg],
                                 capture_output=True, text=True)
            __import__(importname or pkg)
            return True, ""
        except Exception as e:
            return False, str(e)

import tkinter as tk
from tkinter import filedialog, ttk, messagebox

# Detailstufen: relativ zur Bauteilgroesse -> auch grosse Baugruppen bleiben handlich
LEVELS = {
    "Standard (empfohlen)":               dict(tol_linear=0.08, tol_angular=1.0),
    "Fein (mehr Details, groessere Datei)": dict(tol_linear=0.03, tol_angular=0.6),
    "Grob (kleiner, fuer grosse Baugruppen)": dict(tol_linear=0.15, tol_angular=2.0),
}

class App:
    def __init__(self, root):
        self.root = root
        self.path = None
        root.title("Alzinger · STEP → GLB Konverter")
        root.geometry("560x440"); root.configure(bg="#16181a")
        RED = "#c00000"

        tk.Label(root, text="STEP  →  GLB Konverter", fg="white", bg="#16181a",
                 font=("Segoe UI", 16, "bold")).pack(pady=(18, 2))
        tk.Label(root, text="Lepton 5100 · Ersatzteilkatalog", fg="#9a9aa0", bg="#16181a",
                 font=("Consolas", 9)).pack()

        card = tk.Frame(root, bg="#ffffff"); card.pack(fill="both", expand=True, padx=16, pady=14)

        # Datei waehlen
        self.filevar = tk.StringVar(value="Keine Datei gewaehlt")
        tk.Button(card, text="1.  STEP-Datei waehlen …", command=self.choose,
                  bg=RED, fg="white", relief="flat", font=("Segoe UI", 11, "bold"),
                  padx=12, pady=8, cursor="hand2").pack(pady=(16, 6), padx=16, fill="x")
        tk.Label(card, textvariable=self.filevar, bg="#ffffff", fg="#16181a",
                 font=("Consolas", 9), wraplength=480).pack(padx=16)

        # Detailstufe
        row = tk.Frame(card, bg="#ffffff"); row.pack(pady=(14, 4), padx=16, fill="x")
        tk.Label(row, text="2.  Detailgrad:", bg="#ffffff", fg="#16181a",
                 font=("Segoe UI", 10)).pack(side="left")
        self.level = tk.StringVar(value="Standard (empfohlen)")
        ttk.Combobox(row, textvariable=self.level, values=list(LEVELS.keys()),
                     state="readonly", width=34).pack(side="left", padx=8)

        # Umwandeln
        self.btn = tk.Button(card, text="3.  Umwandeln", command=self.start,
                             bg="#16181a", fg="white", relief="flat",
                             font=("Segoe UI", 11, "bold"), padx=12, pady=9, cursor="hand2")
        self.btn.pack(pady=(12, 6), padx=16, fill="x")

        self.prog = ttk.Progressbar(card, mode="indeterminate"); self.prog.pack(padx=16, fill="x")

        self.log = tk.Text(card, height=7, bg="#f7f6f2", fg="#16181a", relief="flat",
                           font=("Consolas", 9), wrap="word")
        self.log.pack(padx=16, pady=12, fill="both", expand=True)
        self.say("Bereit. STEP-Datei waehlen und auf „Umwandeln“ klicken.\n"
                 "Tipp: bei sehr grossen Baugruppen „Grob“ waehlen.")

        # falls per Datei gestartet (Drag auf die .bat): direkt uebernehmen
        if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
            self.set_path(sys.argv[1])

    def say(self, msg, clear=True):
        if clear: self.log.delete("1.0", "end")
        self.log.insert("end", msg); self.log.see("end"); self.root.update_idletasks()

    def choose(self):
        p = filedialog.askopenfilename(title="STEP-Datei waehlen",
                                       filetypes=[("STEP", "*.stp *.step"), ("Alle Dateien", "*.*")])
        if p: self.set_path(p)

    def set_path(self, p):
        self.path = p
        mb = os.path.getsize(p) / 1e6
        self.filevar.set(f"{os.path.basename(p)}  ({mb:.1f} MB)")

    def start(self):
        if not self.path:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine STEP-Datei waehlen."); return
        self.btn.config(state="disabled"); self.prog.start(12)
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        try:
            self.say("Bereite vor … (Umwandel-Bibliothek pruefen/installieren – nur beim 1. Mal)")
            ok, err = ensure("cascadio")
            if not ok:
                self.say("FEHLER beim Installieren von 'cascadio':\n" + err +
                         "\n\nStelle sicher, dass Internet verfuegbar ist, und starte erneut."); return
            import cascadio
            out = os.path.splitext(self.path)[0] + ".glb"
            p = LEVELS[self.level.get()]
            self.say(f"Konvertiere:\n{os.path.basename(self.path)}\n"
                     f"Detailgrad: {self.level.get()}\n\nBitte warten – das rechnet "
                     f"(je nach Groesse einige Minuten) …")
            import time; t = time.time()
            cascadio.step_to_glb(self.path, out, tol_linear=p["tol_linear"],
                                 tol_angular=p["tol_angular"], tol_relative=True,
                                 merge_primitives=True, use_parallel=True)
            data = open(out, "rb").read()
            magic, _v, ln = struct.unpack("<III", data[:12])
            valid = (hex(magic) == "0x46546c67" and ln == len(data))
            mb = len(data) / 1e6
            tris = ""
            ok2, _ = ensure("trimesh")
            if ok2:
                try:
                    import trimesh
                    s = trimesh.load(out)
                    n = sum(len(g.faces) for g in s.geometry.values())
                    tris = f"Dreiecke: {n:,}\n"
                except Exception: pass
            msg = (f"FERTIG ✓   ({time.time()-t:.0f}s)\n\n"
                   f"GLB: {os.path.basename(out)}\nGroesse: {mb:.1f} MB\n{tris}"
                   f"Gueltig: {'JA' if valid else 'NEIN – bitte melden'}\n\n"
                   f"Liegt jetzt neben der STEP-Datei:\n{out}")
            if mb > 28:
                msg += ("\n\n⚠ Ueber 28 MB. Tipp: Detailgrad „Grob“ waehlen, "
                        "oder die .glb vor dem Hochladen zippen.")
            self.say(msg)
        except Exception as e:
            self.say("FEHLER:\n" + str(e) + "\n\n" + traceback.format_exc())
        finally:
            self.prog.stop(); self.btn.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
