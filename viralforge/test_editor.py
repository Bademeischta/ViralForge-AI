import unittest
from unittest.mock import patch, MagicMock, ANY
from viralforge.editor import VideoEditor

class TestVideoEditor(unittest.TestCase):

    def setUp(self):
        self.mock_video_path = "dummy.mp4"
        self.mock_transcript = {'segments': []}
        self.editor = VideoEditor(self.mock_video_path, self.mock_transcript)

    @patch('viralforge.editor.VideoFileClip')
    def test_produce_viral_clips_flow(self, MockVideoFileClip):
        """
        Test the main production flow, ensuring the video file is opened
        and its object is passed to helper methods.
        """
        # --- Mock Setup ---
        mock_video_obj = MagicMock()
        MockVideoFileClip.return_value.__enter__.return_value = mock_video_obj

        # Mock the internal helper methods to prevent actual processing
        with patch.object(self.editor, '_create_base_clip') as mock_create_base, \
             patch.object(self.editor, '_generate_subtitles') as mock_gen_subs, \
             patch('viralforge.editor.CompositeVideoClip') as mock_Composite:

            mock_base_clip = MagicMock()
            mock_base_clip.duration = 10.0
            mock_create_base.return_value = mock_base_clip
            mock_gen_subs.return_value = None

            mock_final_video = MagicMock()
            mock_final_video.write_videofile = MagicMock()
            mock_Composite.return_value = mock_final_video

            # --- Test Data ---
            clips_data = [{'start': 5.0, 'end': 15.0}]

            # --- Test Execution ---
            self.editor.produce_viral_clips(clips_data, "test_output")

            # --- Assertions ---
            # 1. Was the video file opened?
            MockVideoFileClip.assert_called_with(self.mock_video_path)

            # 2. Was the base clip created using the opened video object?
            mock_create_base.assert_called_with(mock_video_obj, 5.0, 15.0)

            # 3. Were subtitles generated for the correct time?
            mock_gen_subs.assert_called_with(5.0, 15.0)

            # 4. Was the final video written to a file?
            self.assertTrue(mock_final_video.write_videofile.called)

if __name__ == '__main__':
    unittest.main()