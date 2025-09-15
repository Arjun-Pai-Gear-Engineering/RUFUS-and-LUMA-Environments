"""
Motor and servo control for robotic dog legs
Handles 4-leg movement, gait patterns, and precise positioning
"""
import time
import math
import threading
from ..config import LEG_SERVOS, SERVO_MIN_PULSE, SERVO_MAX_PULSE, SERVO_FREQUENCY

try:
    from adafruit_servokit import ServoKit
    SERVOKIT_AVAILABLE = True
except ImportError:
    print("Warning: ServoKit not available, using simulation mode")
    SERVOKIT_AVAILABLE = False


class LegController:
    def __init__(self):
        self.kit = None
        self.current_positions = {}
        self.target_positions = {}
        self.movement_lock = threading.Lock()
        self.moving = False
        
        # Initialize position tracking
        for leg in LEG_SERVOS:
            self.current_positions[leg] = {'hip': 90, 'knee': 90, 'ankle': 90}
            self.target_positions[leg] = {'hip': 90, 'knee': 90, 'ankle': 90}
    
    def initialize(self):
        """Initialize servo controller"""
        try:
            if SERVOKIT_AVAILABLE:
                self.kit = ServoKit(channels=16)
                # Configure servo parameters
                for i in range(16):
                    self.kit.servo[i].set_pulse_width_range(SERVO_MIN_PULSE, SERVO_MAX_PULSE)
                
                # Move to default position
                self.move_to_default_position()
                print("Leg controller initialized successfully")
                return True
            else:
                print("Servo controller running in simulation mode")
                return True
                
        except Exception as e:
            print(f"Failed to initialize leg controller: {e}")
            return False
    
    def move_to_default_position(self):
        """Move all legs to default standing position"""
        default_angles = {
            'front_left': {'hip': 90, 'knee': 45, 'ankle': 135},
            'front_right': {'hip': 90, 'knee': 45, 'ankle': 135},
            'rear_left': {'hip': 90, 'knee': 135, 'ankle': 45},
            'rear_right': {'hip': 90, 'knee': 135, 'ankle': 45}
        }
        
        for leg, angles in default_angles.items():
            self.set_leg_position(leg, angles)
        
        time.sleep(1)  # Allow time for movement
    
    def set_leg_position(self, leg, angles):
        """Set position for a specific leg"""
        if leg not in LEG_SERVOS:
            return False
        
        try:
            with self.movement_lock:
                for joint, angle in angles.items():
                    if joint in LEG_SERVOS[leg]:
                        servo_index = LEG_SERVOS[leg][joint]
                        
                        # Constrain angle to valid range
                        angle = max(0, min(180, angle))
                        
                        if SERVOKIT_AVAILABLE and self.kit:
                            self.kit.servo[servo_index].angle = angle
                        
                        self.current_positions[leg][joint] = angle
                        
            return True
            
        except Exception as e:
            print(f"Error setting leg position: {e}")
            return False
    
    def smooth_move_leg(self, leg, target_angles, duration=1.0):
        """Smoothly move leg to target position over specified duration"""
        if leg not in LEG_SERVOS:
            return False
        
        start_angles = self.current_positions[leg].copy()
        steps = int(duration * 20)  # 20 steps per second
        
        for step in range(steps + 1):
            progress = step / steps
            current_angles = {}
            
            for joint in ['hip', 'knee', 'ankle']:
                start_angle = start_angles[joint]
                target_angle = target_angles[joint]
                current_angle = start_angle + (target_angle - start_angle) * progress
                current_angles[joint] = current_angle
            
            self.set_leg_position(leg, current_angles)
            time.sleep(0.05)
        
        return True
    
    def walk_forward(self, step_height=30, step_length=50, speed=1.0):
        """Execute forward walking gait"""
        self.moving = True
        threading.Thread(target=self._walk_gait, 
                        args=('forward', step_height, step_length, speed), 
                        daemon=True).start()
    
    def walk_backward(self, step_height=30, step_length=50, speed=1.0):
        """Execute backward walking gait"""
        self.moving = True
        threading.Thread(target=self._walk_gait, 
                        args=('backward', step_height, step_length, speed), 
                        daemon=True).start()
    
    def turn_left(self, step_height=30, turn_angle=30, speed=1.0):
        """Execute left turn"""
        self.moving = True
        threading.Thread(target=self._turn_gait, 
                        args=('left', step_height, turn_angle, speed), 
                        daemon=True).start()
    
    def turn_right(self, step_height=30, turn_angle=30, speed=1.0):
        """Execute right turn"""
        self.moving = True
        threading.Thread(target=self._turn_gait, 
                        args=('right', step_height, turn_angle, speed), 
                        daemon=True).start()
    
    def stop_movement(self):
        """Stop current movement"""
        self.moving = False
    
    def _walk_gait(self, direction, step_height, step_length, speed):
        """Internal method for walking gait implementation"""
        step_duration = 0.5 / speed
        
        # Simple trot gait: diagonal legs move together
        while self.moving:
            # Phase 1: Lift front_left and rear_right
            self._step_cycle(['front_left', 'rear_right'], direction, 
                           step_height, step_length, step_duration)
            
            if not self.moving:
                break
                
            # Phase 2: Lift front_right and rear_left  
            self._step_cycle(['front_right', 'rear_left'], direction,
                           step_height, step_length, step_duration)
    
    def _step_cycle(self, legs, direction, step_height, step_length, duration):
        """Execute a step cycle for specified legs"""
        # Lift legs
        for leg in legs:
            current = self.current_positions[leg].copy()
            if 'front' in leg:
                current['knee'] = max(10, current['knee'] - step_height)
            else:
                current['ankle'] = min(170, current['ankle'] + step_height)
            self.set_leg_position(leg, current)
        
        time.sleep(duration * 0.25)
        
        # Move legs forward/backward
        for leg in legs:
            current = self.current_positions[leg].copy()
            hip_adjustment = step_length if direction == 'forward' else -step_length
            
            if 'left' in leg:
                current['hip'] = max(45, min(135, current['hip'] + hip_adjustment))
            else:
                current['hip'] = max(45, min(135, current['hip'] - hip_adjustment))
            
            self.set_leg_position(leg, current)
        
        time.sleep(duration * 0.5)
        
        # Lower legs
        for leg in legs:
            current = self.current_positions[leg].copy()
            if 'front' in leg:
                current['knee'] = 45
            else:
                current['ankle'] = 45 if 'rear' in leg else 135
            self.set_leg_position(leg, current)
        
        time.sleep(duration * 0.25)
    
    def _turn_gait(self, direction, step_height, turn_angle, speed):
        """Internal method for turning gait implementation"""
        # Implementation for turning movements
        step_duration = 0.5 / speed
        
        while self.moving:
            # Simplified turn: move legs in sequence
            legs_order = ['front_left', 'rear_left', 'front_right', 'rear_right']
            if direction == 'right':
                legs_order.reverse()
            
            for leg in legs_order:
                if not self.moving:
                    break
                self._turn_step(leg, direction, step_height, turn_angle, step_duration)
    
    def _turn_step(self, leg, direction, step_height, turn_angle, duration):
        """Execute a single turn step"""
        current = self.current_positions[leg].copy()
        
        # Lift leg
        if 'front' in leg:
            current['knee'] = max(10, current['knee'] - step_height)
        else:
            current['ankle'] = min(170, current['ankle'] + step_height)
        self.set_leg_position(leg, current)
        
        time.sleep(duration * 0.3)
        
        # Rotate hip for turn
        hip_adjustment = turn_angle if direction == 'left' else -turn_angle
        current['hip'] = max(45, min(135, current['hip'] + hip_adjustment))
        self.set_leg_position(leg, current)
        
        time.sleep(duration * 0.4)
        
        # Lower leg
        if 'front' in leg:
            current['knee'] = 45
        else:
            current['ankle'] = 45 if 'rear' in leg else 135
        self.set_leg_position(leg, current)
        
        time.sleep(duration * 0.3)
    
    def get_current_positions(self):
        """Get current positions of all servos"""
        return self.current_positions.copy()
    
    def cleanup(self):
        """Cleanup motor controller"""
        self.stop_movement()
        if SERVOKIT_AVAILABLE and self.kit:
            # Move to safe position
            self.move_to_default_position()