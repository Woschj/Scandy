INVENTARVERWALTUNG - BENUTZERHANDBUCH
=====================================

INHALTSVERZEICHNIS
-----------------
1. Installation
2. Ersteinrichtung
3. Bedienung
4. Fehlerbehebung
5. Funktionsweise
6. Backup & Wartung

1. INSTALLATION
--------------
Voraussetzungen:
- Python 3.8 oder höher (https://www.python.org/downloads/)
- Git (optional, für Updates: https://git-scm.com/downloads)
- Webbrowser (Chrome, Firefox, Edge)
- Internetzugang für die Installation

Installationsschritte:

a) Python installieren:
   - Python-Installer von python.org herunterladen
   - "Add Python to PATH" während der Installation aktivieren
   - Installation durchführen

b) Programm installieren:
   1. Ordner für das Programm erstellen (z.B. C:\Inventar)
   2. Kommandozeile öffnen (Windows-Taste + R, dann "cmd" eingeben)
   3. Folgende Befehle nacheinander ausführen:
      cd C:\Inventar
      python -m venv venv
      venv\Scripts\activate
      pip install flask sqlite3 logging

c) Programmdateien kopieren:
   - Alle .py Dateien in den Programmordner kopieren
   - Den "templates" Ordner mit allen HTML-Dateien kopieren
   - Den "static" Ordner mit CSS/JS-Dateien kopieren

2. ERSTEINRICHTUNG
-----------------
a) Datenbank initialisieren:
   1. Kommandozeile im Programmordner öffnen
   2. venv\Scripts\activate
   3. python app.py
   - Die Datenbanken werden automatisch erstellt

b) Admin-Zugang einrichten:
   - Standardpasswort ist "1234"
   - Kann in der app.py geändert werden (ADMIN_PASSWORD)

c) Erststart:
   1. http://localhost:5000 im Browser öffnen
   2. Mit Admin-Passwort anmelden
   3. Grunddaten eingeben:
      - Mitarbeiter anlegen
      - Werkzeuge erfassen
      - Lagerorte definieren

3. BEDIENUNG
-----------
a) Hauptfunktionen:

   WERKZEUGE VERWALTEN:
   - Neues Werkzeug: "+" Button oben rechts
   - Werkzeug bearbeiten: Auf Werkzeugname klicken
   - Werkzeug löschen: Mülleimer-Symbol
   - Werkzeug suchen: Suchfeld oben
   - Filter nutzen: Dropdown-Menüs für Ort/Typ/Status

   AUSLEIHE:
   - Schnellscan: Scanner-Symbol oben
   - Manuelle Ausleihe: "Ausleihe" im Menü
   - Rückgabe: "Rückgabe" Button oder Scan
   
   MITARBEITER:
   - Neuer Mitarbeiter: "+" Button in Mitarbeiterliste
   - Mitarbeiter bearbeiten: Auf Namen klicken
   - Mitarbeiter suchen: Suchfeld in Mitarbeiterliste

b) Scanner-Funktion:
   - Funktioniert mit Webcam/Handyscanner
   - QR-Codes oder Barcodes möglich
   - Bei Problemen manuellen Modus nutzen

4. FEHLERBEHEBUNG
----------------
a) Häufige Probleme:

   PROGRAMM STARTET NICHT:
   - Prüfen ob Python läuft (python --version)
   - Virtuelle Umgebung aktiviert? (venv\Scripts\activate)
   - Alle Abhängigkeiten installiert? (pip list)
   - Fehlermeldungen in app.log prüfen

   SCANNER FUNKTIONIERT NICHT:
   - HTTPS aktivieren oder localhost nutzen
   - Kamerazugriff im Browser erlauben
   - Anderen Browser testen
   - Beleuchtung verbessern

   DATENBANK-FEHLER:
   - Backup einspielen (siehe Punkt 6)
   - Datenbank neu initialisieren
   - Berechtigungen prüfen

b) Logs prüfen:
   - app.log im Programmordner enthält Details
   - Bei Fehlern Zeitstempel notieren
   - Vollständige Fehlermeldung für Support

5. FUNKTIONSWEISE
---------------
Das Programm besteht aus mehreren Komponenten:

a) Datenbanken (im db/ Ordner):
   - workers.db: Mitarbeiterdaten
   - tools.db: Werkzeuge und Geräte
   - lendings.db: Ausleihvorgänge
   - consumables.db: Verbrauchsmaterial
   - system_logs.db: Systemprotokoll

