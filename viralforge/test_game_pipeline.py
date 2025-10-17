import unittest
import os
import shutil
import cv2
from unittest.mock import patch, MagicMock
from viralforge.game_pipeline import GameDataPipeline

class TestGameDataPipeline(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = "test_v2_workspace"
        os.makedirs(self.workspace_dir, exist_ok=True)
        self.pipeline = GameDataPipeline(workspace_dir=self.workspace_dir)

    def tearDown(self):
        shutil.rmtree(self.workspace_dir)

    @patch('yt_dlp.YoutubeDL')
    def test_download_video_requests_correct_quality(self, MockYoutubeDL):
        """Test if download_video uses the correct format string for 1080p 60fps."""
        mock_ydl_instance = MockYoutubeDL.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = {
            'title': 'test_video',
            'ext': 'mp4',
            'height': 1080,
            'fps': 60
        }
        mock_ydl_instance.prepare_filename.return_value = os.path.join(self.workspace_dir, "test_video.mp4")

        self.pipeline.download_video("dummy_url")

        # Verify that the format option was set correctly
        called_ydl_opts = MockYoutubeDL.call_args[0][0]
        self.assertIn('bestvideo[height=1080][fps=60]', called_ydl_opts['format'])

    @patch('cv2.VideoCapture')
    def test_extract_game_frames(self, MockVideoCapture):
        """Test the frame extraction logic."""
        # --- Mock Setup ---
        mock_cap_instance = MockVideoCapture.return_value
        mock_cap_instance.isOpened.return_value = True

        # Configure a more robust mock for the 'get' method
        def get_side_effect(prop_id):
            if prop_id == cv2.CAP_PROP_FPS:
                return 60.0
            if prop_id == cv2.CAP_PROP_POS_MSEC:
                # Simulate time passing
                get_side_effect.msec_counter += 100
                return get_side_effect.msec_counter
            return 0
        get_side_effect.msec_counter = -100 # Start at -100 so first call is 0

        mock_cap_instance.get.side_effect = get_side_effect

        # Simulate reading 61 frames to get 11 saved frames (at 10fps from 60fps video)
        mock_cap_instance.read.side_effect = [(True, "fake_frame_data")] * 61 + [(False, None)]

        # Create a dummy video file for the method to find
        dummy_video_path = os.path.join(self.workspace_dir, "video.mp4")
        with open(dummy_video_path, "w") as f:
            f.write("dummy")

        with patch('cv2.imwrite') as mock_imwrite:
            frames_dir = self.pipeline.extract_game_frames(dummy_video_path, frame_rate=10)

            # --- Assertions ---
            self.assertIsNotNone(frames_dir)
            self.assertTrue(os.path.exists(frames_dir))

            # We expect to save a frame every 6 frames (60fps / 10 target fps)
            # For 61 total frames, we should save at frame 0, 6, 12, ..., 60. That's 11 frames.
            self.assertEqual(mock_imwrite.call_count, 11)

            # Check the filename of the first and second call
            first_call_args = mock_imwrite.call_args_list[0][0]
            self.assertIn("frame_00000000.jpg", first_call_args[0])

            second_call_args = mock_imwrite.call_args_list[1][0]
            self.assertIn("frame_00000100.jpg", second_call_args[0])

if __name__ == '__main__':
    unittest.main()