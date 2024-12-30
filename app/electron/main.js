const { app, BrowserWindow, Notification } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
let flaskProcess = null;
let mainWindow = null;

function showNotification(title, body) {
    new Notification({
        title: title,
        body: body,
        icon: path.join(__dirname, '../static/images/scandy-logo.png')
    }).show();
}

function startFlaskServer() {
    console.log('Starting Flask server...');
    
    // Pfad zur Python-Executable im venv
    const pythonPath = path.join(__dirname, '../../venv/bin/python');
    const scriptPath = path.join(__dirname, '../wsgi.py');
    
    flaskProcess = spawn(pythonPath, [scriptPath]);
    
    flaskProcess.stdout.on('data', (data) => {
        console.log('Flask:', data.toString());
    });
    
    flaskProcess.stderr.on('data', (data) => {
        console.log('Flask Error:', data.toString());
    });
}

function stopFlaskServer() {
    if (flaskProcess) {
        // Unter Windows
        if (process.platform === 'win32') {
            spawn('taskkill', ['/pid', flaskProcess.pid, '/f', '/t']);
        } else {
            // Unter Unix-basierten Systemen
            flaskProcess.kill('SIGTERM');
        }
        flaskProcess = null;
        console.log('Flask server stopped');
    }
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        titleBarStyle: 'hidden',
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });
    
    // Warte kurz, bis der Flask-Server gestartet ist
    setTimeout(() => {
        mainWindow.loadURL('http://localhost:5000');
    }, 2000);
    
    // Event-Handler für das Schließen des Fensters
    mainWindow.on('closed', () => {
        stopFlaskServer();
        mainWindow = null;
    });
}

// App Events
app.whenReady().then(() => {
    startFlaskServer();
    createWindow();
});

app.on('window-all-closed', () => {
    stopFlaskServer();
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});

// Cleanup beim Beenden der App
app.on('before-quit', () => {
    stopFlaskServer();
});

// App im Dock/Taskbar behalten
app.setActivationPolicy('regular');

// Single Instance Lock
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
    app.quit();
} else {
    app.on('second-instance', (event, commandLine, workingDirectory) => {
        if (mainWindow) {
            if (mainWindow.isMinimized()) mainWindow.restore();
            mainWindow.focus();
        }
    });
} 