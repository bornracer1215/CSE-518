"""
Gesture Controller for Adaptive Reading Interface
Uses MediaPipe Hands for real-time gesture recognition
"""

import cv2
import mediapipe as mp
import time
from collections import deque
import config


class GestureController:
    def __init__(self, on_gesture_callback=None):
        """
        Initialize the gesture controller
        """
        self.on_gesture_callback = on_gesture_callback
        
        # MediaPipe setup
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.8,
            min_tracking_confidence=0.8
        )
        
        # Camera
        self.cap = None
        self.is_running = False
        
        # Gesture cooldown
        self.last_gesture_time = 0
        self.cooldown = config.GESTURE_COOLDOWN
        
        # Gesture stabilization - require consistent detection
        self.gesture_history = deque(maxlen=10)  # Last 10 frames
        self.stable_gesture = None
        self.last_triggered_gesture = None
        
        # Landmark indices
        self.WRIST = 0
        self.THUMB_CMC = 1
        self.THUMB_MCP = 2
        self.THUMB_IP = 3
        self.THUMB_TIP = 4
        self.INDEX_MCP = 5
        self.INDEX_PIP = 6
        self.INDEX_DIP = 7
        self.INDEX_TIP = 8
        self.MIDDLE_MCP = 9
        self.MIDDLE_PIP = 10
        self.MIDDLE_DIP = 11
        self.MIDDLE_TIP = 12
        self.RING_MCP = 13
        self.RING_PIP = 14
        self.RING_DIP = 15
        self.RING_TIP = 16
        self.PINKY_MCP = 17
        self.PINKY_PIP = 18
        self.PINKY_DIP = 19
        self.PINKY_TIP = 20
    
    def _get_finger_state(self, landmarks):
        """
        Get the state of each finger (extended or curled)
        Returns dict with True = extended, False = curled
        """
        # For fingers (not thumb): compare tip.y with pip.y
        # Lower y = higher on screen = extended
        
        index_extended = landmarks[self.INDEX_TIP].y < landmarks[self.INDEX_PIP].y
        middle_extended = landmarks[self.MIDDLE_TIP].y < landmarks[self.MIDDLE_PIP].y
        ring_extended = landmarks[self.RING_TIP].y < landmarks[self.RING_PIP].y
        pinky_extended = landmarks[self.PINKY_TIP].y < landmarks[self.PINKY_PIP].y
        
        return {
            'index': index_extended,
            'middle': middle_extended,
            'ring': ring_extended,
            'pinky': pinky_extended
        }
    
    def _get_thumb_direction(self, landmarks):
        """
        Determine thumb direction: 'up', 'down', 'side', or 'curled'
        """
        thumb_tip = landmarks[self.THUMB_TIP]
        thumb_ip = landmarks[self.THUMB_IP]
        thumb_mcp = landmarks[self.THUMB_MCP]
        wrist = landmarks[self.WRIST]
        index_mcp = landmarks[self.INDEX_MCP]
        
        # Calculate vertical difference between thumb tip and wrist
        # Positive = thumb tip is ABOVE wrist (thumb up)
        # Negative = thumb tip is BELOW wrist (thumb down)
        vertical_diff = wrist.y - thumb_tip.y
        
        # Calculate how far thumb tip extends from the palm horizontally
        horizontal_diff = abs(thumb_tip.x - wrist.x)
        
        # Debug values (will be shown on screen)
        self.debug_thumb_v = vertical_diff
        self.debug_thumb_h = horizontal_diff
        
        # Thresholds
        UP_THRESHOLD = 0.15    # Thumb tip significantly above wrist
        DOWN_THRESHOLD = -0.10  # Thumb tip significantly below wrist
        
        if vertical_diff > UP_THRESHOLD:
            return 'up'
        elif vertical_diff < DOWN_THRESHOLD:
            return 'down'
        elif horizontal_diff > 0.12:
            return 'side'
        else:
            return 'curled'
    
    def _is_thumb_up(self, landmarks, fingers):
        """Check for thumbs up gesture"""
        thumb_dir = self._get_thumb_direction(landmarks)
        
        # Thumb must be pointing up
        if thumb_dir != 'up':
            return False
        
        # All other fingers must be curled
        all_curled = not fingers['index'] and not fingers['middle'] and not fingers['ring'] and not fingers['pinky']
        
        return all_curled
    
    def _is_thumb_down(self, landmarks, fingers):
        """Check for thumbs down gesture"""
        thumb_dir = self._get_thumb_direction(landmarks)
        
        # Thumb must be pointing down
        if thumb_dir != 'down':
            return False
        
        # All other fingers must be curled
        all_curled = not fingers['index'] and not fingers['middle'] and not fingers['ring'] and not fingers['pinky']
        
        return all_curled
    
    def _is_open_palm(self, landmarks, fingers):
        """Check for open palm (all fingers extended)"""
        thumb_dir = self._get_thumb_direction(landmarks)
        thumb_out = thumb_dir in ['up', 'side']
        
        all_extended = fingers['index'] and fingers['middle'] and fingers['ring'] and fingers['pinky']
        
        return all_extended and thumb_out
    
    def _is_fist(self, landmarks, fingers):
        """Check for fist (all fingers curled)"""
        # All four fingers must be curled
        all_curled = not fingers['index'] and not fingers['middle'] and not fingers['ring'] and not fingers['pinky']
        
        if not all_curled:
            return False
        
        # For fist, thumb should be tucked in or wrapped around fingers
        # Check that thumb tip is close to palm (near index MCP)
        thumb_tip = landmarks[self.THUMB_TIP]
        index_mcp = landmarks[self.INDEX_MCP]
        middle_mcp = landmarks[self.MIDDLE_MCP]
        wrist = landmarks[self.WRIST]
        
        # Calculate palm center
        palm_center_x = (index_mcp.x + wrist.x) / 2
        palm_center_y = (index_mcp.y + wrist.y) / 2
        
        # Thumb tip should be close to palm center (tucked in)
        thumb_to_palm_x = abs(thumb_tip.x - palm_center_x)
        thumb_to_palm_y = abs(thumb_tip.y - palm_center_y)
        
        # Thumb should be near the palm, not sticking up or down
        thumb_tucked = thumb_to_palm_x < 0.15 and thumb_to_palm_y < 0.15
        
        # Also make sure thumb is not pointing strongly up or down
        thumb_tip_y = thumb_tip.y
        wrist_y = wrist.y
        vertical_diff = abs(wrist_y - thumb_tip_y)
        
        # If thumb is too far vertically from wrist, it's thumbs up/down, not fist
        thumb_not_pointing = vertical_diff < 0.12
        
        return all_curled and (thumb_tucked or thumb_not_pointing)
    
    def _is_peace_sign(self, landmarks, fingers):
        """Check for peace/victory sign"""
        # Index and middle extended, others curled
        return (fingers['index'] and fingers['middle'] and 
                not fingers['ring'] and not fingers['pinky'])
    
    def _is_pointing_up(self, landmarks, fingers):
        """Check for pointing up (only index extended)"""
        return (fingers['index'] and not fingers['middle'] and 
                not fingers['ring'] and not fingers['pinky'])
    
    def detect_gesture(self, landmarks):
        """Detect which gesture is being made"""
        fingers = self._get_finger_state(landmarks)
        
        # Check gestures in order of specificity
        if self._is_thumb_up(landmarks, fingers):
            return "thumbs_up"
        elif self._is_thumb_down(landmarks, fingers):
            return "thumbs_down"
        elif self._is_pointing_up(landmarks, fingers):
            return "point_up"
        elif self._is_peace_sign(landmarks, fingers):
            return "peace"
        elif self._is_open_palm(landmarks, fingers):
            return "open_palm"
        elif self._is_fist(landmarks, fingers):
            return "fist"
        else:
            return None
    
    def _get_stable_gesture(self, current_gesture):
        """
        Get stable gesture by checking consistency over recent frames
        Returns gesture only if it's been consistent
        """
        self.gesture_history.append(current_gesture)
        
        if len(self.gesture_history) < 5:
            return None
        
        # Count occurrences of each gesture in history
        gesture_counts = {}
        for g in self.gesture_history:
            if g:
                gesture_counts[g] = gesture_counts.get(g, 0) + 1
        
        if not gesture_counts:
            return None
        
        # Find most common gesture
        most_common = max(gesture_counts, key=gesture_counts.get)
        count = gesture_counts[most_common]
        
        # Require gesture to appear in at least 60% of recent frames
        if count >= len(self.gesture_history) * 0.6:
            return most_common
        
        return None
    
    def _trigger_gesture(self, gesture):
        """Trigger a gesture action with cooldown"""
        current_time = time.time()
        
        # Check cooldown
        if current_time - self.last_gesture_time < self.cooldown:
            return
        
        # Only trigger if gesture changed from last triggered
        if gesture == self.last_triggered_gesture:
            return
        
        self.last_triggered_gesture = gesture
        self.last_gesture_time = current_time
        
        # Get action for this gesture
        action = config.GESTURE_ACTIONS.get(gesture)
        
        if action and self.on_gesture_callback:
            self.on_gesture_callback(gesture, action)
    
    def start_camera(self):
        """Start the camera capture"""
        if self.cap is None:
            # Try different camera indices
            for camera_index in [0, 1]:
                try:
                    self.cap = cv2.VideoCapture(camera_index)  # Use default backend
                    
                    # Wait a moment for camera to initialize
                    import time
                    time.sleep(0.5)
                    
                    if self.cap.isOpened():
                        # Test if we can actually read a frame
                        ret, test_frame = self.cap.read()
                        if ret and test_frame is not None:
                            print(f"Camera opened successfully on index {camera_index}")
                            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                            break
                    
                    self.cap.release()
                    self.cap = None
                except Exception as e:
                    print(f"Failed to open camera {camera_index}: {e}")
                    if self.cap:
                        self.cap.release()
                    self.cap = None
                    continue
            
            if self.cap is None:
                print("Could not find any working camera")
                return False
        
        self.is_running = True
        return self.cap is not None and self.cap.isOpened()
    
    def stop_camera(self):
        """Stop the camera capture"""
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def process_frame(self):
        """Process a single frame and return it with annotations"""
        if not self.cap or not self.is_running:
            return None, None
        
        ret, frame = self.cap.read()
        if not ret:
            return None, None
        
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process with MediaPipe
        results = self.hands.process(rgb_frame)
        
        detected_gesture = None
        stable_gesture = None
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw landmarks
                self.mp_draw.draw_landmarks(
                    frame, 
                    hand_landmarks, 
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    self.mp_draw.DrawingSpec(color=(255, 255, 255), thickness=2)
                )
                
                # Detect gesture
                detected_gesture = self.detect_gesture(hand_landmarks.landmark)
                
                # Get stable gesture
                stable_gesture = self._get_stable_gesture(detected_gesture)
                
                # Draw debug info for thumb
                thumb_dir = self._get_thumb_direction(hand_landmarks.landmark)
                cv2.putText(
                    frame, 
                    f"Thumb: {thumb_dir} (v:{self.debug_thumb_v:.2f} h:{self.debug_thumb_h:.2f})", 
                    (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, 
                    (255, 128, 0), 
                    2
                )
                
                # Draw finger states
                fingers = self._get_finger_state(hand_landmarks.landmark)
                finger_str = f"I:{int(fingers['index'])} M:{int(fingers['middle'])} R:{int(fingers['ring'])} P:{int(fingers['pinky'])}"
                cv2.putText(
                    frame, 
                    f"Fingers: {finger_str}", 
                    (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.6, 
                    (255, 128, 0), 
                    2
                )
                
                # Draw detected gesture (raw)
                if detected_gesture:
                    cv2.putText(
                        frame, 
                        f"Detected: {detected_gesture}", 
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.7, 
                        (255, 255, 0), 
                        2
                    )
                
                # Draw stable gesture (confirmed)
                if stable_gesture:
                    cv2.putText(
                        frame, 
                        f"Gesture: {stable_gesture}", 
                        (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.9, 
                        (0, 255, 0), 
                        2
                    )
                    
                    # Trigger action
                    self._trigger_gesture(stable_gesture)
        else:
            # No hand detected - clear history
            self.gesture_history.clear()
            self.last_triggered_gesture = None
        
        # Draw instructions
        cv2.putText(frame, "Press 'q' to quit", (10, frame.shape[0] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 128, 128), 1)
        
        return frame, stable_gesture
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_camera()
        self.hands.close()


# Test the gesture controller independently
if __name__ == "__main__":
    def on_gesture(gesture, action):
        print(f">>> TRIGGERED: {gesture} -> {action}")
    
    controller = GestureController(on_gesture_callback=on_gesture)
    
    if controller.start_camera():
        print("=" * 50)
        print("Gesture Control Test")
        print("=" * 50)
        print("\nGestures to try:")
        print("  👍 Thumbs Up   - Increase font")
        print("  👎 Thumbs Down - Decrease font")
        print("  ✋ Open Palm   - Toggle TTS")
        print("  ✊ Fist        - Stop TTS")
        print("  ☝️  Point Up    - Next page")
        print("  ✌️  Peace Sign  - Previous page")
        print("\nHold gesture steady for ~1 second")
        print("Press 'q' to quit")
        print("=" * 50)
        
        while True:
            frame, gesture = controller.process_frame()
            
            if frame is not None:
                cv2.imshow("Gesture Control Test", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        controller.cleanup()
        cv2.destroyAllWindows()
    else:
        print("Failed to open camera!")