b) Weboberfläche:
   - Läuft im Browser
   - Responsive Design (PC/Tablet/Smartphone)
   - Einfache Bedienung durch Scan-Funktion

c) Automatische Funktionen:
   - Backup täglich um Mitternacht
   - Protokollierung aller Vorgänge
   - Bestandsüberwachung
   - Statusaktualisierungen

6. BACKUP & WARTUNG
-----------------
a) Automatisches Backup:
   - Täglich im backup/ Ordner
   - 7 Tage werden aufbewahrt
   - Format: YYYY-MM-DD_backup.zip

b) Manuelles Backup:
   1. Programm beenden
   2. Ordner db/ kopieren
   3. Sicher aufbewahren

c) Backup einspielen:
   1. Programm beenden
   2. Aktuellen db/ Ordner umbenennen
   3. Backup-Ordner als db/ einsetzen
   4. Programm starten

d) Regelmäßige Wartung:
   - Logs prüfen (app.log)
   - Alte Backups löschen
   - Datenbank optimieren
   - Updates einspielen

SUPPORT & HILFE
--------------
Bei Problemen oder Fragen:
1. Dieses Handbuch konsultieren
2. Logs prüfen (app.log)

Route-Dokumentation
1. admin.py
Verwaltet den Admin-Bereich der Anwendung.
Hauptrouten:
/dashboard: Zeigt Systemübersicht und Statistiken
/update_design: Aktualisiert UI-Farbschema
/manual_lending: Manuelle Ausleihe-Verwaltung
/process_lending: Verarbeitet Ausleihen
/process_return: Verarbeitet Rückgaben
Besonderheiten:
Alle Routen mit @admin_required geschützt
Integriertes Logging für Fehlerdiagnose
Dashboard mit Live-Statistiken
2. api.py
REST-API-Endpunkte für externe Zugriffe.
Hauptrouten:
/api/workers: Liste aller Mitarbeiter
/api/tools/<barcode>: Tool-Details
/api/settings/colors: Farbschema-Verwaltung
/api/lending/process: Ausleihe-Verarbeitung
/api/lending/return: Rückgabe-Verarbeitung
Features:
Request/Response Logging
Fehlerbehandlung mit detaillierten Responses
JSON-basierte Kommunikation
3. auth.py
Authentifizierung und Autorisierung.
Hauptrouten:
/auth/login: Login-Formular und -Verarbeitung
/auth/logout: Beendet Benutzersession
Sicherheitsfeatures:
Session-basierte Authentifizierung
Admin-Rechte-Prüfung via Decorator
Passwort-Validierung
4. consumables.py
Verwaltet Verbrauchsmaterialien.
Hauptrouten:
/: Übersicht aller Materialien
/add: Neues Material hinzufügen
/<barcode>: Material-Details
/<barcode>/edit: Material bearbeiten
/<barcode>/delete: Material löschen
Funktionen:
Bestandsverwaltung
Mindestbestand-Überwachung
Verbrauchshistorie
5. inventory.py
Zentrale Inventarverwaltung.
Hauptfunktionen:
Werkzeug-Statistiken
Mitarbeiter-Statistiken
Verbrauchsmaterial-Statistiken
Aktuelle Ausleihen
Wichtige Routen:
/tools: Werkzeug-Übersicht
/workers: Mitarbeiter-Übersicht
/consumables: Material-Übersicht
/manual-lending: Manuelle Ausleihe
6. tools.py
Werkzeugverwaltung.
Hauptrouten:
/tools: Werkzeug-Liste
/tools/add: Neues Werkzeug
/tools/<barcode>: Werkzeug-Details
/tools/<barcode>/edit: Werkzeug bearbeiten
/tools/search: Werkzeug-Suche
Features:
Barcode-basierte Identifikation
Ausleih-Historie
Soft-Delete Funktion
7. workers.py
Mitarbeiterverwaltung.
Hauptrouten:
/workers: Mitarbeiter-Liste
/workers/add: Neuer Mitarbeiter
/workers/<barcode>: Mitarbeiter-Details
/workers/<barcode>/edit: Mitarbeiter bearbeiten
/workers/search: Mitarbeiter-Suche
Features:
Abteilungszuordnung
Ausleih-Historie pro Mitarbeiter
E-Mail-Verwaltung
8. quick_scan.py
Schnellzugriff für Barcode-Scanning.
Route:
/quick_scan: Scanner-Interface
9. history.py
Systemweite Historie.
Route:
/history: Zeigt alle Ausleihen und Rückgaben
10. index.py
Startseite-Weiterleitung.
Route:
/: Redirect zur Werkzeug-Übersicht
Jede Route-Datei ist Teil eines größeren Blueprints und trägt zur modularen Struktur der Anwendung bei. Die Routen sind durch verschiedene Decorator-Funktionen geschützt und implementieren spezifische Geschäftslogik für ihren Bereich.

