# 🐕 Robotic Dog for Raspberry Pi 4 B+

A comprehensive robotic dog control system with AI capabilities, dual control interfaces (tablet and WiFi remote), GPS navigation, and advanced computer vision.

## 🌟 Features

### Core Capabilities
- **4-Leg Movement Control**: Servo-based leg control with gait patterns
- **HD Camera**: Live streaming, photo capture, and computer vision
- **GPS Navigation**: Location tracking, waypoint navigation, and mapping
- **AI Integration**: Object detection, scene analysis, and voice commands
- **Dual Control**: Tablet app and NodeMCU WiFi remote

### AI Features
- **Computer Vision**: Object detection using Hugging Face DETR models
- **Scene Analysis**: Environment classification and obstacle detection
- **Voice Control**: Natural language command processing
- **Autonomous Navigation**: Path planning and obstacle avoidance
- **Real-time Analysis**: Continuous scene monitoring and decision making

### Control Interfaces
1. **Tablet App**: Full-featured Electron-based control panel
2. **NodeMCU Remote**: Physical WiFi remote with joystick and buttons
3. **Web Interface**: Browser-based control panel
4. **Voice Commands**: Natural language control
5. **WebSocket API**: For custom integrations

## 🛠️ Hardware Requirements

### Raspberry Pi 4 B+ Setup
- Raspberry Pi 4 Model B+ (4GB+ recommended)
- MicroSD card (32GB+ Class 10)
- Raspberry Pi Camera Module v2
- PCA9685 16-Channel Servo Driver
- 12x Servo Motors (SG90 or similar)
- GPS Module (NEO-6M or similar)
- USB Microphone (for voice commands)
- 7-inch Touch Display (optional, for tablet mode)

### NodeMCU Remote Components
- ESP8266 NodeMCU Development Board
- 128x64 OLED Display (SSD1306)
- Analog Joystick Module
- 4x Push Buttons
- LED indicators
- Breadboard and jumper wires

### Mechanical Components
- Robotic dog chassis/frame
- Servo mounting hardware
- Power distribution board
- LiPo battery (7.4V 2200mAh recommended)
- Voltage regulators (5V for servos, 3.3V for sensors)

## 🚀 Quick Installation

### Automatic Installation (Recommended)
```bash
# Clone the repository
git clone https://github.com/Arjun-Pai-Gear-Engineering/RUFUS-and-LUMA-Environments.git
cd RUFUS-and-LUMA-Environments

# Run the installation script
chmod +x install.sh
sudo ./install.sh
```

### Manual Installation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip nodejs npm i2c-tools gpsd

# Install Python packages
pip3 install -r robotic_dog/requirements.txt

# Install Electron dependencies
npm install

# Enable hardware interfaces
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_camera 0
```

## 🎮 Usage

### Starting the System
```bash
# Start robotic dog controller
python3 main.py

# Or use the service (after installation)
sudo systemctl start robotic-dog
```

### Access Methods
- **Web Control Panel**: http://localhost:5000
- **Tablet Mode**: `npm start` (Electron app)
- **WebSocket API**: ws://localhost:8765
- **NodeMCU Remote**: Upload Arduino code and connect

### Voice Commands
- "move forward/backward/left/right"
- "stop"
- "take photo"
- "where am i"
- "analyze scene"
- "autonomous mode on/off"

### API Keys Setup
Set environment variables for AI services:
```bash
export OPENAI_API_KEY="your_openai_key"
export HUGGINGFACE_API_KEY="your_huggingface_key"
```

## 🤖 AI Integration

### Free AI Services Used
1. **Hugging Face**: Object detection and image classification
2. **OpenAI GPT-3.5**: Voice command understanding (optional)
3. **Google Speech Recognition**: Voice-to-text conversion
4. **MediaPipe**: Computer vision and pose estimation

### Vision AI Capabilities
- Real-time object detection
- Scene classification
- Obstacle detection for navigation
- Environmental analysis
- Safety monitoring

## 📡 Communication Protocols

### WebSocket API
```json
{
  "command": "move",
  "params": {
    "direction": "forward",
    "speed": 1.0
  }
}
```

### Supported Commands
- `move`: Control robot movement
- `camera`: Photo/video operations
- `gps`: Location and navigation
- `ai`: AI analysis requests
- `status`: System status
- `autonomous`: Toggle autonomous mode

## 🔧 Configuration

### Robot Configuration (`config/robot.conf`)
```ini
[HARDWARE]
camera_enabled = true
servo_enabled = true
gps_enabled = true

