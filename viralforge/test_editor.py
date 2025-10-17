import unittest
from unittest.mock import patch, MagicMock, ANY
from viralforge.editor import VideoEditor

class TestVideoEditor(unittest.TestCase):

    def setUp(self):
        """Set up a mock transcript result."""
        self.mock_video_path = "dummy.mp4"
        self.mock_transcript = {
            'segments': [{'words': [
                {'word': 'Test', 'start': 0.5, 'end': 1.0},
                {'word': 'Wow', 'start': 2.5, 'end': 3.0}
            ]}]
        }
        self.editor = VideoEditor(self.mock_video_path, self.mock_transcript)

    # Patch the names as they are looked up in the 'editor' module
    @patch('viralforge.editor.CompositeVideoClip')
    @patch('viralforge.editor.crop')
    @patch('viralforge.editor.VideoFileClip')
    def test_create_clip_logic(self, MockVideoFileClip, mock_crop, MockCompositeVideoClip):
        """Test if create_clip calls moviepy functions correctly."""
        # --- Mock Setup ---
        # Mock the chained calls to return a mock object
        mock_video_instance = MagicMock()
        mock_subclip_instance = MagicMock()
        mock_subclip_instance.copy.return_value.resize.return_value.set_position.return_value = mock_subclip_instance

        MockVideoFileClip.return_value.__enter__.return_value = mock_video_instance
        mock_video_instance.subclip.return_value = mock_subclip_instance
        mock_crop.return_value = mock_subclip_instance

        # --- Test Execution ---
        self.editor.create_clip(start_time=2.0, end_time=5.0)

        # --- Assertions ---
        MockVideoFileClip.assert_called_with(self.mock_video_path)
        mock_video_instance.subclip.assert_called_with(2.0, 5.0)
        self.assertTrue(mock_crop.called)
        # Verify that CompositeVideoClip was called with a list of clips and a size
        MockCompositeVideoClip.assert_called_with(ANY, size=ANY)

    @patch('viralforge.editor.CompositeVideoClip')
    @patch('viralforge.editor.TextClip')
    def test_generate_subtitles_logic(self, MockTextClip, MockCompositeVideoClip):
        """Test if generate_subtitles calls TextClip correctly."""
        # --- Mock Setup ---
        mock_text_clip_instance = MagicMock()
        mock_text_clip_instance.set_start.return_value.set_duration.return_value.set_position.return_value = mock_text_clip_instance
        MockTextClip.return_value = mock_text_clip_instance

        # --- Test Execution ---
        self.editor.generate_subtitles(start_time=2.0, end_time=3.5)

        # --- Assertions ---
        self.assertEqual(MockTextClip.call_count, 1)
        MockTextClip.assert_called_with('WOW', fontsize=70, color='yellow', font='Impact', stroke_color='black', stroke_width=3)
        MockCompositeVideoClip.assert_called_with(ANY)

    @patch('viralforge.editor.CompositeVideoClip')
    @patch('viralforge.editor.VideoEditor.generate_subtitles')
    @patch('viralforge.editor.VideoEditor.create_clip')
    def test_produce_viral_clips_flow(self, mock_create_clip, mock_generate_subtitles, MockCompositeVideoClip):
        """Test the main production flow orchestration."""
        # --- Mock Setup ---
        mock_video = MagicMock(duration=3.0)
        mock_subs = MagicMock()
        mock_subs.set_duration.return_value = mock_subs

        final_clip = MagicMock()
        final_clip.write_videofile = MagicMock()

        mock_create_clip.return_value = mock_video
        mock_generate_subtitles.return_value = mock_subs
        MockCompositeVideoClip.return_value = final_clip

        clips_data = [{'start': 2.0, 'end': 5.0}]
        output_dir = "test_output"

        # --- Test Execution ---
        self.editor.produce_viral_clips(clips_data, output_dir)

        # --- Assertions ---
        mock_create_clip.assert_called_with(2.0, 5.0)
        mock_generate_subtitles.assert_called_with(2.0, 5.0)
        MockCompositeVideoClip.assert_called_with([mock_video, mock_subs])
        final_clip.write_videofile.assert_called_once()
        output_path_call = final_clip.write_videofile.call_args[0][0]
        self.assertIn("clip_2-5s.mp4", output_path_call)

if __name__ == '__main__':
    unittest.main()