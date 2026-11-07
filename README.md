# SNAP DISAPPEAR – Real-Time Avengers Dust VFX ⚡

An advanced, real-time computer vision and visual effects desktop application in Python that recreates the cinematic **Avengers: Infinity War** disintegration effect triggered by snapping your fingers in front of your webcam.

When you snap your fingers, your real body dissolves into thousands of organic, glowing dust, ember, and ash particles that drift away into the wind, leaving your physical room background completely preserved. When you snap again, the particles swirl back and reconstruct your body, smoothly returning you to the live feed.

The application includes direct **Virtual Camera** output (`pyvirtualcam`), allowing you to use this effect live in **Zoom**, **Google Meet**, and **Microsoft Teams**.

---

## 🌟 Key Features

1. **Biomechanical Finger-Snap Detection**:
   - Multi-stage kinematic tracking using MediaPipe Hand Landmarkers.
   - Accurately tracks thumb, middle finger, and index finger relative velocities, contact pressure, and sudden release stroke into the palm.
   - Rejects false positives (waving, fists, pinches, peace signs).
   - Independent Left and Right hand detection with individual toggles.
   - Configurable sensitivity slider, cooldown debounce, and visual on-screen indicator.

2. **Accurate Person Segmentation & Real Background Preservation**:
   - Powered by MediaPipe Neural Selfie Segmentation.
   - Separates body, hair, clothes, and arms with feathered anti-aliased edge smoothing.
   - **True Background Preservation**: Auto-accumulates and stitches uncovered background pixels over time, or allows instant 1-click calibration (`B` key).
   - When you disappear, your actual room, furniture, and wall behind you remain visible—never a black screen or fake cut-out.

3. **Cinematic Avengers Dust Particle Engine**:
   - **Real Pixel Color Sampling**: Particles sample their base color directly from your actual clothes, skin, and hair pixels.
   - **Mixed Media Particle Field**:
     - *Sampled Body Pixels*: Real wardrobe and skin colors with contrast boost.
     - *Golden Glowing Embers*: Additive bloom blending with high-energy amber cores (`RGB 255, 200, 60`).
     - *Dark Carbon Ash*: Flaky dark gray and charcoal fragments (`RGB 45, 45, 50`).
   - **Aerodynamic Simulation**:
     - Dual-sine curl noise turbulence for organic swirling.
     - Upward thermal buoyancy and lateral wind drift.
     - Dynamic particle shrinkage, gravity, and power-law alpha decay.
   - **Dissolution Wave & Burning Ember Rim**: The body erodes progressively from the snap point outwards with a glowing orange/gold edge rim.

4. **Reverse Particle Swarm Reappearance**:
   - Snap again to trigger reverse particle reconstruction.
   - Thousands of glowing embers swirl from space back into your body coordinates, reforming you seamlessly.

5. **Live Virtual Camera Support**:
   - Direct integration via `pyvirtualcam` (OBS Virtual Camera compatible).
   - Outputs live processed VFX feed into meeting software without watermarks or lag.

6. **Professional Desktop Dashboard**:
   - Built with PyQt6 with a dark Infinity War/Quantum-realm aesthetic.
   - 4 Live monitors: Main Processed Output, Raw Camera, Person Mask, and Preserved Background Plate.
   - Real-time FPS counter, gesture status badges, sensitivity sliders, duration controls, and particle density tuning.

---

## 🛠️ Technology Stack

- **Language**: Python 3.11 - 3.14
- **Computer Vision**: OpenCV (`cv2`)
- **Hand & Body AI**: MediaPipe Tasks Vision (`HandLandmarker`, `ImageSegmenter`)
- **Particle & Physics**: NumPy (Fully vectorized array operations)
- **Audio Engine**: Low-latency asynchronous sound synthesizer & Windows Native Audio
- **Desktop UI**: PyQt6
- **Virtual Camera Output**: PyVirtualCam

---

## 🚀 Quick Start Guide

### 1. Installation

Clone or extract the repository, open PowerShell or Terminal in the project directory, and install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Launching the Application

Run the main application:

```bash
python main.py
```

Optional Command-Line Arguments:
```bash
python main.py --camera 0 --width 1280 --height 720 --sensitivity 0.75 --particles 12000
```

---

## 🎮 Controls & Keyboard Shortcuts

