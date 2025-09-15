"""
Configuration settings for the robotic dog
"""
import os

# Hardware Configuration
CAMERA_RESOLUTION = (640, 480)
CAMERA_FRAMERATE = 30
SERVO_MIN_PULSE = 500
SERVO_MAX_PULSE = 2500
SERVO_FREQUENCY = 50

# Leg servo pin mappings (using PCA9685 servo driver)
LEG_SERVOS = {
    'front_left': {'hip': 0, 'knee': 1, 'ankle': 2},
    'front_right': {'hip': 3, 'knee': 4, 'ankle': 5},
    'rear_left': {'hip': 6, 'knee': 7, 'ankle': 8},
    'rear_right': {'hip': 9, 'knee': 10, 'ankle': 11}
}

# Movement parameters
DEFAULT_STEP_HEIGHT = 30  # mm
DEFAULT_STEP_LENGTH = 50  # mm
DEFAULT_SPEED = 1.0  # multiplier

# Communication
WEBSOCKET_PORT = 8765
HTTP_PORT = 5000
NODEMCU_PORT = 8080

# GPS Configuration
GPS_DEVICE = '/dev/ttyAMA0'
GPS_BAUDRATE = 9600

# AI Configuration
VISION_MODEL_PATH = 'models/vision_model.tflite'
NAVIGATION_CONFIDENCE_THRESHOLD = 0.7

# Free AI API Keys (you'll need to replace with actual keys)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', '')

# Camera stream settings
STREAM_PORT = 8554
STREAM_PATH = '/stream'

# Logging
LOG_LEVEL = 'INFO'
LOG_FILE = '/var/log/robotic_dog.log'