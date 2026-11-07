"""
Unit tests for the Vectorized Particle Engine and Physics Simulation.
"""

import unittest
import numpy as np
from effects.particle_engine import ParticleEngine

class TestParticleEngine(unittest.TestCase):

    def setUp(self):
        self.engine = ParticleEngine(max_particles=5000)

    def test_allocation(self):
        """Tests buffer allocation and initial state."""
        self.assertEqual(self.engine.count, 0)
        self.assertEqual(self.engine.pos.shape, (5000, 2))
        self.assertEqual(self.engine.vel.shape, (5000, 2))
        self.assertEqual(self.engine.color.shape, (5000, 3))

    def test_spawning(self):
        """Tests spawning particles from pixel coordinates."""
        # Create a mock 100x100 circle of eroded pixels
        y_grid, x_grid = np.ogrid[:100, :100]
        mask = (x_grid - 50)**2 + (y_grid - 50)**2 <= 20**2
        coords = np.where(mask)
        mock_bgr = np.ones((100, 100, 3), dtype=np.uint8) * 180

        self.engine.spawn_from_dissolution(coords, mock_bgr, spawn_fraction=0.5)

        self.assertGreater(self.engine.count, 0)
        self.assertLessEqual(self.engine.count, len(coords[0]))
        # Ensure alphas are initialized
        self.assertTrue(np.all(self.engine.alpha[:self.engine.count] == 1.0))

    def test_physics_integration(self):
        """Tests update step advances positions according to velocities and wind."""
        self.engine.pos[0] = [100.0, 100.0]
        self.engine.vel[0] = [50.0, -30.0]
        self.engine.max_life[0] = 3.0
        self.engine.initial_size[0] = 4.0
        self.engine.count = 1

        self.engine.update(dt=0.033)

        # Position should have advanced
        self.assertNotEqual(self.engine.pos[0, 0], 100.0)
        self.assertNotEqual(self.engine.pos[0, 1], 100.0)
        # Life should have increased
        self.assertGreater(self.engine.life[0], 0.0)

    def test_rendering(self):
        """Tests rendering does not crash and alters the canvas."""
        canvas = np.zeros((480, 640, 3), dtype=np.uint8)
        self.engine.pos[0] = [320.0, 240.0]
        self.engine.color[0] = [0, 215, 255] # Gold
        self.engine.size[0] = 3.0
        self.engine.alpha[0] = 1.0
        self.engine.is_glow[0] = 1
        self.engine.count = 1

        out = self.engine.render(canvas)
        self.assertEqual(out.shape, (480, 640, 3))
        # At pixel (240, 320), output must not be zero
        self.assertGreater(np.sum(out[238:243, 318:323]), 0)

if __name__ == "__main__":
    unittest.main()

