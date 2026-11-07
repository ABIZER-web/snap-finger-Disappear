"""
Virtual Camera Output Module.
Transmits the real-time processed video feed (with Avengers dust effects and empty background)
to a virtual webcam device using pyvirtualcam, making it usable in Google Meet, Zoom, MS Teams, etc.
"""

import cv2
import numpy as np
import threading
from typing import Optional

class VirtualCameraManager:
    """Manages streaming to a virtual webcam device."""

    def __init__(self, width: int = 1280, height: int = 720, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self.cam = None
        self.is_active = False
        self.is_available = False
        self.backend_name = "None"
        self.error_message = ""
        self._lock = threading.Lock()
        
        self._check_library()

    def _check_library(self):
        """Checks if pyvirtualcam is installed."""
        try:
            import pyvirtualcam
            self.is_available = True
        except ImportError:
            self.is_available = False
            self.error_message = "pyvirtualcam is not installed."

    def start(self, width: Optional[int] = None, height: Optional[int] = None, fps: Optional[int] = None) -> bool:
        """Starts streaming to virtual camera device."""
        if self.is_active:
            return True

        if width: self.width = width
        if height: self.height = height
        if fps: self.fps = fps

        try:
            import pyvirtualcam
            # Auto-detect supported virtual camera backends (e.g. OBS, UnityCapture, or DirectShow)
            self.cam = pyvirtualcam.Camera(
                width=self.width,
                height=self.height,
                fps=self.fps,
                fmt=pyvirtualcam.PixelFormat.BGR,
                print_fps=False
            )
            self.backend_name = str(self.cam.device)
            self.is_active = True
            self.error_message = ""
            print(f"[VirtualCamera] Started on device: {self.backend_name} ({self.width}x{self.height} @ {self.fps}fps)")
            return True
        except Exception as e:
            self.is_active = False
            self.cam = None
            self.error_message = f"Virtual camera error: {str(e)}"
            print(f"[VirtualCamera] Could not start virtual camera: {e}")
            return False

    def send_frame(self, bgr_frame: np.ndarray):
        """Sends a BGR frame to the virtual camera device."""
        if not self.is_active or self.cam is None or bgr_frame is None:
            return

        with self._lock:
            try:
                # Resize if frame dimensions don't match virtual camera config
                h, w = bgr_frame.shape[:2]
                if w != self.width or h != self.height:
                    out_frame = cv2.resize(bgr_frame, (self.width, self.height))
                else:
                    out_frame = bgr_frame

                self.cam.send(out_frame)
                self.cam.sleep_until_next_frame()
            except Exception as e:
                # Silently catch frame drop or disconnection
                pass

    def stop(self):
        """Closes the virtual camera device."""
        with self._lock:
            if self.cam is not None:
                try:
                    self.cam.close()
                except Exception:
                    pass
                self.cam = None
            self.is_active = False
            self.backend_name = "None"

