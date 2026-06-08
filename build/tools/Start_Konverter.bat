@echo off
title Alzinger  -  STEP nach GLB Konverter
rem Startet das Konverter-Fenster. Python muss installiert sein.
where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo   Python ist nicht installiert.
  echo   Bitte hier herunterladen:  https://www.python.org/downloads/
  echo   Beim Setup unbedingt "Add python.exe to PATH" anhaken.
  echo   Danach diese Datei erneut doppelklicken.
  echo.
  pause
  exit /b
)
start "" python "%~dp0step2glb_gui.pyw" %*
