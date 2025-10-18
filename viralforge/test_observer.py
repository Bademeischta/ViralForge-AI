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
        os.makedirs(os.path.join(self.assets_dir, "templates", "valorant", "agents"), exist_ok=True)
        os.makedirs(os.path.join(self.assets_dir, "templates", "valorant", "icons"), exist_ok=True)
        os.makedirs(self.frames_dir, exist_ok=True)

        self.observer = GameObserver(
            frames_dir=self.frames_dir,
            video_resolution=(1920, 1080),
            player_name="Player1",
            assets_dir=self.assets_dir
        )

    def tearDown(self):
        shutil.rmtree(self.workspace_dir)
        shutil.rmtree(self.assets_dir)

    def test_color_filter_ego_kill(self):
        """Test if the green color of an ego kill is correctly identified."""
        # Create a dummy image that is mostly green
        green_image = np.full((50, 200, 3), (35, 250, 150), dtype=np.uint8) # Green in BGR
        is_ego = self.observer._is_ego_kill_color(green_image)
        self.assertTrue(is_ego)

    def test_color_filter_enemy_kill(self):
        """Test if the red color of an enemy kill is correctly filtered out."""
        # Create a dummy image that is mostly red
        red_image = np.full((50, 200, 3), (0, 0, 200), dtype=np.uint8) # Red in BGR
        is_ego = self.observer._is_ego_kill_color(red_image)
        self.assertFalse(is_ego)

    @patch('pytesseract.image_to_string')
    def test_name_verification_fuzzy_match(self, mock_image_to_string):
        """Test if fuzzy string matching correctly identifies the player's name."""
        dummy_roi = np.zeros((30, 100, 3), dtype=np.uint8)

        # Test 1: Perfect match
        mock_image_to_string.return_value = "Player1"
        self.assertTrue(self.observer._verify_player_name(dummy_roi))

        # Test 2: OCR error (I instead of 1)
        mock_image_to_string.return_value = "PlayerI"
        self.assertTrue(self.observer._verify_player_name(dummy_roi))

        # Test 3: Completely different name
        mock_image_to_string.return_value = "EnemyPlayer"
        self.assertFalse(self.observer._verify_player_name(dummy_roi))

        # Test 4: No text found
        mock_image_to_string.return_value = ""
        self.assertFalse(self.observer._verify_player_name(dummy_roi))

if __name__ == '__main__':
    unittest.main()