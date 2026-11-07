"""
Background Capture and Modeling Module.
Preserves the real physical room background so that when the person disintegrates,
the real background remains visible and natural without black voids or ghosting.
"""

import cv2
import numpy as np
from typing import Optional, Tuple

class BackgroundManager:
    """
    Manages background plate capture, temporal background synthesis,
    and hole-filling inpainting for unoccluded background reconstruction.
    """

    def __init__(self):
        self.background_frame: Optional[np.ndarray] = None
        self.coverage_map: Optional[np.ndarray] = None # float32 [0.0, 1.0] indicating filled regions
        self.is_captured: bool = False
        self.manual_override: bool = False

    def capture_manual(self, frame: np.ndarray):
        """Manually records current camera frame as the pristine background plate."""
        if frame is not None:
            self.background_frame = frame.copy()
            self.coverage_map = np.ones(frame.shape[:2], dtype=np.float32)
            self.is_captured = True
            self.manual_override = True

    def update_auto(self, frame: np.ndarray, alpha_mask: np.ndarray):
        """
        Incrementally accumulates clean background pixels in areas where no person is detected.
        As the user naturally shifts or gestures, revealed background regions are stored.
        """
        if self.manual_override or frame is None or alpha_mask is None:
            return

        h, w = frame.shape[:2]
        if self.background_frame is None or self.background_frame.shape[:2] != (h, w):
            self.background_frame = frame.copy()
            # If no manual capture yet, background coverage is initially high where alpha is low
            bg_weight = np.clip(1.0 - alpha_mask, 0.0, 1.0)
            self.coverage_map = bg_weight.copy()
            self.is_captured = True
            return

        # Pixels with alpha < 0.15 are pure background
        pure_bg_mask = (alpha_mask < 0.15).astype(np.float32)
        if np.any(pure_bg_mask > 0):
            # Running average update for clean background
            lr = 0.08
            bg_update_factor = pure_bg_mask * lr
            bg_update_factor_3ch = np.repeat(bg_update_factor[:, :, np.newaxis], 3, axis=2)

            self.background_frame = (
                self.background_frame.astype(np.float32) * (1.0 - bg_update_factor_3ch) +
                frame.astype(np.float32) * bg_update_factor_3ch
            ).astype(np.uint8)

            # Update coverage
            self.coverage_map = np.maximum(self.coverage_map, pure_bg_mask)

    def get_background(self, fallback_frame: Optional[np.ndarray] = None, person_mask: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Returns a complete, high-fidelity background image.
        If any region behind the person was not uncovered, applies edge-aware inpainting
        to seamlessly reconstruct the missing physical background.
        """
        if self.background_frame is not None:
            # If manually captured or full coverage, return directly
            if self.manual_override or self.coverage_map is None:
                return self.background_frame.copy()

            # Check if any uncovered hole exists behind the person
            uncovered_holes = (self.coverage_map < 0.3)
            if np.any(uncovered_holes):
                # Inpaint missing background regions using surrounding valid background pixels
                inpaint_mask = (uncovered_holes.astype(np.uint8)) * 255
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
                inpaint_mask = cv2.dilate(inpaint_mask, kernel, iterations=2)
                
                reconstructed = cv2.inpaint(self.background_frame, inpaint_mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
                return reconstructed

            return self.background_frame.copy()

        # If background hasn't been captured yet, fallback to inpainting the current frame behind mask
        if fallback_frame is not None and person_mask is not None:
            inpaint_mask = (person_mask > 10).astype(np.uint8) * 255
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
            inpaint_mask = cv2.dilate(inpaint_mask, kernel, iterations=2)
            bg = cv2.inpaint(fallback_frame, inpaint_mask, inpaintRadius=7, flags=cv2.INPAINT_TELEA)
            return bg

        # Absolute fallback: black or neutral frame
        if fallback_frame is not None:
            return fallback_frame.copy()
        return np.zeros((720, 1280, 3), dtype=np.uint8)

    def reset(self):
        """Resets background plate to allow new calibration."""
        self.background_frame = None
        self.coverage_map = None
        self.is_captured = False
        self.manual_override = False

