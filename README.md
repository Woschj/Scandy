# Scandy - Inventarverwaltung

Eine webbasierte Anwendung zur Verwaltung von Werkzeugen und Verbrauchsmaterialien.

## Deployment auf Render.com

1. Erstellen Sie einen Account auf [Render.com](https://render.com)
2. Verbinden Sie Ihr GitHub-Repository
3. Klicken Sie auf "New Web Service"
4. Wählen Sie Ihr Repository aus
5. Konfigurieren Sie den Service:
   - Name: scandy (oder Ihr gewünschter Name)
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn "app:create_app()" --bind 0.0.0.0:$PORT`
   
## Wichtige Hinweise

- Die Datenbank wird im Filesystem gespeichert. Render.com verwendet ein ephemeres Filesystem, d.h. Änderungen gehen beim Neustart verloren.
- Für produktive Nutzung sollten Sie einen persistenten Speicher einrichten (z.B. PostgreSQL).
- Backups werden im `backups`-Verzeichnis gespeichert.

## Lokale Entwicklung

1. Python 3.8 oder höher installieren
2. Repository klonen
3. Virtuelle Umgebung erstellen: `python -m venv venv`
4. Abhängigkeiten installieren: `pip install -r requirements.txt`
5. Server starten: `flask run`

## Features

- Werkzeug- und Materialverwaltung
- Barcode-Scanning
- Ausleihverwaltung
- Bestandsüberwachung
- Backup/Restore-Funktion 