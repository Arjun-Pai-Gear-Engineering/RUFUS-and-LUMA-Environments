#!/bin/bash

# RUFUS-LUMA Tablet OS Setup Script for Raspberry Pi 4 B+
# This script sets up the tablet OS environment on a fresh Raspberry Pi OS installation

set -e

echo "🚀 RUFUS-LUMA Tablet OS Setup for Raspberry Pi 4 B+"
echo "=================================================="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "⚠️  Warning: This script is designed for Raspberry Pi hardware"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "📦 Installing required packages..."
sudo apt install -y \
    nodejs \
    npm \
    git \
    chromium-browser \
    x11-xserver-utils \
    xinit \
    openbox \
    xorg \
    lightdm \
    unclutter \
    wmctrl \
    python3 \
    python3-pip

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Set up auto-start configuration
echo "⚙️  Setting up auto-start configuration..."

# Create desktop session file
sudo tee /usr/share/xsessions/rufus-luma.desktop > /dev/null << EOF
[Desktop Entry]
Name=RUFUS-LUMA Tablet OS
Comment=Tablet-like OS for Raspberry Pi
Exec=/home/pi/rufus-luma-session.sh
Type=Application
EOF

# Create session script
tee /home/pi/rufus-luma-session.sh > /dev/null << EOF
#!/bin/bash

# Set up display
export DISPLAY=:0
xset s off
xset -dpms
xset s noblank

# Hide cursor after 5 seconds of inactivity
unclutter -idle 5 &

# Start window manager
openbox-session &

# Wait for window manager
sleep 2

# Start the tablet OS
cd /home/pi/RUFUS-and-LUMA-Environments
npm start
EOF

chmod +x /home/pi/rufus-luma-session.sh

# Set up auto-login
echo "⚙️  Setting up auto-login..."
sudo tee /etc/lightdm/lightdm.conf.d/01-autologin.conf > /dev/null << EOF
[SeatDefaults]
autologin-user=pi
autologin-user-timeout=0
user-session=rufus-luma
EOF

# Configure touch screen if available
echo "📱 Configuring touch screen support..."
sudo tee /usr/share/X11/xorg.conf.d/40-libinput.conf > /dev/null << EOF
# Touch screen configuration for tablets
Section "InputClass"
    Identifier "libinput touchscreen catchall"
    MatchIsTouchscreen "on"
    MatchDevicePath "/dev/input/event*"
    Driver "libinput"
    Option "Calibration" "0 4095 0 4095"
EndSection
EOF

# Set up tablet optimizations
echo "⚙️  Setting up tablet optimizations..."

# Create openbox configuration for kiosk mode
mkdir -p /home/pi/.config/openbox
tee /home/pi/.config/openbox/rc.xml > /dev/null << EOF
<?xml version="1.0" encoding="UTF-8"?>
<openbox_config xmlns="http://openbox.org/3.4/rc">
  <resistance>
    <strength>10</strength>
    <screen_edge_strength>20</screen_edge_strength>
  </resistance>
  <focus>
    <focusNew>yes</focusNew>
    <followMouse>no</followMouse>
    <focusLast>yes</focusLast>
    <underMouse>no</underMouse>
    <focusDelay>200</focusDelay>
    <raiseOnFocus>no</raiseOnFocus>
  </focus>
  <placement>
    <policy>Smart</policy>
    <center>yes</center>
    <monitor>Any</monitor>
    <primaryMonitor>1</primaryMonitor>
  </placement>
  <theme>
    <name>Clearlooks</name>
    <titleLayout>NLIMC</titleLayout>
    <keepBorder>no</keepBorder>
    <animateIconify>no</animateIconify>
    <font place="ActiveWindow">
      <name>sans</name>
      <size>8</size>
      <weight>bold</weight>
      <slant>normal</slant>
    </font>
    <font place="InactiveWindow">
      <name>sans</name>
      <size>8</size>
      <weight>bold</weight>
      <slant>normal</slant>
    </font>
  </theme>
  <desktops>
    <number>1</number>
    <firstdesk>1</firstdesk>
    <names>
      <name>RUFUS-LUMA</name>
    </names>
    <popupTime>875</popupTime>
  </desktops>
  <resize>
    <drawContents>yes</drawContents>
    <popupShow>Nonpixel</popupShow>
    <popupPosition>Center</popupPosition>
    <popupFixedPosition>
      <x>10</x>
      <y>10</y>
    </popupFixedPosition>
  </resize>
  <applications>
    <application name="*">
      <decor>no</decor>
      <maximized>true</maximized>
      <fullscreen>yes</fullscreen>
    </application>
  </applications>
</openbox_config>
EOF

# Set up boot configuration for performance
echo "⚙️  Optimizing boot configuration..."
sudo tee -a /boot/config.txt > /dev/null << EOF

# RUFUS-LUMA Tablet OS Optimizations
# GPU memory split for better graphics performance
gpu_mem=128

# Enable hardware acceleration
dtparam=audio=on
gpu_mem_256=128
gpu_mem_512=256
gpu_mem_1024=256

# Disable overscan for tablets
disable_overscan=1

# Set HDMI mode for tablets (adjust as needed)
hdmi_group=2
hdmi_mode=82

# Enable touch screen support
dtoverlay=rpi-ft5406

# Optimize for touch input
dtparam=spi=on
dtparam=i2c_arm=on
EOF

# Create startup service
echo "⚙️  Creating system service..."
sudo tee /etc/systemd/system/rufus-luma.service > /dev/null << EOF
[Unit]
Description=RUFUS-LUMA Tablet OS
After=graphical-session.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/RUFUS-and-LUMA-Environments
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10
Environment=DISPLAY=:0

[Install]
WantedBy=graphical-session.target
EOF

# Enable the service
sudo systemctl enable rufus-luma.service

# Set up Wi-Fi hotspot capability (optional)
echo "📶 Setting up Wi-Fi hotspot capability..."
sudo apt install -y hostapd dnsmasq

# Create hotspot configuration template
sudo tee /etc/hostapd/hostapd.conf.template > /dev/null << EOF
# RUFUS-LUMA Tablet Hotspot Configuration
interface=wlan0
driver=nl80211
ssid=RUFUS-LUMA-Tablet
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=tabletos123
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# Create network configuration script
tee /home/pi/setup-hotspot.sh > /dev/null << EOF
#!/bin/bash
# Script to enable Wi-Fi hotspot mode
echo "Setting up Wi-Fi hotspot..."
sudo cp /etc/hostapd/hostapd.conf.template /etc/hostapd/hostapd.conf
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq
echo "Hotspot configured. Reboot to activate."
EOF

chmod +x /home/pi/setup-hotspot.sh

# Set ownership
sudo chown -R pi:pi /home/pi/

echo ""
echo "✅ RUFUS-LUMA Tablet OS setup complete!"
echo ""
echo "🔧 Next steps:"
echo "1. Reboot your Raspberry Pi: sudo reboot"
echo "2. The tablet OS will start automatically"
echo "3. To enable Wi-Fi hotspot: ./setup-hotspot.sh"
echo ""
echo "📱 Features configured:"
echo "   - Auto-start tablet OS on boot"
echo "   - Touch screen support"
echo "   - Kiosk mode interface"
echo "   - Hardware acceleration"
echo "   - Wi-Fi hotspot capability"
echo ""
echo "🎯 The tablet will be accessible at the login screen"
echo "   Default session: RUFUS-LUMA Tablet OS"
echo ""

read -p "Reboot now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo reboot
fi