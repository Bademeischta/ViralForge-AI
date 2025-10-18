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
    def test_process_game_video_returns_resolution(self, MockVideoCapture):
        """Test that the full pipeline returns the video resolution."""
        # --- Mock Setup ---
        mock_cap_instance = MockVideoCapture.return_value
        mock_cap_instance.isOpened.return_value = True

        # Mock the return values for width and height
        def get_side_effect(prop_id):
            if prop_id == cv2.CAP_PROP_FRAME_WIDTH:
                return 1920
            if prop_id == cv2.CAP_PROP_FRAME_HEIGHT:
                return 1080
            return 60.0 # Default for other 'get' calls like FPS
        mock_cap_instance.get.side_effect = get_side_effect
        mock_cap_instance.read.side_effect = [(False, None)] # Stop after first read

        # Mock the other pipeline methods to return dummy data
        with patch.object(self.pipeline, 'download_video', return_value="dummy_path.mp4"), \
             patch.object(self.pipeline, 'extract_audio', return_value="dummy_path.mp3"), \
             patch.object(self.pipeline, 'transcribe_audio', return_value={'text': 'dummy'}), \
             patch.object(self.pipeline, 'extract_game_frames', return_value="dummy_frames_dir"):

            # --- Test Execution ---
            result = self.pipeline.process_game_video("dummy_url")

            # --- Assertions ---
            self.assertIn("video_resolution", result)
            self.assertEqual(result["video_resolution"], (1920, 1080))

if __name__ == '__main__':
    unittest.main()