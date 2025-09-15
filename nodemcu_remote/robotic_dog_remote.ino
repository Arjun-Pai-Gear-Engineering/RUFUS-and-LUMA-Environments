/*
 * NodeMCU WiFi Remote Control for Robotic Dog
 * Hardware: ESP8266 NodeMCU with joystick, buttons, and OLED display
 */

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <SSD1306Wire.h>
#include <Wire.h>

// Pin definitions
#define JOYSTICK_X_PIN A0
#define JOYSTICK_Y_PIN A1  // Note: ESP8266 only has one ADC, this is simulated
#define JOYSTICK_BUTTON_PIN D3
#define BUTTON_1_PIN D4  // Stop button
#define BUTTON_2_PIN D5  // Photo button
#define BUTTON_3_PIN D6  // Autonomous mode toggle
#define BUTTON_4_PIN D7  // Voice command button
#define LED_PIN D0

// OLED Display
SSD1306Wire display(0x3c, D2, D1);

// WiFi Configuration
const char* ssid = "RoboticDog_Remote";
const char* password = "DogRemote123";
const char* robot_ip = "192.168.4.1";  // Robot's WiFi IP
const int robot_port = 8765;

// WebSocket client
WebSocketsClient webSocket;

// Remote state
struct RemoteState {
  int joystick_x = 512;
  int joystick_y = 512;
  bool joystick_button = false;
  bool button1 = false;  // Stop
  bool button2 = false;  // Photo
  bool button3 = false;  // Autonomous
  bool button4 = false;  // Voice
  bool robot_connected = false;
  bool autonomous_mode = false;
  float battery_level = 0;
  String robot_status = "Disconnected";
} remote;

// Timing variables
unsigned long lastCommandTime = 0;
unsigned long lastDisplayUpdate = 0;
unsigned long lastHeartbeat = 0;
const unsigned long COMMAND_INTERVAL = 100;  // 10Hz command rate
const unsigned long DISPLAY_INTERVAL = 200;  // 5Hz display update
const unsigned long HEARTBEAT_INTERVAL = 5000;  // 5 second heartbeat

void setup() {
  Serial.begin(115200);
  
  // Initialize display
  display.init();
  display.flipScreenVertically();
  display.setFont(ArialMT_Plain_10);
  display.clear();
  display.drawString(0, 0, "Robotic Dog Remote");
  display.drawString(0, 20, "Initializing...");
  display.display();
  
  // Initialize pins
  pinMode(JOYSTICK_BUTTON_PIN, INPUT_PULLUP);
  pinMode(BUTTON_1_PIN, INPUT_PULLUP);
  pinMode(BUTTON_2_PIN, INPUT_PULLUP);
  pinMode(BUTTON_3_PIN, INPUT_PULLUP);
  pinMode(BUTTON_4_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  
  // Initialize WiFi
  setupWiFi();
  
  // Initialize WebSocket
  setupWebSocket();
  
  Serial.println("NodeMCU Remote Control initialized");
}

void loop() {
  // Handle WebSocket events
  webSocket.loop();
  
  // Read inputs
  readInputs();
  
  // Send commands to robot
  if (millis() - lastCommandTime > COMMAND_INTERVAL) {
    sendRobotCommand();
    lastCommandTime = millis();
  }
  
  // Update display
  if (millis() - lastDisplayUpdate > DISPLAY_INTERVAL) {
    updateDisplay();
    lastDisplayUpdate = millis();
  }
  
  // Send heartbeat
  if (millis() - lastHeartbeat > HEARTBEAT_INTERVAL) {
    sendHeartbeat();
    lastHeartbeat = millis();
  }
  
  // Update status LED
  digitalWrite(LED_PIN, remote.robot_connected ? HIGH : LOW);
}

void setupWiFi() {
  display.clear();
  display.drawString(0, 0, "Connecting WiFi...");
  display.display();
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.print("Connected to ");
    Serial.println(ssid);
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
    
    display.clear();
    display.drawString(0, 0, "WiFi Connected");
    display.drawString(0, 20, WiFi.localIP().toString());
    display.display();
  } else {
    display.clear();
    display.drawString(0, 0, "WiFi Failed");
    display.drawString(0, 20, "Check credentials");
    display.display();
    Serial.println("WiFi connection failed");
  }
  
  delay(2000);
}

