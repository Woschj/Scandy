#!/bin/bash

# Setze Besitzer und Gruppe für alle Backup-Dateien
chown -R www-data:www-data /app/backups

# Setze Berechtigungen
chmod -R 755 /app/backups
chmod -R 644 /app/backups/*.db
chmod -R 644 /app/backups/*.json 