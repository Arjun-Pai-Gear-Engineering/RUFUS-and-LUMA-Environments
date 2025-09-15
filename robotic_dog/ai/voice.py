"""
Voice AI module for voice command processing
"""
import speech_recognition as sr
import requests
import json
import re
from ..config import OPENAI_API_KEY


class VoiceAI:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.openai_api_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Initialize microphone if available
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
            print("Microphone initialized successfully")
        except Exception as e:
            print(f"Warning: Microphone not available: {e}")
    
    def listen_for_command(self, timeout=5):
        """Listen for voice command"""
        if not self.microphone:
            return None
            
        try:
            with self.microphone as source:
                print("Listening for command...")
                audio = self.recognizer.listen(source, timeout=timeout)
            
            # Use Google Speech Recognition (free tier)
            text = self.recognizer.recognize_google(audio)
            print(f"Heard: {text}")
            return text.lower()
            
        except sr.WaitTimeoutError:
            print("Listening timeout")
            return None
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Could not request results: {e}")
            return None
    
    async def process_voice_command(self, text):
        """Process voice command and return robot action"""
        if not text:
            return None
        
        # Clean and normalize text
        text = text.lower().strip()
        
        # First, try pattern matching for common commands
        pattern_result = self.match_command_patterns(text)
        if pattern_result:
            return pattern_result
        
        # If no pattern match, use AI for more complex understanding
        ai_result = await self.ai_command_understanding(text)
        return ai_result
    
    def match_command_patterns(self, text):
        """Match common voice command patterns"""
        patterns = {
            # Movement commands
            r'(go|move|walk)\s*(forward|ahead|straight)': {
                'command': 'move',
                'params': {'direction': 'forward', 'speed': 1.0}
            },
            r'(go|move|walk)\s*(backward|back)': {
                'command': 'move', 
                'params': {'direction': 'backward', 'speed': 1.0}
            },
            r'(turn|go)\s*(left)': {
                'command': 'move',
                'params': {'direction': 'left', 'speed': 1.0}
            },
            r'(turn|go)\s*(right)': {
                'command': 'move',
                'params': {'direction': 'right', 'speed': 1.0}
            },
            r'(stop|halt|wait|pause)': {
                'command': 'move',
                'params': {'direction': 'stop'}
            },
            
            # Camera commands
            r'(take|capture)\s*(photo|picture|pic)': {
                'command': 'camera',
                'params': {'action': 'photo'}
            },
            r'(start|begin)\s*(recording|video)': {
                'command': 'camera',
                'params': {'action': 'start_recording'}
            },
            r'(stop)\s*(recording|video)': {
                'command': 'camera',
                'params': {'action': 'stop_recording'}
            },
            
            # Navigation commands
            r'(where|what)\s*(am i|is my location)': {
                'command': 'gps',
                'params': {'action': 'get_location'}
            },
            r'(go|navigate)\s*to': {
                'command': 'navigation',
                'params': {'action': 'parse_destination', 'text': text}
            },
            
            # AI commands
            r'(what|describe)\s*(do you see|can you see)': {
                'command': 'ai',
                'params': {'action': 'analyze_scene'}
            },
            r'(analyze|examine|look at)\s*(scene|area|surroundings)': {
                'command': 'ai',
                'params': {'action': 'analyze_scene'}
            },
            
            # Status commands
            r'(status|how are you|what.*status)': {
                'command': 'status',
                'params': {}
            },
            
            # Greeting and interaction
            r'(hello|hi|hey)\s*(dog|buddy|robot)': {
                'command': 'interaction',
                'params': {'action': 'greeting', 'response': 'Hello! I\'m ready for commands.'}
            }
        }
        
        for pattern, command_info in patterns.items():
            if re.search(pattern, text):
                return command_info
        
        return None
    
    async def ai_command_understanding(self, text):
        """Use AI to understand complex voice commands"""
        if not OPENAI_API_KEY:
            return {
                'command': 'error',
                'params': {'message': 'AI command understanding not available'}
            }
        
        try:
            prompt = f"""
            You are an AI assistant for a robotic dog. Parse the following voice command and return a JSON response with the appropriate robot action.

            Available commands:
            - move: directions can be 'forward', 'backward', 'left', 'right', 'stop'
            - camera: actions can be 'photo', 'start_recording', 'stop_recording'
            - gps: actions can be 'get_location', 'navigate'
            - ai: actions can be 'analyze_scene'
            - status: get robot status

            Voice command: "{text}"

            Return only a JSON object with 'command' and 'params' fields.
            """
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 150,
                "temperature": 0.3
            }
            
            response = requests.post(self.openai_api_url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
                
                # Try to parse JSON response
                try:
                    command_data = json.loads(ai_response)
                    return command_data
                except json.JSONDecodeError:
                    # Fallback to text response
                    return {
                        'command': 'interaction',
                        'params': {'action': 'ai_response', 'response': ai_response}
                    }
            else:
                return self.fallback_command_understanding(text)
                
        except Exception as e:
            print(f"AI command understanding error: {e}")
            return self.fallback_command_understanding(text)
    
    def fallback_command_understanding(self, text):
        """Fallback command understanding using keyword matching"""
        # Simple keyword-based understanding
        keywords = {
            'move': ['move', 'go', 'walk', 'forward', 'backward', 'left', 'right'],
            'stop': ['stop', 'halt', 'wait', 'pause'],
            'photo': ['photo', 'picture', 'take', 'capture'],
            'location': ['location', 'where', 'position', 'gps'],
            'analyze': ['analyze', 'see', 'look', 'describe', 'what']
        }
        
        word_counts = {}
        for category, words in keywords.items():
            word_counts[category] = sum(1 for word in words if word in text)
        
        # Find category with most matches
        best_category = max(word_counts, key=word_counts.get)
        
        if word_counts[best_category] > 0:
            if best_category == 'move':
                if 'forward' in text or 'ahead' in text:
                    direction = 'forward'
                elif 'backward' in text or 'back' in text:
                    direction = 'backward'
                elif 'left' in text:
                    direction = 'left'
                elif 'right' in text:
                    direction = 'right'
                else:
                    direction = 'forward'  # Default
                
                return {
                    'command': 'move',
                    'params': {'direction': direction, 'speed': 1.0}
                }
            elif best_category == 'stop':
                return {
                    'command': 'move',
                    'params': {'direction': 'stop'}
                }
            elif best_category == 'photo':
                return {
                    'command': 'camera',
                    'params': {'action': 'photo'}
                }
            elif best_category == 'location':
                return {
                    'command': 'gps',
                    'params': {'action': 'get_location'}
                }
            elif best_category == 'analyze':
                return {
                    'command': 'ai',
                    'params': {'action': 'analyze_scene'}
                }
        
        # If no match found, return unknown command
        return {
            'command': 'interaction',
            'params': {
                'action': 'unknown_command',
                'response': f"I didn't understand the command: {text}. Please try again."
            }
        }
    
    def generate_response(self, command_result):
        """Generate voice response for command result"""
        if not command_result:
            return "I couldn't process that command."
        
        command = command_result.get('command')
        status = command_result.get('status', 'unknown')
        
        if status == 'success':
            if command == 'move':
                direction = command_result.get('params', {}).get('direction', 'unknown')
                if direction == 'stop':
                    return "Stopping movement."
                else:
                    return f"Moving {direction}."
            elif command == 'camera':
                action = command_result.get('params', {}).get('action')
                if action == 'photo':
                    return "Photo taken successfully."
                elif action == 'start_recording':
                    return "Started video recording."
                elif action == 'stop_recording':
                    return "Stopped video recording."
            elif command == 'gps':
                return "Location information retrieved."
            elif command == 'ai':
                return "Scene analysis complete."
            elif command == 'status':
                return "Status information updated."
            else:
                return "Command executed successfully."
        else:
            error_msg = command_result.get('message', 'Unknown error')
            return f"Command failed: {error_msg}"
    
    def extract_coordinates_from_text(self, text):
        """Extract GPS coordinates from voice command text"""
        # Look for coordinate patterns
        coord_patterns = [
            r'(\d+\.?\d*)\s*degrees?\s*north.*?(\d+\.?\d*)\s*degrees?\s*west',
            r'(\d+\.?\d*)\s*degrees?\s*south.*?(\d+\.?\d*)\s*degrees?\s*east',
            r'latitude\s*(\d+\.?\d*).*?longitude\s*(\d+\.?\d*)',
            r'lat\s*(\d+\.?\d*).*?lon\s*(\d+\.?\d*)'
        ]
        
        for pattern in coord_patterns:
            match = re.search(pattern, text.lower())
            if match:
                lat, lon = float(match.group(1)), float(match.group(2))
                return {'latitude': lat, 'longitude': lon}
        
        return None