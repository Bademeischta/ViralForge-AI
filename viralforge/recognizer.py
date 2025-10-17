import numpy as np
import librosa
import logging
import re
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SignalRecognizer:
    """
    Analyzes transcript and audio data to find signals indicating "interesting" moments.
    """

    def __init__(self, transcript: List[Dict], audio_path: str):
        """
        Initializes the SignalRecognizer.

        Args:
            transcript (List[Dict]): The timestamped transcript from ContentPipeline.
            audio_path (str): The file path to the audio file (.mp3).
        """
        self.transcript = transcript
        self.audio_path = audio_path

        # Simple, extendable list of keywords indicating strong emotion or opinion.
        self.keywords = [
            "problem", "amazing", "incredible", "crazy", "wow", "best", "worst",
            "omg", "unbelievable", "terrible", "horrible", "love", "hate",
            "genius", "insane", "really?"
        ]
        # Simple list of question words to check at the beginning of a sentence.
        self.question_words = ["what", "who", "how", "why", "where", "when", "is", "are", "do", "does"]

    def analyze_transcript(self) -> List[Dict]:
        """
        Analyzes the text transcript to find text-based signals.

        Identifies:
        - Questions based on question marks or starting words.
        - Keywords from a predefined list.
        - Exclamations based on '!' marks.

        Returns:
            List[Dict]: A list of signal events with timestamps.
        """
        logging.info("Analyzing transcript for text-based signals...")
        signals = []
        for segment in self.transcript:
            text_original = segment['text'].strip()
            text_lower = text_original.lower()
            start_time = segment['start']
            end_time = segment['end']

            # 1. Check for questions
            first_word = text_lower.split(' ', 1)[0].strip("?,.")
            if text_lower.endswith('?') or first_word in self.question_words:
                signals.append({
                    'type': 'question',
                    'text': text_original,
                    'start': start_time,
                    'end': end_time
                })

            # 2. Check for keywords (punctuation-insensitive)
            # Remove punctuation and check words
            clean_text = re.sub(r'[^\w\s]', '', text_lower)
            for keyword in self.keywords:
                # Use word boundaries to avoid matching substrings
                if re.search(r'\b' + re.escape(keyword.strip("?")) + r'\b', clean_text):
                    signals.append({
                        'type': 'keyword',
                        'word': keyword,
                        'text': text_original,
                        'start': start_time,
                        'end': end_time
                    })

            # 3. Check for exclamations
            if '!' in text_lower:
                signals.append({
                    'type': 'exclamation',
                    'text': text_original,
                    'start': start_time,
                    'end': end_time
                })

        logging.info(f"Found {len(signals)} text-based signals.")
        return signals

    def analyze_audio(self, loudness_threshold_factor: float = 1.8, silence_threshold_sec: float = 1.0) -> List[Dict]:
        """
        Analyzes the audio file to find audio-based signals.

        Identifies:
        - Segments of high volume (potential laughter, excitement).
        - Significant periods of silence.

        Args:
            loudness_threshold_factor (float): Factor by which RMS must exceed the mean to be "loud".
            silence_threshold_sec (float): Minimum duration of silence to be considered a signal.

        Returns:
            List[Dict]: A list of audio signal events with timestamps.
        """
        logging.info(f"Analyzing audio file: {self.audio_path}")
        signals = []
        try:
            y, sr = librosa.load(self.audio_path, sr=None)
            frame_length = 2048
            hop_length = 512

            # 1. Loudness Analysis
            rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
            rms_mean = np.mean(rms)
            loudness_threshold = rms_mean * loudness_threshold_factor

            is_loud_frames = np.where(rms > loudness_threshold)[0]

            if len(is_loud_frames) > 0:
                # Find contiguous blocks of loud frames
                loud_groups = np.split(is_loud_frames, np.where(np.diff(is_loud_frames) != 1)[0] + 1)
                for group in loud_groups:
                    if len(group) == 0: continue

                    start_frame = group[0]
                    end_frame = group[-1]

                    start_time = librosa.frames_to_time(start_frame, sr=sr, hop_length=hop_length)
                    end_time = librosa.frames_to_time(end_frame, sr=sr, hop_length=hop_length)

                    if end_time - start_time > 0.5: # Filter out very short spikes
                        signals.append({
                            'type': 'loud_segment',
                            'start': start_time,
                            'end': end_time,
                            'reason': f'RMS exceeded threshold of {loudness_threshold:.2f}'
                        })

            # 2. Silence Analysis
            non_silent_intervals = librosa.effects.split(y, top_db=40) # top_db is decibels below max
            last_end_time = 0.0

            for start_frame, end_frame in non_silent_intervals:
                start_time = librosa.frames_to_time(start_frame, sr=sr)
                silence_duration = start_time - last_end_time
                if silence_duration >= silence_threshold_sec:
                    signals.append({
                        'type': 'silence',
                        'start': last_end_time,
                        'end': start_time,
                        'duration': silence_duration
                    })
                last_end_time = librosa.frames_to_time(end_frame, sr=sr)

            # Check for silence at the very end
            total_duration = librosa.get_duration(y=y, sr=sr)
            final_silence = total_duration - last_end_time
            if final_silence >= silence_threshold_sec:
                signals.append({
                    'type': 'silence',
                    'start': last_end_time,
                    'end': total_duration,
                    'duration': final_silence
                })

        except Exception as e:
            logging.error(f"Could not process audio file {self.audio_path}: {e}")
            return []

        logging.info(f"Found {len(signals)} audio-based signals.")
        return signals

    def find_signals(self) -> List[Dict[str, Any]]:
        """
        Runs all analysis methods and combines the results into a single, sorted list.

        Returns:
            List[Dict[str, Any]]: A chronologically sorted list of all detected signals.
        """
        logging.info("Starting signal recognition process...")
        text_signals = self.analyze_transcript()
        audio_signals = self.analyze_audio()

        all_signals = text_signals + audio_signals

        # Sort all signals by their start time
        sorted_signals = sorted(all_signals, key=lambda x: x['start'])

        logging.info(f"Total signals found: {len(sorted_signals)}")
        return sorted_signals