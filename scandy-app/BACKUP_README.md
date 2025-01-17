# Scandy Backup-System

## Übersicht
Das Backup-System von Scandy erstellt automatisch tägliche Sicherungen der Datenbanken (inventory.db und users.db).

## Automatische Backups
- **Zeitplan**: Täglich um 06:00 Uhr
- **Speicherort**: `/scandy-app/backups/`
- **Namensformat**: 
  - `inventory_YYYYMMDD_HHMMSS.db` (Hauptdatenbank)
  - `users_YYYYMMDD_HHMMSS.db` (Benutzerdatenbank)
- **Aufbewahrung**: 30 Tage (ältere Backups werden automatisch gelöscht)

## Backup-Typen
1. **Automatische Backups** (via Cron)
   - Erstellt täglich um 06:00 Uhr
   - Vollständige Kopie beider Datenbanken
   - Protokollierung in `/app/logs/backup.log`

2. **Manuelle Backups** (via Web-Interface)
   - Können über die Admin-Oberfläche erstellt werden
   - Gleicher Speicherort wie automatische Backups
   - Mit Beschreibung und Metadaten
   - Sichert beide Datenbanken gleichzeitig

## Monitoring
- Backup-Status wird in `/app/logs/backup.log` protokolliert
- Fehler werden im Log mit Zeitstempel und Details dokumentiert
- Status beider Datenbanken wird separat protokolliert

## Wiederherstellung
Backups können auf zwei Wegen wiederhergestellt werden:
1. Über die Admin-Oberfläche in der Web-App
2. Manuell durch Kopieren der Backup-Dateien

Bei der Wiederherstellung werden immer beide Datenbanken als Set behandelt, um Konsistenz zu gewährleisten.

## Verzeichnisstruktur
```
scandy-app/
├── backups/                    # Backup-Dateien
│   ├── inventory_*.db         # Inventory-Datenbank-Backups
│   ├── users_*.db            # Benutzer-Datenbank-Backups
│   └── inventory_*.json      # Zugehörige Metadaten
├── logs/
│   └── backup.log           # Backup-Protokolle
└── database/
    ├── inventory.db         # Aktive Hauptdatenbank
    └── users.db            # Aktive Benutzerdatenbank
```

## Sicherheitshinweise
- Backups werden automatisch nach 30 Tagen gelöscht
- Wichtige Backups sollten zusätzlich extern gesichert werden
- Zugriff auf Backup-Verzeichnis nur für Administratoren
- Beide Datenbanken werden immer zusammen gesichert und wiederhergestellt 