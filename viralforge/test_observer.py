import unittest
import os
import shutil
import json
import numpy as np
import cv2
from unittest.mock import patch, MagicMock
from viralforge.observer import GameObserver

class TestGameObserver(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = "test_observer_workspace"
        self.frames_dir = os.path.join(self.workspace_dir, "frames")
        self.assets_dir = "test_assets"
        os.makedirs(os.path.join(self.assets_dir, "templates", "valorant"), exist_ok=True)
        os.makedirs(self.frames_dir, exist_ok=True)

        # Create a valid, non-empty dummy template file
        dummy_template = np.random.randint(0, 255, (10, 10), dtype=np.uint8)
        cv2.imwrite(os.path.join(self.assets_dir, "templates", "valorant", "kill_icon.png"), dummy_template)
        cv2.imwrite(os.path.join(self.assets_dir, "templates", "valorant", "headshot_icon.png"), dummy_template)

    def tearDown(self):
        shutil.rmtree(self.workspace_dir)
        shutil.rmtree(self.assets_dir)

    def test_load_templates(self):
        """Test if templates are loaded correctly."""
        observer = GameObserver(self.frames_dir, (1920, 1080), self.assets_dir)
        self.assertIn('kill_icon', observer.templates)
        self.assertIn('headshot_icon', observer.templates)

    def test_empty_templates_fail_gracefully(self):
        """Test that analysis stops if templates are empty or invalid."""
        # Overwrite a valid template with an empty file
        open(os.path.join(self.assets_dir, "templates", "valorant", "kill_icon.png"), 'w').close()

        observer = GameObserver(self.frames_dir, (1920, 1080), self.assets_dir)
        # The observer should now be marked as invalid
        self.assertFalse(observer.templates_valid)
        # Analysis should return an empty list immediately
        events = observer.analyze_all_frames()
        self.assertEqual(events, [])

    @patch('cv2.imread')
    @patch('cv2.matchTemplate')
    def test_analyze_all_frames_with_debouncing(self, mock_matchTemplate, mock_imread):
        """Test the full frame analysis pipeline, focusing on debouncing logic."""
        # --- Mock Setup ---
        dummy_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        frame_files = {
            "frame_00001000.jpg": 1.0, "frame_00001100.jpg": 1.1,
            "frame_00002500.jpg": 2.5
        }
        for f_name in frame_files:
            cv2.imwrite(os.path.join(self.frames_dir, f_name), dummy_frame)

        mock_imread.return_value = dummy_frame
        mock_res = np.zeros((200, 200), dtype=np.float32)
        mock_res[50, 10] = 0.9
        mock_res[100, 10] = 0.95
        mock_matchTemplate.return_value = mock_res

        with patch('numpy.where') as mock_where:
            def where_side_effect(condition):
                current_file = os.path.basename(mock_imread.call_args[0][0])
                if current_file == "frame_00001000.jpg":
                    return (np.array([50]), np.array([10]))
                if current_file == "frame_00001100.jpg":
                    return (np.array([50]), np.array([10]))
                if current_file == "frame_00002500.jpg":
                    return (np.array([100]), np.array([10]))
                return (np.array([]), np.array([]))

            mock_where.side_effect = where_side_effect

            # --- Test Execution ---
            observer = GameObserver(self.frames_dir, (1920, 1080), self.assets_dir)
            observer.templates = {'kill_icon': np.zeros((10,10))}
            events = observer.analyze_all_frames()

            # --- Assertions ---
            self.assertEqual(len(events), 2)
            self.assertAlmostEqual(events[0]['timestamp'], 1.0)
            self.assertAlmostEqual(events[1]['timestamp'], 2.5)

if __name__ == '__main__':
    unittest.main()