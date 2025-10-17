import os
import shutil
import subprocess
import whisper
import yt_dlp
from typing import List, Dict, Any

class ContentPipeline:
    """
    A pipeline for downloading YouTube videos, extracting audio, and transcribing it.
    """

    def __init__(self, workspace_dir: str = "temp_workspace"):
        """
        Initializes the ContentPipeline and creates a workspace directory.

        :param workspace_dir: The directory to store temporary files.
        """
        self.workspace_dir = workspace_dir
        if not os.path.exists(self.workspace_dir):
            os.makedirs(self.workspace_dir)
        print(f"Workspace created at: {self.workspace_dir}")

    def download_video(self, youtube_url: str) -> str | None:
        """
        Downloads a video from YouTube using yt-dlp.

        :param youtube_url: The URL of the YouTube video.
        :return: The file path to the downloaded video, or None if an error occurs.
        """
        print(f"Starting video download from: {youtube_url}")
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(self.workspace_dir, '%(title)s.%(ext)s'),
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_url, download=True)
                video_path = ydl.prepare_filename(info_dict)
                print(f"Video downloaded successfully to: {video_path}")
                return video_path
        except Exception as e:
            print(f"Error downloading video: {e}")
            return None

    def extract_audio(self, video_path: str) -> str | None:
        """
        Extracts the audio from a video file using ffmpeg.

        :param video_path: The path to the video file.
        :return: The file path to the extracted .mp3 audio file, or None if an error occurs.
        """
        if not os.path.exists(video_path):
            print(f"Error: Video file not found at {video_path}")
            return None

        audio_path = os.path.splitext(video_path)[0] + '.mp3'
        command = [
            'ffmpeg',
            '-i', video_path,
            '-q:a', '0',  # for best quality
            '-map', 'a',
            '-y',  # overwrite output file if it exists
            audio_path
        ]
        print(f"Extracting audio to: {audio_path}")
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Audio extracted successfully.")
            return audio_path
        except subprocess.CalledProcessError as e:
            print(f"Error extracting audio with ffmpeg: {e}")
            print(f"FFmpeg stderr: {e.stderr.decode()}")
            return None

    def transcribe_audio(self, audio_path: str) -> List[Dict[str, Any]] | None:
        """
        Transcribes an audio file using OpenAI's Whisper model.

        :param audio_path: The path to the audio file.
        :return: A list of segments with text, start, and end times, or None if an error occurs.
        """
        if not os.path.exists(audio_path):
            print(f"Error: Audio file not found at {audio_path}")
            return None

        print("Loading Whisper model...")
        model = whisper.load_model("base")
        print("Starting transcription...")
        try:
            result = model.transcribe(audio_path)
            print("Transcription completed.")
            return result['segments']
        except Exception as e:
            print(f"Error during transcription: {e}")
            return None

    def process_url(self, youtube_url: str, cleanup: bool = True) -> List[Dict[str, Any]] | None:
        """
        Processes a YouTube URL by downloading, extracting audio, and transcribing.

        :param youtube_url: The URL of the YouTube video.
        :param cleanup: If True, deletes temporary video and audio files after processing.
        :return: The transcribed segments or None if any step fails.
        """
        video_path = self.download_video(youtube_url)
        if not video_path:
            return None

        audio_path = self.extract_audio(video_path)
        if not audio_path:
            if cleanup:
                os.remove(video_path)
            return None

        transcription = self.transcribe_audio(audio_path)

        if cleanup:
            print("Cleaning up temporary files...")
            try:
                os.remove(video_path)
                os.remove(audio_path)
                print("Temporary files deleted.")
            except OSError as e:
                print(f"Error during cleanup: {e}")

        return transcription

    def __del__(self):
        """
        Destructor to clean up the workspace directory if it's empty.
        """
        if os.path.exists(self.workspace_dir) and not os.listdir(self.workspace_dir):
            shutil.rmtree(self.workspace_dir)
            print(f"Workspace directory {self.workspace_dir} removed.")