@echo off
echo Starte Build-Prozess für Scandy...

echo Aktiviere virtuelle Umgebung...
call venv\Scripts\activate.bat

echo Installiere PyInstaller...
pip install pyinstaller

echo Bereinige alte Build-Dateien...
rmdir /S /Q build
rmdir /S /Q dist

echo Erstelle Server-EXE...
pyinstaller --name=scandy_server ^
    --console ^
    --add-data "app;app" ^
    --add-data "instance;instance" ^
    --add-data ".env;." ^
    --clean ^
    --noconfirm ^
    run.py

echo Erstelle Client-EXE...
pyinstaller --name=scandy_client ^
    --noconsole ^
    --clean ^
    --noconfirm ^
    run_client.py

echo Build abgeschlossen. Starte Inno Setup Compiler...
echo Erstelle Server-Installer...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" server_setup.iss

echo Erstelle Client-Installer...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" client_setup.iss

echo Build-Prozess abgeschlossen!
echo Die Installer befinden sich im Ordner 'installer'
pause 