"""
Computer vision AI module using multiple free APIs
"""
import cv2
import numpy as np
import requests
import base64
import io
from PIL import Image
import json
from ..config import HUGGINGFACE_API_KEY, VISION_MODEL_PATH


class VisionAI:
    def __init__(self):
        self.hf_api_url = "https://api-inference.huggingface.co/models/"
        self.headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        self.models = {
            'object_detection': 'facebook/detr-resnet-50',
            'image_classification': 'google/vit-base-patch16-224',
            'depth_estimation': 'Intel/dpt-large'
        }
        
    def encode_image_to_base64(self, image):
        """Convert OpenCV image to base64 string"""
        _, buffer = cv2.imencode('.jpg', image)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        return img_base64
    
    def preprocess_image(self, image, target_size=(224, 224)):
        """Preprocess image for AI models"""
        if len(image.shape) == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
            
        image_pil = Image.fromarray(image_rgb)
        image_resized = image_pil.resize(target_size)
        
        return np.array(image_resized)
    
    async def detect_objects(self, image):
        """Detect objects in image using Hugging Face DETR model"""
        try:
            # Encode image
            image_bytes = cv2.imencode('.jpg', image)[1].tobytes()
            
            # Call Hugging Face API
            response = requests.post(
                f"{self.hf_api_url}{self.models['object_detection']}",
                headers=self.headers,
                data=image_bytes
            )
            
            if response.status_code == 200:
                results = response.json()
                
                # Process results
                objects = []
                for detection in results:
                    if detection['score'] > 0.5:  # Confidence threshold
                        objects.append({
                            'label': detection['label'],
                            'confidence': detection['score'],
                            'bbox': detection['box']
                        })
                
                return objects
            else:
                # Fallback to local OpenCV detection
                return self.detect_objects_opencv(image)
                
        except Exception as e:
            print(f"Object detection error: {e}")
            return self.detect_objects_opencv(image)
    
    def detect_objects_opencv(self, image):
        """Fallback object detection using OpenCV"""
        # Simple color-based detection as fallback
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Define color ranges
        color_ranges = {
            'person': {'lower': np.array([0, 0, 50]), 'upper': np.array([180, 50, 255])},
            'red_object': {'lower': np.array([0, 50, 50]), 'upper': np.array([10, 255, 255])},
            'blue_object': {'lower': np.array([100, 50, 50]), 'upper': np.array([130, 255, 255])},
            'green_object': {'lower': np.array([40, 50, 50]), 'upper': np.array([80, 255, 255])}
        }
        
        detected_objects = []
        
        for label, color_range in color_ranges.items():
            mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:  # Minimum area
                    x, y, w, h = cv2.boundingRect(contour)
                    detected_objects.append({
                        'label': label,
                        'confidence': 0.8,
                        'bbox': {'x': x, 'y': y, 'width': w, 'height': h},
                        'center': (x + w//2, y + h//2)
                    })
        
        return detected_objects
    
    async def classify_scene(self, image):
        """Classify the overall scene using Vision Transformer"""
        try:
            image_bytes = cv2.imencode('.jpg', image)[1].tobytes()
            
            response = requests.post(
                f"{self.hf_api_url}{self.models['image_classification']}",
                headers=self.headers,
                data=image_bytes
            )
            
            if response.status_code == 200:
                results = response.json()
                
                # Get top 3 classifications
                top_results = sorted(results, key=lambda x: x['score'], reverse=True)[:3]
                
                return {
                    'scene_type': top_results[0]['label'],
                    'confidence': top_results[0]['score'],
                    'alternatives': top_results[1:],
                    'environment': self.analyze_environment(top_results)
                }
            else:
                return self.classify_scene_basic(image)
                
        except Exception as e:
            print(f"Scene classification error: {e}")
            return self.classify_scene_basic(image)
    
    def classify_scene_basic(self, image):
        """Basic scene classification using color analysis"""
        # Analyze dominant colors
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Calculate color histograms
        hist_h = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], None, [256], [0, 256])
        hist_v = cv2.calcHist([hsv], [2], None, [256], [0, 256])
        
        # Analyze brightness
        avg_brightness = np.mean(hsv[:, :, 2])
        
        # Simple scene classification based on colors and brightness
        if avg_brightness > 200:
            scene = "bright_indoor" if np.mean(hist_s) < 50 else "sunny_outdoor"
        elif avg_brightness > 100:
            scene = "normal_lighting"
        else:
            scene = "dark_environment"
        
        return {
            'scene_type': scene,
            'confidence': 0.7,
            'environment': scene,
            'brightness': avg_brightness
        }
    
    def analyze_environment(self, classification_results):
        """Analyze environment type from classification results"""
        indoor_keywords = ['room', 'kitchen', 'bedroom', 'office', 'indoor']
        outdoor_keywords = ['park', 'street', 'garden', 'outdoor', 'field']
        
        for result in classification_results:
            label = result['label'].lower()
            if any(keyword in label for keyword in indoor_keywords):
                return 'indoor'
            elif any(keyword in label for keyword in outdoor_keywords):
                return 'outdoor'
        
        return 'unknown'
    
    def detect_obstacles(self, image):
        """Detect obstacles for navigation"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        obstacles = []
        height, width = image.shape[:2]
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # Minimum obstacle size
                x, y, w, h = cv2.boundingRect(contour)
                
                # Calculate relative position
                center_x = (x + w//2) / width
                center_y = (y + h//2) / height
                
                # Determine obstacle position relative to robot
                if center_x < 0.3:
                    position = 'left'
                elif center_x > 0.7:
                    position = 'right'
                else:
                    position = 'center'
                
                # Estimate distance based on size and position
                distance_estimate = max(1, 10 - (area / 1000))
                
                obstacles.append({
                    'position': position,
                    'distance_estimate': distance_estimate,
                    'bbox': {'x': x, 'y': y, 'width': w, 'height': h},
                    'area': area
                })
        
        return obstacles
    
    def calculate_safe_path(self, obstacles, image_width):
        """Calculate safe navigation path based on detected obstacles"""
        # Divide image into zones
        zones = {'left': [], 'center': [], 'right': []}
        
        for obstacle in obstacles:
            bbox = obstacle['bbox']
            center_x = bbox['x'] + bbox['width'] // 2
            
            if center_x < image_width * 0.33:
                zones['left'].append(obstacle)
            elif center_x < image_width * 0.67:
                zones['center'].append(obstacle)
            else:
                zones['right'].append(obstacle)
        
        # Determine safest direction
        zone_scores = {}
        for zone, zone_obstacles in zones.items():
            if not zone_obstacles:
                zone_scores[zone] = 100  # Clear path
            else:
                # Score based on distance and number of obstacles
                total_distance = sum(obs['distance_estimate'] for obs in zone_obstacles)
                avg_distance = total_distance / len(zone_obstacles)
                zone_scores[zone] = avg_distance * 10 - len(zone_obstacles) * 20
        
        # Choose best direction
        best_zone = max(zone_scores, key=zone_scores.get)
        
        return {
            'recommended_direction': best_zone,
            'zone_scores': zone_scores,
            'obstacles_by_zone': zones,
            'safe_to_proceed': zone_scores[best_zone] > 30
        }
    
    async def analyze_frame_complete(self, image):
        """Complete frame analysis including objects, scene, and obstacles"""
        try:
            # Run all analyses
            objects = await self.detect_objects(image)
            scene = await self.classify_scene(image)
            obstacles = self.detect_obstacles(image)
            safe_path = self.calculate_safe_path(obstacles, image.shape[1])
            
            return {
                'timestamp': time.time(),
                'objects': objects,
                'scene': scene,
                'obstacles': obstacles,
                'navigation': safe_path,
                'summary': self.generate_scene_summary(objects, scene, obstacles)
            }
            
        except Exception as e:
            print(f"Complete frame analysis error: {e}")
            return None
    
    def generate_scene_summary(self, objects, scene, obstacles):
        """Generate human-readable scene summary"""
        summary = []
        
        # Scene description
        summary.append(f"Environment: {scene.get('scene_type', 'unknown')}")
        
        # Object count
        if objects:
            object_types = {}
            for obj in objects:
                label = obj['label']
                object_types[label] = object_types.get(label, 0) + 1
            
            object_desc = ", ".join([f"{count} {obj}" for obj, count in object_types.items()])
            summary.append(f"Objects detected: {object_desc}")
        else:
            summary.append("No objects detected")
        
        # Obstacle warning
        if obstacles:
            obstacle_count = len(obstacles)
            summary.append(f"{obstacle_count} obstacle(s) detected")
        else:
            summary.append("Path appears clear")
        
        return ". ".join(summary)


# Import time for timestamp
import time