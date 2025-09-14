# RUFUS-LUMA Tablet OS

A tablet-like operating system designed specifically for Raspberry Pi 4 B+, providing an iPad-like interface with touch support, built-in apps, and an extensible app ecosystem.

## Features

🎯 **Tablet Experience**
- iPad-like interface with smooth animations
- Touch-screen optimized controls
- Intuitive gesture support
- Status bar with system information

🚀 **Built-in Apps**
- **Browser**: Chromium-based web browser with bookmarks and history
- **Camera**: Take photos and record videos with filters and effects
- **Calculator**: Scientific calculator with history
- **Notes**: Rich text editor with auto-save and search
- **Settings**: System configuration and customization

📱 **App Store**
- Install and manage applications
- Featured apps and recommendations
- Easy app installation and removal

⚙️ **Raspberry Pi Optimized**
- Hardware acceleration support
- Touch screen drivers
- Optimized for Raspberry Pi 4 B+ performance
- Low power consumption mode

## Quick Start

### Prerequisites
- Raspberry Pi 4 B+ (4GB RAM recommended)
- MicroSD card (32GB or larger)
- Touch screen display (optional but recommended)
- Raspberry Pi OS Lite or Desktop

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Arjun-Pai-Gear-Engineering/RUFUS-and-LUMA-Environments.git
   cd RUFUS-and-LUMA-Environments
   ```

2. **Run the setup script**
   ```bash
   chmod +x scripts/setup-pi.sh
   sudo ./scripts/setup-pi.sh
   ```

3. **Reboot your Pi**
   ```bash
   sudo reboot
   ```

The tablet OS will automatically start after reboot!

### Manual Installation

If you prefer to install manually:

1. **Install Node.js and dependencies**
   ```bash
   sudo apt update
   sudo apt install nodejs npm
   npm install
   ```

2. **Start the OS**
   ```bash
   npm start
   ```

## Usage

### Navigation
- **Home Screen**: Displays all installed apps in a grid layout
- **Dock**: Quick access to frequently used apps
- **Status Bar**: Shows time, battery, and network status
- **App Store**: Browse and install new applications

### Built-in Apps

#### Browser 🌐
- Full web browsing with Chromium engine
- Bookmarks and history management
- Touch-optimized interface

#### Camera 📷
- Photo and video capture
- Real-time filters and effects
- Gallery with organization features

#### Calculator 🔢
- Basic and scientific calculations
- History and memory functions
- Large touch-friendly buttons

#### Notes 📝
- Rich text editing
- Auto-save functionality
- Search and organization

## Development

### Creating Custom Apps

Apps are web-based and follow a simple structure:

```
src/apps/your-app/
├── manifest.json
├── index.html
├── styles.css (optional)
└── script.js (optional)
```

### Building and Testing

```bash
# Install dependencies
npm install

# Start development mode
npm run dev

# Build for production
npm run build
```

## Hardware Requirements

### Minimum Requirements
- Raspberry Pi 4 B+ (2GB RAM)
- MicroSD card (16GB)
- Any HDMI display

### Recommended Setup
- Raspberry Pi 4 B+ (4GB or 8GB RAM)
- Official Raspberry Pi Touch Display (7")
- High-speed MicroSD card (32GB+, Class 10)
- Active cooling (fan or heatsink)

## License

This project is licensed under the MIT License.

---

**Made with ❤️ for the Raspberry Pi community**