void setupWebSocket() {
  webSocket.begin(robot_ip, robot_port, "/");
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(5000);
  
  Serial.println("WebSocket client configured");
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch(type) {
    case WStype_DISCONNECTED:
      remote.robot_connected = false;
      remote.robot_status = "Disconnected";
      Serial.println("WebSocket Disconnected");
      break;
      
    case WStype_CONNECTED:
      remote.robot_connected = true;
      remote.robot_status = "Connected";
      Serial.printf("WebSocket Connected to: %s\n", payload);
      
      // Send initial status request
      sendStatusRequest();
      break;
      
    case WStype_TEXT:
      handleRobotMessage((char*)payload);
      break;
      
    case WStype_ERROR:
      remote.robot_connected = false;
      remote.robot_status = "Error";
      Serial.printf("WebSocket Error: %s\n", payload);
      break;
      
    default:
      break;
  }
}

void readInputs() {
  // Read joystick (simulated Y-axis since ESP8266 has only one ADC)
  remote.joystick_x = analogRead(JOYSTICK_X_PIN);
  // For Y-axis, we'll use digital pins to simulate up/down
  // In real implementation, use an I2C ADC or multiplexer
  
  // Read buttons (active low with pull-up)
  remote.joystick_button = !digitalRead(JOYSTICK_BUTTON_PIN);
  
  bool button1_new = !digitalRead(BUTTON_1_PIN);
  bool button2_new = !digitalRead(BUTTON_2_PIN);
  bool button3_new = !digitalRead(BUTTON_3_PIN);
  bool button4_new = !digitalRead(BUTTON_4_PIN);
  
  // Detect button press edges (not held)
  if (button1_new && !remote.button1) {
    // Stop button pressed
    sendStopCommand();
  }
  
  if (button2_new && !remote.button2) {
    // Photo button pressed
    sendPhotoCommand();
  }
  
  if (button3_new && !remote.button3) {
    // Autonomous toggle pressed
    toggleAutonomousMode();
  }
  
  if (button4_new && !remote.button4) {
    // Voice command button pressed
    sendVoiceCommand();
  }
  
  // Update button states
  remote.button1 = button1_new;
  remote.button2 = button2_new;
  remote.button3 = button3_new;
  remote.button4 = button4_new;
}

void sendRobotCommand() {
  if (!remote.robot_connected) return;
  
  // Convert joystick values to movement commands
  int x_center = 512;
  int deadzone = 100;
  
  String command = "";
  String direction = "";
  
  if (remote.joystick_x < (x_center - deadzone)) {
    direction = "left";
  } else if (remote.joystick_x > (x_center + deadzone)) {
    direction = "right";
  }
  
  // For forward/backward, we'd normally use Y-axis
  // Since we only have one ADC, we'll use button combinations
  // or implement with digital pins
  
  if (direction != "") {
    DynamicJsonDocument doc(200);
    doc["command"] = "move";
    doc["params"]["direction"] = direction;
    doc["params"]["speed"] = calculateSpeed();
    
    String jsonString;
    serializeJson(doc, jsonString);
    webSocket.sendTXT(jsonString);
  }
}

float calculateSpeed() {
  // Calculate speed based on joystick position
  int distance = abs(remote.joystick_x - 512);
  float speed = (float)distance / 512.0;
  return constrain(speed, 0.0, 1.0);
}

void sendStopCommand() {
  if (!remote.robot_connected) return;
  
  DynamicJsonDocument doc(200);
  doc["command"] = "move";
  doc["params"]["direction"] = "stop";
  
  String jsonString;
  serializeJson(doc, jsonString);
  webSocket.sendTXT(jsonString);
  
  Serial.println("Stop command sent");
}

void sendPhotoCommand() {
  if (!remote.robot_connected) return;
  
  DynamicJsonDocument doc(200);
  doc["command"] = "camera";
  doc["params"]["action"] = "photo";
  
  String jsonString;
  serializeJson(doc, jsonString);
  webSocket.sendTXT(jsonString);
  
  Serial.println("Photo command sent");
}

