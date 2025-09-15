"""
WebSocket server for real-time communication with tablet and remote control
"""
import asyncio
import websockets
import json
import threading
from ..config import WEBSOCKET_PORT

class WebSocketServer:
    def __init__(self, robot_controller):
        self.robot_controller = robot_controller
        self.clients = set()
        self.running = False
        self.server = None
        
    async def register_client(self, websocket, path):
        """Register a new client connection"""
        self.clients.add(websocket)
        print(f"Client connected: {websocket.remote_address}")
        
        try:
            # Send initial status
            await self.send_status_update(websocket)
            
            async for message in websocket:
                await self.handle_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            print(f"Client disconnected: {websocket.remote_address}")
    
    async def handle_message(self, websocket, message):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            command = data.get('command')
            params = data.get('params', {})
            
            response = await self.process_command(command, params)
            
            # Send response back to client
            await websocket.send(json.dumps(response))
            
            # Broadcast status update to all clients
            await self.broadcast_status()
            
        except Exception as e:
            error_response = {
                'status': 'error',
                'message': str(e)
            }
            await websocket.send(json.dumps(error_response))
    
    async def process_command(self, command, params):
        """Process robot control commands"""
        try:
            if command == 'move':
                direction = params.get('direction')
                speed = params.get('speed', 1.0)
                
                if direction == 'forward':
                    self.robot_controller.move_forward(speed)
                elif direction == 'backward':
                    self.robot_controller.move_backward(speed)
                elif direction == 'left':
                    self.robot_controller.turn_left(speed)
                elif direction == 'right':
                    self.robot_controller.turn_right(speed)
                elif direction == 'stop':
                    self.robot_controller.stop()
                
                return {'status': 'success', 'command': command}
            
            elif command == 'camera':
                action = params.get('action')
                
                if action == 'photo':
                    filename = self.robot_controller.take_photo()
                    return {'status': 'success', 'filename': filename}
                elif action == 'start_stream':
                    self.robot_controller.start_camera_stream()
                    return {'status': 'success', 'message': 'Stream started'}
                elif action == 'stop_stream':
                    self.robot_controller.stop_camera_stream()
                    return {'status': 'success', 'message': 'Stream stopped'}
            
            elif command == 'gps':
                action = params.get('action')
                
                if action == 'get_location':
                    location = self.robot_controller.get_current_location()
                    return {'status': 'success', 'location': location}
                elif action == 'navigate':
                    target_lat = params.get('latitude')
                    target_lon = params.get('longitude')
                    navigation = self.robot_controller.navigate_to(target_lat, target_lon)
                    return {'status': 'success', 'navigation': navigation}
            
            elif command == 'status':
                status = self.robot_controller.get_status()
                return {'status': 'success', 'robot_status': status}
            
            elif command == 'ai':
                action = params.get('action')
                
                if action == 'analyze_scene':
                    analysis = await self.robot_controller.analyze_current_scene()
                    return {'status': 'success', 'analysis': analysis}
                elif action == 'voice_command':
                    text = params.get('text')
                    result = await self.robot_controller.process_voice_command(text)
                    return {'status': 'success', 'result': result}
            
            else:
                return {'status': 'error', 'message': f'Unknown command: {command}'}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    async def send_status_update(self, websocket):
        """Send status update to specific client"""
        try:
            status = self.robot_controller.get_status()
            message = {
                'type': 'status_update',
                'data': status
            }
            await websocket.send(json.dumps(message))
        except Exception as e:
            print(f"Error sending status update: {e}")
    
    async def broadcast_status(self):
        """Broadcast status update to all connected clients"""
        if self.clients:
            status = self.robot_controller.get_status()
            message = {
                'type': 'status_update',
                'data': status
            }
            
            # Send to all clients
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in self.clients],
                return_exceptions=True
            )
    
    async def broadcast_camera_frame(self, frame_data):
        """Broadcast camera frame to all clients"""
        if self.clients:
            message = {
                'type': 'camera_frame',
                'data': frame_data
            }
            
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in self.clients],
                return_exceptions=True
            )
    
    def start_server(self):
        """Start the WebSocket server"""
        self.running = True
        
        def run_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            start_server = websockets.serve(
                self.register_client, 
                "0.0.0.0", 
                WEBSOCKET_PORT
            )
            
            self.server = loop.run_until_complete(start_server)
            print(f"WebSocket server started on port {WEBSOCKET_PORT}")
            
            try:
                loop.run_forever()
            except KeyboardInterrupt:
                pass
            finally:
                loop.close()
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        return True
    
    def stop_server(self):
        """Stop the WebSocket server"""
        self.running = False
        if self.server:
            self.server.close()
    
    def cleanup(self):
        """Cleanup server resources"""
        self.stop_server()