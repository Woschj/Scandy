@echo off
echo Starte Build-Prozess für Scandy...

echo Aktiviere virtuelle Umgebung...
call venv\Scripts\activate.bat || (
    echo Fehler beim Aktivieren der virtuellen Umgebung!
    pause
    exit /b 1
)

echo Installiere Nuitka und benötigte Tools...
pip install nuitka wheel || (
    echo Fehler beim Installieren von Nuitka!
    pause
    exit /b 1
)

echo Bereinige alte Build-Dateien...
if exist build rmdir /S /Q build
if exist dist rmdir /S /Q dist
if exist scandy_server.build rmdir /S /Q scandy_server.build
if exist scandy_server.dist rmdir /S /Q scandy_server.dist
if exist scandy_client.build rmdir /S /Q scandy_client.build
if exist scandy_client.dist rmdir /S /Q scandy_client.dist

echo Erstelle Server-EXE...
python -m nuitka ^
    --standalone ^
    --mingw64 ^
    --follow-imports ^
    --windows-company-name="Scandy" ^
    --windows-product-name="Scandy Server" ^
    --windows-file-version=1.0.0 ^
    --windows-product-version=1.0.0 ^
    --include-data-dir=app/database=database ^
    --include-data-dir=app/sql=sql ^
    --include-data-dir=app/static=static ^
    --include-data-dir=app/templates=templates ^
    --include-data-dir=app/migrations=migrations ^
    --include-data-file=app/config/db_schema.json=config/db_schema.json ^
    --include-data-file=app/schema.sql=schema.sql ^
    --include-data-file=instance/scandy.db=instance/scandy.db ^
    --output-dir=dist ^
    run.py || (
        echo Fehler beim Erstellen der Server-EXE!
        pause
        exit /b 1
    )

echo Erstelle Client-EXE...
python -m nuitka ^
    --standalone ^
    --mingw64 ^
    --follow-imports ^
    --windows-company-name="Scandy" ^
    --windows-product-name="Scandy Client" ^
    --windows-file-version=1.0.0 ^
    --windows-product-version=1.0.0 ^
    --windows-disable-console ^
    --include-data-file=client/main.py=main.py ^
    --output-dir=dist ^
    run_client.py || (
        echo Fehler beim Erstellen der Client-EXE!
        pause
        exit /b 1
    )

echo Kopiere Dateien in die richtige Struktur...
if not exist dist\server mkdir dist\server
if not exist dist\client mkdir dist\client

echo Kopiere Server-Dateien...
if exist "dist\run.dist" (
    xcopy /E /I /Y "dist\run.dist\*" "dist\server\" || (
        echo Fehler beim Kopieren der Server-Dateien!
        pause
        exit /b 1
    )
) else (
    echo Server-Build-Verzeichnis nicht gefunden!
    pause
    exit /b 1
)

echo Kopiere Client-Dateien...
if exist "dist\run_client.dist" (
    xcopy /E /I /Y "dist\run_client.dist\*" "dist\client\" || (
        echo Fehler beim Kopieren der Client-Dateien!
        pause
        exit /b 1
    )
) else (
    echo Client-Build-Verzeichnis nicht gefunden!
    pause
    exit /b 1
)

echo Build abgeschlossen. Starte Inno Setup Compiler...
if not exist installer mkdir installer
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" scandy_setup.iss || (
    echo Fehler beim Erstellen des Installers!
    pause
    exit /b 1
)

echo Build-Prozess erfolgreich abgeschlossen!
echo Der Installer befindet sich im Ordner 'installer'
pause