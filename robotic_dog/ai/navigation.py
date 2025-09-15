"""
Navigation AI module for path planning and autonomous movement
"""
import math
import numpy as np
from collections import deque
import heapq
import time


class NavigationAI:
    def __init__(self):
        self.current_goal = None
        self.path_history = []
        self.obstacle_map = {}
        self.grid_size = 0.1  # 10cm grid resolution
        self.safety_distance = 0.5  # 50cm safety margin
        
    def set_goal(self, target_lat, target_lon):
        """Set navigation goal"""
        self.current_goal = {
            'latitude': target_lat,
            'longitude': target_lon,
            'timestamp': time.time()
        }
        
    def calculate_path_to_goal(self, current_lat, current_lon, obstacles=None):
        """Calculate optimal path to goal considering obstacles"""
        if not self.current_goal:
            return None
            
        # Calculate direct distance and bearing
        distance = self.calculate_distance(
            current_lat, current_lon,
            self.current_goal['latitude'], self.current_goal['longitude']
        )
        
        bearing = self.calculate_bearing(
            current_lat, current_lon,
            self.current_goal['latitude'], self.current_goal['longitude']
        )
        
        # If close to goal, return simple path
        if distance < 2.0:  # Within 2 meters
            return {
                'type': 'direct',
                'distance': distance,
                'bearing': bearing,
                'waypoints': [self.current_goal],
                'estimated_time': distance / 0.5  # Assuming 0.5 m/s speed
            }
        
        # For longer distances, create waypoint path
        waypoints = self.generate_waypoints(
            current_lat, current_lon,
            self.current_goal['latitude'], self.current_goal['longitude'],
            obstacles
        )
        
        return {
            'type': 'waypoint',
            'distance': distance,
            'bearing': bearing,
            'waypoints': waypoints,
            'estimated_time': distance / 0.5
        }
    
    def generate_waypoints(self, start_lat, start_lon, end_lat, end_lon, obstacles=None):
        """Generate intermediate waypoints for navigation"""
        waypoints = []
        
        # Calculate number of waypoints based on distance
        total_distance = self.calculate_distance(start_lat, start_lon, end_lat, end_lon)
        num_waypoints = max(2, int(total_distance / 10))  # Waypoint every 10 meters
        
        for i in range(1, num_waypoints + 1):
            progress = i / num_waypoints
            
            # Linear interpolation for basic path
            lat = start_lat + (end_lat - start_lat) * progress
            lon = start_lon + (end_lon - start_lon) * progress
            
            waypoints.append({
                'latitude': lat,
                'longitude': lon,
                'waypoint_id': i
            })
        
        # Add obstacle avoidance adjustments
        if obstacles:
            waypoints = self.adjust_waypoints_for_obstacles(waypoints, obstacles)
        
        return waypoints
    
    def adjust_waypoints_for_obstacles(self, waypoints, obstacles):
        """Adjust waypoints to avoid obstacles"""
        adjusted_waypoints = []
        
        for waypoint in waypoints:
            # Check if waypoint conflicts with any obstacle
            conflict = False
            for obstacle in obstacles:
                if self.point_in_obstacle(waypoint, obstacle):
                    conflict = True
                    break
            
            if conflict:
                # Find alternative position
                adjusted_waypoint = self.find_safe_waypoint(waypoint, obstacles)
                adjusted_waypoints.append(adjusted_waypoint)
            else:
                adjusted_waypoints.append(waypoint)
        
        return adjusted_waypoints
    
    def point_in_obstacle(self, point, obstacle):
        """Check if point is within obstacle boundary"""
        # Simple circular obstacle model
        obstacle_lat = obstacle.get('latitude', 0)
        obstacle_lon = obstacle.get('longitude', 0)
        obstacle_radius = obstacle.get('radius', 1.0)  # Default 1 meter radius
        
        distance = self.calculate_distance(
            point['latitude'], point['longitude'],
            obstacle_lat, obstacle_lon
        )
        
        return distance < (obstacle_radius + self.safety_distance)
    
    def find_safe_waypoint(self, original_waypoint, obstacles):
        """Find safe alternative waypoint position"""
        # Try positions in a circle around the original waypoint
        search_radius = 2.0  # 2 meter search radius
        angles = np.linspace(0, 2*np.pi, 8)  # 8 directions
        
        for angle in angles:
            # Calculate offset position
            lat_offset = search_radius * np.cos(angle) / 111000  # Rough lat conversion
            lon_offset = search_radius * np.sin(angle) / (111000 * np.cos(np.radians(original_waypoint['latitude'])))
            
            test_waypoint = {
                'latitude': original_waypoint['latitude'] + lat_offset,
                'longitude': original_waypoint['longitude'] + lon_offset,
                'waypoint_id': original_waypoint.get('waypoint_id', 0)
            }
            
            # Check if this position is safe
            safe = True
            for obstacle in obstacles:
                if self.point_in_obstacle(test_waypoint, obstacle):
                    safe = False
                    break
            
            if safe:
                return test_waypoint
        
        # If no safe position found, return original with warning
        original_waypoint['warning'] = 'No safe alternative found'
        return original_waypoint
    
    def get_next_movement_command(self, current_lat, current_lon, current_heading, vision_obstacles=None):
        """Get next movement command based on current position and obstacles"""
        if not self.current_goal:
            return {'command': 'stop', 'reason': 'No goal set'}
        
        # Calculate direction to goal
        distance_to_goal = self.calculate_distance(
            current_lat, current_lon,
            self.current_goal['latitude'], self.current_goal['longitude']
        )
        
        # Check if we've reached the goal
        if distance_to_goal < 1.0:  # Within 1 meter
            return {
                'command': 'stop',
                'reason': 'Goal reached',
                'goal_achieved': True
            }
        
        bearing_to_goal = self.calculate_bearing(
            current_lat, current_lon,
            self.current_goal['latitude'], self.current_goal['longitude']
        )
        
        # Calculate relative bearing
        relative_bearing = (bearing_to_goal - current_heading + 360) % 360
        
        # Check for immediate obstacles
        if vision_obstacles:
            obstacle_response = self.analyze_immediate_obstacles(vision_obstacles)
            if obstacle_response:
                return obstacle_response
        
        # Determine movement command based on relative bearing
        if abs(relative_bearing) < 15 or abs(relative_bearing - 360) < 15:
            return {
                'command': 'forward',
                'speed': min(1.0, distance_to_goal / 10),  # Slow down as we approach
                'distance_to_goal': distance_to_goal
            }
        elif 15 <= relative_bearing < 180:
            return {
                'command': 'turn_right',
                'angle': min(relative_bearing, 45),  # Max 45 degree turn
                'distance_to_goal': distance_to_goal
            }
        else:
            return {
                'command': 'turn_left',
                'angle': min(360 - relative_bearing, 45),  # Max 45 degree turn
                'distance_to_goal': distance_to_goal
            }
    
    def analyze_immediate_obstacles(self, vision_obstacles):
        """Analyze immediate obstacles from vision system"""
        # Check for obstacles directly ahead
        center_obstacles = [obs for obs in vision_obstacles if obs.get('position') == 'center']
        
        if center_obstacles:
            # Check if any obstacles are too close
            close_obstacles = [obs for obs in center_obstacles if obs.get('distance_estimate', 10) < 2]
            
            if close_obstacles:
                # Determine best avoidance direction
                left_obstacles = [obs for obs in vision_obstacles if obs.get('position') == 'left']
                right_obstacles = [obs for obs in vision_obstacles if obs.get('position') == 'right']
                
                left_score = len(left_obstacles) + sum(1/max(obs.get('distance_estimate', 1), 0.5) for obs in left_obstacles)
                right_score = len(right_obstacles) + sum(1/max(obs.get('distance_estimate', 1), 0.5) for obs in right_obstacles)
                
                if left_score < right_score:
                    return {
                        'command': 'turn_left',
                        'angle': 30,
                        'reason': 'Avoiding obstacle - turn left'
                    }
                else:
                    return {
                        'command': 'turn_right',
                        'angle': 30,
                        'reason': 'Avoiding obstacle - turn right'
                    }
        
        return None
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two GPS coordinates (in meters)"""
        # Haversine formula
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        earth_radius = 6371000  # Earth radius in meters
        distance = earth_radius * c
        
        return distance
    
    def calculate_bearing(self, lat1, lon1, lat2, lon2):
        """Calculate bearing from point 1 to point 2 (in degrees)"""
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
    
    def add_obstacle_to_map(self, lat, lon, radius=1.0, obstacle_type='unknown'):
        """Add obstacle to persistent obstacle map"""
        obstacle_id = f"{lat:.6f}_{lon:.6f}"
        self.obstacle_map[obstacle_id] = {
            'latitude': lat,
            'longitude': lon,
            'radius': radius,
            'type': obstacle_type,
            'timestamp': time.time()
        }
    
    def clear_old_obstacles(self, max_age_seconds=300):
        """Remove obstacles older than specified age"""
        current_time = time.time()
        to_remove = []
        
        for obstacle_id, obstacle in self.obstacle_map.items():
            if current_time - obstacle['timestamp'] > max_age_seconds:
                to_remove.append(obstacle_id)
        
        for obstacle_id in to_remove:
            del self.obstacle_map[obstacle_id]
    
    def get_exploration_target(self, current_lat, current_lon, explored_radius=50):
        """Generate exploration target for autonomous mode"""
        # Simple exploration: move in expanding circles
        angle = (time.time() % 360) * 6  # Slow rotation
        radius = 10 + (time.time() % 100) / 10  # 10-20 meter radius
        
        # Calculate target coordinates
        lat_offset = radius * math.cos(math.radians(angle)) / 111000
        lon_offset = radius * math.sin(math.radians(angle)) / (111000 * math.cos(math.radians(current_lat)))
        
        target_lat = current_lat + lat_offset
        target_lon = current_lon + lon_offset
        
        return {
            'latitude': target_lat,
            'longitude': target_lon,
            'type': 'exploration',
            'radius': radius,
            'angle': angle
        }