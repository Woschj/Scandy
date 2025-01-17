#!/bin/bash

# Konfiguration
CONTAINER_NAME="scandy-flask"
CONTAINER_BACKUP_DIR="/app/internal_backups"
HOST_BACKUP_DIR="../backups"

# Stelle sicher, dass das Host-Backup-Verzeichnis existiert
mkdir -p "$HOST_BACKUP_DIR"

# Kopiere neue Backups aus dem Container
echo "Exportiere Backups aus Container..."
docker cp "$CONTAINER_NAME:$CONTAINER_BACKUP_DIR/." "$HOST_BACKUP_DIR/"

# Setze Berechtigungen
echo "Setze Berechtigungen..."
chmod -R 755 "$HOST_BACKUP_DIR"
find "$HOST_BACKUP_DIR" -type f -name "*.db" -exec chmod 644 {} \;
find "$HOST_BACKUP_DIR" -type f -name "*.json" -exec chmod 644 {} \;

echo "Backup-Export abgeschlossen" 