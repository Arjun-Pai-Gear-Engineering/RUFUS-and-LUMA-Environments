"""
GPS and navigation module for robotic dog
Handles GPS data, mapping, and location tracking
"""
import time
import threading
import json
from datetime import datetime
from ..config import GPS_DEVICE, GPS_BAUDRATE

try:
    import gpsd
    GPSD_AVAILABLE = True
except ImportError:
    print("Warning: gpsd not available, using simulation mode")
    GPSD_AVAILABLE = False


class GPSController:
    def __init__(self):
        self.connected = False
        self.current_location = None
        self.location_history = []
        self.tracking_enabled = False
        self.track_lock = threading.Lock()
        
    def initialize(self):
        """Initialize GPS connection"""
        try:
            if GPSD_AVAILABLE:
                gpsd.connect()
                self.connected = True
                print("GPS controller initialized successfully")
            else:
                print("GPS controller running in simulation mode")
                self.connected = True
            return True
            
        except Exception as e:
            print(f"Failed to initialize GPS: {e}")
            return False
    
    def start_tracking(self):
        """Start GPS tracking"""
        if not self.connected:
            return False
            
        self.tracking_enabled = True
        threading.Thread(target=self._tracking_worker, daemon=True).start()
        return True
    
    def stop_tracking(self):
        """Stop GPS tracking"""
        self.tracking_enabled = False
    
    def _tracking_worker(self):
        """Worker thread for continuous GPS data collection"""
        while self.tracking_enabled:
            try:
                if GPSD_AVAILABLE:
                    packet = gpsd.get_current()
                    if packet.mode >= 2:  # 2D fix or better
                        location_data = {
                            'timestamp': datetime.now().isoformat(),
                            'latitude': packet.lat,
                            'longitude': packet.lon,
                            'altitude': packet.alt if packet.mode >= 3 else None,
                            'speed': packet.hspeed,
                            'heading': packet.track,
                            'accuracy': packet.error.get('h', None)
                        }
                    else:
                        location_data = None
                else:
                    # Simulation mode - generate fake GPS data
                    location_data = {
                        'timestamp': datetime.now().isoformat(),
                        'latitude': 37.7749 + (time.time() % 100) * 0.0001,
                        'longitude': -122.4194 + (time.time() % 100) * 0.0001,
                        'altitude': 50.0,
                        'speed': 0.5,
                        'heading': 0.0,
                        'accuracy': 3.0
                    }
                
                if location_data:
                    with self.track_lock:
                        self.current_location = location_data
                        self.location_history.append(location_data)
                        
                        # Keep only last 1000 points
                        if len(self.location_history) > 1000:
                            self.location_history = self.location_history[-1000:]
                
                time.sleep(1)  # Update every second
                
            except Exception as e:
                print(f"GPS tracking error: {e}")
                time.sleep(5)  # Wait before retry
    
    def get_current_location(self):
        """Get current GPS location"""
        with self.track_lock:
            return self.current_location.copy() if self.current_location else None
    
    def get_location_history(self, limit=None):
        """Get location history"""
        with self.track_lock:
            history = self.location_history.copy()
            if limit:
                history = history[-limit:]
            return history
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two GPS coordinates (in meters)"""
        import math
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of Earth in meters
        earth_radius = 6371000
        distance = earth_radius * c
        
        return distance
    
    def calculate_bearing(self, lat1, lon1, lat2, lon2):
        """Calculate bearing from point 1 to point 2 (in degrees)"""
        import math
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlon_rad = math.radians(lon2 - lon1)
        
        y = math.sin(dlon_rad) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad))
        
        bearing_rad = math.atan2(y, x)
        bearing_deg = math.degrees(bearing_rad)
        
        # Normalize to 0-360 degrees
        bearing_deg = (bearing_deg + 360) % 360
        
        return bearing_deg
    
    def navigate_to_target(self, target_lat, target_lon):
        """Calculate navigation instructions to target"""
        current = self.get_current_location()
        if not current:
            return None
        
        distance = self.calculate_distance(
            current['latitude'], current['longitude'],
            target_lat, target_lon
        )
        
        bearing = self.calculate_bearing(
            current['latitude'], current['longitude'],
            target_lat, target_lon
        )
        
        # Calculate relative bearing (difference from current heading)
        current_heading = current.get('heading', 0)
        relative_bearing = (bearing - current_heading + 360) % 360
        
        return {
            'distance': distance,
            'bearing': bearing,
            'relative_bearing': relative_bearing,
            'instructions': self._generate_navigation_instructions(relative_bearing, distance)
        }
    
    def _generate_navigation_instructions(self, relative_bearing, distance):
        """Generate human-readable navigation instructions"""
        if distance < 2:
            return "You have arrived at your destination"
        
        if relative_bearing < 10 or relative_bearing > 350:
            direction = "straight ahead"
        elif 10 <= relative_bearing < 80:
            direction = "slightly right"
        elif 80 <= relative_bearing < 100:
            direction = "right"
        elif 100 <= relative_bearing < 170:
            direction = "sharp right"
        elif 170 <= relative_bearing < 190:
            direction = "behind you"
        elif 190 <= relative_bearing < 260:
            direction = "sharp left"
        elif 260 <= relative_bearing < 280:
            direction = "left"
        elif 280 <= relative_bearing <= 350:
            direction = "slightly left"
        
        if distance < 10:
            distance_text = f"{distance:.1f} meters"
        elif distance < 1000:
            distance_text = f"{int(distance)} meters"
        else:
            distance_text = f"{distance/1000:.1f} kilometers"
        
        return f"Go {direction} for {distance_text}"
    
    def save_track(self, filename=None):
        """Save current track to file"""
        if not filename:
            filename = f"track_{int(time.time())}.json"
        
        track_data = {
            'start_time': self.location_history[0]['timestamp'] if self.location_history else None,
            'end_time': self.location_history[-1]['timestamp'] if self.location_history else None,
            'total_points': len(self.location_history),
            'track': self.get_location_history()
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(track_data, f, indent=2)
            return filename
        except Exception as e:
            print(f"Error saving track: {e}")
            return None
    
    def load_track(self, filename):
        """Load track from file"""
        try:
            with open(filename, 'r') as f:
                track_data = json.load(f)
            return track_data
        except Exception as e:
            print(f"Error loading track: {e}")
            return None
    
    def cleanup(self):
        """Cleanup GPS controller"""
        self.stop_tracking()
        if GPSD_AVAILABLE and self.connected:
            gpsd.disconnect()