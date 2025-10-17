import unittest
from unittest.mock import patch, MagicMock, ANY
from viralforge.hollywood_editor import HollywoodEditor

class TestHollywoodEditor(unittest.TestCase):

    def setUp(self):
        """Set up a mock transcript result."""
        self.mock_video_path = "dummy.mp4"
        self.mock_transcript = {'segments': []} # Needed for init, but not for these tests
        self.editor = HollywoodEditor(self.mock_video_path, self.mock_transcript)

    @patch('viralforge.hollywood_editor.CompositeVideoClip')
    @patch('viralforge.hollywood_editor.TextClip')
    @patch.object(HollywoodEditor, 'create_clip')
    @patch.object(HollywoodEditor, 'generate_subtitles')
    def test_produce_valorant_clips_effects(self, mock_gen_subs, mock_create_clip, mock_TextClip, mock_CompositeClip):
        """
        Test if produce_valorant_clips applies the correct dynamic effects
        based on the narrative type and events.
        """
        # --- Mock Setup ---
        # Mock the base clip and the final composite clip
        mock_base_clip = MagicMock(duration=10.0)
        mock_fx_clip = MagicMock(duration=10.0)
        mock_final_clip = MagicMock()
        mock_final_clip.write_videofile = MagicMock()

        # Chain the mock effects
        mock_base_clip.fx.return_value = mock_fx_clip
        mock_create_clip.return_value = mock_base_clip
        mock_gen_subs.return_value = None # No subtitles for this test to simplify
        mock_CompositeClip.return_value = mock_final_clip

        # --- Test Data ---
        narrative_clips = [
            {
                'type': 'reaction_kill',
                'start': 5.0, 'end': 15.0,
                'events': [
                    {'event': 'kill', 'timestamp': 10.0, 'details': {'type': 'headshot'}},
                    {'type': 'loud_segment', 'timestamp': 11.0}
                ]
            },
            {
                'type': 'multi_kill',
                'start': 20.0, 'end': 30.0,
                'events': [
                    {'event': 'kill', 'timestamp': 22.0, 'details': {'type': 'bodyshot'}},
                    {'event': 'kill', 'timestamp': 24.0, 'details': {'type': 'bodyshot'}}
                ]
            }
        ]

        # --- Test Execution ---
        self.editor.produce_valorant_clips(narrative_clips, "test_output")

        # --- Assertions ---
        # Check that effects were called for the first clip (reaction_kill with headshot)
        # We expect only speedx (for headshot) to be called
        self.assertEqual(mock_base_clip.fx.call_count, 1)

        # Check the call was for the correct effect
        fx_calls = mock_base_clip.fx.call_args_list
        called_fx_names = [call[0][0].__name__ for call in fx_calls]
        self.assertIn('speedx', called_fx_names)

        # Check that the context overlay TextClip was created for 'REACTION!'
        mock_TextClip.assert_any_call("REACTION!", fontsize=ANY, color=ANY, font=ANY, stroke_color=ANY, stroke_width=ANY)

        # Check that the context overlay TextClip was created for 'MULTI-KILL'
        mock_TextClip.assert_any_call("MULTI-KILL", fontsize=ANY, color=ANY, font=ANY, stroke_color=ANY, stroke_width=ANY)

        # Check that two clips were written to file
        self.assertEqual(mock_final_clip.write_videofile.call_count, 2)


if __name__ == '__main__':
    unittest.main()