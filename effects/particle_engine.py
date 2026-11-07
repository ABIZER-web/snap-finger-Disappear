"""
High-Performance Particle Engine for Avengers Dust Disintegration.
Uses fully vectorized NumPy operations for simulating thousands of dust, ash,
and glowing ember particles in real-time.
"""

import cv2
import time
import numpy as np
from typing import Tuple, Optional

class ParticleEngine:
    """
    Simulates dynamic dust, ash, and glowing embers.
    Features:
      - Real body pixel color sampling
      - Golden glowing embers with additive blending
      - Dark carbon ash fragments and flaky dust
      - Simplex/Curl-like sinusoidal aerodynamic turbulence
      - Dynamic thermal buoyancy and wind drift
    """

    def __init__(self, max_particles: int = 15000):
        self.max_particles = max_particles
        self.count = 0

        # Pre-allocated contiguous numpy buffers
        self.pos = np.zeros((max_particles, 2), dtype=np.float32)        # (x, y)
        self.vel = np.zeros((max_particles, 2), dtype=np.float32)        # (vx, vy)
        self.color = np.zeros((max_particles, 3), dtype=np.uint8)        # BGR
        self.alpha = np.zeros(max_particles, dtype=np.float32)           # [0.0, 1.0]
        self.size = np.zeros(max_particles, dtype=np.float32)            # Radius in px
        self.initial_size = np.zeros(max_particles, dtype=np.float32)    # Base size
        self.life = np.zeros(max_particles, dtype=np.float32)            # Elapsed life in sec
        self.max_life = np.zeros(max_particles, dtype=np.float32)        # Max life in sec
        self.is_glow = np.zeros(max_particles, dtype=np.uint8)           # 1 for glowing ember, 0 for ash
        self.seed = np.zeros(max_particles, dtype=np.float32)            # Random phase for turbulence

        # Target coordinates for reverse reappearance
        self.target_pos = np.zeros((max_particles, 2), dtype=np.float32)

        # Environmental parameters
        self.wind_x = 220.0             # Horizontal drift
        self.wind_y = -130.0            # Thermal buoyancy (upwards)
        self.turbulence = 50.0          # Aerodynamic turbulence scale
        self.drag = 0.85                # Air resistance
        self.glow_intensity = 0.85      # Additive blend strength

        # Preset Colors (BGR)
        self.ember_color = (50, 215, 255)
        self.alt_color = (30, 110, 255)

        self.last_update_time = time.time()

    def set_preset_colors(self, ember_bgr: tuple, alt_bgr: tuple):
        """Updates particle color palette based on active character preset."""
        self.ember_color = ember_bgr
        self.alt_color = alt_bgr

    def reset(self):
        """Clears all active particles."""
        self.count = 0

    def spawn_from_dissolution(self,
                               coords_yx: Tuple[np.ndarray, np.ndarray],
                               source_bgr: np.ndarray,
                               spawn_fraction: float = 0.40,
                               normal_dir: Tuple[float, float] = (1.0, -0.3)):
        """
        Spawns particles at the active erosion wave front.
        Args:
            coords_yx: Tuple of (y_indices, x_indices) of newly eroded body pixels
            source_bgr: Webcam frame to sample real skin/hair/clothes colors from
            spawn_fraction: Percentage of pixels that spawn visible particles
            normal_dir: Outward blast normal vector (nx, ny)
        """
        num_pixels = len(coords_yx[0])
        if num_pixels == 0 or self.count >= self.max_particles:
            return

        # Determine how many particles to spawn
        num_to_spawn = int(num_pixels * spawn_fraction)
        if num_to_spawn <= 0:
            return

        available_slots = self.max_particles - self.count
        num_to_spawn = min(num_to_spawn, available_slots)

        # Randomly sample pixel indices
        sampled_indices = np.random.choice(num_pixels, num_to_spawn, replace=False)
        y_sel = coords_yx[0][sampled_indices]
        x_sel = coords_yx[1][sampled_indices]

        start_idx = self.count
        end_idx = start_idx + num_to_spawn

        # 1. Initial Positions
        self.pos[start_idx:end_idx, 0] = x_sel.astype(np.float32) + np.random.uniform(-1.5, 1.5, num_to_spawn)
        self.pos[start_idx:end_idx, 1] = y_sel.astype(np.float32) + np.random.uniform(-1.5, 1.5, num_to_spawn)

        # 2. Initial Velocities: Outward blast + random thermal scatter
        nx, ny = normal_dir
        burst_speed = np.random.uniform(40.0, 160.0, num_to_spawn)
        angle_jitter = np.random.uniform(-0.8, 0.8, num_to_spawn)

        # Direction rotated by angle jitter
        cos_j = np.cos(angle_jitter)
        sin_j = np.sin(angle_jitter)
        dir_x = nx * cos_j - ny * sin_j
        dir_y = nx * sin_j + ny * cos_j

        self.vel[start_idx:end_idx, 0] = dir_x * burst_speed + np.random.uniform(-30.0, 30.0, num_to_spawn)
        self.vel[start_idx:end_idx, 1] = dir_y * burst_speed + np.random.uniform(-40.0, 10.0, num_to_spawn)

        # 3. Particle Colors & Types
        # Sample genuine pixel colors from camera frame
        sampled_colors = source_bgr[y_sel, x_sel]
        
        # Determine particle types:
        # 65% real body color fragments, 20% glowing golden embers, 15% dark carbon ash
        rand_types = np.random.uniform(0.0, 1.0, num_to_spawn)
        
        colors = sampled_colors.copy()
        glow_flags = np.zeros(num_to_spawn, dtype=np.uint8)

        # Glowing Embers (20%)
        ember_mask = (rand_types > 0.65) & (rand_types <= 0.85)
        num_embers = np.count_nonzero(ember_mask)
        if num_embers > 0:
            e_b, e_g, e_r = self.ember_color
            colors[ember_mask, 0] = np.clip(e_b + np.random.randint(-20, 20, num_embers), 0, 255)
            colors[ember_mask, 1] = np.clip(e_g + np.random.randint(-20, 20, num_embers), 0, 255)
            colors[ember_mask, 2] = np.clip(e_r + np.random.randint(-20, 20, num_embers), 0, 255)
            glow_flags[ember_mask] = 1

        # Dark Ash Fragments (15%)
        ash_mask = rand_types > 0.85
        ash_gray = np.random.randint(35, 75, np.count_nonzero(ash_mask), dtype=np.uint8)
        colors[ash_mask, 0] = ash_gray
        colors[ash_mask, 1] = ash_gray
        colors[ash_mask, 2] = ash_gray
        glow_flags[ash_mask] = 0

        # Body pixels: add slight contrast/saturation boost
        body_mask = rand_types <= 0.65
        colors[body_mask] = np.clip(colors[body_mask].astype(np.int16) * 1.15, 0, 255).astype(np.uint8)
        # Small percentage of body fragments also spark
        spark_mask = body_mask & (np.random.uniform(0.0, 1.0, num_to_spawn) < 0.25)
        glow_flags[spark_mask] = 1

        self.color[start_idx:end_idx] = colors
        self.is_glow[start_idx:end_idx] = glow_flags

        # 4. Sizes & Lifetimes
        sizes = np.random.uniform(1.2, 4.5, num_to_spawn).astype(np.float32)
        # Glowing embers are slightly smaller and more intense
        sizes[ember_mask] = np.random.uniform(1.0, 3.2, np.count_nonzero(ember_mask))
        self.initial_size[start_idx:end_idx] = sizes
        self.size[start_idx:end_idx] = sizes

        lifespans = np.random.uniform(1.8, 3.2, num_to_spawn).astype(np.float32)
        self.max_life[start_idx:end_idx] = lifespans
        self.life[start_idx:end_idx] = 0.0
        self.alpha[start_idx:end_idx] = 1.0
        self.seed[start_idx:end_idx] = np.random.uniform(0.0, 100.0, num_to_spawn)

        self.count = end_idx

    def update(self, dt: float):
        """Advances particle physics simulation by dt seconds."""
        if self.count == 0:
            return

        dt = float(np.clip(dt, 0.001, 0.05))
        now = time.time()
        n = self.count

        # Slices of active particles
        p_pos = self.pos[:n]
        p_vel = self.vel[:n]
        p_life = self.life[:n]
        p_max_life = self.max_life[:n]
        p_seed = self.seed[:n]

        # 1. Age progression
        p_life += dt

        # 2. Turbulence calculations (Curl-noise approximation using dual sine waves)
        turb_x = np.sin(p_pos[:, 1] * 0.015 + p_seed + now * 3.5) * self.turbulence
        turb_y = np.cos(p_pos[:, 0] * 0.015 + p_seed * 1.5 + now * 3.0) * (self.turbulence * 0.75)

        # 3. Aerodynamic forces: Wind drift + thermal draft + turbulence
        target_vx = self.wind_x + turb_x
        target_vy = self.wind_y + turb_y

        p_vel[:, 0] += (target_vx - p_vel[:, 0]) * (self.drag * dt * 2.5)
        p_vel[:, 1] += (target_vy - p_vel[:, 1]) * (self.drag * dt * 2.5)

        # 4. Integrate position
        p_pos += p_vel * dt

        # 5. Dynamic Alpha and Shrinking Size
        life_ratio = np.clip(p_life / p_max_life, 0.0, 1.0)
        self.alpha[:n] = np.clip(1.0 - (life_ratio ** 1.3), 0.0, 1.0)
        self.size[:n] = self.initial_size[:n] * (1.0 - 0.45 * life_ratio)

        # 6. Cull dead or off-screen particles
        alive_mask = (p_life < p_max_life) & (p_pos[:, 1] > -50) & (p_pos[:, 0] < 2000) & (p_pos[:, 0] > -100)
        num_alive = np.count_nonzero(alive_mask)

        if num_alive < n:
            # Compress arrays keeping only alive particles
            self.pos[:num_alive] = self.pos[:n][alive_mask]
            self.vel[:num_alive] = self.vel[:n][alive_mask]
            self.color[:num_alive] = self.color[:n][alive_mask]
            self.alpha[:num_alive] = self.alpha[:n][alive_mask]
            self.size[:num_alive] = self.size[:n][alive_mask]
            self.initial_size[:num_alive] = self.initial_size[:n][alive_mask]
            self.life[:num_alive] = self.life[:n][alive_mask]
            self.max_life[:num_alive] = self.max_life[:n][alive_mask]
            self.is_glow[:num_alive] = self.is_glow[:n][alive_mask]
            self.seed[:num_alive] = self.seed[:n][alive_mask]
            self.count = num_alive

    def render(self, target_frame: np.ndarray) -> np.ndarray:
        """
        Renders active particles onto target_frame with high-performance OpenCV blending.
        Glowing particles receive additive bloom blending.
        """
        if self.count == 0 or target_frame is None:
            return target_frame

        h, w = target_frame.shape[:2]
        n = self.count

        # Screen-space bounding filter
        xs = self.pos[:n, 0].astype(np.int32)
        ys = self.pos[:n, 1].astype(np.int32)
        valid = (xs >= 0) & (xs < w) & (ys >= 0) & (ys < h) & (self.alpha[:n] > 0.05)
        
        valid_indices = np.where(valid)[0]
        if len(valid_indices) == 0:
            return target_frame

        # Split into solid dust particles and glowing embers
        glow_flags = self.is_glow[valid_indices]
        glow_idx = valid_indices[glow_flags == 1]
        solid_idx = valid_indices[glow_flags == 0]

        # 1. Render Solid Ash / Body Pixel Dust
        if len(solid_idx) > 0:
            s_xs = xs[solid_idx]
            s_ys = ys[solid_idx]
            s_sizes = np.clip(self.size[solid_idx].astype(np.int32), 1, 6)
            s_colors = self.color[solid_idx]
            s_alphas = self.alpha[solid_idx]

            # For fine particles (size == 1), direct numpy indexing is blazing fast
            fine_mask = (s_sizes == 1)
            if np.any(fine_mask):
                fx = s_xs[fine_mask]
                fy = s_ys[fine_mask]
                fa = s_alphas[fine_mask, np.newaxis]
                fc = s_colors[fine_mask]
                target_frame[fy, fx] = (target_frame[fy, fx].astype(np.float32) * (1.0 - fa) + fc.astype(np.float32) * fa).astype(np.uint8)

            # For larger fragments, draw discs
            large_mask = ~fine_mask
            if np.any(large_mask):
                for idx in np.where(large_mask)[0]:
                    x = int(s_xs[idx])
                    y = int(s_ys[idx])
                    r = int(s_sizes[idx])
                    b, g, r_col = int(s_colors[idx][0]), int(s_colors[idx][1]), int(s_colors[idx][2])
                    cv2.circle(target_frame, (x, y), r, (b, g, r_col), -1, cv2.LINE_AA)

        # 2. Render Glowing Embers (Additive Blending)
        if len(glow_idx) > 0:
            g_xs = xs[glow_idx]
            g_ys = ys[glow_idx]
            g_sizes = np.clip(self.size[glow_idx].astype(np.int32), 1, 5)
            g_colors = self.color[glow_idx]
            g_alphas = self.alpha[glow_idx] * self.glow_intensity

            # Additive accumulator layer
            glow_layer = np.zeros_like(target_frame)

            for idx in range(len(glow_idx)):
                x = int(g_xs[idx])
                y = int(g_ys[idx])
                r = int(g_sizes[idx])
                a = float(g_alphas[idx])
                col = (
                    int(g_colors[idx][0] * a),
                    int(g_colors[idx][1] * a),
                    int(g_colors[idx][2] * a)
                )
                # Inner hot core
                cv2.circle(glow_layer, (x, y), r, col, -1, cv2.LINE_AA)
                # Outer glow halo
                cv2.circle(glow_layer, (x, y), r + 2, (int(col[0] * 0.4), int(col[1] * 0.4), int(col[2] * 0.4)), -1, cv2.LINE_AA)

            # Add glow layer to target frame
            target_frame = cv2.add(target_frame, glow_layer)

        return target_frame