Utility-Module:
1. db_schema.py
Verwaltet das Datenbankschema
Generiert und lädt Schema-Definitionen
Erstellt dynamische SQL-Abfragen
Bietet Debug-Funktionen für Schema-Analyse
decorators.py
@login_required: Prüft Login-Status
@admin_required: Prüft Admin-Rechte
@log_route: Protokolliert Route-Aufrufe
@log_db_operation: Protokolliert Datenbankoperationen
url_config.py
Zentrale URL-Konfiguration
Definiert alle Routen-Namen
Verhindert hartcodierte URLs
Ermöglicht einfache URL-Änderungen
color_extractor.py
Extrahiert Farben aus Logos/Bildern
Generiert Farbschemata
Berechnet passende Akzentfarben
Fallback auf Standardfarben
context_processors.py
Injiziert globale Template-Variablen
Lädt Farbeinstellungen
Stellt URLs bereit
Verwaltet Systemeinstellungen
6. logger.py
Konfiguriert verschiedene Logger
Protokolliert Benutzeraktionen
Erfasst Fehler
Dokumentiert Datenbankzugriffe
routes.py
Definiert alle Routen-Konstanten
Gruppiert Routen nach Funktionalität
Bietet Hilfsmethoden für Routing
Zentrale Route-Verwaltung
structure_viewer.py
Analysiert Projektstruktur
Zeigt Datenbankstruktur
Erstellt Statistiken
Hilft bei der Dokumentation
Hauptdateien:
9. main.py
Flask-Anwendungsinitialisierung
Blueprint-Registrierung
Datenbank-Setup
Server-Konfiguration
create_test_data.py
Erstellt Testdaten
Generiert Beispiel-Einträge
Simuliert Verleihdaten
Hilft beim Testen
db_migration.py
Verwaltet Datenbankmigrationen
Aktualisiert Schema
Fügt neue Spalten hinzu
Sichert Datenintegrität
12. files.py
Verwaltet Dateisystem
Zeigt Projektstruktur
Analysiert Codedateien
Hilft bei der Organisation
routes.md
Dokumentiert alle Routen
Beschreibt API-Endpunkte
Erklärt Zugriffsrechte
Definiert URL-Parameter


Admin Templates:
1. add_consumable.html
Route: /admin/add_consumable
Funktion: Formular zum Hinzufügen neuer Verbrauchsmaterialien
add_tool.html
Route: /admin/add_tool
Funktion: Formular zum Hinzufügen neuer Werkzeuge
add_worker.html
Route: /admin/add_worker
Funktion: Formular zum Hinzufügen neuer Mitarbeiter
4. dashboard.html
Route: /admin/dashboard
Funktion: Übersichtsseite für Administratoren mit Statistiken
logs.html & system_logs.html
Route: /admin/logs
Funktion: Anzeige der Systemprotokolle
manual_lending.html
Route: /admin/manual_lending
Funktion: Interface für manuelle Ausleihen/Rückgaben
trash.html
Route: /admin/trash
Funktion: Papierkorb für gelöschte Einträge
Haupttemplates:
base.html
Funktion: Basis-Template mit Layout/Navigation
Wird von allen anderen Templates erweitert
9. consumables.html & consumable_details.html
Routes: /consumables, /consumables/<barcode>
Funktion: Übersicht und Details von Verbrauchsmaterialien
edit_consumable.html
Route: /consumables/<barcode>/edit
Funktion: Bearbeitung von Verbrauchsmaterialien
quick_scan.html
Route: /quick-scan
Funktion: Schnellscan-Interface für Ausleihen/Rückgaben
tools.html & tool_details.html
Routes: /tools, /tools/<barcode>
Funktion: Übersicht und Details von Werkzeugen
workers.html & worker_details.html
Routes: /workers, /workers/<barcode>
Funktion: Übersicht und Details von Mitarbeitern
Die Templates nutzen verschiedene gemeinsame Komponenten wie:
Navigation
Formulare
Tabellen
Modals
Barcode-Scanner Integration
Fehlerbehandlung
Alle Templates sind responsiv gestaltet und nutzen Tailwind CSS mit DaisyUI für das Styling.