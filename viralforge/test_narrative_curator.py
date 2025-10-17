import unittest
from viralforge.narrative_curator import NarrativeCurator

class TestNarrativeCurator(unittest.TestCase):

    def setUp(self):
        """Set up a mock transcript result for context."""
        self.mock_transcript = {'segments': []}

    def test_find_multi_kill_narrative(self):
        """Test the detection of a multi-kill sequence."""
        events = [
            {'timestamp': 10.0, 'event': 'kill', 'details': {'type': 'bodyshot'}},
            {'timestamp': 12.0, 'event': 'kill', 'details': {'type': 'headshot'}},
            {'timestamp': 18.0, 'event': 'kill', 'details': {'type': 'bodyshot'}}, # Too late
        ]
        curator = NarrativeCurator(events, self.mock_transcript)
        narratives = curator.find_narratives()

        self.assertEqual(len(narratives), 1)
        self.assertEqual(narratives[0]['type'], 'multi_kill')
        self.assertEqual(len(narratives[0]['events']), 2)

    def test_find_reaction_kill_narrative(self):
        """Test the detection of a kill followed by a loud user reaction."""
        events = [
            {'timestamp': 20.0, 'event': 'kill', 'details': {'type': 'headshot'}},
            {'timestamp': 21.5, 'type': 'loud_segment', 'end': 22.5},
            {'timestamp': 30.0, 'event': 'kill', 'details': {'type': 'bodyshot'}},
            {'timestamp': 33.0, 'type': 'loud_segment', 'end': 34.0}, # Too late
        ]
        curator = NarrativeCurator(events, self.mock_transcript)
        narratives = curator.find_narratives()

        self.assertEqual(len(narratives), 1)
        self.assertEqual(narratives[0]['type'], 'reaction_kill')
        self.assertEqual(narratives[0]['events'][0]['event'], 'kill')
        self.assertEqual(narratives[0]['events'][1]['type'], 'loud_segment')

    def test_multiplicative_scoring_multi_kill(self):
        """Test the scoring for a high-value multi-kill."""
        # A double kill with a headshot
        multi_kill_events = [
            {'timestamp': 10.0, 'event': 'kill', 'details': {'type': 'bodyshot'}},
            {'timestamp': 12.0, 'event': 'kill', 'details': {'type': 'headshot'}},
        ]
        curator = NarrativeCurator([], self.mock_transcript)

        # Base score: kill(10) + kill(10) = 20
        # Multipliers:
        # - First kill: none
        # - Second kill: headshot (x2.5), multi-kill (x3)
        # Calculation: (10 + 10) * 2.5 * 3 = 20 * 7.5 = 150
        score = curator.score_narrative(multi_kill_events)
        self.assertAlmostEqual(score, 150.0)

    def test_multiplicative_scoring_reaction_kill(self):
        """Test the scoring for a high-value reaction kill."""
        reaction_kill_events = [
            {'timestamp': 20.0, 'event': 'kill', 'details': {'type': 'headshot'}},
            {'timestamp': 21.5, 'type': 'loud_segment', 'end': 22.5},
        ]
        curator = NarrativeCurator([], self.mock_transcript)

        # Base score: kill(10) + loud_segment(5) = 15
        # Multipliers:
        # - Kill: headshot (x2.5)
        # - Chain: reaction_kill (x4)
        # Calculation: (10 + 5) * 2.5 * 4 = 15 * 10 = 150
        score = curator.score_narrative(reaction_kill_events)
        self.assertAlmostEqual(score, 150.0)

    def test_select_best_clips_boundary_and_buffer(self):
        """Test if clip boundaries are set correctly around the narrative."""
        events = [
            {'timestamp': 10.0, 'event': 'kill', 'details': {'type': 'bodyshot'}},
            {'timestamp': 12.0, 'event': 'kill', 'details': {'type': 'headshot'}},
        ]
        curator = NarrativeCurator(events, self.mock_transcript)
        clips = curator.select_best_clips(top_n=1, buffer=2)

        self.assertEqual(len(clips), 1)

        # Expected start: min_timestamp(10.0) - buffer(2) = 8.0
        # Expected end: max_timestamp(12.0) + buffer(2) = 14.0
        self.assertAlmostEqual(clips[0]['start'], 8.0)
        self.assertAlmostEqual(clips[0]['end'], 14.0)

if __name__ == '__main__':
    unittest.main()