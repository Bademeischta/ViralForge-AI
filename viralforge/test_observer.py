import unittest
import os
import shutil
import numpy as np
import cv2
from unittest.mock import patch, MagicMock
from viralforge.observer import GameObserver

class TestEgoCentricObserver(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = "test_observer_workspace"
        self.frames_dir = os.path.join(self.workspace_dir, "frames")
        self.assets_dir = "test_assets_v2"
        # Create the full required directory structure
        agents_path = os.path.join(self.assets_dir, "templates", "valorant", "agents")
        icons_path = os.path.join(self.assets_dir, "templates", "valorant", "icons")
        os.makedirs(agents_path, exist_ok=True)
        os.makedirs(icons_path, exist_ok=True)
        os.makedirs(self.frames_dir, exist_ok=True)

        # Create valid dummy templates
        cv2.imwrite(os.path.join(agents_path, "jett.png"), np.random.randint(0, 255, (10, 10), dtype=np.uint8))
        cv2.imwrite(os.path.join(icons_path, "kill.png"), np.random.randint(0, 255, (10, 10), dtype=np.uint8))

    def tearDown(self):
        shutil.rmtree(self.workspace_dir)
        shutil.rmtree(self.assets_dir)

    def test_four_factor_verification_success(self):
        """Test a successful ego-kill detection where all four factors match."""
        observer = GameObserver(
            frames_dir=self.frames_dir,
            video_resolution=(1920, 1080),
            player_name="Player1",
            assets_dir=self.assets_dir
        )

        # --- Mocking the four factors ---
        with patch.object(observer, '_is_ego_kill_color', return_value=True) as mock_color, \
             patch.object(observer, '_find_template_in_roi', return_value=True) as mock_template, \
             patch.object(observer, '_verify_player_name', return_value=True) as mock_name:

            # Create a dummy frame to trigger the analysis
            dummy_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
            cv2.imwrite(os.path.join(self.frames_dir, "frame_00001000.jpg"), dummy_frame)

            events = observer.analyze_all_frames()

            # --- Assertions ---
            # All checks should have been called
            self.assertTrue(mock_color.called)
            self.assertTrue(mock_template.called)
            self.assertTrue(mock_name.called)

            # A single ego-kill event should be created
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]['event'], 'kill')
            self.assertEqual(events[0]['details']['type'], 'Ego-Kill (Verified)')

    def test_four_factor_verification_fail_on_color(self):
        """Test that the check fails if the color is wrong."""
        observer = GameObserver(self.frames_dir, (1920, 1080), "Player1", self.assets_dir)

        with patch.object(observer, '_is_ego_kill_color', return_value=False) as mock_color, \
             patch.object(observer, '_find_template_in_roi') as mock_template, \
             patch.object(observer, '_verify_player_name') as mock_name:

            dummy_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
            cv2.imwrite(os.path.join(self.frames_dir, "frame_00001000.jpg"), dummy_frame)
            events = observer.analyze_all_frames()

            # The color check should be called, but the others should NOT be called
            self.assertTrue(mock_color.called)
            self.assertFalse(mock_template.called)
            self.assertFalse(mock_name.called)

            # No event should be created
            self.assertEqual(len(events), 0)

if __name__ == '__main__':
    unittest.main()