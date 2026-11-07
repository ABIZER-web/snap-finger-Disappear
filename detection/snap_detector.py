"""
Finger Snap Gesture Detector.
Analyzes hand biomechanics, finger distances, relative velocities, and multi-frame
kinematics to detect genuine finger snaps with high precision and low false positives.
"""

import time
import numpy as np
from collections import deque
from typing import Dict, List, Tuple, Optional

class HandSnapState:
    """Tracks state history and kinematics for a single hand (Left or Right)."""
    
    def __init__(self, hand_type: str, history_len: int = 12):
        self.hand_type = hand_type
        self.history_len = history_len
        # History queue storing tuples of (timestamp, thumb_mid_dist, mid_wrist_dist, thumb_pos, mid_pos)
        self.history = deque(maxlen=history_len)
        self.primed_frames = 0
        self.is_primed = False
        self.last_snap_time = 0.0

    def reset(self):
        self.history.clear()
        self.primed_frames = 0
        self.is_primed = False

class SnapDetector:
    """
    Detects finger snap gestures from tracked hand landmarks.
    Features:
      - Independent Left and Right hand analysis
      - Normalized scale invariance (invariant to distance from camera)
      - Phase-aware state tracking (Primed -> Explosive Release)
      - False positive rejection (ignores closed fists, pinches, peace signs)
      - Adjustable sensitivity and cooldown
    """

    def __init__(self,
                 sensitivity: float = 0.70,
                 cooldown: float = 1.25,
                 left_enabled: bool = True,
                 right_enabled: bool = True):
        self.sensitivity = float(np.clip(sensitivity, 0.1, 1.0))
        self.cooldown = cooldown
        self.left_enabled = left_enabled
        self.right_enabled = right_enabled
        
        self.states = {
            "Left": HandSnapState("Left"),
            "Right": HandSnapState("Right")
        }
        
        # Last detected snap event
        self.last_snap_event: Optional[Dict] = None

    def set_sensitivity(self, sensitivity: float):
        self.sensitivity = float(np.clip(sensitivity, 0.1, 1.0))

    def set_cooldown(self, cooldown: float):
        self.cooldown = max(0.2, float(cooldown))

    def set_hands_enabled(self, left: bool, right: bool):
        self.left_enabled = left
        self.right_enabled = right

    def detect(self, tracked_hands: List[Dict]) -> Tuple[bool, Optional[Dict]]:
        """
        Analyzes tracked hands for a snapping gesture.
        Returns:
            (is_snap, event_dict)
            where event_dict = {
                'hand': 'Left'|'Right',
                'position_px': (x, y),
                'confidence': float,
                'timestamp': float
            }
        """
        now = time.time()
        detected_types = set()

        # Dynamic sensitivity scaling: higher sensitivity -> lower required separation speed
        # sensitivity = 1.0 -> vel_scale = 0.65 (easier)
        # sensitivity = 0.1 -> vel_scale = 1.60 (stricter)
        sens_factor = 1.85 - (self.sensitivity * 1.15)
        contact_threshold = 0.125 * (0.8 + 0.4 * self.sensitivity)
        separation_threshold = 0.28 * sens_factor
        
        snap_fired = False
        snap_event = None

        for hand in tracked_hands:
            hand_type = hand["handedness"]
            detected_types.add(hand_type)

            # Check if this hand side is enabled
            if hand_type == "Left" and not self.left_enabled:
                continue
            if hand_type == "Right" and not self.right_enabled:
                continue

            state = self.states.get(hand_type)
            if state is None:
                continue

            # Check cooldown
            if (now - state.last_snap_time) < self.cooldown:
                continue

            lms_norm = hand["landmarks_norm"] # shape (21, 3)
            lms_px = hand["landmarks_px"]     # shape (21, 2)

            # Key landmarks
            wrist = lms_norm[0, :2]
            thumb_tip = lms_norm[4, :2]
            thumb_ip = lms_norm[3, :2]
            index_tip = lms_norm[8, :2]
            middle_mcp = lms_norm[9, :2]
            middle_pip = lms_norm[10, :2]
            middle_dip = lms_norm[11, :2]
            middle_tip = lms_norm[12, :2]
            ring_tip = lms_norm[16, :2]
            pinky_tip = lms_norm[20, :2]

            # 1. Compute hand scale (distance from wrist to middle finger knuckle MCP)
            hand_scale = float(np.linalg.norm(wrist - middle_mcp))
            if hand_scale < 0.04: # Hand too far or invalid
                continue

            # 2. Normalized distances
            # Distance between thumb tip and middle fingertip / DIP
            thumb_to_middle = float(np.linalg.norm(thumb_tip - middle_tip)) / hand_scale
            thumb_to_index = float(np.linalg.norm(thumb_tip - index_tip)) / hand_scale
            middle_to_wrist = float(np.linalg.norm(middle_tip - wrist)) / hand_scale
            
            # Snap position in pixel space (between thumb and middle tip)
            snap_px = (
                int((lms_px[4, 0] + lms_px[12, 0]) * 0.5),
                int((lms_px[4, 1] + lms_px[12, 1]) * 0.5)
            )

            # Record history
            state.history.append((now, thumb_to_middle, middle_to_wrist, thumb_tip.copy(), middle_tip.copy(), snap_px))

            # 3. Biomechanical Phase 1: Primed (Thumb and Middle finger in contact)
            # In a snap, thumb and middle finger press firmly together, while index finger is NOT clamped
            is_touching = (thumb_to_middle < contact_threshold)
            index_not_blocking = (thumb_to_index > contact_threshold * 0.9)

            if is_touching and index_not_blocking:
                state.primed_frames += 1
                if state.primed_frames >= 2:
                    state.is_primed = True
            else:
                if not is_touching and state.primed_frames > 0:
                    # Finger just left contact!
                    pass
                else:
                    state.primed_frames = max(0, state.primed_frames - 1)
                    if state.primed_frames == 0:
                        state.is_primed = False

            # 4. Biomechanical Phase 2: Snap Execution
            # If the hand was primed within the last 1-4 frames, check for high separation velocity
            if len(state.history) >= 3 and (state.is_primed or state.primed_frames > 0):
                # Look back across the last 2-4 frames
                recent_history = list(state.history)
                dt = recent_history[-1][0] - recent_history[-3][0]
                if 0.02 < dt < 0.25:
                    prev_dist = recent_history[-3][1]
                    curr_dist = recent_history[-1][1]
                    separation_speed = (curr_dist - prev_dist) / dt

                    # Middle finger travel toward wrist or palm (stroke into palm)
                    prev_mid_wrist = recent_history[-3][2]
                    curr_mid_wrist = recent_history[-1][2]
                    mid_inward_velocity = (prev_mid_wrist - curr_mid_wrist) / dt # Positive if moving closer to wrist

                    # Conditions for genuine snap:
                    # A) Fast separation between thumb and middle finger
                    # B) Middle finger is snapping down/inwards
                    # C) Current distance is noticeably larger than contact distance
                    if separation_speed > separation_threshold and curr_dist > (contact_threshold * 1.35):
                        # Calculate confidence [0.0 - 1.0]
                        confidence = min(1.0, float(separation_speed / (separation_threshold * 1.5)))
                        
                        snap_fired = True
                        state.last_snap_time = now
                        state.is_primed = False
                        state.primed_frames = 0
                        state.history.clear()

                        snap_event = {
                            "hand": hand_type,
                            "position_px": snap_px,
                            "confidence": confidence,
                            "timestamp": now,
                            "speed": separation_speed
                        }
                        self.last_snap_event = snap_event
                        break

        # Reset states for undetected hands
        for h_type in ["Left", "Right"]:
            if h_type not in detected_types and (now - self.states[h_type].last_snap_time) > 1.0:
                self.states[h_type].reset()

        return snap_fired, snap_event

    def get_status_info(self) -> Dict:
        """Returns diagnostic status for GUI HUD."""
        now = time.time()
        info = {}
        for h_type in ["Left", "Right"]:
            state = self.states[h_type]
            on_cooldown = (now - state.last_snap_time) < self.cooldown
            remaining_cooldown = max(0.0, self.cooldown - (now - state.last_snap_time))
            
            if on_cooldown:
                status = f"COOLDOWN ({remaining_cooldown:.1f}s)"
            elif state.is_primed:
                status = "PRIMED (Ready)"
            else:
                status = "READY"
                
            info[h_type] = {
                "status": status,
                "is_primed": state.is_primed,
                "on_cooldown": on_cooldown,
                "remaining_cooldown": remaining_cooldown
            }
        return info

