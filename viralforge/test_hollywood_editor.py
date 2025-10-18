import unittest
from unittest.mock import patch, MagicMock, ANY
from viralforge.hollywood_editor import HollywoodEditor

class TestHollywoodEditor(unittest.TestCase):

    def setUp(self):
        self.mock_video_path = "dummy.mp4"
        self.mock_transcript = {'segments': []}
        self.editor = HollywoodEditor(self.mock_video_path, self.mock_transcript)

    @patch('viralforge.hollywood_editor.VideoFileClip')
    def test_produce_valorant_clips_effects(self, MockVideoFileClip):
        """
        Test if produce_valorant_clips applies the correct dynamic effects
        by checking if the correct VFX functions are called.
        """
        # --- Mock Setup ---
        mock_video_obj = MagicMock()
        MockVideoFileClip.return_value.__enter__.return_value = mock_video_obj

        mock_base_clip = MagicMock(duration=10.0)
        mock_fx_clip = MagicMock(duration=10.0) # The clip after effects are applied
        mock_base_clip.fx.return_value = mock_fx_clip

        # Mock the internal helper methods
        with patch.object(self.editor, '_create_base_clip', return_value=mock_base_clip) as mock_create_base, \
             patch.object(self.editor, '_generate_subtitles', return_value=None) as mock_gen_subs, \
             patch('viralforge.hollywood_editor.CompositeVideoClip') as mock_Composite, \
             patch('viralforge.hollywood_editor.TextClip') as mock_TextClip:

            mock_final_video = MagicMock()
            mock_final_video.write_videofile = MagicMock()
            mock_Composite.return_value = mock_final_video
            mock_TextClip.return_value.set_position.return_value.set_duration.return_value.set_start.return_value = MagicMock()

            # --- Test Data ---
            narrative_clips = [{
                'type': 'reaction_kill',
                'start': 5.0, 'end': 15.0,
                'events': [
                    {'event': 'kill', 'timestamp': 10.0, 'details': {'type': 'headshot'}},
                ]
            }]

            # --- Test Execution ---
            self.editor.produce_valorant_clips(narrative_clips, "test_output")

            # --- Assertions ---
            # 1. Was the video file opened?
            MockVideoFileClip.assert_called_with(self.mock_video_path)

            # 2. Was the base clip created with the open video object?
            mock_create_base.assert_called_with(mock_video_obj, 5.0, 15.0)

            # 3. Was the slomo effect for the headshot applied?
            mock_base_clip.fx.assert_called_once()
            fx_call_args = mock_base_clip.fx.call_args
            self.assertEqual(fx_call_args[0][0].__name__, 'speedx')

            # 4. Was the 'REACTION!' overlay created?
            mock_TextClip.assert_any_call("REACTION!", fontsize=ANY, color=ANY, font=ANY, stroke_color=ANY, stroke_width=ANY)

            # 5. Was the final video written to a file?
            self.assertTrue(mock_final_video.write_videofile.called)

if __name__ == '__main__':
    unittest.main()