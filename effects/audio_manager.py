"""
Audio Manager for Snap Disappear.
Plays high-quality cinematic sound effects asynchronously without blocking video processing.
Uses native Windows winsound when on Windows, or sounddevice / threading as fallback.
"""

import os
import threading
import sys

class AudioManager:
    """Manages sound effect playback asynchronously."""
    
    def __init__(self):
        self._enabled = True
        self._lock = threading.Lock()
        self._use_winsound = sys.platform.startswith("win")
        
        # Pre-verify sound files
        self.sounds = {}
    
    def register_sound(self, name: str, filepath: str):
        """Registers a sound file by name."""
        if os.path.exists(filepath):
            self.sounds[name] = os.path.abspath(filepath)
        else:
            print(f"[AudioManager] Warning: Sound file not found: {filepath}")

    def play(self, name: str):
        """Plays registered sound asynchronously in a separate worker thread."""
        if not self._enabled:
            return
        
        filepath = self.sounds.get(name)
        if not filepath or not os.path.exists(filepath):
            return

        # Windows native winsound is instantaneous and thread-safe
        def _play_worker():
            try:
                if self._use_winsound:
                    import winsound
                    winsound.PlaySound(filepath, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    # Fallback using sounddevice / soundfile
                    import soundfile as sf
                    import sounddevice as sd
                    data, fs = sf.read(filepath, dtype='float32')
                    sd.play(data, fs)
                    sd.wait()
            except Exception as e:
                print(f"[AudioManager] Playback error: {e}")

        threading.Thread(target=_play_worker, daemon=True).start()

    def set_enabled(self, enabled: bool):
        self._enabled = enabled

# Global singleton instance
audio_manager = AudioManager()

