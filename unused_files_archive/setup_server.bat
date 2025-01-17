@echo off
echo Starte Server-Setup...

REM Prüfe ob Python installiert ist
python --version > nul 2>&1
if errorlevel 1 (
    echo Python ist nicht installiert oder nicht im PATH!
    echo Bitte installieren Sie Python von https://www.python.org/downloads/
    echo und stellen Sie sicher, dass "Add Python to PATH" aktiviert ist.
    pause
    exit /b 1
)

REM Führe das Setup-Skript aus
python setup_server.py

if errorlevel 1 (
    echo Setup fehlgeschlagen!
    pause
    exit /b 1
)

echo.
echo Setup erfolgreich abgeschlossen!
pause 