const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const fs = require('fs');

class TabletOS {
  constructor() {
    this.mainWindow = null;
    this.apps = new Map();
    this.isDevMode = process.argv.includes('--dev');
  }

  createMainWindow() {
    this.mainWindow = new BrowserWindow({
      width: 1024,
      height: 768,
      fullscreen: !this.isDevMode,
      frame: false,
      webPreferences: {
        nodeIntegration: true,
        contextIsolation: false,
        enableRemoteModule: true,
        webSecurity: false
      },
      icon: path.join(__dirname, 'assets/icon.png')
    });

    this.mainWindow.loadFile('src/index.html');

    if (this.isDevMode) {
      this.mainWindow.webContents.openDevTools();
    }

    // Handle window closed
    this.mainWindow.on('closed', () => {
      this.mainWindow = null;
    });

    // Set up IPC handlers
    this.setupIpcHandlers();
  }

  setupIpcHandlers() {
    // Launch app
    ipcMain.handle('launch-app', async (event, appId) => {
      return this.launchApp(appId);
    });

    // Get installed apps
    ipcMain.handle('get-apps', async () => {
      return this.getInstalledApps();
    });

    // Open external URL
    ipcMain.handle('open-external', async (event, url) => {
      shell.openExternal(url);
    });

    // System operations
    ipcMain.handle('system-shutdown', async () => {
      app.quit();
    });
  }

  launchApp(appId) {
    try {
      const appPath = path.join(__dirname, 'apps', appId);
      if (fs.existsSync(appPath)) {
        // Create new window for app
        const appWindow = new BrowserWindow({
          width: 800,
          height: 600,
          parent: this.mainWindow,
          webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
          }
        });

        const appIndexPath = path.join(appPath, 'index.html');
        if (fs.existsSync(appIndexPath)) {
          appWindow.loadFile(appIndexPath);
        } else {
          appWindow.loadURL(`file://${appPath}/index.html`);
        }

        this.apps.set(appId, appWindow);

        appWindow.on('closed', () => {
          this.apps.delete(appId);
        });

        return { success: true, message: `Launched ${appId}` };
      } else {
        return { success: false, message: `App ${appId} not found` };
      }
    } catch (error) {
      return { success: false, message: error.message };
    }
  }

  getInstalledApps() {
    const appsDir = path.join(__dirname, 'apps');
    const apps = [];

    if (fs.existsSync(appsDir)) {
      const appFolders = fs.readdirSync(appsDir);
      
      appFolders.forEach(folder => {
        const appManifestPath = path.join(appsDir, folder, 'manifest.json');
        if (fs.existsSync(appManifestPath)) {
          try {
            const manifest = JSON.parse(fs.readFileSync(appManifestPath, 'utf8'));
            apps.push({
              id: folder,
              ...manifest
            });
          } catch (e) {
            console.error(`Error reading manifest for ${folder}:`, e);
          }
        }
      });
    }

    return apps;
  }

  initialize() {
    app.whenReady().then(() => {
      this.createMainWindow();

      app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
          this.createMainWindow();
        }
      });
    });

    app.on('window-all-closed', () => {
      if (process.platform !== 'darwin') {
        app.quit();
      }
    });
  }
}

// Initialize the Tablet OS
const tabletOS = new TabletOS();
tabletOS.initialize();