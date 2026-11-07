"""
Unit tests for the Biomechanical Snap Detector.
Tests primed states, explosive release kinematics, sensitivity, cooldown, and false positive rejection.
"""

import unittest
import time
import numpy as np
from detection.snap_detector import SnapDetector

class TestSnapDetector(unittest.TestCase):

    def setUp(self):
        self.detector = SnapDetector(sensitivity=0.70, cooldown=1.0, left_enabled=True, right_enabled=True)

    def _create_mock_hand(self, thumb_mid_dist: float, handedness: str = "Right") -> dict:
        """Constructs synthetic normalized landmarks for a hand with controlled thumb-middle distance."""
        lms_norm = np.zeros((21, 3), dtype=np.float32)
        # Wrist at (0.5, 0.8)
        lms_norm[0] = [0.5, 0.8, 0.0]
        # Middle MCP at (0.5, 0.5) -> hand_scale = 0.3
        lms_norm[9] = [0.5, 0.5, 0.0]
        
        # Index tip far away at (0.4, 0.3)
        lms_norm[8] = [0.4, 0.3, 0.0]

        # Thumb tip at (0.5, 0.4)
        lms_norm[4] = [0.5, 0.4, 0.0]
        # Middle tip at thumb_tip + (0, thumb_mid_dist * hand_scale)
        lms_norm[12] = [0.5, 0.4 + (thumb_mid_dist * 0.3), 0.0]

        lms_px = (lms_norm[:, :2] * np.array([640, 480])).astype(np.int32)

        return {
            "handedness": handedness,
            "landmarks_norm": lms_norm,
            "landmarks_px": lms_px,
            "score": 0.95
        }

    def test_primed_state(self):
        """Tests that holding thumb and middle finger together primes the snap state."""
        # Frame 1: Thumb and middle touching (normalized dist = 0.03)
        hand1 = self._create_mock_hand(thumb_mid_dist=0.03)
        is_snap, _ = self.detector.detect([hand1])
        self.assertFalse(is_snap)

        # Frame 2: Still touching -> should be primed
        is_snap, _ = self.detector.detect([hand1])
        self.assertFalse(is_snap)
        self.assertTrue(self.detector.states["Right"].is_primed)

    def test_snap_trigger(self):
        """Tests that an abrupt separation following a primed state fires a snap event."""
        hand_primed = self._create_mock_hand(thumb_mid_dist=0.02)
        
        # Prime the hand over 3 frames
        for _ in range(3):
            self.detector.detect([hand_primed])
            time.sleep(0.03)

        self.assertTrue(self.detector.states["Right"].is_primed)

        # Frame 4: Sudden explosive release (thumb_mid_dist jumps from 0.02 to 0.40)
        hand_released = self._create_mock_hand(thumb_mid_dist=0.45)
        time.sleep(0.04)
        is_snap, event = self.detector.detect([hand_released])

        self.assertTrue(is_snap)
        self.assertIsNotNone(event)
        self.assertEqual(event["hand"], "Right")
        self.assertGreater(event["confidence"], 0.0)

    def test_cooldown_rejection(self):
        """Tests that another snap cannot immediately fire within the cooldown window."""
        self.detector.set_cooldown(1.5)
        self.detector.states["Right"].last_snap_time = time.time() - 0.2 # 0.2s ago

        hand_primed = self._create_mock_hand(thumb_mid_dist=0.02)
        self.detector.detect([hand_primed])

        hand_released = self._create_mock_hand(thumb_mid_dist=0.45)
        is_snap, _ = self.detector.detect([hand_released])
        self.assertFalse(is_snap, "Snap should have been rejected due to active cooldown.")

    def test_left_hand_toggle(self):
        """Tests that disabling the left hand prevents it from triggering a snap."""
        self.detector.set_hands_enabled(left=False, right=True)

        hand_left = self._create_mock_hand(thumb_mid_dist=0.02, handedness="Left")
        for _ in range(3):
            self.detector.detect([hand_left])
            time.sleep(0.03)

        hand_released = self._create_mock_hand(thumb_mid_dist=0.45, handedness="Left")
        time.sleep(0.04)
        is_snap, _ = self.detector.detect([hand_released])
        self.assertFalse(is_snap, "Left hand snap should be ignored when left hand is disabled.")

if __name__ == "__main__":
    unittest.main()

