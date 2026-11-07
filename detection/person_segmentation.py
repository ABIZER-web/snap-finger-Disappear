"""
Person Segmentation Module using MediaPipe ImageSegmenter.
Extracts clean, feathered, anti-aliased person masks separating human foreground from background.
"""

import os
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision
from typing import Tuple, Optional

class PersonSegmenter:
    """
    Performs high-resolution person segmentation.
    Produces:
      - Clean binary mask (0 or 255)
      - Soft alpha mask (float32 [0.0, 1.0]) with feathered edge feathering
      - Bounding box and contour coordinates of the person
    """

    def __init__(self, model_path: str, threshold: float = 0.50, feather_radius: int = 5):
        self.model_path = model_path
        self.threshold = threshold
        self.feather_radius = feather_radius
        self.segmenter = None
        self._prev_mask: Optional[np.ndarray] = None
        self._init_model()

    def _init_model(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Selfie segmenter model not found at: {self.model_path}")

        base_options = mp_python.BaseOptions(model_asset_path=self.model_path)
        options = vision.ImageSegmenterOptions(
            base_options=base_options,
            output_confidence_masks=True
        )
        self.segmenter = vision.ImageSegmenter.create_from_options(options)

    def process(self, bgr_frame: np.ndarray, temporal_alpha: float = 0.75) -> Tuple[np.ndarray, np.ndarray, Optional[Tuple[int, int, int, int]]]:
        """
        Segments person from the camera frame.
        Args:
            bgr_frame: Input BGR image (H, W, 3)
            temporal_alpha: Weight for temporal smoothing (prevents edge jitter)
        Returns:
            binary_mask: uint8 (H, W), values 0 or 255
            alpha_mask: float32 (H, W), values in [0.0, 1.0] with anti-aliasing
            bbox: (x, y, w, h) bounding box of detected person or None
        """
        if self.segmenter is None or bgr_frame is None:
            h, w = bgr_frame.shape[:2] if bgr_frame is not None else (480, 640)
            return np.zeros((h, w), dtype=np.uint8), np.zeros((h, w), dtype=np.float32), None

        h, w = bgr_frame.shape[:2]
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        result = self.segmenter.segment(mp_image)
        if not result.confidence_masks:
            return np.zeros((h, w), dtype=np.uint8), np.zeros((h, w), dtype=np.float32), None

        # Extract raw confidence float32 [0.0, 1.0]
        raw_mask = result.confidence_masks[0].numpy_view()
        if raw_mask.ndim == 3:
            raw_mask = raw_mask[:, :, 0]

        # Resize if dimensions differ from original
        if raw_mask.shape[:2] != (h, w):
            raw_mask = cv2.resize(raw_mask, (w, h), interpolation=cv2.INTER_LINEAR)

        # Temporal smoothing to eliminate frame-to-frame edge shimmer
        if self._prev_mask is not None and self._prev_mask.shape == raw_mask.shape:
            raw_mask = temporal_alpha * raw_mask + (1.0 - temporal_alpha) * self._prev_mask
        self._prev_mask = raw_mask.copy()

        # Generate binary thresholded mask
        binary_mask = (raw_mask > self.threshold).astype(np.uint8) * 255

        # Morphological clean-up: close holes in clothes/hair, eliminate lone pixel noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)
        binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)

        # Smooth feathered alpha mask along boundaries
        if self.feather_radius > 0:
            ksize = self.feather_radius * 2 + 1
            feathered = cv2.GaussianBlur(raw_mask, (ksize, ksize), 0)
            # Re-normalize feathered mask for crisp contrast while retaining soft perimeter
            alpha_mask = np.clip((feathered - (self.threshold - 0.2)) / 0.4, 0.0, 1.0).astype(np.float32)
        else:
            alpha_mask = (binary_mask.astype(np.float32) / 255.0)

        # Compute bounding box
        coords = cv2.findNonZero(binary_mask)
        bbox = cv2.boundingRect(coords) if coords is not None else None

        return binary_mask, alpha_mask, bbox

