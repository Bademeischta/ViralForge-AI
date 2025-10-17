import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ClipCurator:
    """
    Scores signals, identifies high-potential moments, and selects the best clips.
    """

    BASE_SCORES = {
        'loud_segment': 30,
        'keyword': 20,
        'question': 15,
        'exclamation': 10,
        'silence': 5,
    }

    def __init__(self, signals: List[Dict], transcript: List[Dict]):
        """
        Initializes the ClipCurator.

        Args:
            signals (List[Dict]): The sorted list of signals from SignalRecognizer.
            transcript (List[Dict]): The full, timestamped transcript.
        """
        self.signals = signals
        self.transcript = transcript
        if not self.transcript:
            self.video_duration = 0
        else:
            # Determine video duration from the end of the last transcript segment
            self.video_duration = self.transcript[-1]['end'] if self.transcript else 0

    def score_signals(self) -> List[Dict]:
        """
        Assigns a base score to each signal based on its type.

        Returns:
            List[Dict]: The list of signals, with a 'score' key added to each dictionary.
        """
        for signal in self.signals:
            signal['score'] = self.BASE_SCORES.get(signal['type'], 0)
        return self.signals

    def find_moments(self, window_size: int = 15, step_size: int = 1) -> List[Dict]:
        """
        Analyzes the video in overlapping windows to find high-scoring moments.

        Args:
            window_size (int): The duration of the sliding window in seconds.
            step_size (int): The step of the sliding window in seconds.

        Returns:
            List[Dict]: A list of moment dictionaries with start, end, score, and signals.
        """
        logging.info("Finding high-potential moments using a sliding window...")
        moments = []
        if not self.signals:
            return []

        scored_signals = self.score_signals()

        for window_start in range(0, int(self.video_duration) - window_size + 1, step_size):
            window_end = window_start + window_size

            signals_in_window = [s for s in scored_signals if window_start <= s['start'] < window_end]

            if not signals_in_window:
                continue

            # Calculate base score
            moment_score = sum(s['score'] for s in signals_in_window)

            # --- Apply Combination Bonuses ---
            # Bonus 1: Question followed by a loud segment
            has_question = any(s['type'] == 'question' for s in signals_in_window)
            has_loud_segment = any(s['type'] == 'loud_segment' for s in signals_in_window)
            if has_question and has_loud_segment:
                question_time = next(s['start'] for s in signals_in_window if s['type'] == 'question')
                loud_time = next(s['start'] for s in signals_in_window if s['type'] == 'loud_segment')
                if 0 < (loud_time - question_time) < 10: # Loud segment within 10s of question
                    moment_score += 25

            # Bonus 2: Keyword and exclamation in the same segment
            # This requires checking the original text segment
            text_segments_in_window = {s['text'] for s in signals_in_window if 'text' in s}
            for text in text_segments_in_window:
                has_keyword = any(s['type'] == 'keyword' and s['text'] == text for s in signals_in_window)
                has_exclamation = any(s['type'] == 'exclamation' and s['text'] == text for s in signals_in_window)
                if has_keyword and has_exclamation:
                    moment_score += 15

            moments.append({
                'start': window_start,
                'end': window_end,
                'score': moment_score,
                'signals_in_moment': signals_in_window
            })

        logging.info(f"Identified {len(moments)} potential moments.")
        return moments

    def select_best_clips(self, top_n: int = 10, overlap_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Selects the best, non-overlapping clips from a list of moments.

        Args:
            top_n (int): The number of top candidates to consider.
            overlap_threshold (float): The maximum allowed overlap ratio between clips.

        Returns:
            List[Dict[str, Any]]: The final list of selected clips with adjusted boundaries.
        """
        moments = self.find_moments()
        if not moments:
            return []

        # Sort all potential moments by score
        candidates = sorted(moments, key=lambda m: m['score'], reverse=True)

        logging.info(f"Selecting best clips from {len(candidates)} potential moments...")
        final_clips = []

        while candidates and len(final_clips) < top_n:
            # Take the best candidate
            best_candidate = candidates.pop(0)
            final_clips.append(best_candidate)

            # Remove all other candidates that overlap with the one we just added
            remaining_candidates = []
            for candidate in candidates:
                overlap_start = max(best_candidate['start'], candidate['start'])
                overlap_end = min(best_candidate['end'], candidate['end'])
                overlap_duration = max(0, overlap_end - overlap_start)

                candidate_duration = candidate['end'] - candidate['start']

                # If the candidate overlaps significantly with the clip we just added, discard it.
                if candidate_duration > 0 and (overlap_duration / candidate_duration) > overlap_threshold:
                    continue

                remaining_candidates.append(candidate)

            # Replace the candidate list with the filtered list for the next iteration
            candidates = sorted(remaining_candidates, key=lambda m: m['score'], reverse=True)

        # Adjust boundaries to align with transcript segments
        adjusted_clips = []
        for clip in final_clips:
            # Find the earliest start time and latest end time of signals *within* the moment
            if not clip['signals_in_moment']:
                continue

            first_signal_start = min(s['start'] for s in clip['signals_in_moment'])
            last_signal_end = max(s['end'] for s in clip['signals_in_moment'])

            # Find the transcript segment that contains the first signal
            start_segment = next((seg for seg in self.transcript if seg['start'] <= first_signal_start < seg['end']), None)

            # Find the transcript segment that contains the last signal
            end_segment = next((seg for seg in self.transcript if seg['start'] <= last_signal_end <= seg['end']), None)

            new_start = start_segment['start'] if start_segment else clip['start']
            new_end = end_segment['end'] if end_segment else clip['end']

            adjusted_clips.append({
                'start': new_start,
                'end': new_end,
                'score': clip['score'],
                'signals': clip['signals_in_moment']
            })

        logging.info(f"Selected {len(adjusted_clips)} final clips after removing overlaps and adjusting boundaries.")
        # Sort final clips by start time before returning
        return sorted(adjusted_clips, key=lambda c: c['start'])