const { app, BrowserWindow, Notification } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
let flaskProcess = null;

function showNotification(title, body) {
    new Notification({
        title: title,
        body: body,
        icon: path.join(__dirname, '../static/images/scandy-logo.png')
    }).show();
}

function startFlaskServer() {
    console.log('Starting Flask server...');
    // Nutze die virtuelle Umgebung
    const pythonPath = process.platform === 'win32' 
        ? 'venv\\Scripts\\python.exe'
        : 'venv/bin/python';
    
    flaskProcess = spawn(pythonPath, ['-m', 'flask', 'run'], {
        env: {
            ...process.env,
            FLASK_APP: 'wsgi.py',
            FLASK_ENV: 'development'
        }
    });
    
    flaskProcess.stdout.on('data', (data) => {
        console.log(`Flask: ${data}`);
    });

    flaskProcess.stderr.on('data', (data) => {
        console.error(`Flask Error: ${data}`);
    });
}

function createWindow() {
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        titleBarStyle: 'hidden',
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        },
        minWidth: 800,
        minHeight: 600,
        backgroundColor: '#ffffff',
        show: false
    });

    win.once('ready-to-show', () => {
        win.show();
    });

    if (process.env.NODE_ENV === 'production') {
        win.setMenu(null);
    }

    // Warte kurz, bis der Flask-Server gestartet ist
    setTimeout(() => {
        win.loadURL('http://localhost:5000');
    }, 2000);
}

app.whenReady().then(() => {
    startFlaskServer();
    createWindow();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
    // Beende den Flask-Server
    if (flaskProcess) {
        flaskProcess.kill();
    }
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