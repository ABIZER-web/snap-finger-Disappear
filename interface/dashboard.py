"""
Main Dashboard Window for SNAP DISAPPEAR.
Complete cinematic desktop interface with live previews, character presets,
biometric tension gauges, HUD overlays, hotkeys, and diagnostics.
"""

import cv2
import time
import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QCheckBox, QComboBox, QFrame, QScrollArea,
    QSizePolicy, QMessageBox, QTabWidget, QButtonGroup
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QKeySequence, QShortcut, QIcon

from config import (
    STATE_NORMAL, STATE_DISAPPEARING, STATE_INVISIBLE, STATE_REAPPEARING,
    DEFAULT_SNAP_SENSITIVITY, DEFAULT_SNAP_COOLDOWN, DEFAULT_LEFT_HAND_ENABLED,
    DEFAULT_RIGHT_HAND_ENABLED, DEFAULT_PARTICLE_COUNT, DEFAULT_DISAPPEAR_DURATION,
    DEFAULT_REAPPEAR_DURATION, DEFAULT_TURBULENCE, DEFAULT_GLOW_INTENSITY,
    DEFAULT_WIND_X, DEFAULT_WIND_Y, PRESETS
)
from camera.webcam import WebcamStream
from camera.virtual_camera import VirtualCameraManager
from camera.background_capture import BackgroundManager
from detection.hand_tracking import HandTracker
from detection.snap_detector import SnapDetector
from detection.person_segmentation import PersonSegmenter
from effects.particle_engine import ParticleEngine
from effects.visual_renderer import VisualRenderer
from effects.audio_manager import audio_manager
from interface.controls import VideoDisplayWidget, LabeledSlider, StatusBadge, BiometricSnapGauge
from interface.styles import DARK_THEME_QSS

