"""
Camera control module for robotic dog
Handles RPi camera operations, streaming, and computer vision
"""
import cv2
import numpy as np
import threading
import time
from ..config import CAMERA_RESOLUTION, CAMERA_FRAMERATE, STREAM_PORT

try:
    from picamera import PiCamera
    from picamera.array import PiRGBArray
    PICAMERA_AVAILABLE = True
except ImportError:
    print("Warning: PiCamera not available, using OpenCV fallback")
    PICAMERA_AVAILABLE = False


class CameraController:
    def __init__(self):
        self.camera = None
        self.stream = None
        self.frame = None
        self.frame_lock = threading.Lock()
        self.streaming = False
        self.recording = False
        
    def initialize(self):
        """Initialize camera system"""
        try:
            if PICAMERA_AVAILABLE:
                self.camera = PiCamera()
                self.camera.resolution = CAMERA_RESOLUTION
                self.camera.framerate = CAMERA_FRAMERATE
                self.camera.rotation = 0
                self.stream = PiRGBArray(self.camera, size=CAMERA_RESOLUTION)
                time.sleep(2)  # Camera warm-up
            else:
                # Fallback to USB camera
                self.camera = cv2.VideoCapture(0)
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_RESOLUTION[0])
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_RESOLUTION[1])
                self.camera.set(cv2.CAP_PROP_FPS, CAMERA_FRAMERATE)
            
            print("Camera initialized successfully")
            return True
            
        except Exception as e:
            print(f"Failed to initialize camera: {e}")
            return False
    
    def start_streaming(self):
        """Start video streaming"""
        if not self.camera:
            return False
            
        self.streaming = True
        threading.Thread(target=self._stream_worker, daemon=True).start()
        return True
    
    def stop_streaming(self):
        """Stop video streaming"""
        self.streaming = False
    
    def _stream_worker(self):
        """Worker thread for continuous frame capture"""
        if PICAMERA_AVAILABLE and self.stream:
            for frame in self.camera.capture_continuous(self.stream, format="bgr", use_video_port=True):
                if not self.streaming:
                    break
                    
                with self.frame_lock:
                    self.frame = frame.array.copy()
                
                self.stream.truncate(0)
                time.sleep(0.03)  # ~30 FPS
        else:
            # USB camera fallback
            while self.streaming:
                ret, frame = self.camera.read()
                if ret:
                    with self.frame_lock:
                        self.frame = frame
                time.sleep(0.03)
    
    def get_frame(self):
        """Get current frame"""
        with self.frame_lock:
            return self.frame.copy() if self.frame is not None else None
    
    def take_photo(self, filename=None):
        """Take a photo"""
        if not filename:
            filename = f"photo_{int(time.time())}.jpg"
            
        frame = self.get_frame()
        if frame is not None:
            cv2.imwrite(filename, frame)
            return filename
        return None
    
    def start_recording(self, filename=None):
        """Start video recording"""
        if not filename:
            filename = f"video_{int(time.time())}.mp4"
            
        # Implementation depends on requirements
        self.recording = True
        return filename
    
    def stop_recording(self):
        """Stop video recording"""
        self.recording = False
    
    def detect_objects(self, frame=None):
        """Basic object detection using OpenCV"""
        if frame is None:
            frame = self.get_frame()
            
        if frame is None:
            return []
        
        # Simple color-based object detection
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Define color ranges for common objects
        color_ranges = {
            'red': [(0, 50, 50), (10, 255, 255)],
            'blue': [(100, 50, 50), (130, 255, 255)],
            'green': [(40, 50, 50), (80, 255, 255)]
        }
        
        detected_objects = []
        
        for color_name, (lower, upper) in color_ranges.items():
            mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # Minimum area threshold
                    x, y, w, h = cv2.boundingRect(contour)
                    detected_objects.append({
                        'color': color_name,
                        'bbox': (x, y, w, h),
                        'area': area,
                        'center': (x + w//2, y + h//2)
                    })
        
        return detected_objects
    
    def cleanup(self):
        """Cleanup camera resources"""
        self.streaming = False
        self.recording = False
        
        if self.camera:
            if PICAMERA_AVAILABLE:
                self.camera.close()
            else:
                self.camera.release()
        
        cv2.destroyAllWindows()