| Key / Control | Action | Description |
| :--- | :--- | :--- |
| **Finger Snap** | **Disappear / Reappear** | Natural finger snap gesture in front of camera |
| <kbd>SPACE</kbd> | **Disappear** | Manual trigger to start Avengers dust disintegration |
| <kbd>R</kbd> | **Reappear** | Manual trigger to reverse-reconstruct your body |
| <kbd>B</kbd> | **Capture Background** | Calibrates/locks the clean room background frame |
| <kbd>ESC</kbd> | **Exit** | Closes the application safely |
| **Emergency Restore** | **Instant Reset** | Instantly reverts back to visible camera feed |

---

## 📷 Background Calibration (Best Results)

To ensure your empty room looks 100% natural when you disappear:
1. When starting the app, sit in your normal meeting position.
2. The app **automatically learns** the background as you naturally move.
3. For the **pristine cinematic shot**:
   - Briefly lean or step out of the camera view for 1 second.
   - Press <kbd>B</kbd> (or click **Recapture Background**).
   - Step back in. The background is now permanently locked!

---

## 🌐 Virtual Camera Setup (Zoom, Google Meet, Teams)

### Prerequisites (Windows)
1. Download and install **OBS Studio** (Free & Open Source from [obsproject.com](https://obsproject.com/)).
2. Launch OBS Studio once, and click **Start Virtual Camera** (bottom right controls dock). You can then stop it or close OBS. This permanently registers the Windows virtual camera driver.

### Enabling in Snap Disappear
1. In the Snap Disappear dashboard, navigate to the **Camera & Streaming** card on the right.
2. Click **🌐 Enable Virtual Camera**.
3. The badge in the top right will change to `VIRTUAL CAM: ACTIVE`.

### Selecting in Meeting Applications

#### Google Meet:
1. Join or start a Google Meet call.
2. Click the **More Options** (3 dots) at the bottom $\rightarrow$ **Settings** $\rightarrow$ **Video**.
3. Under **Camera**, select **OBS Virtual Camera** (or the registered virtual device).

#### Zoom:
1. Open Zoom Settings $\rightarrow$ **Video**.
2. Under **Camera**, select **OBS Virtual Camera**.
3. Uncheck *Mirror my video* if desired (Snap Disappear already mirrors the preview naturally).

#### Microsoft Teams:
1. In Teams, go to **Settings** $\rightarrow$ **Devices**.
2. Under **Camera**, choose **OBS Virtual Camera**.

---

## 🔬 How the Finger Snap Detector Works

A real finger snap consists of distinct biomechanical phases:
1. **Pinch & Friction Contact (`PRIMED`)**:
   - The thumb pad (Landmark 4) and middle finger pad (Landmark 12/11) compress together.
   - Hand scale normalization: `hand_scale = ||Wrist - Middle_MCP||`.
   - Contact threshold: Normalized distance $< 0.12$.
   - Held for at least 2 consecutive frames to build muscular tension.
2. **Explosive Release & Downward Stroke (`FIRE`)**:
   - The middle finger rapidly slides off the thumb pad and accelerates inward toward the palm / wrist.
   - Velocity check: Separation speed $\frac{\Delta \text{dist}}{\Delta t} > \text{threshold}$.
   - Handedness separation: Tracked independently for Left and Right hands.
3. **Debounce Cooldown**:
   - Once a snap fires, a 1.25s cooldown prevents accidental repeated triggers.

---

## 🧪 Running Automated Tests

Run the full automated test suite covering snap detection kinematics and particle physics:

```bash
python -m unittest discover tests
```

Output:
```text
Ran 8 tests in 0.297s
OK
```

---

## 🛠️ Troubleshooting

- **Webcam not showing video**:
  - In the **Camera & Streaming** panel, select a different **Camera Index** (e.g. index 1 or 2 if you have an external USB webcam).
  - Check that other applications (like Windows Camera app) are not exclusively locking the webcam.
- **Virtual Camera says "UNAVAILABLE"**:
  - Ensure OBS Studio has been installed and its virtual camera driver registered.
- **Snap not triggering easily**:
  - Increase the **Snap Sensitivity** slider to `0.85` or `0.90`.
  - Ensure your hand is well-lit and clearly visible within the camera frame.
  - Or use the instant hotkey: <kbd>SPACE</kbd> to Disappear, <kbd>R</kbd> to Reappear.
- **Low Frame Rate (FPS < 20)**:
  - In the **Resolution** dropdown, select `640 x 480 (Fast)`.
  - Lower the **Max Particle Count** slider to `5000`.

---

## 📜 License & Credits

Built with ❤️ for cinematic VFX enthusiasts and Python developers.
Inspired by Marvel Studios' *Avengers: Infinity War* & *Avengers: Endgame*.