class SnapDisappearDashboard(QMainWindow):
    """Primary application dashboard window with cinematic Avengers aesthetics."""

    def __init__(self,
                 webcam: WebcamStream,
                 vcam: VirtualCameraManager,
                 bg_manager: BackgroundManager,
                 hand_tracker: HandTracker,
                 snap_detector: SnapDetector,
                 segmenter: PersonSegmenter,
                 particle_engine: ParticleEngine,
                 renderer: VisualRenderer):
        super().__init__()

        self.webcam = webcam
        self.vcam = vcam
        self.bg_manager = bg_manager
        self.hand_tracker = hand_tracker
        self.snap_detector = snap_detector
        self.segmenter = segmenter
        self.particle_engine = particle_engine
        self.renderer = renderer

        # Flags and state
        self.show_skeleton = True
        self.camera_running = False
        self.audio_enabled = True
        self.fps_counter = 0
        self.last_fps_calc = time.time()
        self.current_fps = 0.0
        self.active_preset_name = "Thanos (Infinity War)"

        # Window Setup
        self.setWindowTitle("SNAP DISAPPEAR – Real-Time Avengers Dust VFX")
        self.resize(1380, 870)
        self.setMinimumSize(1080, 700)
        self.setStyleSheet(DARK_THEME_QSS)

        # Build UI
        self._init_ui()
        self._setup_shortcuts()

        # Processing Loop Timer (Target: ~30 FPS = 33ms)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._process_frame)

        # Auto-start camera
        self._toggle_camera()

    def _init_ui(self):
        """Constructs layout, header, presets bar, previews, and tabbed controls."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 14, 18, 16)
        main_layout.setSpacing(12)

        # 1. TOP HEADER BAR
        header_frame = QFrame()
        header_frame.setProperty("class", "glass-card")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(18, 10, 18, 10)

        # Title & Branding
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel("⚡ SNAP DISAPPEAR")
        title_lbl.setProperty("class", "title-label")
        subtitle_lbl = QLabel("CINEMATIC AVENGERS PARTICLE DISINTEGRATION ENGINE")
        subtitle_lbl.setProperty("class", "subtitle-label")
        title_box.addWidget(title_lbl)
        title_box.addWidget(subtitle_lbl)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # Character Preset Quick Chips
        preset_box = QHBoxLayout()
        preset_box.setSpacing(6)
        preset_lbl = QLabel("VFX PRESET:")
        preset_lbl.setStyleSheet("color: #7d8299; font-size: 11px; font-weight: 700;")
        preset_box.addWidget(preset_lbl)

        self.preset_btn_group = QButtonGroup(self)
        preset_chips = [
            ("🪐 Thanos", "Thanos (Infinity War)"),
            ("🔮 Dr. Strange", "Doctor Strange (Mystic)"),
            ("🕷️ Spider-Man", "Spider-Man (Fine Ash)"),
            ("🔴 Scarlet Witch", "Scarlet Witch (Chaos Magic)"),
            ("🔷 Space Stone", "Space Stone (Cosmic Blue)")
        ]

        self.preset_buttons = {}
        for idx, (label, p_name) in enumerate(preset_chips):
            btn = QPushButton(label)
            btn.setProperty("class", "preset-chip-active" if idx == 0 else "preset-chip")
            btn.setCheckable(True)
            btn.setChecked(idx == 0)
            btn.clicked.connect(lambda checked, name=p_name: self._apply_preset(name))
            self.preset_btn_group.addButton(btn, idx)
            self.preset_buttons[p_name] = btn
            preset_box.addWidget(btn)

        header_layout.addLayout(preset_box)
        header_layout.addSpacing(14)

        # Audio Toggle Button
        self.btn_audio = QPushButton("🔊 Audio: ON")
        self.btn_audio.setFixedWidth(105)
        self.btn_audio.clicked.connect(self._toggle_audio)
        header_layout.addWidget(self.btn_audio)

        # Status Indicators
        self.badge_fps = StatusBadge("FPS: 0.0", "gray")
        self.badge_cam = StatusBadge("CAM: CONNECTING", "gold")
        self.badge_vcam = StatusBadge("VIRTUAL CAM: OFF", "gray")

        header_layout.addWidget(self.badge_fps)
        header_layout.addWidget(self.badge_cam)
        header_layout.addWidget(self.badge_vcam)

        main_layout.addWidget(header_frame)

        # 2. MAIN BODY (Left: Previews & Action Bar, Right: Tabbed Controls)
        body_layout = QHBoxLayout()
        body_layout.setSpacing(14)

        # LEFT COLUMN: PREVIEWS & HERO ACTION BAR
        left_box = QVBoxLayout()
        left_box.setSpacing(10)

        # Primary Output Video Monitor Card
        out_card = QFrame()
        out_card.setProperty("class", "glass-card-highlight")
        out_layout = QVBoxLayout(out_card)
        out_layout.setContentsMargins(10, 8, 10, 10)

        out_header = QHBoxLayout()
        out_title = QLabel("MASTER VFX COMPOSITOR OUTPUT (LIVE / VIRTUAL CAMERA)")
        out_title.setProperty("class", "section-header")
        
        self.btn_fullscreen = QPushButton("⛶ Fullscreen [F11]")
        self.btn_fullscreen.setFixedHeight(26)
        self.btn_fullscreen.clicked.connect(self._toggle_fullscreen)

        out_header.addWidget(out_title)
        out_header.addStretch()
        out_header.addWidget(self.btn_fullscreen)
        out_layout.addLayout(out_header)

        self.view_main = VideoDisplayWidget("Starting Video Feed...", self)
        self.view_main.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.view_main.setMinimumHeight(440)
        out_layout.addWidget(self.view_main)

        # Quick Hero Action Bar
        hero_bar = QHBoxLayout()
        hero_bar.setSpacing(8)

        self.btn_disappear = QPushButton("✨ SNAP DISAPPEAR [SPACE]")
        self.btn_disappear.setProperty("class", "btn-gold-hero")
        self.btn_disappear.setToolTip("Trigger Disintegration Effect [SPACE]")
        self.btn_disappear.clicked.connect(self._manual_disappear)

        self.btn_reappear = QPushButton("🌀 RECONSTRUCT [R]")
        self.btn_reappear.setProperty("class", "btn-cyan-hero")
        self.btn_reappear.setToolTip("Trigger Reappearance Effect [R]")
        self.btn_reappear.clicked.connect(self._manual_reappear)

        self.btn_capture_bg = QPushButton("📷 Lock Background [B]")
        self.btn_capture_bg.setToolTip("Step aside and click to calibrate pristine background [B]")
        self.btn_capture_bg.clicked.connect(self._recapture_background)

        self.btn_reset = QPushButton("↺ Restore")
        self.btn_reset.setToolTip("Instantly restores normal view")
        self.btn_reset.clicked.connect(self._reset_effect)

        hero_bar.addWidget(self.btn_disappear, stretch=3)
        hero_bar.addWidget(self.btn_reappear, stretch=3)
        hero_bar.addWidget(self.btn_capture_bg, stretch=2)
        hero_bar.addWidget(self.btn_reset, stretch=1)
        out_layout.addLayout(hero_bar)

        left_box.addWidget(out_card, stretch=4)

        # Thumbnail Previews Deck (Raw Camera, Mask, Background)
        thumb_deck = QFrame()
        thumb_deck.setProperty("class", "glass-card")
        thumb_layout = QGridLayout(thumb_deck)
        thumb_layout.setContentsMargins(10, 8, 10, 8)
        thumb_layout.setSpacing(8)

        # Raw Camera Thumbnail
        raw_box = QVBoxLayout()
        raw_lbl = QLabel("RAW WEBCAM FEED")
        raw_lbl.setStyleSheet("color: #7d8299; font-size: 11px; font-weight: 700;")
        self.view_raw = VideoDisplayWidget("Camera", self)
        self.view_raw.setMaximumHeight(110)
        raw_box.addWidget(raw_lbl)
        raw_box.addWidget(self.view_raw)
        thumb_layout.addLayout(raw_box, 0, 0)

        # Person Segmentation Thumbnail
        seg_box = QVBoxLayout()
        seg_lbl = QLabel("PERSON SEGMENTATION MASK")
        seg_lbl.setStyleSheet("color: #7d8299; font-size: 11px; font-weight: 700;")
        self.view_seg = VideoDisplayWidget("Mask", self)
        self.view_seg.setMaximumHeight(110)
        seg_box.addWidget(seg_lbl)
        seg_box.addWidget(self.view_seg)
        thumb_layout.addLayout(seg_box, 0, 1)

        # Background Plate Thumbnail
        bg_box = QVBoxLayout()
        bg_lbl = QLabel("PRESERVED ROOM BACKGROUND")
        bg_lbl.setStyleSheet("color: #7d8299; font-size: 11px; font-weight: 700;")
        self.view_bg = VideoDisplayWidget("Background", self)
        self.view_bg.setMaximumHeight(110)
        bg_box.addWidget(bg_lbl)
        bg_box.addWidget(self.view_bg)
        thumb_layout.addLayout(bg_box, 0, 2)

        left_box.addWidget(thumb_deck, stretch=1)
        body_layout.addLayout(left_box, stretch=3)

        # RIGHT COLUMN: TABBED CONTROL DECK
        self.tab_widget = QTabWidget()
        self.tab_widget.setMinimumWidth(360)
        self.tab_widget.setMaximumWidth(450)

        # TAB 1: 🌟 VFX & PARTICLES
        tab_vfx = QWidget()
        vfx_layout = QVBoxLayout(tab_vfx)
        vfx_layout.setContentsMargins(14, 14, 14, 14)
        vfx_layout.setSpacing(12)

        vfx_hdr = QLabel("PARTICLE DYNAMICS & AESTHETICS")
        vfx_hdr.setProperty("class", "section-header")
        vfx_layout.addWidget(vfx_hdr)

        self.slider_particles = LabeledSlider("Max Particle Count", 2000, 25000, DEFAULT_PARTICLE_COUNT, step=1000)
        self.slider_particles.valueChanged.connect(lambda v: setattr(self.particle_engine, "max_particles", int(v)))
        vfx_layout.addWidget(self.slider_particles)

        self.slider_disappear_dur = LabeledSlider("Disappearance Duration", 1.2, 5.0, DEFAULT_DISAPPEAR_DURATION, step=0.1, unit="s")
        self.slider_disappear_dur.valueChanged.connect(lambda v: setattr(self.renderer.disintegrate_ctrl, "duration", v))
        vfx_layout.addWidget(self.slider_disappear_dur)

        self.slider_reappear_dur = LabeledSlider("Reappearance Duration", 1.0, 4.5, DEFAULT_REAPPEAR_DURATION, step=0.1, unit="s")
        self.slider_reappear_dur.valueChanged.connect(lambda v: setattr(self.renderer.reappear_ctrl, "duration", v))
        vfx_layout.addWidget(self.slider_reappear_dur)

        self.slider_turb = LabeledSlider("Aerodynamic Turbulence", 10.0, 100.0, DEFAULT_TURBULENCE, step=5.0)
        self.slider_turb.valueChanged.connect(lambda v: setattr(self.particle_engine, "turbulence", v))
        vfx_layout.addWidget(self.slider_turb)

        self.slider_glow = LabeledSlider("Ember Glow Intensity", 0.2, 1.5, DEFAULT_GLOW_INTENSITY, step=0.05)
        self.slider_glow.valueChanged.connect(lambda v: setattr(self.particle_engine, "glow_intensity", v))
        vfx_layout.addWidget(self.slider_glow)

        self.slider_wind = LabeledSlider("Wind Drift Velocity", 50.0, 500.0, DEFAULT_WIND_X, step=25.0, unit="px")
        self.slider_wind.valueChanged.connect(lambda v: setattr(self.particle_engine, "wind_x", v))
        vfx_layout.addWidget(self.slider_wind)

        vfx_layout.addStretch()
        self.tab_widget.addTab(tab_vfx, "🌟 VFX")

        # TAB 2: ✋ SNAP & GESTURES
        tab_gesture = QWidget()
        gest_layout = QVBoxLayout(tab_gesture)
        gest_layout.setContentsMargins(14, 14, 14, 14)
        gest_layout.setSpacing(12)

        gest_hdr = QLabel("BIOMECHANICAL SNAP DETECTION")
        gest_hdr.setProperty("class", "section-header")
        gest_layout.addWidget(gest_hdr)

        # Biometric Live Gauge
        self.gauge = BiometricSnapGauge()
        gest_layout.addWidget(self.gauge)

        hand_toggles = QHBoxLayout()
        self.chk_left = QCheckBox("Left Hand")
        self.chk_left.setChecked(DEFAULT_LEFT_HAND_ENABLED)
        self.chk_left.toggled.connect(self._on_hand_toggled)

        self.chk_right = QCheckBox("Right Hand")
        self.chk_right.setChecked(DEFAULT_RIGHT_HAND_ENABLED)
        self.chk_right.toggled.connect(self._on_hand_toggled)

        self.chk_skeleton = QCheckBox("Landmark Overlay")
        self.chk_skeleton.setChecked(True)
        self.chk_skeleton.toggled.connect(lambda v: setattr(self, "show_skeleton", v))

        hand_toggles.addWidget(self.chk_left)
        hand_toggles.addWidget(self.chk_right)
        hand_toggles.addWidget(self.chk_skeleton)
        gest_layout.addLayout(hand_toggles)

        self.slider_sens = LabeledSlider("Snap Sensitivity", 0.1, 1.0, DEFAULT_SNAP_SENSITIVITY, step=0.05)
        self.slider_sens.valueChanged.connect(self.snap_detector.set_sensitivity)
        gest_layout.addWidget(self.slider_sens)

        self.slider_cooldown = LabeledSlider("Gesture Cooldown", 0.5, 3.0, DEFAULT_SNAP_COOLDOWN, step=0.1, unit="s")
        self.slider_cooldown.valueChanged.connect(self.snap_detector.set_cooldown)
        gest_layout.addWidget(self.slider_cooldown)

        gest_layout.addStretch()
        self.tab_widget.addTab(tab_gesture, "✋ Gestures")

        # TAB 3: 📹 CAMERA & VIRTUAL CAM
        tab_cam = QWidget()
        cam_layout = QVBoxLayout(tab_cam)
        cam_layout.setContentsMargins(14, 14, 14, 14)
        cam_layout.setSpacing(12)

        cam_hdr = QLabel("HARDWARE & BROADCASTING")
        cam_hdr.setProperty("class", "section-header")
        cam_layout.addWidget(cam_hdr)

        # Webcam Device Selector
        dev_row = QHBoxLayout()
        dev_lbl = QLabel("Camera Device:")
        dev_lbl.setStyleSheet("color: #9fa4b8;")
        self.combo_cam = QComboBox()
        available_cams = WebcamStream.list_available_cameras()
        for idx in available_cams:
            self.combo_cam.addItem(f"Webcam Index {idx}", idx)
        self.combo_cam.currentIndexChanged.connect(self._on_cam_changed)
        dev_row.addWidget(dev_lbl)
        dev_row.addWidget(self.combo_cam)
        cam_layout.addLayout(dev_row)

        # Resolution Selector
        res_row = QHBoxLayout()
        res_lbl = QLabel("Resolution:")
        res_lbl.setStyleSheet("color: #9fa4b8;")
        self.combo_res = QComboBox()
        self.combo_res.addItem("1280 x 720 (HD - Recommended)", (1280, 720))
        self.combo_res.addItem("640 x 480 (Fast)", (640, 480))
        self.combo_res.currentIndexChanged.connect(self._on_res_changed)
        res_row.addWidget(res_lbl)
        res_row.addWidget(self.combo_res)
        cam_layout.addLayout(res_row)

        self.btn_toggle_cam = QPushButton("⏹ Stop Camera")
        self.btn_toggle_cam.clicked.connect(self._toggle_camera)
        cam_layout.addWidget(self.btn_toggle_cam)

        cam_layout.addSpacing(10)

        # Virtual Camera Section
        vcam_box = QFrame()
        vcam_box.setProperty("class", "glass-card-glow")
        vcam_inner = QVBoxLayout(vcam_box)
        vcam_title = QLabel("VIRTUAL WEBCAM BROADCASTER")
        vcam_title.setStyleSheet("color: #c084fc; font-weight: 800; font-size: 12px;")
        vcam_desc = QLabel("Broadcasts this real-time effect to Zoom, Google Meet, and MS Teams.")
        vcam_desc.setStyleSheet("color: #8c90a4; font-size: 11px;")
        vcam_desc.setWordWrap(True)

        self.btn_toggle_vcam = QPushButton("🌐 Enable Virtual Camera")
        self.btn_toggle_vcam.setProperty("class", "btn-purple")
        self.btn_toggle_vcam.clicked.connect(self._toggle_virtual_camera)

        vcam_inner.addWidget(vcam_title)
        vcam_inner.addWidget(vcam_desc)
        vcam_inner.addWidget(self.btn_toggle_vcam)
        cam_layout.addWidget(vcam_box)

        cam_layout.addStretch()
        self.tab_widget.addTab(tab_cam, "📹 Stream")

        body_layout.addWidget(self.tab_widget, stretch=1)
        main_layout.addLayout(body_layout)

    def _setup_shortcuts(self):
        """Initializes global hotkeys."""
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, activated=self._manual_disappear)
        QShortcut(QKeySequence(Qt.Key.Key_R), self, activated=self._manual_reappear)
        QShortcut(QKeySequence(Qt.Key.Key_B), self, activated=self._recapture_background)
        QShortcut(QKeySequence(Qt.Key.Key_F11), self, activated=self._toggle_fullscreen)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, activated=self.close)

    def _apply_preset(self, preset_name: str):
        """Applies character VFX preset parameters."""
        p = PRESETS.get(preset_name)
        if not p:
            return
        self.active_preset_name = preset_name
        self.particle_engine.set_preset_colors(p["ember_color"], p["alt_color"])
        self.particle_engine.wind_x = p["wind_x"]
        self.particle_engine.wind_y = p["wind_y"]
        self.particle_engine.turbulence = p["turbulence"]
        self.particle_engine.glow_intensity = p["glow"]
        self.renderer.disintegrate_ctrl.duration = p["duration"]

        # Update sliders in UI
        self.slider_wind.set_value(p["wind_x"])
        self.slider_turb.set_value(p["turbulence"])
        self.slider_glow.set_value(p["glow"])
        self.slider_disappear_dur.set_value(p["duration"])

        # Update chip styling
        for name, btn in self.preset_buttons.items():
            btn.setProperty("class", "preset-chip-active" if name == preset_name else "preset-chip")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self.view_main.show_toast(f"Preset Applied: {preset_name}")

    def _toggle_audio(self):
        self.audio_enabled = not self.audio_enabled
        audio_manager.set_enabled(self.audio_enabled)
        self.btn_audio.setText("🔊 Audio: ON" if self.audio_enabled else "🔇 Audio: OFF")

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.btn_fullscreen.setText("⛶ Fullscreen [F11]")
        else:
            self.showFullScreen()
            self.btn_fullscreen.setText("🗗 Windowed [F11]")

    def _on_hand_toggled(self):
        self.snap_detector.set_hands_enabled(
            self.chk_left.isChecked(),
            self.chk_right.isChecked()
        )

    def _on_cam_changed(self, idx: int):
        cam_idx = self.combo_cam.currentData()
        if cam_idx is not None and self.camera_running:
            self.webcam.change_camera(cam_idx)

    def _on_res_changed(self, idx: int):
        dims = self.combo_res.currentData()
        if dims and self.camera_running:
            w, h = dims
            self.webcam.change_camera(self.webcam.camera_index, width=w, height=h)

    def _toggle_camera(self):
        """Starts or stops webcam capture thread."""
        if self.camera_running:
            self.timer.stop()
            self.webcam.stop()
            self.camera_running = False
            self.btn_toggle_cam.setText("▶ Start Camera")
            self.badge_cam.setText("CAM: STOPPED")
            self.badge_cam.set_variant("gray")
        else:
            success = self.webcam.start()
            if success:
                self.camera_running = True
                self.btn_toggle_cam.setText("⏹ Stop Camera")
                self.badge_cam.setText("CAM: CONNECTED")
                self.badge_cam.set_variant("green")
                self.timer.start(30)
            else:
                self.badge_cam.setText("CAM: ERROR")
                self.badge_cam.set_variant("gold")
                QMessageBox.warning(self, "Camera Error", "Could not connect to webcam. Verify device is not locked by another app.")

    def _toggle_virtual_camera(self):
        """Enables or disables virtual webcam transmission."""
        if self.vcam.is_active:
            self.vcam.stop()
            self.btn_toggle_vcam.setText("🌐 Enable Virtual Camera")
            self.badge_vcam.setText("VIRTUAL CAM: OFF")
            self.badge_vcam.set_variant("gray")
            self.view_main.show_toast("Virtual Camera Stopped")
        else:
            w, h = self.webcam.width, self.webcam.height
            success = self.vcam.start(width=w, height=h, fps=30)
            if success:
                self.btn_toggle_vcam.setText("⏹ Stop Virtual Camera")
                self.badge_vcam.setText("VIRTUAL CAM: ACTIVE")
                self.badge_vcam.set_variant("green")
                self.view_main.show_toast("🌐 Virtual Camera Active in Zoom / Meet!")
            else:
                self.badge_vcam.setText("VIRTUAL CAM: UNAVAILABLE")
                self.badge_vcam.set_variant("gold")
                QMessageBox.information(
                    self,
                    "Virtual Camera Setup",
                    "Virtual Camera backend not detected.\n\n"
                    "Run 'OBS-Studio-Installer.exe' located in your project folder,\n"
                    "click 'Start Virtual Camera' once in OBS, then re-enable here!"
                )

    def _recapture_background(self):
        """Captures clean background plate."""
        ret, frame = self.webcam.read()
        if ret and frame is not None:
            self.bg_manager.capture_manual(frame)
            if self.audio_enabled:
                audio_manager.play("snap")
            self.view_main.show_toast("📷 Room Background Locked!")

    def _reset_effect(self):
        """Instantly restores normal view."""
        self.renderer.reset_to_normal()
        self.view_main.show_toast("Restored Live Video")

    def _manual_disappear(self):
        """Manual trigger for disappearance."""
        if self.renderer.state == STATE_NORMAL:
            if self.audio_enabled:
                audio_manager.play("snap")
                audio_manager.play("disintegrate")
            ret, frame = self.webcam.read()
            binary_mask, alpha_mask, _ = self.segmenter.process(frame) if (ret and frame is not None) else (None, None, None)
            
            h, w = frame.shape[:2] if frame is not None else (720, 1280)
            event = {"hand": "Right", "position_px": (w // 2, h // 2), "confidence": 1.0}
            self.renderer.trigger_disappear(snap_event=event, current_frame=frame, alpha_mask=alpha_mask)
            self.view_main.show_toast("✨ Disintegration Triggered!")

    def _manual_reappear(self):
        """Manual trigger for reappearance."""
        if self.renderer.state in [STATE_INVISIBLE, STATE_DISAPPEARING]:
            if self.audio_enabled:
                audio_manager.play("snap")
                audio_manager.play("reappear")
            ret, frame = self.webcam.read()
            binary_mask, alpha_mask, _ = self.segmenter.process(frame) if (ret and frame is not None) else (None, None, None)
            
            h, w = frame.shape[:2] if frame is not None else (720, 1280)
            event = {"hand": "Right", "position_px": (w // 2, h // 2), "confidence": 1.0}
            self.renderer.trigger_reappear(snap_event=event, current_frame=frame, alpha_mask=alpha_mask)
            self.view_main.show_toast("🌀 Reconstructing Body...")

    @pyqtSlot()
    def _process_frame(self):
        """Main frame processing pipeline running every timer tick."""
        ret, raw_frame = self.webcam.read()
        if not ret or raw_frame is None:
            return

        # 1. Person Segmentation
        binary_mask, alpha_mask, bbox = self.segmenter.process(raw_frame)

        # 2. Hand Tracking
        tracked_hands = self.hand_tracker.process(raw_frame)

        # 3. Snap Detection
        is_snap, snap_event = self.snap_detector.detect(tracked_hands)
        if is_snap and snap_event is not None:
            hand_type = snap_event["hand"]
            if self.renderer.state == STATE_NORMAL:
                if self.audio_enabled:
                    audio_manager.play("snap")
                    audio_manager.play("disintegrate")
                self.renderer.trigger_disappear(snap_event=snap_event, current_frame=raw_frame, alpha_mask=alpha_mask)
                self.view_main.show_toast(f"⚡ SNAP DETECTED ({hand_type.upper()})")
            elif self.renderer.state in [STATE_INVISIBLE, STATE_DISAPPEARING]:
                if self.audio_enabled:
                    audio_manager.play("snap")
                    audio_manager.play("reappear")
                self.renderer.trigger_reappear(snap_event=snap_event, current_frame=raw_frame, alpha_mask=alpha_mask)
                self.view_main.show_toast(f"⚡ REAPPEAR SNAP ({hand_type.upper()})")

        # 4. Master VFX Compositing
        output_frame, mask_preview, bg_preview = self.renderer.render(
            raw_frame,
            binary_mask,
            alpha_mask,
            tracked_hands,
            show_landmarks=self.show_skeleton
        )

        # 5. Virtual Camera Streaming
        if self.vcam.is_active:
            self.vcam.send_frame(output_frame)

        # 6. Update HUD Diagnostics
        self._update_hud_diagnostics()

        # 7. Render frames to UI displays
        self.view_main.set_frame(output_frame)
        self.view_raw.set_frame(raw_frame)
        self.view_seg.set_frame(mask_preview)
        self.view_bg.set_frame(bg_preview)

    def _update_hud_diagnostics(self):
        """Updates FPS, on-screen HUD badge, and Biometric tension gauge."""
        self.fps_counter += 1
        now = time.time()
        if (now - self.last_fps_calc) >= 1.0:
            self.current_fps = self.fps_counter / (now - self.last_fps_calc)
            self.fps_counter = 0
            self.last_fps_calc = now
            self.badge_fps.setText(f"FPS: {self.current_fps:.1f}")
            self.badge_fps.set_variant("green" if self.current_fps >= 24 else "gold")

        # Map state to HUD banner
        st = self.renderer.state
        if st == STATE_NORMAL:
            hud_text = "VISIBLE (LIVE)"
            hud_var = "green"
        elif st == STATE_DISAPPEARING:
            prog = int(self.renderer.disintegrate_ctrl.progress * 100)
            hud_text = f"DISSOLVING ({prog}%)"
            hud_var = "gold"
        elif st == STATE_INVISIBLE:
            hud_text = "INVISIBLE (BACKGROUND ONLY)"
            hud_var = "purple"
        elif st == STATE_REAPPEARING:
            prog = int(self.renderer.reappear_ctrl.progress * 100)
            hud_text = f"RECONSTRUCTING ({prog}%)"
            hud_var = "cyan"
        else:
            hud_text = "NORMAL"
            hud_var = "green"

        fps_str = f"{self.current_fps:.0f} FPS" if self.current_fps > 0 else ""
        self.view_main.set_hud_status(hud_text, hud_var, fps=fps_str)

        # Update Biometric Snap Gauge
        status_info = self.snap_detector.get_status_info()
        r_primed = status_info["Right"]["is_primed"]
        l_primed = status_info["Left"]["is_primed"]
        r_cool = status_info["Right"]["on_cooldown"]

        if r_cool:
            rem = status_info["Right"]["remaining_cooldown"]
            self.gauge.set_tension(int((rem / self.snap_detector.cooldown) * 100), f"COOLDOWN ({rem:.1f}s)", "#9499ab")
        elif r_primed or l_primed:
            self.gauge.set_tension(90, "PRIMED (SNAP READY!)", "#f59e0b")
        else:
            self.gauge.set_tension(15, "READY FOR SNAP", "#10b981")

    def closeEvent(self, event):
        """Clean resource release upon window exit."""
        self.timer.stop()
        self.webcam.stop()
        if self.vcam.is_active:
            self.vcam.stop()
        event.accept()