void toggleAutonomousMode() {
  if (!remote.robot_connected) return;
  
  remote.autonomous_mode = !remote.autonomous_mode;
  
  DynamicJsonDocument doc(200);
  doc["command"] = "autonomous";
  doc["params"]["enabled"] = remote.autonomous_mode;
  
  String jsonString;
  serializeJson(doc, jsonString);
  webSocket.sendTXT(jsonString);
  
  Serial.printf("Autonomous mode: %s\n", remote.autonomous_mode ? "ON" : "OFF");
}

void sendVoiceCommand() {
  if (!remote.robot_connected) return;
  
  // Simulate voice command - in real implementation, 
  // this could trigger voice recording/processing
  DynamicJsonDocument doc(200);
  doc["command"] = "ai";
  doc["params"]["action"] = "analyze_scene";
  
  String jsonString;
  serializeJson(doc, jsonString);
  webSocket.sendTXT(jsonString);
  
  Serial.println("Voice/AI command sent");
}

void sendStatusRequest() {
  if (!remote.robot_connected) return;
  
  DynamicJsonDocument doc(100);
  doc["command"] = "status";
  
  String jsonString;
  serializeJson(doc, jsonString);
  webSocket.sendTXT(jsonString);
}

void sendHeartbeat() {
  if (!remote.robot_connected) return;
  
  DynamicJsonDocument doc(150);
  doc["command"] = "heartbeat";
  doc["params"]["remote_id"] = "nodemcu_001";
  doc["params"]["signal_strength"] = WiFi.RSSI();
  
  String jsonString;
  serializeJson(doc, jsonString);
  webSocket.sendTXT(jsonString);
}

void handleRobotMessage(const char* message) {
  DynamicJsonDocument doc(1024);
  DeserializationError error = deserializeJson(doc, message);
  
  if (error) {
    Serial.print("JSON parsing failed: ");
    Serial.println(error.c_str());
    return;
  }
  
  // Handle status updates
  if (doc.containsKey("robot_status")) {
    JsonObject status = doc["robot_status"];
    
    if (status.containsKey("battery")) {
      remote.battery_level = status["battery"];
    }
    
    if (status.containsKey("autonomous_mode")) {
      remote.autonomous_mode = status["autonomous_mode"];
    }
  }
  
  // Handle command responses
  if (doc.containsKey("status")) {
    String status = doc["status"];
    if (status == "success") {
      remote.robot_status = "Command OK";
    } else {
      remote.robot_status = "Command Error";
    }
  }
}

void updateDisplay() {
  display.clear();
  
  // Title
  display.setFont(ArialMT_Plain_10);
  display.drawString(0, 0, "🐕 Dog Remote");
  
  // Connection status
  display.setFont(ArialMT_Plain_10);
  if (remote.robot_connected) {
    display.drawString(0, 15, "🟢 Connected");
  } else {
    display.drawString(0, 15, "🔴 Disconnected");
  }
  
  // Battery level
  if (remote.battery_level > 0) {
    display.drawString(0, 30, "🔋 " + String((int)remote.battery_level) + "%");
  }
  
  // Mode
  display.drawString(0, 45, remote.autonomous_mode ? "🤖 Auto" : "🎮 Manual");
  
  // Joystick position
  display.drawString(80, 15, "X:" + String(remote.joystick_x));
  
  // Button states
  String buttons = "";
  if (remote.button1) buttons += "S ";
  if (remote.button2) buttons += "P ";
  if (remote.button3) buttons += "A ";
  if (remote.button4) buttons += "V ";
  if (buttons.length() > 0) {
    display.drawString(80, 30, buttons);
  }
  
  // Status message
  display.setFont(ArialMT_Plain_10);
  display.drawString(0, 55, remote.robot_status.substring(0, 15));
  
  display.display();
}

// Additional functions for expanded remote features

void setupWebServer() {
  // Optional: Set up a web server on the remote for configuration
  // This would allow configuring WiFi credentials, robot IP, etc.
}

void handleOTA() {
  // Optional: Over-the-air updates for the remote firmware
}

void deepSleep() {
  // Optional: Put ESP8266 into deep sleep to save battery
  // Wake up on button press or timer
}