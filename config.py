"""
Configuration module for SNAP DISAPPEAR.
Contains all constants, default parameters, asset paths, and VFX settings.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
MODELS_DIR = ASSETS_DIR / "models"
SOUNDS_DIR = ASSETS_DIR / "sounds"

# Model paths
HAND_LANDMARKER_MODEL = str(MODELS_DIR / "hand_landmarker.task")
SELFIE_SEGMENTER_MODEL = str(MODELS_DIR / "selfie_segmenter.tflite")

# Sound paths
SOUND_SNAP = str(SOUNDS_DIR / "snap.wav")
SOUND_DISINTEGRATE = str(SOUNDS_DIR / "disintegrate.wav")
SOUND_REAPPEAR = str(SOUNDS_DIR / "reappear.wav")

# Application States
STATE_NORMAL = "NORMAL"
STATE_DISAPPEARING = "DISAPPEARING"
STATE_INVISIBLE = "INVISIBLE"
STATE_REAPPEARING = "REAPPEARING"

# Camera Defaults
DEFAULT_CAMERA_INDEX = 0
DEFAULT_FRAME_WIDTH = 1280
DEFAULT_FRAME_HEIGHT = 720
TARGET_FPS = 30

# Gesture & Snap Detection Defaults
DEFAULT_SNAP_SENSITIVITY = 0.70         # 0.1 (low) to 1.0 (high)
DEFAULT_SNAP_COOLDOWN = 1.25            # Cooldown seconds between snaps
DEFAULT_LEFT_HAND_ENABLED = True
DEFAULT_RIGHT_HAND_ENABLED = True
CONTACT_THRESHOLD_BASE = 0.08           # Max normalized distance between thumb and middle tip
SEPARATION_VELOCITY_BASE = 0.35         # Min velocity of separation to register snap
SNAP_TRAVEL_THRESHOLD = 0.05            # Downward displacement of middle fingertip

# VFX & Particle Defaults
DEFAULT_PARTICLE_COUNT = 10000          # Active particle cap
DEFAULT_DISAPPEAR_DURATION = 2.4        # Seconds
DEFAULT_REAPPEAR_DURATION = 2.2         # Seconds
DEFAULT_TURBULENCE = 55.0               # Curl noise scale
DEFAULT_GLOW_INTENSITY = 0.85           # Additive glow blend factor
DEFAULT_WIND_X = 220.0                  # Pixels/sec horizontal drift
DEFAULT_WIND_Y = -140.0                 # Pixels/sec upward buoyancy

# Particle Color Palettes (BGR for OpenCV compositing)
COLOR_EMBER_GOLD = (50, 215, 255)       # Glowing Gold/Amber in BGR
COLOR_EMBER_FIRE = (30, 110, 255)       # Hot Orange/Flame in BGR
COLOR_ASH_DARK = (45, 45, 48)           # Carbon dark ash
COLOR_ASH_LIGHT = (90, 95, 100)         # Flaky grey ash
COLOR_ENERGY_CYAN = (255, 220, 50)      # Infinity Stone flare

# VFX Presets
PRESETS = {
    "Thanos (Infinity War)": {
        "ember_color": (50, 215, 255),      # Gold / Amber
        "alt_color": (30, 110, 255),        # Hot Orange
        "wind_x": 220.0,
        "wind_y": -140.0,
        "turbulence": 55.0,
        "duration": 2.4,
        "glow": 0.85
    },
    "Doctor Strange (Mystic)": {
        "ember_color": (30, 140, 255),      # Eldritch Orange
        "alt_color": (70, 230, 255),        # Bright Gold
        "wind_x": 120.0,
        "wind_y": -180.0,
        "turbulence": 85.0,
        "duration": 2.2,
        "glow": 1.2
    },
    "Spider-Man (Fine Ash)": {
        "ember_color": (70, 180, 240),      # Soft Amber
        "alt_color": (60, 60, 65),          # Carbon Ash
        "wind_x": 140.0,
        "wind_y": -90.0,
        "turbulence": 35.0,
        "duration": 3.0,
        "glow": 0.65
    },
    "Scarlet Witch (Chaos Magic)": {
        "ember_color": (60, 20, 255),       # Crimson Red
        "alt_color": (160, 40, 240),        # Chaos Magenta
        "wind_x": 180.0,
        "wind_y": -160.0,
        "turbulence": 70.0,
        "duration": 2.3,
        "glow": 1.1
    },
    "Space Stone (Cosmic Blue)": {
        "ember_color": (255, 200, 30),      # Celestial Cyan
        "alt_color": (255, 100, 20),        # Electric Cobalt
        "wind_x": 200.0,
        "wind_y": -150.0,
        "turbulence": 60.0,
        "duration": 2.0,
        "glow": 1.3
    }
}


