"""
Hand Tracking Module using MediaPipe Tasks Vision.
Tracks hands, landmarks, and handedness in real-time camera frames.
"""

import os
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
from typing import List, Dict, Tuple, Optional

class HandTracker:
    """Detects and tracks 21 hand landmarks for up to 2 hands."""

    # Landmark index constants
    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_DIP = 7
    INDEX_TIP = 8
    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_DIP = 11
    MIDDLE_TIP = 12
    RING_MCP = 13
    RING_PIP = 14
    RING_DIP = 15
    RING_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20

    # Skeleton connections
    CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
        (0, 5), (5, 6), (6, 7), (7, 8),        # Index
        (0, 9), (9, 10), (10, 11), (11, 12),    # Middle
        (0, 13), (13, 14), (14, 15), (15, 16), # Ring
        (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
        (5, 9), (9, 13), (13, 17)              # Palm base
    ]

    def __init__(self, model_path: str, max_hands: int = 2):
        self.model_path = model_path
        self.max_hands = max_hands
        self.detector = None
        self._init_detector()

    def _init_detector(self):
        """Initializes the MediaPipe HandLandmarker."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Hand landmark model not found at: {self.model_path}")

        base_options = mp_python.BaseOptions(model_asset_path=self.model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=self.max_hands,
            min_hand_detection_confidence=0.55,
            min_hand_presence_confidence=0.55,
            min_tracking_confidence=0.55
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

    def process(self, bgr_frame: np.ndarray) -> List[Dict]:
        """
        Processes a BGR video frame and returns a list of tracked hands.
        Each hand dict contains:
            - 'handedness': 'Left' or 'Right'
            - 'landmarks_norm': np.ndarray of shape (21, 3) normalized [0, 1]
            - 'landmarks_px': np.ndarray of shape (21, 2) pixel coords (x, y)
            - 'score': float confidence score
        """
        if self.detector is None or bgr_frame is None:
            return []

        h, w = bgr_frame.shape[:2]
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        
        result = self.detector.detect(mp_image)
        tracked_hands = []

        if result.hand_landmarks and len(result.hand_landmarks) > 0:
            for idx, hand_lms in enumerate(result.hand_landmarks):
                # Extract handedness label ('Left' / 'Right')
                label = "Unknown"
                score = 0.9
                if result.handedness and idx < len(result.handedness):
                    category = result.handedness[idx][0]
                    label = category.category_name or category.display_name or "Unknown"
                    score = category.score

                # Extract normalized and pixel coordinates
                norm_coords = np.array([[lm.x, lm.y, lm.z] for lm in hand_lms], dtype=np.float32)
                px_coords = np.zeros((21, 2), dtype=np.int32)
                px_coords[:, 0] = np.clip((norm_coords[:, 0] * w).astype(np.int32), 0, w - 1)
                px_coords[:, 1] = np.clip((norm_coords[:, 1] * h).astype(np.int32), 0, h - 1)

                tracked_hands.append({
                    "handedness": label,
                    "landmarks_norm": norm_coords,
                    "landmarks_px": px_coords,
                    "score": float(score)
                })

        return tracked_hands

    def draw_hands(self, frame: np.ndarray, tracked_hands: List[Dict], draw_glow: bool = True) -> np.ndarray:
        """Draws aesthetic glowing hand skeletons onto the given frame."""
        overlay = frame.copy()
        
        for hand in tracked_hands:
            pts = hand["landmarks_px"]
            is_right = hand["handedness"] == "Right"
            bone_color = (255, 180, 50) if is_right else (200, 100, 255) # Amber for Right, Purple for Left
            glow_color = (255, 230, 120) if is_right else (240, 160, 255)

            # Draw bones
            for p1_idx, p2_idx in self.CONNECTIONS:
                p1 = tuple(pts[p1_idx])
                p2 = tuple(pts[p2_idx])
                cv2.line(overlay, p1, p2, bone_color, 2, cv2.LINE_AA)

            # Draw joints
            for i, p in enumerate(pts):
                radius = 4 if i in [4, 8, 12, 16, 20] else 3
                if i in [4, 12]: # Thumb and middle fingertips highlighted
                    cv2.circle(overlay, tuple(p), 6, glow_color, -1, cv2.LINE_AA)
                    cv2.circle(overlay, tuple(p), 8, (255, 255, 255), 1, cv2.LINE_AA)
                else:
                    cv2.circle(overlay, tuple(p), radius, bone_color, -1, cv2.LINE_AA)

        if draw_glow:
            cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)
        else:
            np.copyto(frame, overlay)
            
        return frame

