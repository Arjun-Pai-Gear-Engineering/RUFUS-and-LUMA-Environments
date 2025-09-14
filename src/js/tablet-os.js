// RUFUS-LUMA Tablet OS JavaScript
const { ipcRenderer } = require('electron');

class TabletOSInterface {
    constructor() {
        this.currentScreen = 'home-screen';
        this.installedApps = [];
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.updateStatusBar();
        this.loadApps();
        this.hideLoading();
        
        // Update time every second
        setInterval(() => this.updateStatusBar(), 1000);
    }

    setupEventListeners() {
        // Dock app clicks
        document.querySelectorAll('.dock-app').forEach(app => {
            app.addEventListener('click', (e) => {
                const appId = e.currentTarget.dataset.app;
                this.handleDockAppClick(appId);
            });
        });

        // Settings shutdown button
        const shutdownBtn = document.getElementById('shutdown-btn');
        if (shutdownBtn) {
            shutdownBtn.addEventListener('click', () => this.shutdown());
        }

        // App store button (if we add one to dock)
        this.addAppStoreToHomeScreen();

        // Settings listeners
        this.setupSettingsListeners();

        // Touch/click handlers for better tablet experience
        this.setupTouchHandlers();
    }

    setupTouchHandlers() {
        // Add touch feedback for all interactive elements
        document.addEventListener('touchstart', (e) => {
            if (e.target.closest('.app-item, .dock-app, .back-btn, button')) {
                e.target.closest('.app-item, .dock-app, .back-btn, button').style.opacity = '0.7';
            }
        });

        document.addEventListener('touchend', (e) => {
            if (e.target.closest('.app-item, .dock-app, .back-btn, button')) {
                setTimeout(() => {
                    e.target.closest('.app-item, .dock-app, .back-btn, button').style.opacity = '1';
                }, 150);
            }
        });
    }

    handleDockAppClick(appId) {
        switch (appId) {
            case 'home':
                this.showScreen('home-screen');
                break;
            case 'browser':
                this.launchApp('browser');
                break;
            case 'camera':
                this.launchApp('camera');
                break;
            case 'settings':
                this.showScreen('settings-screen');
                break;
            default:
                this.launchApp(appId);
        }
    }

    async launchApp(appId) {
        this.showLoading();
        
        try {
            const result = await ipcRenderer.invoke('launch-app', appId);
            
            if (result.success) {
                console.log(`Launched app: ${appId}`);
                // Add visual feedback
                this.showNotification(`Launching ${appId}...`);
            } else {
                console.error(`Failed to launch app: ${result.message}`);
                this.showNotification(`Failed to launch ${appId}: ${result.message}`, 'error');
            }
        } catch (error) {
            console.error('Error launching app:', error);
            this.showNotification('Error launching app', 'error');
        }
        
        this.hideLoading();
    }

    showScreen(screenId) {
        // Hide all screens
        document.querySelectorAll('.screen').forEach(screen => {
            screen.classList.remove('active');
        });

        // Show target screen
        const targetScreen = document.getElementById(screenId);
        if (targetScreen) {
            targetScreen.classList.add('active');
            this.currentScreen = screenId;
        }
    }

    async loadApps() {
        try {
            this.installedApps = await ipcRenderer.invoke('get-apps');
            this.renderAppGrid();
            this.renderInstalledApps();
        } catch (error) {
            console.error('Error loading apps:', error);
        }
    }

    renderAppGrid() {
        const appGrid = document.getElementById('app-grid');
        appGrid.innerHTML = '';

        // Add app store first
        const appStoreItem = this.createAppItem('app-store', '🏪', 'App Store');
        appStoreItem.addEventListener('click', () => this.showScreen('app-store-screen'));
        appGrid.appendChild(appStoreItem);

        // Add installed apps
        this.installedApps.forEach(app => {
            const appItem = this.createAppItem(app.id, app.icon, app.name);
            appItem.addEventListener('click', () => this.launchApp(app.id));
            appGrid.appendChild(appItem);
        });
    }

    createAppItem(id, icon, name) {
        const appItem = document.createElement('div');
        appItem.className = 'app-item';
        appItem.innerHTML = `
            <div class="app-icon">${icon}</div>
            <span class="app-name">${name}</span>
        `;
        return appItem;
    }

    renderInstalledApps() {
        const installedAppsList = document.getElementById('installed-apps-list');
        if (!installedAppsList) return;

        installedAppsList.innerHTML = '';

        this.installedApps.forEach(app => {
            const appItem = this.createStoreAppItem(app, true);
            installedAppsList.appendChild(appItem);
        });
    }

