import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class NarrativeCurator:
    """
    Identifies and scores narrative event chains from a combined list of game and audio/text events.
    """
    BASE_SCORES = {
        'kill': 10,
        'loud_segment': 5,
        'keyword': 3, # Lowered score as they are context for narratives
        'question': 2,
        'exclamation': 1,
        'silence': 1,
    }

    def __init__(self, all_events: List[Dict], transcript_result: Dict):
        """
        Initializes the NarrativeCurator.

        Args:
            all_events (List[Dict]): A chronologically sorted list of all events
                                     (from GameObserver and SignalRecognizer).
            transcript_result (Dict): The full transcript object for context.
        """
        self.all_events = sorted(all_events, key=lambda x: x['timestamp'])
        self.transcript = transcript_result.get('segments', [])

    def find_narratives(self) -> List[Dict]:
        """
        The core pattern recognition engine. Finds narrative sequences in the event list.

        Returns:
            A list of found narratives, where each narrative is a dictionary containing
            the narrative type, the events comprising it, and its calculated score.
        """
        logging.info("Finding narrative patterns in the event stream...")
        narratives = []

        # --- Pattern 1: Multi-Kill ---
        # Find sequences of 2 or more kills within 5 seconds.
        for i, event in enumerate(self.all_events):
            if event.get('event') == 'kill':
                multi_kill_chain = [event]
                for next_event in self.all_events[i+1:]:
                    if next_event.get('event') == 'kill':
                        # Check if the next kill is within the time window
                        if next_event['timestamp'] - event['timestamp'] < 5.0:
                            multi_kill_chain.append(next_event)
                        else:
                            break # Window exceeded

                if len(multi_kill_chain) >= 2:
                    narratives.append({
                        'type': 'multi_kill',
                        'events': multi_kill_chain,
                        'score': self.score_narrative(multi_kill_chain)
                    })

        # --- Pattern 2: Reaction Kill ---
        # Find a kill followed by a loud audio segment within 2 seconds.
        for i, event in enumerate(self.all_events):
            if event.get('event') == 'kill':
                for next_event in self.all_events[i+1:]:
                    # Search for the next loud segment
                    if next_event.get('type') == 'loud_segment':
                        if 0 < (next_event['timestamp'] - event['timestamp']) <= 2.0:
                            reaction_chain = [event, next_event]
                            narratives.append({
                                'type': 'reaction_kill',
                                'events': reaction_chain,
                                'score': self.score_narrative(reaction_chain)
                            })
                        break # Found the closest loud_segment, stop searching from this kill

        logging.info(f"Found {len(narratives)} potential narrative moments.")
        return narratives

    def score_narrative(self, narrative_events: List[Dict]) -> float:
        """
        Scores a narrative chain using a multiplicative system.

        Args:
            narrative_events (List[Dict]): The list of events that form the narrative.

        Returns:
            The calculated score for the narrative.
        """
        score = 0.0
        kill_count_in_chain = 0

        # Calculate base score from all events
        for event in narrative_events:
            score += self.BASE_SCORES.get(event.get('type'), 0)
            score += self.BASE_SCORES.get(event.get('event'), 0)

        # Apply multipliers for kill-specific events
        for event in narrative_events:
            if event.get('event') == 'kill':
                kill_count_in_chain += 1
                # Headshot multiplier
                if event.get('details', {}).get('type') == 'headshot':
                    score *= 2.5
                # Multi-kill multiplier (only for the second, third, etc. kill)
                if kill_count_in_chain > 1:
                    score *= 3.0

        # Apply multipliers for the entire narrative chain
        # Reaction Kill multiplier (applied once if a loud segment is in the chain)
        if any(e.get('type') == 'loud_segment' for e in narrative_events):
            score *= 4.0

        return score

    def select_best_clips(self, top_n: int = 5, overlap_threshold: float = 0.5, buffer: int = 2) -> List[Dict]:
        """
        Selects the best, non-overlapping clips based on narrative scores.

        Args:
            top_n (int): The number of top clips to return.
            overlap_threshold (float): The maximum allowed overlap ratio.
            buffer (int): Seconds to add before and after the narrative's events.

        Returns:
            The final list of selected clips with start and end times.
        """
        narratives = self.find_narratives()
        if not narratives:
            return []

        # Define clip boundaries based on the narrative events
        for narrative in narratives:
            min_ts = min(e['timestamp'] for e in narrative['events'])
            max_ts = max(e.get('end', e['timestamp']) for e in narrative['events'])
            narrative['start'] = max(0, min_ts - buffer)
            narrative['end'] = max_ts + buffer

        # Sort narratives by score
        candidates = sorted(narratives, key=lambda x: x['score'], reverse=True)

        # De-duplication logic (from V1 Curator)
        final_clips = []
        while candidates and len(final_clips) < top_n:
            best_candidate = candidates.pop(0)
            final_clips.append(best_candidate)

            remaining_candidates = []
            for candidate in candidates:
                overlap_start = max(best_candidate['start'], candidate['start'])
                overlap_end = min(best_candidate['end'], candidate['end'])
                overlap_duration = max(0, overlap_end - overlap_start)

                candidate_duration = candidate['end'] - candidate['start']
                if candidate_duration > 0 and (overlap_duration / candidate_duration) > overlap_threshold:
                    continue
                remaining_candidates.append(candidate)

            candidates = sorted(remaining_candidates, key=lambda x: x['score'], reverse=True)

        logging.info(f"Selected {len(final_clips)} final narrative clips.")
        return final_clips