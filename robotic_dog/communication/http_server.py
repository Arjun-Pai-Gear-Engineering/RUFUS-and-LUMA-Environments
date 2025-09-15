"""
HTTP server for web interface and REST API
"""
from flask import Flask, jsonify, request, send_file
from flask_socketio import SocketIO, emit
import os
import base64
from ..config import HTTP_PORT

class HTTPServer:
    def __init__(self, robot_controller):
        self.robot_controller = robot_controller
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'robotic_dog_secret_key'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self.setup_routes()
        self.setup_socketio_events()
    
    def setup_routes(self):
        """Setup HTTP routes"""
        
        @self.app.route('/')
        def index():
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Robotic Dog Control</title>
                <style>
                    body { font-family: Arial; margin: 20px; background: #f0f0f0; }
                    .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
                    .control-panel { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 20px 0; }
                    .btn { padding: 15px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
                    .btn-primary { background: #007bff; color: white; }
                    .btn-danger { background: #dc3545; color: white; }
                    .btn-success { background: #28a745; color: white; }
                    .status-panel { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }
                    .camera-view { text-align: center; margin: 20px 0; }
                    #camera-feed { max-width: 100%; border-radius: 5px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🐕 Robotic Dog Control Panel</h1>
                    
                    <div class="status-panel">
                        <h3>Status</h3>
                        <div id="status">Connecting...</div>
                    </div>
                    
                    <div class="camera-view">
                        <h3>Camera Feed</h3>
                        <img id="camera-feed" src="/api/camera/feed" alt="Camera Feed">
                    </div>
                    
                    <div class="control-panel">
                        <button class="btn btn-primary" onclick="sendCommand('move', {direction: 'forward'})">⬆️ Forward</button>
                        <button class="btn btn-primary" onclick="sendCommand('move', {direction: 'left'})">⬅️ Left</button>
                        <button class="btn btn-primary" onclick="sendCommand('move', {direction: 'right'})">➡️ Right</button>
                        <button class="btn btn-primary" onclick="sendCommand('move', {direction: 'backward'})">⬇️ Backward</button>
                        <button class="btn btn-danger" onclick="sendCommand('move', {direction: 'stop'})">🛑 Stop</button>
                        <button class="btn btn-success" onclick="sendCommand('camera', {action: 'photo'})">📷 Photo</button>
                    </div>
                    
                    <div class="control-panel">
                        <button class="btn btn-success" onclick="sendCommand('gps', {action: 'get_location'})">📍 Get Location</button>
                        <button class="btn btn-success" onclick="sendCommand('ai', {action: 'analyze_scene'})">🤖 Analyze Scene</button>
                        <button class="btn btn-success" onclick="sendCommand('status')">📊 Get Status</button>
                    </div>
                </div>
                
                <script src="/static/socket.io.js"></script>
                <script>
                    const socket = io();
                    
                    socket.on('connect', function() {
                        document.getElementById('status').innerHTML = '✅ Connected';
                    });
                    
                    socket.on('status_update', function(data) {
                        document.getElementById('status').innerHTML = 
                            '✅ Connected - Battery: ' + (data.battery || 'N/A') + 
                            '% - GPS: ' + (data.gps_status || 'N/A');
                    });
                    
                    function sendCommand(command, params = {}) {
                        socket.emit('command', {command: command, params: params});
                    }
                    
                    // Refresh camera feed
                    setInterval(() => {
                        document.getElementById('camera-feed').src = 
                            '/api/camera/feed?' + new Date().getTime();
                    }, 1000);
                </script>
            </body>
            </html>
            """
        
        @self.app.route('/api/status')
        def get_status():
            status = self.robot_controller.get_status()
            return jsonify(status)
        
        @self.app.route('/api/camera/feed')
        def camera_feed():
            frame = self.robot_controller.get_camera_frame()
            if frame is not None:
                return send_file(frame, mimetype='image/jpeg')
            else:
                return "No camera feed available", 404
        
        @self.app.route('/api/command', methods=['POST'])
        def handle_command():
            data = request.json
            command = data.get('command')
            params = data.get('params', {})
            
            try:
                result = self.robot_controller.execute_command(command, params)
                return jsonify({'status': 'success', 'result': result})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 400
    
    def setup_socketio_events(self):
        """Setup SocketIO events"""
        
        @self.socketio.on('connect')
        def handle_connect():
            print(f"Client connected: {request.sid}")
            status = self.robot_controller.get_status()
            emit('status_update', status)
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('command')
        def handle_command(data):
            command = data.get('command')
            params = data.get('params', {})
            
            try:
                result = self.robot_controller.execute_command(command, params)
                emit('command_result', {'status': 'success', 'result': result})
                
                # Broadcast status update
                status = self.robot_controller.get_status()
                self.socketio.emit('status_update', status)
                
            except Exception as e:
                emit('command_result', {'status': 'error', 'message': str(e)})
    
    def start_server(self):
        """Start the HTTP server"""
        print(f"HTTP server starting on port {HTTP_PORT}")
        self.socketio.run(self.app, host='0.0.0.0', port=HTTP_PORT, debug=False)
    
    def cleanup(self):
        """Cleanup server resources"""
        pass