    createStoreAppItem(app, isInstalled = false) {
        const appItem = document.createElement('div');
        appItem.className = 'store-app-item';
        
        appItem.innerHTML = `
            <div class="store-app-header">
                <div class="store-app-icon">${app.icon}</div>
                <div class="store-app-info">
                    <h3>${app.name}</h3>
                    <span class="version">v${app.version || '1.0.0'}</span>
                </div>
            </div>
            <p class="store-app-description">${app.description || 'No description available'}</p>
            <button class="${isInstalled ? 'launch-btn' : 'install-btn'}" 
                    onclick="tabletOS.${isInstalled ? 'launchApp' : 'installApp'}('${app.id}')">
                ${isInstalled ? 'Launch' : 'Install'}
            </button>
        `;

        return appItem;
    }

    addAppStoreToHomeScreen() {
        // This adds featured apps to the app store
        const featuredAppsList = document.getElementById('featured-apps-list');
        if (!featuredAppsList) return;

        const featuredApps = [
            {
                id: 'calculator',
                name: 'Calculator',
                icon: '🔢',
                description: 'Simple calculator app for basic math operations',
                version: '1.0.0'
            },
            {
                id: 'notes',
                name: 'Notes',
                icon: '📝',
                description: 'Take notes and organize your thoughts',
                version: '1.0.0'
            },
            {
                id: 'weather',
                name: 'Weather',
                icon: '🌤️',
                description: 'Check current weather and forecasts',
                version: '1.0.0'
            }
        ];

        featuredApps.forEach(app => {
            const appItem = this.createStoreAppItem(app, false);
            featuredAppsList.appendChild(appItem);
        });
    }

    async installApp(appId) {
        this.showLoading();
        this.showNotification(`Installing ${appId}...`);
        
        // Simulate app installation
        setTimeout(() => {
            this.showNotification(`${appId} installed successfully!`);
            this.loadApps(); // Reload apps
            this.hideLoading();
        }, 2000);
    }

    setupSettingsListeners() {
        // Brightness control
        const brightnessSlider = document.getElementById('brightness');
        if (brightnessSlider) {
            brightnessSlider.addEventListener('input', (e) => {
                const brightness = e.target.value;
                document.body.style.filter = `brightness(${brightness}%)`;
            });
        }

        // Wallpaper selection
        const wallpaperSelect = document.getElementById('wallpaper-select');
        if (wallpaperSelect) {
            wallpaperSelect.addEventListener('change', (e) => {
                this.changeWallpaper(e.target.value);
            });
        }

        // Device name
        const deviceNameInput = document.getElementById('device-name');
        if (deviceNameInput) {
            deviceNameInput.addEventListener('change', (e) => {
                const systemName = document.getElementById('system-name');
                if (systemName) {
                    systemName.textContent = e.target.value;
                }
            });
        }
    }

    changeWallpaper(wallpaper) {
        const wallpaperEl = document.querySelector('.wallpaper');
        if (!wallpaperEl) return;

        const wallpapers = {
            default: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            nature: 'linear-gradient(135deg, #4CAF50 0%, #8BC34A 100%)',
            abstract: 'linear-gradient(135deg, #FF5722 0%, #FF9800 100%)'
        };

        wallpaperEl.style.background = wallpapers[wallpaper] || wallpapers.default;
    }

    updateStatusBar() {
        const timeEl = document.getElementById('time');
        if (timeEl) {
            const now = new Date();
            timeEl.textContent = now.toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        }

        // Simulate battery level
        const batteryEl = document.getElementById('battery');
        if (batteryEl) {
            const batteryLevel = Math.floor(Math.random() * 20) + 80; // 80-100%
            batteryEl.textContent = `${batteryLevel}%`;
        }
    }

    showLoading() {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.classList.remove('hidden');
        }
    }

    hideLoading() {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.classList.add('hidden');
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 60px;
            right: 20px;
            background: ${type === 'error' ? '#FF3B30' : '#34C759'};
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 500;
            z-index: 3000;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        `;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);

        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }

    async shutdown() {
        this.showNotification('Shutting down...');
        this.showLoading();
        
        setTimeout(async () => {
            try {
                await ipcRenderer.invoke('system-shutdown');
            } catch (error) {
                console.error('Error during shutdown:', error);
            }
        }, 2000);
    }
}

// Global functions for HTML onclick handlers
function showScreen(screenId) {
    tabletOS.showScreen(screenId);
}

// Initialize the tablet OS when DOM is loaded
let tabletOS;
document.addEventListener('DOMContentLoaded', () => {
    tabletOS = new TabletOSInterface();
});