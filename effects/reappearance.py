"""
Reappearance Effect Module.
Reconstructs the person's body through a reverse particle swarm convergence,
golden energy matrix materialization, and seamless transition back to live video.
"""

import cv2
import time
import numpy as np
from typing import Tuple, Optional
from effects.particle_engine import ParticleEngine

class ReappearanceController:
    """Controls the reverse particle convergence and body reconstitution."""

    def __init__(self, particle_engine: ParticleEngine, duration: float = 2.2):
        self.engine = particle_engine
        self.duration = duration

        self.is_active = False
        self.start_time = 0.0
        self.progress = 0.0
        
        self.snap_hand = "Right"
        self.reconstruct_map: Optional[np.ndarray] = None
        self.last_shape: Optional[Tuple[int, int]] = None

    def start(self, snap_event: Optional[dict] = None, frame_shape: Tuple[int, int] = (720, 1280), alpha_mask: Optional[np.ndarray] = None):
        """Initiates the reappearance animation."""
        self.is_active = True
        self.start_time = time.time()
        self.progress = 0.0

        if snap_event:
            self.snap_hand = snap_event.get("hand", "Right")
        else:
            self.snap_hand = "Right"

        self._prepare_reconstruct_map(frame_shape)
        self._spawn_converging_swarm(frame_shape, alpha_mask)

    def _prepare_reconstruct_map(self, shape: Tuple[int, int]):
        """Generates the heightmap controlling body materialization order."""
        h, w = shape[:2]
        if self.reconstruct_map is not None and self.last_shape == (h, w):
            return

        self.last_shape = (h, w)
        y_grid, x_grid = np.indices((h, w), dtype=np.float32)
        norm_x = x_grid / w
        norm_y = y_grid / h

        # Materialization wave from snap side inwards
        if self.snap_hand == "Right":
            base_gradient = norm_x * 0.70 + (1.0 - norm_y) * 0.30
        else:
            base_gradient = (1.0 - norm_x) * 0.70 + (1.0 - norm_y) * 0.30

        noise = (np.sin(norm_x * 24.0 + norm_y * 18.0) * 0.12 +
                 np.cos(norm_x * 45.0 - norm_y * 36.0) * 0.08)

        combined = base_gradient + noise
        min_v = np.min(combined)
        max_v = np.max(combined)
        self.reconstruct_map = (combined - min_v) / (max_v - min_v + 1e-6)

    def _spawn_converging_swarm(self, frame_shape: Tuple[int, int], alpha_mask: Optional[np.ndarray]):
        """Spawns an inward-swirling particle cloud around the body silhouette."""
        h, w = frame_shape[:2]
        if alpha_mask is None or np.count_nonzero(alpha_mask > 0.2) == 0:
            # Fallback coordinates centered in frame
            cx, cy = w // 2, h // 2
            target_xs = np.random.normal(cx, w * 0.15, 3000).astype(np.int32)
            target_ys = np.random.normal(cy, h * 0.25, 3000).astype(np.int32)
        else:
            body_coords = np.where(alpha_mask > 0.25)
            num_samples = min(4000, len(body_coords[0]))
            sel = np.random.choice(len(body_coords[0]), num_samples, replace=False)
            target_ys = body_coords[0][sel]
            target_xs = body_coords[1][sel]

        num_p = len(target_xs)
        available = self.engine.max_particles - self.engine.count
        num_p = min(num_p, available)
        if num_p <= 0:
            return

        start_idx = self.engine.count
        end_idx = start_idx + num_p

        # Start positions scattered outside the body (windward and upwards)
        angles = np.random.uniform(0, 2 * np.pi, num_p)
        radii = np.random.uniform(150, 450, num_p)
        start_x = target_xs[:num_p] + np.cos(angles) * radii + np.random.uniform(50, 200, num_p)
        start_y = target_ys[:num_p] + np.sin(angles) * radii - np.random.uniform(100, 300, num_p)

        self.engine.pos[start_idx:end_idx, 0] = start_x
        self.engine.pos[start_idx:end_idx, 1] = start_y

        # Velocity pointed toward target position
        dx = target_xs[:num_p] - start_x
        dy = target_ys[:num_p] - start_y
        dist = np.sqrt(dx**2 + dy**2) + 1e-5
        speed = dist / (self.duration * 0.85)

        self.engine.vel[start_idx:end_idx, 0] = (dx / dist) * speed
        self.engine.vel[start_idx:end_idx, 1] = (dy / dist) * speed

        # Glowing golden ember colors
        colors = np.zeros((num_p, 3), dtype=np.uint8)
        colors[:, 0] = np.random.randint(40, 80, num_p)    # B
        colors[:, 1] = np.random.randint(180, 230, num_p)  # G
        colors[:, 2] = np.random.randint(240, 256, num_p)  # R (Gold/Amber)

        self.engine.color[start_idx:end_idx] = colors
        self.engine.is_glow[start_idx:end_idx] = 1
        self.engine.size[start_idx:end_idx] = np.random.uniform(1.5, 4.0, num_p)
        self.engine.initial_size[start_idx:end_idx] = self.engine.size[start_idx:end_idx]
        self.engine.life[start_idx:end_idx] = 0.0
        self.engine.max_life[start_idx:end_idx] = self.duration * 1.1
        self.engine.alpha[start_idx:end_idx] = 0.95
        self.engine.seed[start_idx:end_idx] = np.random.uniform(0, 100, num_p)

        self.engine.count = end_idx

    def update(self, dt: float) -> bool:
        """Updates reappearance progress. Returns True if active, False when done."""
        if not self.is_active:
            return False

        elapsed = time.time() - self.start_time
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
        Materializes the body as progress advances from 0 to 1.
        Returns:
            reconstructed_bgr: Person image with golden energy shimmer
            reconstructed_alpha: Alpha mask matching the currently reformed body
        """
        h, w = person_bgr.shape[:2]
        if self.reconstruct_map is None or self.last_shape != (h, w):
            self._prepare_reconstruct_map((h, w))

        # Reconstructed body region
        reformed_mask = (self.reconstruct_map <= self.progress) & (alpha_mask > 0.15)

        # Active materialization boundary rim
        rim_mask = (self.reconstruct_map >= self.progress - 0.06) & (self.reconstruct_map <= self.progress) & (alpha_mask > 0.15)

        reconstructed_bgr = person_bgr.copy()
        if np.any(rim_mask):
            energy_overlay = np.zeros_like(person_bgr)
            # Bright golden-cyan energy edge in BGR: (255, 220, 60)
            energy_overlay[rim_mask] = (255, 215, 50)
            reconstructed_bgr = cv2.addWeighted(reconstructed_bgr, 0.8, energy_overlay, 0.85, 0)

        # Alpha increases with materialization
        reconstructed_alpha = np.zeros_like(alpha_mask)
        reconstructed_alpha[reformed_mask] = alpha_mask[reformed_mask]

        return reconstructed_bgr, reconstructed_alpha

