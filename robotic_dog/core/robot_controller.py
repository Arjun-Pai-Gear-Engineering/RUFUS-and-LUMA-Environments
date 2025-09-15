"""
Main robotic dog controller that coordinates all subsystems
"""
import asyncio
import threading
import time
import json
import cv2
import numpy as np
from .hardware import CameraController, LegController, GPSController
from .ai import VisionAI, NavigationAI, VoiceAI
from .communication import WebSocketServer, HTTPServer
from .config import *


class RoboticDogController:
    def __init__(self):
        # Hardware controllers
        self.camera = CameraController()
        self.legs = LegController()
        self.gps = GPSController()
        
        # AI modules
        self.vision_ai = VisionAI()
        self.navigation_ai = NavigationAI()
        self.voice_ai = VoiceAI()
        
        # Communication servers
        self.websocket_server = WebSocketServer(self)
        self.http_server = HTTPServer(self)
        
        # System state
        self.running = False
        self.autonomous_mode = False
        self.current_command = None
        self.system_status = {
            'battery': 100,
            'temperature': 25,
            'wifi_connected': True,
            'camera_active': False,
            'gps_active': False,
            'movement_active': False
        }
        
        # Performance monitoring
        self.last_frame_time = 0
        self.fps = 0
        self.command_history = []
        
    async def initialize(self):
        """Initialize all subsystems"""
        print("🐕 Initializing Robotic Dog Controller...")
        
        initialization_results = {}
        
        # Initialize hardware
        print("📷 Initializing camera...")
        initialization_results['camera'] = self.camera.initialize()
        
        print("🦿 Initializing leg controllers...")
        initialization_results['legs'] = self.legs.initialize()
        
        print("🛰️ Initializing GPS...")
        initialization_results['gps'] = self.gps.initialize()
        
        # Start subsystem services
        if initialization_results['camera']:
            self.camera.start_streaming()
            self.system_status['camera_active'] = True
        
        if initialization_results['gps']:
            self.gps.start_tracking()
            self.system_status['gps_active'] = True
        
        # Start communication servers
        print("🌐 Starting communication servers...")
        self.websocket_server.start_server()
        
        # Start main control loop
        self.running = True
        asyncio.create_task(self.main_control_loop())
        
        print("✅ Robotic Dog Controller initialized successfully!")
        print(f"📊 Initialization results: {initialization_results}")
        
        return all(initialization_results.values())
    
    async def main_control_loop(self):
        """Main control loop for autonomous operations"""
        print("🔄 Starting main control loop...")
        
        while self.running:
            try:
                # Update system status
                await self.update_system_status()
                
                # Process current frame for AI analysis
                if self.system_status['camera_active']:
                    await self.process_camera_frame()
                
                # Handle autonomous navigation
                if self.autonomous_mode:
                    await self.autonomous_navigation_step()
                
                # Listen for voice commands
                await self.process_voice_commands()
                
                # Sleep to maintain reasonable loop frequency
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Error in main control loop: {e}")
                await asyncio.sleep(1)
    
    async def update_system_status(self):
        """Update system status information"""
        # Simulate battery drain (would be real sensor in actual implementation)
        if self.system_status['movement_active']:
            self.system_status['battery'] = max(0, self.system_status['battery'] - 0.01)
        
        # Update temperature (simulated)
        self.system_status['temperature'] = 25 + np.random.normal(0, 2)
        
        # Update GPS status
        location = self.gps.get_current_location()
        self.system_status['gps_location'] = location
        
        # Update FPS
        current_time = time.time()
        if self.last_frame_time > 0:
            self.fps = 1.0 / (current_time - self.last_frame_time)
        self.last_frame_time = current_time
    
    async def process_camera_frame(self):
        """Process current camera frame with AI"""
        frame = self.camera.get_frame()
        if frame is not None:
            # Run vision AI analysis
            analysis = await self.vision_ai.analyze_frame_complete(frame)
            
            if analysis:
                # Store analysis for other systems to use
                self.current_frame_analysis = analysis
                
                # Update navigation AI with obstacle information
                obstacles = analysis.get('obstacles', [])
                if obstacles:
                    self.navigation_ai.obstacle_map.update({
                        f"vision_{time.time()}": {
                            'obstacles': obstacles,
                            'timestamp': time.time()
                        }
                    })
    
    async def autonomous_navigation_step(self):
        """Execute one step of autonomous navigation"""
        location = self.gps.get_current_location()
        if not location:
            return
        
        # Get current heading (would come from compass in real implementation)
        current_heading = location.get('heading', 0)
        
        # Get vision obstacles
        vision_obstacles = getattr(self, 'current_frame_analysis', {}).get('obstacles', [])
        
        # Get next movement command from navigation AI
        nav_command = self.navigation_ai.get_next_movement_command(
            location['latitude'],
            location['longitude'],
            current_heading,
            vision_obstacles
        )
        
        if nav_command:
            await self.execute_navigation_command(nav_command)
    
    async def execute_navigation_command(self, nav_command):
        """Execute navigation command"""
        command = nav_command.get('command')
        
        if command == 'forward':
            speed = nav_command.get('speed', 1.0)
            self.move_forward(speed)
        elif command == 'turn_left':
            angle = nav_command.get('angle', 30)
            self.turn_left()
        elif command == 'turn_right':
            angle = nav_command.get('angle', 30)
            self.turn_right()
        elif command == 'stop':
            self.stop()
            
            # Check if goal was reached
            if nav_command.get('goal_achieved'):
                self.autonomous_mode = False
                print("🎯 Navigation goal achieved!")
    
    async def process_voice_commands(self):
        """Process voice commands if available"""
        try:
            # Listen for voice command (non-blocking)
            voice_text = self.voice_ai.listen_for_command(timeout=1)
            
            if voice_text:
                print(f"🎤 Voice command received: {voice_text}")
                
                # Process the command
                command_result = await self.voice_ai.process_voice_command(voice_text)
                
                if command_result:
                    # Execute the command
                    await self.execute_command(
                        command_result.get('command'),
                        command_result.get('params', {})
                    )
                    
                    # Generate voice response
                    response = self.voice_ai.generate_response(command_result)
                    print(f"🔊 Response: {response}")
                    
        except Exception as e:
            print(f"❌ Voice command processing error: {e}")
    
    # Movement control methods
    def move_forward(self, speed=1.0):
        """Move robot forward"""
        self.legs.walk_forward(speed=speed)
        self.system_status['movement_active'] = True
        self.current_command = {'command': 'forward', 'speed': speed}
    
    def move_backward(self, speed=1.0):
        """Move robot backward"""
        self.legs.walk_backward(speed=speed)
        self.system_status['movement_active'] = True
        self.current_command = {'command': 'backward', 'speed': speed}
    
    def turn_left(self, speed=1.0):
        """Turn robot left"""
        self.legs.turn_left(speed=speed)
        self.system_status['movement_active'] = True
        self.current_command = {'command': 'left', 'speed': speed}
    
    def turn_right(self, speed=1.0):
        """Turn robot right"""
        self.legs.turn_right(speed=speed)
        self.system_status['movement_active'] = True
        self.current_command = {'command': 'right', 'speed': speed}
    
    def stop(self):
        """Stop all movement"""
        self.legs.stop_movement()
        self.system_status['movement_active'] = False
        self.current_command = {'command': 'stop'}
    
    # Camera control methods
    def take_photo(self):
        """Take a photo"""
        filename = self.camera.take_photo()
        return filename
    
    def start_camera_stream(self):
        """Start camera streaming"""
        return self.camera.start_streaming()
    
    def stop_camera_stream(self):
        """Stop camera streaming"""
        self.camera.stop_streaming()
    
    def get_camera_frame(self):
        """Get current camera frame"""
        return self.camera.get_frame()
    
    # GPS and navigation methods
    def get_current_location(self):
        """Get current GPS location"""
        return self.gps.get_current_location()
    
    def navigate_to(self, target_lat, target_lon):
        """Navigate to specific coordinates"""
        self.navigation_ai.set_goal(target_lat, target_lon)
        location = self.get_current_location()
        
        if location:
            path = self.navigation_ai.calculate_path_to_goal(
                location['latitude'], location['longitude']
            )
            
            # Enable autonomous mode for navigation
            self.autonomous_mode = True
            
            return path
        
        return None
    
    def set_autonomous_mode(self, enabled):
        """Enable or disable autonomous mode"""
        self.autonomous_mode = enabled
        if enabled:
            print("🤖 Autonomous mode enabled")
        else:
            print("🎮 Manual control mode enabled")
    
    # AI methods
    async def analyze_current_scene(self):
        """Analyze current camera scene"""
        frame = self.get_camera_frame()
        if frame is not None:
            analysis = await self.vision_ai.analyze_frame_complete(frame)
            return analysis
        return None
    
    async def process_voice_command(self, text):
        """Process voice command text"""
        return await self.voice_ai.process_voice_command(text)
    
    # Command execution
    async def execute_command(self, command, params):
        """Execute a command with parameters"""
        try:
            if command == 'move':
                direction = params.get('direction')
                speed = params.get('speed', 1.0)
                
                if direction == 'forward':
                    self.move_forward(speed)
                elif direction == 'backward':
                    self.move_backward(speed)
                elif direction == 'left':
                    self.turn_left(speed)
                elif direction == 'right':
                    self.turn_right(speed)
                elif direction == 'stop':
                    self.stop()
                
                return {'status': 'success', 'command': command}
            
            elif command == 'camera':
                action = params.get('action')
                
                if action == 'photo':
                    filename = self.take_photo()
                    return {'status': 'success', 'filename': filename}
                elif action == 'start_stream':
                    self.start_camera_stream()
                    return {'status': 'success'}
                elif action == 'stop_stream':
                    self.stop_camera_stream()
                    return {'status': 'success'}
            
            elif command == 'gps':
                action = params.get('action')
                
                if action == 'get_location':
                    location = self.get_current_location()
                    return {'status': 'success', 'location': location}
                elif action == 'navigate':
                    lat = params.get('latitude')
                    lon = params.get('longitude')
                    if lat and lon:
                        path = self.navigate_to(lat, lon)
                        return {'status': 'success', 'path': path}
            
            elif command == 'ai':
                action = params.get('action')
                
                if action == 'analyze_scene':
                    analysis = await self.analyze_current_scene()
                    return {'status': 'success', 'analysis': analysis}
            
            elif command == 'status':
                return {'status': 'success', 'robot_status': self.get_status()}
            
            elif command == 'autonomous':
                enabled = params.get('enabled', False)
                self.set_autonomous_mode(enabled)
                return {'status': 'success', 'autonomous_mode': enabled}
            
            else:
                return {'status': 'error', 'message': f'Unknown command: {command}'}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def get_status(self):
        """Get comprehensive system status"""
        status = self.system_status.copy()
        status.update({
            'current_command': self.current_command,
            'autonomous_mode': self.autonomous_mode,
            'fps': round(self.fps, 1),
            'leg_positions': self.legs.get_current_positions(),
            'navigation_goal': self.navigation_ai.current_goal,
            'uptime': time.time() - getattr(self, 'start_time', time.time())
        })
        return status
    
    def start_http_server(self):
        """Start HTTP server in separate thread"""
        def run_server():
            self.http_server.start_server()
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
    
    async def shutdown(self):
        """Shutdown all systems gracefully"""
        print("🛑 Shutting down Robotic Dog Controller...")
        
        self.running = False
        self.autonomous_mode = False
        
        # Stop movement
        self.stop()
        
        # Cleanup hardware
        self.camera.cleanup()
        self.legs.cleanup()
        self.gps.cleanup()
        
        # Cleanup communication
        self.websocket_server.cleanup()
        self.http_server.cleanup()
        
        print("✅ Shutdown complete")


# Set start time when module is imported
import time
_start_time = time.time()