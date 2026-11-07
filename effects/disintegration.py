"""
Disintegration Effect Module.
Orchestrates the progressive peeling erosion wave, burning ember rim, and particle emission
to recreate the iconic Avengers: Infinity War disintegration effect.
"""

import cv2
import time
import numpy as np
from typing import Tuple, Optional
from effects.particle_engine import ParticleEngine

class DisintegrationController:
    """Controls the progressive dissolution wave and particle spawning."""

    def __init__(self, particle_engine: ParticleEngine, duration: float = 2.4):
        self.engine = particle_engine
        self.duration = duration
        
        self.is_active = False
        self.start_time = 0.0
        self.progress = 0.0
        self.prev_progress = 0.0
        
        self.snap_origin = (640, 360)
        self.snap_hand = "Right"
        
        # Precomputed noise map for turbulent edge dissolution
        self.noise_map: Optional[np.ndarray] = None
        self.erosion_map: Optional[np.ndarray] = None
        self.last_shape: Optional[Tuple[int, int]] = None

    def start(self, snap_event: Optional[dict] = None, frame_shape: Tuple[int, int] = (720, 1280)):
        """Initiates the disintegration animation."""
        self.is_active = True
        self.start_time = time.time()
        self.progress = 0.0
        self.prev_progress = 0.0

        if snap_event:
            self.snap_hand = snap_event.get("hand", "Right")
            self.snap_origin = snap_event.get("position_px", (frame_shape[1] // 2, frame_shape[0] // 2))
        else:
            self.snap_hand = "Right"
            self.snap_origin = (frame_shape[1] // 2, frame_shape[0] // 2)

        self._prepare_erosion_map(frame_shape)

    def _prepare_erosion_map(self, shape: Tuple[int, int]):
        """Generates a turbulent heightmap that dictates the sequence of pixel dissolution."""
        h, w = shape[:2]
        if self.erosion_map is not None and self.last_shape == (h, w):
            return

        self.last_shape = (h, w)

        # Coordinate grids
        y_grid, x_grid = np.indices((h, w), dtype=np.float32)
        norm_x = x_grid / w
        norm_y = y_grid / h

        # Directional gradient based on snap side
        # If right hand snapped, dissolve moves right-to-left.
        # If left hand snapped, dissolve moves left-to-right.
        if self.snap_hand == "Right":
            base_gradient = (1.0 - norm_x) * 0.70 + norm_y * 0.30
        else:
            base_gradient = norm_x * 0.70 + norm_y * 0.30

        # Multi-scale sinusoidal fractal noise to create organic flaky disintegration
        noise1 = np.sin(norm_x * 18.0 + norm_y * 12.0) * 0.15
        noise2 = np.cos(norm_x * 35.0 - norm_y * 28.0) * 0.10
        noise3 = np.sin(norm_x * 70.0 + norm_y * 65.0) * 0.05
        turbulent_noise = noise1 + noise2 + noise3

        combined = base_gradient + turbulent_noise
        min_v = np.min(combined)
        max_v = np.max(combined)
        self.erosion_map = (combined - min_v) / (max_v - min_v + 1e-6)

    def update(self, dt: float) -> bool:
        """
        Updates the disintegration progress.
        Returns True while active, False when finished.
        """
        if not self.is_active:
            return False

        elapsed = time.time() - self.start_time
        self.prev_progress = self.progress
        self.progress = float(np.clip(elapsed / self.duration, 0.0, 1.0))

        if self.progress >= 1.0:
            self.is_active = False
            return False
        return True

    def apply(self,
              person_bgr: np.ndarray,
              alpha_mask: np.ndarray,
              dt: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Erodes the person mask, emits dust particles, and adds glowing ember rims.
        Returns:
            eroded_bgr: Person image with disintegrated pixels removed and glowing rims added
            eroded_alpha: Alpha mask reflecting the remaining body
        """
        h, w = person_bgr.shape[:2]
        if self.erosion_map is None or self.last_shape != (h, w):
            self._prepare_erosion_map((h, w))

        # Determine which pixels remain visible and which are newly dissolved
        visible_mask = (self.erosion_map > self.progress) & (alpha_mask > 0.15)
        newly_eroded_mask = (self.erosion_map >= self.prev_progress) & (self.erosion_map < self.progress) & (alpha_mask > 0.15)

        # 1. Spawn particles at newly eroded pixels
        new_coords = np.where(newly_eroded_mask)
        if len(new_coords[0]) > 0:
            # Blast normal: particles fly away from the dissolution wave
            blast_dir = (-1.0, -0.35) if self.snap_hand == "Right" else (1.0, -0.35)
            self.engine.spawn_from_dissolution(new_coords, person_bgr, spawn_fraction=0.35, normal_dir=blast_dir)

        # 2. Glowing burning edge (rim right at the current dissolution threshold)
        edge_thickness = 0.04
        burning_rim_mask = (self.erosion_map >= self.progress) & (self.erosion_map <= self.progress + edge_thickness) & (alpha_mask > 0.15)

        eroded_bgr = person_bgr.copy()
        if np.any(burning_rim_mask):
            ember_overlay = np.zeros_like(person_bgr)
            ember_overlay[burning_rim_mask] = self.engine.ember_color
            eroded_bgr = cv2.addWeighted(eroded_bgr, 0.75, ember_overlay, 0.85, 0)

        # 3. Create updated alpha mask
        eroded_alpha = np.zeros_like(alpha_mask)
        eroded_alpha[visible_mask] = alpha_mask[visible_mask]

        return eroded_bgr, eroded_alpha

