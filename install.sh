#!/bin/bash

# Robotic Dog Installation Script for Raspberry Pi 4 B+
# This script installs all dependencies and sets up the robotic dog system

set -e

echo "🐕 Robotic Dog System Installation"
echo "=================================="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "⚠️  Warning: This script is designed for Raspberry Pi"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    nodejs \
    npm \
    i2c-tools \
    gpsd \
    gpsd-clients \
    ffmpeg \
    cmake \
    build-essential \
    libopencv-dev \
    python3-opencv \
    libgpiod2 \
    pigpio \
    pulseaudio \
    alsa-utils

# Enable required interfaces
echo "🔌 Enabling hardware interfaces..."
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_camera 0
sudo raspi-config nonint do_ssh 0

# Create project directory
PROJECT_DIR="/opt/robotic_dog"
echo "📁 Creating project directory: $PROJECT_DIR"
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR

# Copy project files
echo "📋 Copying project files..."
cp -r robotic_dog $PROJECT_DIR/
cp main.py $PROJECT_DIR/
cp requirements.txt $PROJECT_DIR/ 2>/dev/null || echo "No requirements.txt found in root"

# Create Python virtual environment
echo "🐍 Creating Python virtual environment..."
cd $PROJECT_DIR
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
if [ -f "robotic_dog/requirements.txt" ]; then
    pip install -r robotic_dog/requirements.txt
fi

# Additional AI/ML packages
echo "🤖 Installing AI/ML packages..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install transformers

# Install tablet OS dependencies
echo "📱 Installing tablet OS dependencies..."
cd /tmp
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Electron for tablet interface
echo "💻 Setting up tablet interface..."
cd $PROJECT_DIR
if [ -f "package.json" ]; then
    npm install
fi

# Set up systemd service
echo "🔧 Setting up system service..."
sudo tee /etc/systemd/system/robotic-dog.service > /dev/null <<EOF
[Unit]
Description=Robotic Dog Controller
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Set up GPIO permissions
echo "🔐 Setting up GPIO permissions..."
sudo usermod -a -G gpio,i2c,spi $USER

# Configure GPS
echo "🛰️ Configuring GPS..."
sudo tee /etc/default/gpsd > /dev/null <<EOF
# Devices gpsd should collect to at boot time.
DEVICES="/dev/ttyAMA0"

# Other options you want to pass to gpsd
GPSD_OPTIONS="-n"

# Automatically hot-plug USB GPS devices via gpsdctl
USBAUTO="true"
EOF

# Configure camera
echo "📷 Configuring camera..."
if ! grep -q "start_x=1" /boot/config.txt; then
    echo "start_x=1" | sudo tee -a /boot/config.txt
fi

if ! grep -q "gpu_mem=128" /boot/config.txt; then
    echo "gpu_mem=128" | sudo tee -a /boot/config.txt
fi

# Set up WiFi hotspot for remote control
echo "📶 Setting up WiFi hotspot..."
sudo apt install -y hostapd dnsmasq

sudo tee /etc/hostapd/hostapd.conf > /dev/null <<EOF
interface=wlan1
driver=nl80211
ssid=RoboticDog_Control
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=DogControl123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# Create startup script
echo "🚀 Creating startup script..."
tee $PROJECT_DIR/start.sh > /dev/null <<EOF
#!/bin/bash
cd $PROJECT_DIR
source venv/bin/activate
python main.py
EOF

chmod +x $PROJECT_DIR/start.sh

# Set up log rotation
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/robotic-dog > /dev/null <<EOF
/var/log/robotic_dog.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF

# Create configuration directory
echo "⚙️ Creating configuration..."
mkdir -p $PROJECT_DIR/config
tee $PROJECT_DIR/config/robot.conf > /dev/null <<EOF
# Robotic Dog Configuration
[HARDWARE]
camera_enabled = true
servo_enabled = true
gps_enabled = true

[NETWORK]
websocket_port = 8765
http_port = 5000
wifi_hotspot = true

[AI]
vision_enabled = true
voice_enabled = true
navigation_enabled = true

[LOGGING]
log_level = INFO
log_file = /var/log/robotic_dog.log
EOF

# Enable and start services
echo "🔄 Enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable robotic-dog.service
sudo systemctl enable gpsd.service

# Create desktop shortcut for tablet mode
echo "🖥️ Creating desktop shortcuts..."
mkdir -p /home/$USER/Desktop
tee /home/$USER/Desktop/robotic-dog-control.desktop > /dev/null <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Robotic Dog Control
Comment=Control interface for robotic dog
Exec=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/main.py
Icon=$PROJECT_DIR/icon.png
Terminal=false
StartupNotify=true
Categories=Utility;
EOF

chmod +x /home/$USER/Desktop/robotic-dog-control.desktop

# Create icon (simple placeholder)
echo "🎨 Creating application icon..."
convert -size 64x64 xc:blue -pointsize 30 -fill white -gravity center -annotate +0+0 "🐕" $PROJECT_DIR/icon.png 2>/dev/null || echo "ImageMagick not available, skipping icon creation"

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "📋 Next Steps:"
echo "1. Reboot your Raspberry Pi: sudo reboot"
echo "2. After reboot, the robotic dog service will start automatically"
echo "3. Access the web interface at: http://localhost:5000"
echo "4. For tablet mode, run: npm start (in the project directory)"
echo "5. Upload the NodeMCU remote code to your ESP8266 device"
echo ""
echo "🔧 Manual start: cd $PROJECT_DIR && ./start.sh"
echo "📊 Check status: sudo systemctl status robotic-dog"
echo "📝 View logs: sudo journalctl -u robotic-dog -f"
echo ""
echo "🎮 Control Methods:"
echo "  • Web browser: http://[pi_ip]:5000"
echo "  • Tablet app: Run 'npm start' in project directory"
echo "  • NodeMCU remote: Use the Arduino code in nodemcu_remote/"
echo "  • Voice commands: Say commands near the robot"
echo ""
echo "⚠️  Important: Set your API keys in environment variables:"
echo "   export OPENAI_API_KEY='your_key_here'"
echo "   export HUGGINGFACE_API_KEY='your_key_here'"
echo ""