"""
SNAP DISAPPEAR – Real-Time Avengers Dust Disintegration Effect.
Main application entry point.
"""

import sys
import os
import argparse
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

import config
from camera.webcam import WebcamStream
from camera.virtual_camera import VirtualCameraManager
from camera.background_capture import BackgroundManager
from detection.hand_tracking import HandTracker
from detection.snap_detector import SnapDetector
from detection.person_segmentation import PersonSegmenter
from effects.particle_engine import ParticleEngine
from effects.visual_renderer import VisualRenderer
from effects.audio_manager import audio_manager
from interface.dashboard import SnapDisappearDashboard

def parse_args():
    parser = argparse.ArgumentParser(description="SNAP DISAPPEAR - Real-Time Avengers Dust VFX")
    parser.add_argument("--camera", type=int, default=config.DEFAULT_CAMERA_INDEX, help="Camera device index (default: 0)")
    parser.add_argument("--width", type=int, default=config.DEFAULT_FRAME_WIDTH, help="Camera width (default: 1280)")
    parser.add_argument("--height", type=int, default=config.DEFAULT_FRAME_HEIGHT, help="Camera height (default: 720)")
    parser.add_argument("--sensitivity", type=float, default=config.DEFAULT_SNAP_SENSITIVITY, help="Snap sensitivity [0.1 - 1.0]")
    parser.add_argument("--particles", type=int, default=config.DEFAULT_PARTICLE_COUNT, help="Max particle count (default: 10000)")
    return parser.parse_args()

def main():
    args = parse_args()
    print("=" * 65)
    print("  SNAP DISAPPEAR – REAL-TIME AVENGERS DUST EFFECT")
    print("=" * 65)
    print(f"[Init] Camera: Index {args.camera} ({args.width}x{args.height})")
    print(f"[Init] Models Directory: {config.MODELS_DIR}")
    print(f"[Init] Sounds Directory: {config.SOUNDS_DIR}")

    # Register sound effects
    audio_manager.register_sound("snap", config.SOUND_SNAP)
    audio_manager.register_sound("disintegrate", config.SOUND_DISINTEGRATE)
    audio_manager.register_sound("reappear", config.SOUND_REAPPEAR)

    # Initialize Hardware and Subsystems
    print("[Init] Initializing Webcam Stream...")
    webcam = WebcamStream(camera_index=args.camera, width=args.width, height=args.height, target_fps=config.TARGET_FPS)

    print("[Init] Initializing Virtual Camera Manager...")
    vcam = VirtualCameraManager(width=args.width, height=args.height, fps=config.TARGET_FPS)

    print("[Init] Initializing Background Manager...")
    bg_manager = BackgroundManager()

    print("[Init] Loading MediaPipe Hand Landmarker...")
    hand_tracker = HandTracker(model_path=config.HAND_LANDMARKER_MODEL, max_hands=2)

    print("[Init] Initializing Biomechanical Snap Detector...")
    snap_detector = SnapDetector(
        sensitivity=args.sensitivity,
        cooldown=config.DEFAULT_SNAP_COOLDOWN,
        left_enabled=config.DEFAULT_LEFT_HAND_ENABLED,
        right_enabled=config.DEFAULT_RIGHT_HAND_ENABLED
    )

    print("[Init] Loading MediaPipe Selfie Segmenter...")
    segmenter = PersonSegmenter(model_path=config.SELFIE_SEGMENTER_MODEL)

    print("[Init] Allocating High-Performance Particle Engine...")
    particle_engine = ParticleEngine(max_particles=args.particles)

    print("[Init] Initializing Master Visual Compositor...")
    renderer = VisualRenderer(
        particle_engine=particle_engine,
        background_manager=bg_manager,
        disappear_duration=config.DEFAULT_DISAPPEAR_DURATION,
        reappear_duration=config.DEFAULT_REAPPEAR_DURATION
    )

    # Launch Desktop GUI
    print("[Init] Starting Desktop Dashboard Application...")
    app = QApplication(sys.argv)
    app.setApplicationName("Snap Disappear")

    dashboard = SnapDisappearDashboard(
        webcam=webcam,
        vcam=vcam,
        bg_manager=bg_manager,
        hand_tracker=hand_tracker,
        snap_detector=snap_detector,
        segmenter=segmenter,
        particle_engine=particle_engine,
        renderer=renderer
    )
    dashboard.show()

    print("[Ready] Application running! Enjoy the Avengers dust disintegration!")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

