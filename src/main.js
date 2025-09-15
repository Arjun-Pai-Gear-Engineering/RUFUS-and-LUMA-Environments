const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const express = require('express');
const WebSocket = require('ws');

class TabletControlApp {
    constructor() {
        this.mainWindow = null;
        this.robotConnection = null;
        this.expressApp = express();
        this.setupExpressRoutes();
    }

    setupExpressRoutes() {
        // Serve static files
        this.expressApp.use(express.static(path.join(__dirname, 'public')));
        
        // API routes for robot control
        this.expressApp.get('/api/status', (req, res) => {
            if (this.robotConnection && this.robotConnection.readyState === WebSocket.OPEN) {
                res.json({ connected: true, status: 'Robot connected' });
            } else {
                res.json({ connected: false, status: 'Robot disconnected' });
            }
        });

        this.expressApp.post('/api/command', express.json(), (req, res) => {
            const { command, params } = req.body;
            
            if (this.robotConnection && this.robotConnection.readyState === WebSocket.OPEN) {
                const message = JSON.stringify({ command, params });
                this.robotConnection.send(message);
                res.json({ success: true, message: 'Command sent' });
            } else {
                res.status(503).json({ success: false, message: 'Robot not connected' });
            }
        });
    }

    createMainWindow() {
        this.mainWindow = new BrowserWindow({
            width: 1024,
            height: 768,
            webPreferences: {
                nodeIntegration: true,
                contextIsolation: false
            },
            fullscreen: false, // Set to true for tablet fullscreen
            title: 'Robotic Dog Control'
        });

        // Load the control interface
        this.mainWindow.loadFile(path.join(__dirname, 'index.html'));

        // Handle window closed
        this.mainWindow.on('closed', () => {
            this.mainWindow = null;
        });
    }

    connectToRobot(robotIP = 'localhost', robotPort = 8765) {
        const wsUrl = `ws://${robotIP}:${robotPort}`;
        console.log(`Connecting to robot at ${wsUrl}`);

        this.robotConnection = new WebSocket(wsUrl);

        this.robotConnection.on('open', () => {
            console.log('Connected to robot');
            this.sendToRenderer('robot-connected', true);
        });

        this.robotConnection.on('message', (data) => {
            try {
                const message = JSON.parse(data);
                this.sendToRenderer('robot-message', message);
            } catch (e) {
                console.error('Failed to parse robot message:', e);
            }
        });

        this.robotConnection.on('close', () => {
            console.log('Disconnected from robot');
            this.sendToRenderer('robot-connected', false);
            
            // Attempt to reconnect after 5 seconds
            setTimeout(() => {
                this.connectToRobot(robotIP, robotPort);
            }, 5000);
        });

        this.robotConnection.on('error', (error) => {
            console.error('Robot connection error:', error);
            this.sendToRenderer('robot-error', error.message);
        });
    }

    sendToRenderer(channel, data) {
        if (this.mainWindow && this.mainWindow.webContents) {
            this.mainWindow.webContents.send(channel, data);
        }
    }

    sendCommandToRobot(command, params = {}) {
        if (this.robotConnection && this.robotConnection.readyState === WebSocket.OPEN) {
            const message = JSON.stringify({ command, params });
            this.robotConnection.send(message);
            return true;
        }
        return false;
    }

    setupIpcHandlers() {
        // Handle commands from renderer process
        ipcMain.on('robot-command', (event, { command, params }) => {
            const success = this.sendCommandToRobot(command, params);
            event.reply('command-result', { success, command, params });
        });

        // Handle connection requests
        ipcMain.on('connect-robot', (event, { ip, port }) => {
            this.connectToRobot(ip, port);
        });

        // Handle app control
        ipcMain.on('toggle-fullscreen', () => {
            if (this.mainWindow) {
                this.mainWindow.setFullScreen(!this.mainWindow.isFullScreen());
            }
        });

        ipcMain.on('quit-app', () => {
            app.quit();
        });
    }

    initialize() {
        app.whenReady().then(() => {
            this.createMainWindow();
            this.setupIpcHandlers();
            
            // Start express server for web interface
            this.expressApp.listen(3000, () => {
                console.log('Tablet control server running on port 3000');
            });
            
            // Connect to robot (default local connection)
            this.connectToRobot();
        });

        app.on('window-all-closed', () => {
            if (process.platform !== 'darwin') {
                app.quit();
            }
        });

        app.on('activate', () => {
            if (BrowserWindow.getAllWindows().length === 0) {
                this.createMainWindow();
            }
        });

        app.on('before-quit', () => {
            if (this.robotConnection) {
                this.robotConnection.close();
            }
        });
    }
}

// Create and initialize the app
const tabletApp = new TabletControlApp();
tabletApp.initialize();