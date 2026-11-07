"""
Webcam Capture Module.
Runs a background worker thread to continuously pull fresh frames from the webcam,
ensuring zero latency, high frame-rates, and automatic disconnection recovery.
"""

import cv2
import time
import threading
from typing import Optional, Tuple, List

class WebcamStream:
    """Threaded webcam reader for non-blocking camera frame ingestion."""

    def __init__(self, camera_index: int = 0, width: int = 1280, height: int = 720, target_fps: int = 30):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.target_fps = target_fps

        self.cap: Optional[cv2.VideoCapture] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

        self.latest_frame: Optional[cv2.Mat] = None
        self.frame_count = 0
        self.fps = 0.0
        self.last_fps_time = time.time()
        self.is_connected = False

    @staticmethod
    def list_available_cameras(max_tested: int = 5) -> List[int]:
        """Probes available video devices and returns valid camera indices."""
        available = []
        for i in range(max_tested):
            temp_cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if temp_cap.isOpened():
                available.append(i)
                temp_cap.release()
            else:
                # Try default backend if DSHOW fails
                temp_cap2 = cv2.VideoCapture(i)
                if temp_cap2.isOpened():
                    available.append(i)
                    temp_cap2.release()
        return available if available else [0]

    def start(self) -> bool:
        """Starts the background capture thread."""
        if self.running:
            return True

        self._open_capture()
        if not self.is_connected:
            return False

        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        return True

    def _open_capture(self):
        """Attempts to open the camera with DirectShow (Windows) or standard backend."""
        if self.cap is not None:
            self.cap.release()

        # Try CAP_DSHOW on Windows for fast startup and format control
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_index)

        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            self.is_connected = True
        else:
            self.is_connected = False

    def _capture_loop(self):
        """Continuous background frame acquisition loop."""
        fps_frame_count = 0
        fps_start = time.time()

        while self.running:
            if self.cap is None or not self.cap.isOpened():
                # Attempt reconnection
                time.sleep(1.0)
                self._open_capture()
                continue

            ret, frame = self.cap.read()
            if ret and frame is not None:
                # Mirror frame horizontally for natural selfie view
                frame = cv2.flip(frame, 1)

                with self.lock:
                    self.latest_frame = frame
                    self.frame_count += 1
                    fps_frame_count += 1

                # Update measured FPS
                now = time.time()
                if (now - fps_start) >= 1.0:
                    self.fps = fps_frame_count / (now - fps_start)
                    fps_frame_count = 0
                    fps_start = now
            else:
                self.is_connected = False
                time.sleep(0.1)

            # Cap loop rate to avoid 100% CPU usage
            time.sleep(0.005)

    def read(self) -> Tuple[bool, Optional[cv2.Mat]]:
        """Returns the most recent camera frame."""
        with self.lock:
            if self.latest_frame is not None:
                return True, self.latest_frame.copy()
            return False, None

    def change_camera(self, new_index: int, width: Optional[int] = None, height: Optional[int] = None) -> bool:
        """Switches to another camera index on the fly."""
        self.stop()
        self.camera_index = new_index
        if width:
            self.width = width
        if height:
            self.height = height
        return self.start()

    def stop(self):
        """Stops the capture thread and releases camera hardware."""
        self.running = False
        if self.thread is not None and self.thread.is_alive():
            self.thread.join(timeout=1.5)
        self.thread = None

        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.is_connected = False

