"""
Custom PyQt6 UI Components and Video Display Widgets.
"""

import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor, QFont, QPen, QBrush, QLinearGradient

class VideoDisplayWidget(QLabel):
    """Cinematic video monitor widget with on-screen HUD overlay."""

    def __init__(self, placeholder_text: str = "Video Feed", parent=None):
        super().__init__(parent)
        self.placeholder_text = placeholder_text
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            background-color: #07080d;
            border: 1px solid #1c1f30;
            border-radius: 10px;
            color: #4a5068;
            font-size: 13px;
            font-weight: 700;
        """)
        self.setText(self.placeholder_text)
        self.setMinimumSize(320, 180)

        # HUD Overlay State
        self.hud_state_text = "VISIBLE"
        self.hud_state_variant = "green"
        self.hud_fps_text = ""
        self.hud_toast_text = ""
        self.hud_toast_time = 0.0

    def set_hud_status(self, text: str, variant: str = "green", fps: str = ""):
        self.hud_state_text = text
        self.hud_state_variant = variant
        if fps:
            self.hud_fps_text = fps

    def show_toast(self, message: str, duration: float = 2.0):
        self.hud_toast_text = message
        import time
        self.hud_toast_time = time.time() + duration

    def set_frame(self, bgr_frame: np.ndarray):
        """Draws frame with professional cinematic HUD overlays."""
        if bgr_frame is None or bgr_frame.size == 0:
            return

        h, w, ch = bgr_frame.shape
        bytes_per_line = ch * w

        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

        # Scale to widget preserving aspect ratio
        pixmap = QPixmap.fromImage(q_img).scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # Render HUD elements directly on top of the pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. State Pill (Top-Left)
        pill_rect = QRectF(14, 14, 180, 28)
        grad = QLinearGradient(pill_rect.topLeft(), pill_rect.bottomRight())
        
        if self.hud_state_variant == "gold":
            grad.setColorAt(0, QColor(245, 175, 25, 220))
            grad.setColorAt(1, QColor(230, 92, 0, 220))
            text_color = QColor(10, 10, 15)
        elif self.hud_state_variant == "cyan":
            grad.setColorAt(0, QColor(0, 198, 255, 220))
            grad.setColorAt(1, QColor(0, 114, 255, 220))
            text_color = QColor(255, 255, 255)
        elif self.hud_state_variant == "purple":
            grad.setColorAt(0, QColor(142, 45, 226, 220))
            grad.setColorAt(1, QColor(74, 0, 224, 220))
            text_color = QColor(255, 255, 255)
        else: # Green
            grad.setColorAt(0, QColor(16, 185, 129, 210))
            grad.setColorAt(1, QColor(5, 150, 105, 210))
            text_color = QColor(255, 255, 255)

        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(pill_rect, 14, 14)

        # State text
        painter.setPen(text_color)
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.8)
        painter.setFont(font)
        painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, f"● {self.hud_state_text}")

        # 2. FPS & Live Badge (Top-Right)
        if self.hud_fps_text:
            fps_rect = QRectF(pixmap.width() - 110, 14, 96, 28)
            painter.setBrush(QColor(18, 20, 30, 190))
            painter.setPen(QPen(QColor(50, 55, 80, 180), 1))
            painter.drawRoundedRect(fps_rect, 14, 14)

            painter.setPen(QColor(240, 243, 255))
            font_fps = QFont("Segoe UI", 9, QFont.Weight.Bold)
            painter.setFont(font_fps)
            painter.drawText(fps_rect, Qt.AlignmentFlag.AlignCenter, self.hud_fps_text)

        # 3. Toast message (Center-Bottom)
        import time
        if self.hud_toast_text and time.time() < self.hud_toast_time:
            toast_rect = QRectF((pixmap.width() - 320) / 2, pixmap.height() - 55, 320, 36)
            painter.setBrush(QColor(20, 22, 35, 230))
            painter.setPen(QPen(QColor(243, 186, 47, 220), 1.5))
            painter.drawRoundedRect(toast_rect, 18, 18)

            painter.setPen(QColor(255, 255, 255))
            font_toast = QFont("Segoe UI", 10, QFont.Weight.Bold)
            painter.setFont(font_toast)
            painter.drawText(toast_rect, Qt.AlignmentFlag.AlignCenter, self.hud_toast_text)

        painter.end()
        self.setPixmap(pixmap)

class LabeledSlider(QWidget):
    """Configurable slider with title, unit, and live value display."""
    valueChanged = pyqtSignal(float)

    def __init__(self, title: str, min_val: float, max_val: float, default_val: float, step: float = 0.05, unit: str = "", parent=None):
        super().__init__(parent)
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.unit = unit
        self.multiplier = int(1.0 / step) if step < 1.0 else 1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(4)

        header_layout = QHBoxLayout()
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("color: #9fa4b8; font-size: 12px; font-weight: 500;")

        self.val_lbl = QLabel(f"{default_val:.2f}{self.unit}")
        self.val_lbl.setStyleSheet("color: #f3ba2f; font-size: 12px; font-weight: 700;")

        header_layout.addWidget(self.title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(self.val_lbl)
        layout.addLayout(header_layout)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(int(self.min_val * self.multiplier))
        self.slider.setMaximum(int(self.max_val * self.multiplier))
        self.slider.setValue(int(default_val * self.multiplier))
        self.slider.valueChanged.connect(self._on_slider_moved)
        layout.addWidget(self.slider)

    def _on_slider_moved(self, int_val: int):
        val = int_val / self.multiplier
        if self.step >= 1.0:
            self.val_lbl.setText(f"{int(val)}{self.unit}")
        else:
            self.val_lbl.setText(f"{val:.2f}{self.unit}")
        self.valueChanged.emit(val)

    def get_value(self) -> float:
        return self.slider.value() / self.multiplier

    def set_value(self, val: float):
        self.slider.setValue(int(val * self.multiplier))

class BiometricSnapGauge(QWidget):
    """Visual readiness gauge displaying live finger snap tension & velocity."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(4)

        header = QHBoxLayout()
        lbl = QLabel("GESTURE BIOMETRIC TENSION")
        lbl.setStyleSheet("color: #8c90a4; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        self.status_lbl = QLabel("IDLE")
        self.status_lbl.setStyleSheet("color: #4ade80; font-size: 11px; font-weight: 800;")
        header.addWidget(lbl)
        header.addStretch()
        header.addWidget(self.status_lbl)
        layout.addLayout(header)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(8)
        self.bar.setStyleSheet("""
            QProgressBar {
                background-color: #171926;
                border: 1px solid #292d42;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8e2de2, stop:1 #f3ba2f);
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.bar)

    def set_tension(self, percent: int, text: str, color_hex: str = "#f3ba2f"):
        self.bar.setValue(int(np.clip(percent, 0, 100)))
        self.status_lbl.setText(text)
        self.status_lbl.setStyleSheet(f"color: {color_hex}; font-size: 11px; font-weight: 800;")

class StatusBadge(QLabel):
    """Dynamic status pill."""

    def __init__(self, text: str = "READY", variant: str = "gold", parent=None):
        super().__init__(text, parent)
        self.setProperty("class", "badge")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_variant(variant)

    def set_variant(self, variant: str):
        variants = {
            "green": "badge-green",
            "gold": "badge-gold",
            "purple": "badge-purple",
            "cyan": "badge-cyan",
            "gray": "badge-gray"
        }
        cls_name = variants.get(variant, "badge-gray")
        self.setProperty("class", f"badge {cls_name}")
        self.style().unpolish(self)
        self.style().polish(self)
