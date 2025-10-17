import unittest
from unittest.mock import patch
import numpy as np
from viralforge.recognizer import SignalRecognizer

class TestSignalRecognizer(unittest.TestCase):

    def setUp(self):
        """Set up common test data."""
        self.sample_transcript_result = {
            'segments': [
                {'text': 'Alright, here we go.', 'start': 0.5, 'end': 2.0},
                {'text': 'So, what is the main problem here?', 'start': 3.0, 'end': 5.0},
                {'text': 'This is just incredible!', 'start': 6.0, 'end': 8.0},
                {'text': 'I mean, wow.', 'start': 8.1, 'end': 8.8},
                {'text': 'A normal sentence for testing.', 'start': 10.0, 'end': 12.0},
            ]
        }
        self.dummy_audio_path = "dummy/path/to/audio.mp3"
        self.recognizer = SignalRecognizer(self.sample_transcript_result, self.dummy_audio_path)

    def test_analyze_transcript_signals(self):
        """Test the text analysis for correct signal detection."""
        signals = self.recognizer.analyze_transcript()

        # Expected signals:
        # 1. Question: "what is the main problem here?"
        # 2. Keyword: "problem" in the same sentence
        # 3. Keyword: "incredible"
        # 4. Exclamation: "incredible!"
        # 5. Keyword: "wow"
        self.assertEqual(len(signals), 5)

        signal_types = [s['type'] for s in signals]
        self.assertIn('question', signal_types)
        self.assertIn('keyword', signal_types)
        self.assertIn('exclamation', signal_types)

        keyword_signals = [s for s in signals if s['type'] == 'keyword']
        self.assertEqual(len(keyword_signals), 3)

        found_keywords = {s['word'] for s in keyword_signals}
        self.assertIn('problem', found_keywords)
        self.assertIn('incredible', found_keywords)
        self.assertIn('wow', found_keywords)

    @patch('librosa.load')
    @patch('librosa.get_duration')
    def test_analyze_audio_signals(self, mock_get_duration, mock_load):
        """Test the audio analysis with mocked librosa data."""
        # --- Mock Setup ---
        sr = 22050  # Sample rate
        duration_secs = 20

        # Create a silent audio signal
        y = np.zeros(sr * duration_secs, dtype=np.float32)

        # Add a loud segment from 5s to 7s
        y[5 * sr : 7 * sr] = 0.9

        # Add another loud segment from 15s to 16s
        y[15 * sr : 16 * sr] = 0.8

        # Mock the return values of librosa functions
        mock_load.return_value = (y, sr)
        mock_get_duration.return_value = duration_secs

        # --- Test Execution ---
        signals = self.recognizer.analyze_audio(loudness_threshold_factor=2.0, silence_threshold_sec=1.0)

        # --- Assertions ---
        # Expected signals:
        # 1. Silence: 0s -> 5s (duration 5s > 1s)
        # 2. Loud: 5s -> 7s
        # 3. Silence: 7s -> 15s (duration 8s > 1s)
        # 4. Loud: 15s -> 16s
        # 5. Silence: 16s -> 20s (duration 4s > 1s)

        # Note: The exact number can vary based on librosa's internal frame logic.
        # We check for the presence and types of signals.
        signal_types = [s['type'] for s in signals]

        self.assertIn('silence', signal_types)
        self.assertIn('loud_segment', signal_types)

        silence_count = sum(1 for s in signal_types if s == 'silence')
        loud_count = sum(1 for s in signal_types if s == 'loud_segment')

        self.assertGreaterEqual(silence_count, 2)
        self.assertGreaterEqual(loud_count, 2)

        # Check if the start times are roughly correct
        first_loud = next(s for s in signals if s['type'] == 'loud_segment')
        self.assertAlmostEqual(first_loud['start'], 5.0, delta=0.1)
        self.assertAlmostEqual(first_loud['end'], 7.0, delta=0.1)

    @patch('librosa.load')
    @patch('librosa.get_duration')
    def test_find_signals_combined_and_sorted(self, mock_get_duration, mock_load):
        """Test if find_signals combines and sorts all signals correctly."""
        # --- Mock Setup for Audio ---
        sr = 22050
        duration_secs = 15
        y = np.zeros(sr * duration_secs, dtype=np.float32)
        y[9 * sr : 11 * sr] = 0.9 # Loud segment between text signals
        mock_load.return_value = (y, sr)
        mock_get_duration.return_value = duration_secs

        # --- Test Execution ---
        all_signals = self.recognizer.find_signals()

        # --- Assertions ---
        # Expected: 5 text signals + ~2 audio signals (1 loud, 1-2 silence)
        self.assertGreater(len(all_signals), 5)

        # Verify that the output is sorted by start time
        start_times = [s['start'] for s in all_signals]
        self.assertEqual(start_times, sorted(start_times))

        # Check if a text and audio signal appear in the correct order
        # Example: text signal at 8.1s, loud audio at 9.0s
        signal_types_in_order = [s['type'] for s in all_signals]
        wow_keyword_index = signal_types_in_order.index('keyword') # First keyword is problem, second incredible, third is wow
        loud_segment_index = signal_types_in_order.index('loud_segment')

        # The 'wow' keyword is at 8.1s, the loud segment at 9.0s.
        # So the keyword should appear before the loud segment in the sorted list.
        # This is a bit complex to assert directly, but the sorted start_times check is the main validation.
        self.assertLess(all_signals[wow_keyword_index]['start'], all_signals[loud_segment_index]['start'])


if __name__ == '__main__':
    unittest.main()