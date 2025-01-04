const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let mainWindow;
let flaskProcess;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: true,
            // Cache aktivieren
            partition: 'persist:main'
        },
        // Zeige Fenster erst wenn Inhalt geladen ist
        show: false,
        // Deaktiviere die Menüleiste
        autoHideMenuBar: true,
        // Icon für die Taskleiste und Fenster
        icon: path.join(__dirname, 'assets', 'icon.ico')
    });

    mainWindow.loadURL('http://localhost:5000');
    
    // Zeige Fenster erst wenn Inhalt geladen ist
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    // Cache-Einstellungen über Session
    const ses = mainWindow.webContents.session;
    ses.clearCache();
    
    // Cache-Verhalten konfigurieren
    ses.setPreloads([]);
    ses.setPermissionRequestHandler((webContents, permission, callback) => {
        callback(true);
    });

    mainWindow.on('closed', function() {
        mainWindow = null;
    });
}

function startFlask() {
    console.log('Starting Flask server...');
    
    // Korrigierte Pfade - ein Verzeichnis höher (..)
    const pythonPath = path.join(process.cwd(), '..', 'venv', 'Scripts', 'python.exe');
    const scriptPath = path.join(process.cwd(), '..', 'wsgi.py');
    
    console.log('Python Path:', pythonPath);
    console.log('Script Path:', scriptPath);

    flaskProcess = spawn(pythonPath, [scriptPath], {
        // Arbeitsverzeichnis auf das Hauptverzeichnis setzen
        cwd: path.join(process.cwd(), '..')
    });

    flaskProcess.stdout.on('data', (data) => {
        console.log(`Flask: ${data}`);
    });

    flaskProcess.stderr.on('data', (data) => {
        console.error(`Flask Error: ${data}`);
    });

    flaskProcess.on('error', (error) => {
        console.error('Failed to start Flask:', error);
    });
}

app.on('ready', () => {
    startFlask();
    // Warte kurz bis Flask gestartet ist
    setTimeout(createWindow, 2000);
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});

app.on('will-quit', () => {
    if (flaskProcess) {
        flaskProcess.kill();
    }
}); 