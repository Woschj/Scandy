#!/bin/bash

echo "Starte Server-Setup..."

# Prüfe ob Python installiert ist
if ! command -v python3 &> /dev/null; then
    echo "Python ist nicht installiert!"
    echo "Bitte installieren Sie Python 3.x"
    exit 1
fi

# Führe das Setup-Skript aus
python3 setup_server.py

if [ $? -ne 0 ]; then
    echo "Setup fehlgeschlagen!"
    exit 1
fi

echo
echo "Setup erfolgreich abgeschlossen!" 