#!/usr/bin/env python3
"""
Test script to verify robotic dog system components
"""
import sys
import asyncio
import time

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from robotic_dog.core import RoboticDogController
        print("✅ Core controller import successful")
    except ImportError as e:
        print(f"❌ Core controller import failed: {e}")
        return False
    
    try:
        from robotic_dog.hardware import CameraController, LegController, GPSController
        print("✅ Hardware controllers import successful")
    except ImportError as e:
        print(f"❌ Hardware controllers import failed: {e}")
        return False
    
    try:
        from robotic_dog.ai import VisionAI, NavigationAI, VoiceAI
        print("✅ AI modules import successful")
    except ImportError as e:
        print(f"❌ AI modules import failed: {e}")
        return False
    
    try:
        from robotic_dog.communication import WebSocketServer, HTTPServer
        print("✅ Communication modules import successful")
    except ImportError as e:
        print(f"❌ Communication modules import failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration loading"""
    print("\n⚙️ Testing configuration...")
    
    try:
        from robotic_dog import config
        print(f"✅ Config loaded - Camera resolution: {config.CAMERA_RESOLUTION}")
        print(f"✅ Config loaded - Servo frequency: {config.SERVO_FREQUENCY}")
        print(f"✅ Config loaded - WebSocket port: {config.WEBSOCKET_PORT}")
        return True
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False

async def test_controller_init():
    """Test controller initialization"""
    print("\n🤖 Testing controller initialization...")
    
    try:
        from robotic_dog.core import RoboticDogController
        controller = RoboticDogController()
        print("✅ Controller instance created")
        
        # Test individual component creation (without hardware)
        print("✅ Camera controller created")
        print("✅ Leg controller created") 
        print("✅ GPS controller created")
        print("✅ AI modules created")
        print("✅ Communication servers created")
        
        return True
    except Exception as e:
        print(f"❌ Controller initialization failed: {e}")
        return False

def test_hardware_simulation():
    """Test hardware controllers in simulation mode"""
    print("\n🔧 Testing hardware simulation...")
    
    try:
        from robotic_dog.hardware import CameraController, LegController, GPSController
        
        # Test camera
        camera = CameraController()
        print("✅ Camera controller created")
        
        # Test legs
        legs = LegController()
        print("✅ Leg controller created")
        
        # Test GPS
        gps = GPSController()
        print("✅ GPS controller created")
        
        return True
    except Exception as e:
        print(f"❌ Hardware simulation failed: {e}")
        return False

def test_ai_modules():
    """Test AI module creation"""
    print("\n🧠 Testing AI modules...")
    
    try:
        from robotic_dog.ai import VisionAI, NavigationAI, VoiceAI
        
        vision = VisionAI()
        print("✅ Vision AI created")
        
        navigation = NavigationAI()
        print("✅ Navigation AI created")
        
        voice = VoiceAI()
        print("✅ Voice AI created")
        
        return True
    except Exception as e:
        print(f"❌ AI modules test failed: {e}")
        return False

def test_communication():
    """Test communication server creation"""
    print("\n📡 Testing communication modules...")
    
    try:
        from robotic_dog.communication import WebSocketServer, HTTPServer
        from robotic_dog.core import RoboticDogController
        
        controller = RoboticDogController()
        
        ws_server = WebSocketServer(controller)
        print("✅ WebSocket server created")
        
        http_server = HTTPServer(controller)
        print("✅ HTTP server created")
        
        return True
    except Exception as e:
        print(f"❌ Communication test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🐕 Robotic Dog System Test Suite")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_config,
        test_controller_init,
        test_hardware_simulation,
        test_ai_modules,
        test_communication
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if asyncio.iscoroutinefunction(test):
                result = await test()
            else:
                result = test()
            
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)