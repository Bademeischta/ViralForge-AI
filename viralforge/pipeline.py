import os
import tempfile
import yt_dlp
import ffmpeg
import whisper
import logging
from typing import List, Dict, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ContentPipeline:
    """
    A pipeline for downloading a YouTube video, extracting its audio,
    and transcribing the audio to text with timestamps.
    """

    def __init__(self, workspace_dir: str = None):
        """
        Initializes the ContentPipeline.

        Args:
            workspace_dir (str, optional): The directory to use for temporary files.
                                           If None, a temporary directory will be created.
        """
        if workspace_dir:
            self.workspace_dir = workspace_dir
            os.makedirs(self.workspace_dir, exist_ok=True)
            self.temp_dir_obj = None
        else:
            # Create a temporary directory that will be automatically cleaned up
            self.temp_dir_obj = tempfile.TemporaryDirectory()
            self.workspace_dir = self.temp_dir_obj.name

        logging.info(f"Using workspace directory: {self.workspace_dir}")

    def download_video(self, youtube_url: str) -> Union[str, None]:
        """
        Downloads a video from YouTube.

        Args:
            youtube_url (str): The URL of the YouTube video.

        Returns:
            str: The file path of the downloaded video, or None if an error occurred.
        """
        logging.info(f"Starting video download from: {youtube_url}")
        output_template = os.path.join(self.workspace_dir, '%(title)s.%(ext)s')

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_template,
            'quiet': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_url, download=True)
                video_path = ydl.prepare_filename(info_dict)
                logging.info(f"Video downloaded successfully to: {video_path}")
                return video_path
        except Exception as e:
            logging.error(f"Error downloading video: {e}")
            return None

    def extract_audio(self, video_path: str) -> Union[str, None]:
        """
        Extracts the audio from a video file into an MP3.

        Args:
            video_path (str): The path to the video file.

        Returns:
            str: The file path of the extracted MP3 audio file, or None if an error occurred.
        """
        if not os.path.exists(video_path):
            logging.error(f"Video file not found at: {video_path}")
            return None

        logging.info(f"Extracting audio from: {video_path}")
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        audio_path = os.path.join(self.workspace_dir, f"{base_name}.mp3")

        try:
            (
                ffmpeg
                .input(video_path)
                .output(audio_path, acodec='libmp3lame', audio_bitrate='192k', ar=44100)
                .overwrite_output()
                .run(quiet=True)
            )
            logging.info(f"Audio extracted successfully to: {audio_path}")
            return audio_path
        except ffmpeg.Error as e:
            logging.error(f"Error extracting audio with ffmpeg: {e}")
            return None

    def transcribe_audio(self, audio_path: str) -> Union[List[Dict], None]:
        """
        Transcribes an audio file using OpenAI's Whisper model.

        Args:
            audio_path (str): The path to the audio file.

        Returns:
            list: A list of segment dictionaries with 'text', 'start', and 'end' keys,
                  or None if an error occurred.
        """
        if not os.path.exists(audio_path):
            logging.error(f"Audio file not found at: {audio_path}")
            return None

        logging.info(f"Loading Whisper model (base)...")
        try:
            model = whisper.load_model("base")
            logging.info("Model loaded. Starting transcription...")
            result = model.transcribe(audio_path, verbose=False, word_timestamps=True)
            logging.info("Transcription completed.")
            # The result now contains word-level timestamps, which we will pass along.
            return result
        except Exception as e:
            logging.error(f"Error during audio transcription: {e}")
            return None

    def process_url(self, youtube_url: str, cleanup: bool = True) -> Union[Dict, None]:
        """
        Processes a YouTube URL by downloading, extracting audio, and transcribing.

        Args:
            youtube_url (str): The URL of the YouTube video.
            cleanup (bool, optional): If True, deletes the video and audio files after processing.
                                      Defaults to True.

        Returns:
            dict: A dictionary containing the transcript result and file paths.
        """
        video_path = self.download_video(youtube_url)
        if not video_path:
            return None

        audio_path = self.extract_audio(video_path)
        if not audio_path:
            if cleanup:
                self._cleanup_file(video_path)
            return None

        transcript_result = self.transcribe_audio(audio_path)

        result = {
            "video_path": video_path,
            "audio_path": audio_path,
            "transcript_result": transcript_result
        }

        if cleanup:
            logging.info("Cleaning up temporary files...")
            self._cleanup_file(video_path)
            self._cleanup_file(audio_path)
            if self.temp_dir_obj:
                self.temp_dir_obj.cleanup()
                logging.info(f"Temporary workspace directory {self.workspace_dir} removed.")

        return result

    def _cleanup_file(self, file_path: str):
        """Helper to safely delete a file."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"Removed file: {file_path}")
        except OSError as e:
            logging.error(f"Error removing file {file_path}: {e}")

if __name__ == '__main__':
    # Example usage:
    # You need to have ffmpeg installed on your system.
    # To run this, you also need to install the dependencies from requirements.txt:
    # pip install -r requirements.txt

    pipeline = ContentPipeline()
    # Replace with a real YouTube URL for testing, e.g., a short podcast clip.
    # youtube_url = "https://www.youtube.com/watch?v=your_video_id"
    # transcription = pipeline.process_url(youtube_url)

    # if transcription:
    #     print("\n--- Transcription ---")
    #     for segment in transcription:
    #         start, end, text = segment['start'], segment['end'], segment['text']
    #         print(f"[{start:.2f}s -> {end:.2f}s] {text}")
    # else:
    #     print("Failed to process the video.")
    pass