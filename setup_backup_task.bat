@echo off
echo Einrichten der Backup-Tasks...

REM Morgendliches Backup (7:00 Uhr)
schtasks /create /tn "ScandyBackupMorning" /tr "python %~dp0backup.py" /sc daily /st 07:00 /f

REM Abendliches Backup (19:00 Uhr)
schtasks /create /tn "ScandyBackupEvening" /tr "python %~dp0backup.py" /sc daily /st 19:00 /f

echo Tasks wurden eingerichtet. Überprüfen Sie die Einrichtung mit "schtasks /query /tn Scandy*"
pause 