"""
Cinematic Dark UI Theme and Stylesheet.
Inspired by Marvel Studios / Avengers Infinity War Quantum Realm aesthetic.
Features sleek glassmorphism, glowing accents, Thanos gold, and Cosmic purple highlights.
"""

DARK_THEME_QSS = """
/* Base Window & Widget Defaults */
QMainWindow, QWidget {
    background-color: #090a10;
    color: #e2e4ed;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "SF Pro Text", Roboto, sans-serif;
    font-size: 13px;
}

/* Card Containers & Panels */
QFrame.glass-card {
    background-color: #12141e;
    border: 1px solid #1f2335;
    border-radius: 12px;
}

QFrame.glass-card-highlight {
    background-color: #141624;
    border: 1px solid #362956;
    border-radius: 12px;
}

QFrame.glass-card-glow {
    background-color: #151829;
    border: 1px solid #5a3e9c;
    border-radius: 12px;
}

/* Tab Widget Styling */
QTabWidget::pane {
    border: 1px solid #1f2335;
    border-radius: 10px;
    background-color: #12141e;
    top: -1px;
}

QTabBar::tab {
    background: #0d0f17;
    color: #8c90a4;
    padding: 8px 16px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    border: 1px solid #1a1c29;
    border-bottom: none;
    font-weight: 600;
    font-size: 12px;
}

QTabBar::tab:selected {
    background: #12141e;
    color: #f3ba2f; /* Thanos Gold */
    border: 1px solid #1f2335;
    border-bottom: 2px solid #f3ba2f;
}

QTabBar::tab:hover:!selected {
    background: #141724;
    color: #cdd1e0;
}

/* Section Headers */
QLabel.section-header {
    font-size: 13px;
    font-weight: 800;
    color: #f3ba2f;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

QLabel.title-label {
    font-size: 22px;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: 1.2px;
}

QLabel.subtitle-label {
    font-size: 11px;
    color: #858a9e;
    letter-spacing: 0.6px;
    font-weight: 500;
}

/* Standard Buttons */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e2132, stop:1 #272b40);
    color: #ffffff;
    border: 1px solid #323752;
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 600;
    font-size: 12px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #292d44, stop:1 #353b57);
    border: 1px solid #484f75;
}

QPushButton:pressed {
    background-color: #171926;
    border: 1px solid #23273b;
}

QPushButton:disabled {
    background-color: #11131c;
    color: #4a4d61;
    border: 1px solid #1b1d2b;
}

/* Gold Disappear Hero Button */
QPushButton.btn-gold-hero {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f5af19, stop:1 #e65c00);
    border: 1px solid #fbd38d;
    color: #0b0c10;
    font-weight: 800;
    font-size: 13px;
    border-radius: 9px;
    padding: 10px 18px;
}

QPushButton.btn-gold-hero:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #fabd3b, stop:1 #f06a13);
    border: 1px solid #fef3c7;
}

QPushButton.btn-gold-hero:pressed {
    background-color: #b45309;
}

/* Cyan Reconstruct Hero Button */
QPushButton.btn-cyan-hero {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00c6ff, stop:1 #0072ff);
    border: 1px solid #7dd3fc;
    color: #ffffff;
    font-weight: 800;
    font-size: 13px;
    border-radius: 9px;
    padding: 10px 18px;
}

QPushButton.btn-cyan-hero:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #22d3ee, stop:1 #1d4ed8);
    border: 1px solid #bae6fd;
}

QPushButton.btn-cyan-hero:pressed {
    background-color: #0369a1;
}

/* Purple Cosmic Button */
QPushButton.btn-purple {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8e2de2, stop:1 #4a00e0);
    border: 1px solid #c084fc;
    color: #ffffff;
    font-weight: 700;
    border-radius: 8px;
}

QPushButton.btn-purple:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a855f7, stop:1 #5b21b6);
    border: 1px solid #e9d5ff;
}

/* Character Preset Chips */
QPushButton.preset-chip {
    background: #141724;
    border: 1px solid #23283d;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 11px;
    font-weight: 600;
    color: #a5abbf;
}

QPushButton.preset-chip:hover {
    background: #1e2236;
    border: 1px solid #3d4566;
    color: #ffffff;
}

QPushButton.preset-chip-active {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3c1e6d, stop:1 #522794);
    border: 1px solid #a855f7;
    color: #ffffff;
    font-weight: 700;
}

/* Sliders */
QSlider::groove:horizontal {
    border: none;
    height: 5px;
    background: #1f2335;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8e2de2, stop:1 #f3ba2f);
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: 2px solid #f3ba2f;
    width: 15px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #f3ba2f;
    border: 2px solid #ffffff;
}

/* Checkboxes */
QCheckBox {
    spacing: 8px;
    color: #c4c8d8;
    font-weight: 500;
}

QCheckBox::indicator {
    width: 17px;
    height: 17px;
    background-color: #171926;
    border: 1px solid #323752;
    border-radius: 4px;
}

QCheckBox::indicator:hover {
    border: 1px solid #8e2de2;
}

QCheckBox::indicator:checked {
    background-color: #8e2de2;
    border: 1px solid #a855f7;
}

/* ComboBox Dropdowns */
QComboBox {
    background-color: #171926;
    border: 1px solid #282d44;
    border-radius: 7px;
    padding: 6px 12px;
    color: #ffffff;
    font-weight: 500;
}

QComboBox:hover {
    border: 1px solid #434a6e;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #131521;
    border: 1px solid #282d44;
    selection-background-color: #3d236b;
    selection-color: #ffffff;
    padding: 4px;
}

/* Status Badges */
QLabel.badge {
    padding: 5px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

QLabel.badge-green {
    background-color: #064e3b;
    color: #34d399;
    border: 1px solid #059669;
}

QLabel.badge-gold {
    background-color: #451a03;
    color: #fbbf24;
    border: 1px solid #d97706;
}

QLabel.badge-purple {
    background-color: #3b0764;
    color: #c084fc;
    border: 1px solid #7e22ce;
}

QLabel.badge-cyan {
    background-color: #0c4a6e;
    color: #38bdf8;
    border: 1px solid #0284c7;
}

QLabel.badge-gray {
    background-color: #1a1d2b;
    color: #9499ab;
    border: 1px solid #2a2f45;
}

/* Scroll Area */
QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    border: none;
    background: #0d0e15;
    width: 6px;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background: #23273a;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #3c4263;
}
"""