[NETWORK]
websocket_port = 8765
http_port = 5000

[AI]
vision_enabled = true
voice_enabled = true
```

### Hardware Pin Mapping
```python
LEG_SERVOS = {
    'front_left': {'hip': 0, 'knee': 1, 'ankle': 2},
    'front_right': {'hip': 3, 'knee': 4, 'ankle': 5},
    'rear_left': {'hip': 6, 'knee': 7, 'ankle': 8},
    'rear_right': {'hip': 9, 'knee': 10, 'ankle': 11}
}
```

## 🏗️ Architecture

### System Components
```
Robotic Dog Controller
├── Hardware Layer
│   ├── Camera Controller
│   ├── Motor Controller
│   └── GPS Controller
├── AI Layer
│   ├── Vision AI
│   ├── Navigation AI
│   └── Voice AI
├── Communication Layer
│   ├── WebSocket Server
│   └── HTTP Server
└── Control Interfaces
    ├── Tablet App
    ├── NodeMCU Remote
    └── Web Interface
```

### Data Flow
1. Sensors collect environmental data
2. AI processes data for decision making
3. Navigation AI plans movement
4. Motor controller executes commands
5. Status updates sent to all connected clients

## 🧪 Testing

### Unit Tests
```bash
cd robotic_dog/tests
python3 -m pytest test_camera.py
python3 -m pytest test_motors.py
python3 -m pytest test_navigation.py
```

### Hardware Tests
```bash
# Test camera
python3 -c "from robotic_dog.hardware import CameraController; c = CameraController(); c.initialize()"

# Test servos
python3 -c "from robotic_dog.hardware import LegController; l = LegController(); l.initialize()"

# Test GPS
python3 -c "from robotic_dog.hardware import GPSController; g = GPSController(); g.initialize()"
```

## 🔐 Security

### Network Security
- WiFi hotspot with WPA2 encryption
- WebSocket connection authentication
- API rate limiting
- Input validation and sanitization

### Safety Features
- Emergency stop functionality
- Obstacle detection and avoidance
- Battery monitoring and alerts
- Servo position limits and safety checks

## 📱 Tablet Interface

The tablet interface provides a comprehensive control panel with:
- Live camera feed with AI overlay
- Joystick-style movement controls
- Status monitoring and alerts
- GPS mapping and navigation
- Voice command interface
- System configuration options

## 🎛️ NodeMCU Remote

Physical remote control features:
- Analog joystick for movement
- Dedicated stop button
- Photo capture button
- Autonomous mode toggle
- OLED status display
- WiFi connectivity indicator

## 🗺️ Navigation System

### GPS Features
- Real-time location tracking
- Waypoint navigation
- Path recording and playback
- Distance and bearing calculations
- Geofencing capabilities

### Autonomous Navigation
- Obstacle avoidance using vision
- Path planning algorithms
- Goal-seeking behavior
- Exploration mode
- Return-to-home functionality

## 🔍 Troubleshooting

### Common Issues
1. **Camera not working**: Check camera cable and enable camera interface
2. **Servos not responding**: Verify I2C connection and power supply
3. **GPS not connecting**: Check UART configuration and antenna
4. **Voice commands not working**: Test microphone and audio permissions

### Debug Commands
```bash
# Check system status
sudo systemctl status robotic-dog

# View logs
sudo journalctl -u robotic-dog -f

# Test hardware
python3 -c "from robotic_dog.core import RoboticDogController; import asyncio; asyncio.run(RoboticDogController().initialize())"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Hugging Face for providing free AI model access
- OpenAI for natural language processing capabilities
- Raspberry Pi Foundation for the amazing hardware platform
- Open source robotics community for inspiration and libraries

## 📞 Support

For support and questions:
- Open an issue on GitHub
- Join our Discord community
- Check the documentation wiki
- Email: support@roboticdog.example.com

---

**Made with ❤️ by the RUFUS and LUMA Team**