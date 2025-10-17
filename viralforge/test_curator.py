import unittest
from viralforge.curator import ClipCurator

class TestClipCurator(unittest.TestCase):

    def setUp(self):
        """Set up a mock transcript and a list of signals for testing."""
        self.mock_transcript = [
            {'text': 'Hello there.', 'start': 0.0, 'end': 1.5},
            {'text': 'So, what is the plan?', 'start': 2.0, 'end': 4.0},
            {'text': 'This is just amazing!', 'start': 5.0, 'end': 7.5},
            {'text': 'A regular sentence.', 'start': 8.0, 'end': 9.5},
            {'text': 'And then, boom! A loud sound.', 'start': 10.0, 'end': 12.0},
            {'text': 'Followed by silence.', 'start': 14.0, 'end': 15.5},
            {'text': 'Another question?', 'start': 16.0, 'end': 17.0},
            {'text': 'This is also amazing!', 'start': 18.0, 'end': 20.0},
        ]

        self.mock_signals = [
            # Moment 1: Question followed by loud sound + keyword
            {'type': 'question', 'text': 'So, what is the plan?', 'start': 2.5, 'end': 4.0},
            {'type': 'keyword', 'word': 'amazing', 'text': 'This is just amazing!', 'start': 5.5, 'end': 7.5},
            {'type': 'exclamation', 'text': 'This is just amazing!', 'start': 5.5, 'end': 7.5},
            {'type': 'loud_segment', 'start': 6.0, 'end': 7.0},

            # Moment 2: Overlapping, but lower score
            {'type': 'keyword', 'word': 'amazing', 'text': 'This is also amazing!', 'start': 18.5, 'end': 20.0},
            {'type': 'exclamation', 'text': 'This is also amazing!', 'start': 18.5, 'end': 20.0},

            # Moment 3: A separate, distinct moment
            {'type': 'silence', 'start': 12.5, 'end': 13.8},
            {'type': 'question', 'text': 'Another question?', 'start': 16.2, 'end': 17.0},
        ]

        self.curator = ClipCurator(self.mock_signals, self.mock_transcript)

    def test_score_signals(self):
        """Test if signals are scored correctly."""
        scored_signals = self.curator.score_signals()
        self.assertEqual(scored_signals[0]['score'], 15) # question
        self.assertEqual(scored_signals[1]['score'], 20) # keyword
        self.assertEqual(scored_signals[3]['score'], 30) # loud_segment
        self.assertEqual(scored_signals[6]['score'], 5)  # silence

    def test_find_moments_scoring(self):
        """Test the sliding window and scoring logic, including bonuses."""
        moments = self.curator.find_moments(window_size=10)

        # Find the moment with the highest score (should be the first one)
        top_moment = max(moments, key=lambda m: m['score'])

        # Expected score for the top moment (window starting around 0-2s):
        # Base scores: question(15) + keyword(20) + exclamation(10) + loud(30) = 75
        # Bonus: question + loud = 25
        # Bonus: keyword + exclamation in same text = 15
        # Total = 75 + 25 + 15 = 115
        self.assertEqual(top_moment['score'], 115)
        self.assertEqual(top_moment['start'], 0) # Window starts at 0

    def test_select_best_clips_no_overlap(self):
        """Test that non-overlapping clips are selected correctly."""
        # Modify signals to ensure no overlap between top moments
        self.curator.signals = [
            {'type': 'question', 'start': 2.5, 'end': 4.0},
            {'type': 'loud_segment', 'start': 6.0, 'end': 7.0},
            {'type': 'keyword', 'start': 22.0, 'end': 23.0}, # Far away
        ]
        self.curator.video_duration = 30

        clips = self.curator.select_best_clips(top_n=2)
        self.assertEqual(len(clips), 2)

    def test_select_best_clips_with_overlap(self):
        """Test that overlapping clips are correctly filtered."""
        # Two high-scoring moments that overlap significantly
        overlapping_signals = [
            # Clip 1 (Higher score)
            {'type': 'question', 'start': 2.0, 'end': 3.0, 'text': 'q1'},
            {'type': 'loud_segment', 'start': 4.0, 'end': 5.0},
            # Clip 2 (Lower score, but overlaps)
            {'type': 'keyword', 'start': 3.0, 'end': 4.0, 'text': 'k1'},
        ]
        curator = ClipCurator(overlapping_signals, self.mock_transcript)
        curator.video_duration = 20

        clips = curator.select_best_clips(top_n=2, overlap_threshold=0.3)

        # The first moment (question+loud) should have a higher score and be selected.
        # The second moment (just a keyword) overlaps and should be discarded.
        self.assertEqual(len(clips), 1)
        # Check that the selected clip is the one with the higher score (from question + loud)
        self.assertIn('question', [s['type'] for s in clips[0]['signals']])

    def test_adjust_clip_boundaries(self):
        """Test if clip boundaries are correctly adjusted to transcript segments."""
        signals = [{'type': 'loud_segment', 'start': 6.5, 'end': 7.0, 'score': 30}]
        # Transcript segment is: {'text': 'This is just amazing!', 'start': 5.0, 'end': 7.5}

        curator = ClipCurator(signals, self.mock_transcript)
        curator.video_duration = 20

        clips = curator.select_best_clips(top_n=1)

        self.assertEqual(len(clips), 1)
        final_clip = clips[0]

        # The original moment window might be e.g. 0-15s
        # But the final clip should be snapped to the transcript segment boundaries
        self.assertEqual(final_clip['start'], 5.0)
        self.assertEqual(final_clip['end'], 7.5)

if __name__ == '__main__':
    unittest.main()