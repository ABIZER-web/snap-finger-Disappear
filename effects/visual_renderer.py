"""
Visual Renderer and Compositor Module.
Coordinates the state machine, background compositing, particle simulations,
and visual feedback pulses into the final cinematic video frame.
"""

import cv2
import time
import numpy as np
from typing import Tuple, Dict, Optional, List

from config import (
    STATE_NORMAL,
    STATE_DISAPPEARING,
    STATE_INVISIBLE,
    STATE_REAPPEARING
)
from effects.particle_engine import ParticleEngine
from effects.disintegration import DisintegrationController
from effects.reappearance import ReappearanceController
from camera.background_capture import BackgroundManager

class VisualRenderer:
    """Master VFX Compositor and State Machine."""

    def __init__(self,
                 particle_engine: ParticleEngine,
                 background_manager: BackgroundManager,
                 disappear_duration: float = 2.4,
                 reappear_duration: float = 2.2):
        self.engine = particle_engine
        self.bg_manager = background_manager
        
        self.disintegrate_ctrl = DisintegrationController(self.engine, duration=disappear_duration)
        self.reappear_ctrl = ReappearanceController(self.engine, duration=reappear_duration)

        self.state = STATE_NORMAL
        self.last_frame_time = time.time()
        
        # Snap Flash Pulse effect
        self.snap_pulse: Optional[Dict] = None # {'x': int, 'y': int, 'start_time': float, 'duration': 0.35}

        # Stored frozen body snapshot at moment of snap (prevents segmentation jitter while dissolving)
        self.frozen_body_frame: Optional[np.ndarray] = None
        self.frozen_alpha_mask: Optional[np.ndarray] = None

    def trigger_disappear(self, snap_event: Optional[Dict] = None, current_frame: Optional[np.ndarray] = None, alpha_mask: Optional[np.ndarray] = None):
        """Triggers the disappearance sequence."""
        if self.state != STATE_NORMAL:
            return

        h, w = current_frame.shape[:2] if current_frame is not None else (720, 1280)
        
        # Freeze current appearance for pristine dissolution
        if current_frame is not None and alpha_mask is not None:
            self.frozen_body_frame = current_frame.copy()
            self.frozen_alpha_mask = alpha_mask.copy()
            # Ensure background has a clean snapshot
            if not self.bg_manager.is_captured:
                self.bg_manager.capture_manual(self.bg_manager.get_background(current_frame, alpha_mask))

        self.state = STATE_DISAPPEARING
        self.disintegrate_ctrl.start(snap_event=snap_event, frame_shape=(h, w))

        # Start snap flash pulse
        if snap_event:
            px, py = snap_event.get("position_px", (w // 2, h // 2))
            self.snap_pulse = {
                "x": px,
                "y": py,
                "start_time": time.time(),
                "duration": 0.35
            }

    def trigger_reappear(self, snap_event: Optional[Dict] = None, current_frame: Optional[np.ndarray] = None, alpha_mask: Optional[np.ndarray] = None):
        """Triggers the reappearance sequence."""
        if self.state != STATE_INVISIBLE and self.state != STATE_DISAPPEARING:
            return

        h, w = current_frame.shape[:2] if current_frame is not None else (720, 1280)
        
        # Use frozen mask if current is empty
        active_mask = alpha_mask if (alpha_mask is not None and np.count_nonzero(alpha_mask > 0.2) > 500) else self.frozen_alpha_mask

        self.state = STATE_REAPPEARING
        self.reappear_ctrl.start(snap_event=snap_event, frame_shape=(h, w), alpha_mask=active_mask)

        # Start snap flash pulse
        if snap_event:
            px, py = snap_event.get("position_px", (w // 2, h // 2))
            self.snap_pulse = {
                "x": px,
                "y": py,
                "start_time": time.time(),
                "duration": 0.35
            }

    def reset_to_normal(self):
        """Emergency restore back to normal camera mode."""
        self.state = STATE_NORMAL
        self.disintegrate_ctrl.is_active = False
        self.reappear_ctrl.is_active = False
        self.engine.reset()
        self.snap_pulse = None

    def render(self,
               raw_frame: np.ndarray,
               binary_mask: np.ndarray,
               alpha_mask: np.ndarray,
               tracked_hands: List[Dict],
               show_landmarks: bool = False) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Main rendering pipeline.
        Returns:
            processed_output: Final cinematic video frame
            mask_preview: Visual representation of segmentation
            bg_preview: Clean background plate
        """
        now = time.time()
        dt = now - self.last_frame_time
        self.last_frame_time = now

        h, w = raw_frame.shape[:2]

        # 1. Background Retrieval & Auto-Accumulation
        if self.state == STATE_NORMAL:
            self.bg_manager.update_auto(raw_frame, alpha_mask)

        clean_bg = self.bg_manager.get_background(fallback_frame=raw_frame, person_mask=binary_mask)

        # 2. State Machine Execution
        if self.state == STATE_NORMAL:
            # Normal camera view
            output_frame = raw_frame.copy()

        elif self.state == STATE_DISAPPEARING:
            # Update disintegration
            is_active = self.disintegrate_ctrl.update(dt)
            
            # Use frozen body frame to eliminate real-time mask shivering during dissolution
            body_frame = self.frozen_body_frame if self.frozen_body_frame is not None else raw_frame
            b_alpha = self.frozen_alpha_mask if self.frozen_alpha_mask is not None else alpha_mask

            eroded_bgr, eroded_alpha = self.disintegrate_ctrl.apply(body_frame, b_alpha, dt)

            # Composite background with eroded body
            alpha_3ch = np.repeat(eroded_alpha[:, :, np.newaxis], 3, axis=2)
            output_frame = (
                clean_bg.astype(np.float32) * (1.0 - alpha_3ch) +
                eroded_bgr.astype(np.float32) * alpha_3ch
            ).astype(np.uint8)

            if not is_active:
                self.state = STATE_INVISIBLE

        elif self.state == STATE_INVISIBLE:
            # Person is fully gone. Show only the room background!
            output_frame = clean_bg.copy()

        elif self.state == STATE_REAPPEARING:
            # Update reappearance
            is_active = self.reappear_ctrl.update(dt)

            body_frame = raw_frame if self.frozen_body_frame is None else self.frozen_body_frame
            b_alpha = alpha_mask if self.frozen_alpha_mask is None else self.frozen_alpha_mask

            reformed_bgr, reformed_alpha = self.reappear_ctrl.apply(body_frame, b_alpha, dt)

            # Composite background with reforming body
            alpha_3ch = np.repeat(reformed_alpha[:, :, np.newaxis], 3, axis=2)
            output_frame = (
                clean_bg.astype(np.float32) * (1.0 - alpha_3ch) +
                reformed_bgr.astype(np.float32) * alpha_3ch
            ).astype(np.uint8)

            if not is_active:
                self.state = STATE_NORMAL
                self.engine.reset()

        else:
            output_frame = raw_frame.copy()

        # 3. Update & Render Particle Engine
        self.engine.update(dt)
        output_frame = self.engine.render(output_frame)

        # 4. Render Snap Flash Pulse (Cosmic Shockwave at finger coordinates)
        if self.snap_pulse is not None:
            pulse_elapsed = now - self.snap_pulse["start_time"]
            dur = self.snap_pulse["duration"]
            if pulse_elapsed < dur:
                p_ratio = pulse_elapsed / dur
                radius = int(20 + p_ratio * 120)
                alpha = (1.0 - p_ratio) ** 1.5

                # Shockwave ring
                px, py = self.snap_pulse["x"], self.snap_pulse["y"]
                pulse_overlay = np.zeros_like(output_frame)
                
                ring_color = (
                    int(60 * alpha),
                    int(215 * alpha),
                    int(255 * alpha)  # Golden amber flare in BGR
                )
                thickness = max(1, int(6 * (1.0 - p_ratio)))
                cv2.circle(pulse_overlay, (px, py), radius, ring_color, thickness, cv2.LINE_AA)
                cv2.circle(pulse_overlay, (px, py), int(radius * 0.4), (int(255 * alpha), int(255 * alpha), int(255 * alpha)), -1, cv2.LINE_AA)
                
                output_frame = cv2.add(output_frame, pulse_overlay)
            else:
                self.snap_pulse = None

        # 5. Optional Skeleton Landmark Overlay
        if show_landmarks and tracked_hands:
            for hand in tracked_hands:
                pts = hand["landmarks_px"]
                for p1_i, p2_i in [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
                                  (0, 9), (9, 10), (10, 11), (11, 12), (0, 13), (13, 14), (14, 15),
                                  (15, 16), (0, 17), (17, 18), (18, 19), (19, 20)]:
                    cv2.line(output_frame, tuple(pts[p1_i]), tuple(pts[p2_i]), (0, 240, 255), 2, cv2.LINE_AA)
                for pt in pts:
                    cv2.circle(output_frame, tuple(pt), 3, (255, 180, 50), -1, cv2.LINE_AA)

        # 6. Generate Previews
        mask_preview = cv2.applyColorMap(binary_mask, cv2.COLORMAP_MAGMA)
        bg_preview = clean_bg.copy()

        return output_frame, mask_preview, bg_preview

