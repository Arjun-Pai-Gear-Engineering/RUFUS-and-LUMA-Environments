#!/usr/bin/env python3
"""
Main entry point for the Robotic Dog Controller
Run this script to start the robotic dog system
"""
import asyncio
import signal
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from robotic_dog.core import RoboticDogController
from robotic_dog.config import HTTP_PORT, WEBSOCKET_PORT


class RoboticDogApp:
    def __init__(self):
        self.controller = RoboticDogController()
        self.running = False
    
    async def start(self):
        """Start the robotic dog application"""
        print("🐕 Starting Robotic Dog Application...")
        print("=" * 50)
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # Initialize the controller
            success = await self.controller.initialize()
            
            if not success:
                print("❌ Failed to initialize robotic dog controller")
                return False
            
            # Start HTTP server in background
            self.controller.start_http_server()
            
            # Print access information
            print("\n🌐 Access Information:")
            print(f"📱 Web Control Panel: http://localhost:{HTTP_PORT}")
            print(f"🔌 WebSocket Server: ws://localhost:{WEBSOCKET_PORT}")
            print("\n📋 Available Voice Commands:")
            print("  • 'move forward/backward/left/right'")
            print("  • 'stop'")
            print("  • 'take photo'")
            print("  • 'where am i'")
            print("  • 'analyze scene'")
            print("  • 'status'")
            
            print("\n🎮 Control Methods:")
            print("  1. Web browser control panel")
            print("  2. Voice commands (if microphone available)")
            print("  3. WebSocket API for custom clients")
            print("  4. Tablet app integration")
            print("  5. NodeMCU remote control")
            
            print("\n✅ Robotic Dog is ready!")
            print("Press Ctrl+C to shutdown gracefully")
            print("=" * 50)
            
            self.running = True
            
            # Keep the application running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"❌ Error starting application: {e}")
            return False
        
        return True
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.running = False
        
        # Create shutdown task
        asyncio.create_task(self.shutdown())
    
    async def shutdown(self):
        """Shutdown the application"""
        print("🔄 Shutting down robotic dog...")
        await self.controller.shutdown()
        self.running = False
        print("👋 Goodbye!")


async def main():
    """Main application function"""
    app = RoboticDogApp()
    await app.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        print("🏁 Application ended")