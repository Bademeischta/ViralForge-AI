import os
import logging
import yt_dlp
import ffmpeg
import whisper
import cv2
from typing import Dict, Union

# Re-using the ContentPipeline for base functionality by importing it.
# Inheritance could be an option, but composition is often more flexible.
from viralforge.pipeline import ContentPipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GameDataPipeline(ContentPipeline):
    """
    An extended pipeline for ingesting and preparing game footage for analysis.
    It ensures consistent video quality and extracts frames for computer vision.
    """

    def download_video(self, youtube_url: str) -> Union[str, None]:
        """
        Downloads a video from YouTube, specifically requesting 1080p @ 60fps.

        Args:
            youtube_url (str): The URL of the YouTube video.

        Returns:
            str: The file path of the downloaded video, or None if an error occurred.
        """
        logging.info(f"Starting game video download from: {youtube_url}")
        output_template = os.path.join(self.workspace_dir, '%(title)s.%(ext)s')

        # Valorant analysis requires consistent 1080p, 60fps footage.
        ydl_opts = {
            'format': 'bestvideo[height=1080][fps=60]+bestaudio/best[height=1080]/best',
            'outtmpl': output_template,
            'quiet': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_url, download=True)
                video_path = ydl.prepare_filename(info_dict)

                # Check if the downloaded quality is what we wanted.
                if info_dict.get('height') != 1080 or info_dict.get('fps') != 60:
                    logging.warning(
                        f"Downloaded video may not be 1080p @ 60fps. "
                        f"Actual resolution: {info_dict.get('width')}x{info_dict.get('height')}, "
                        f"FPS: {info_dict.get('fps')}. Analysis may be inaccurate."
                    )

                logging.info(f"Game video downloaded successfully to: {video_path}")
                return video_path
        except Exception as e:
            logging.error(f"Error downloading game video: {e}")
            return None

    def extract_game_frames(self, video_path: str, frame_rate: int = 10) -> Union[str, None]:
        """
        Extracts frames from the video at a constant rate for analysis.

        Args:
            video_path (str): The path to the video file.
            frame_rate (int): The target number of frames to extract per second.

        Returns:
            str: The path to the directory containing the extracted frames, or None.
        """
        logging.info(f"Extracting frames from {video_path} at {frame_rate}fps.")
        frames_dir = os.path.join(self.workspace_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)

        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logging.error("Could not open video file for frame extraction.")
                return None

            video_fps = cap.get(cv2.CAP_PROP_FPS)
            frame_interval = int(video_fps / frame_rate)

            frame_count = 0
            saved_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % frame_interval == 0:
                    timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))
                    frame_filename = f"frame_{timestamp_ms:08d}.jpg"
                    frame_path = os.path.join(frames_dir, frame_filename)
                    cv2.imwrite(frame_path, frame)
                    saved_count += 1

                frame_count += 1

            cap.release()
            logging.info(f"Successfully extracted {saved_count} frames to {frames_dir}.")
            return frames_dir

        except Exception as e:
            logging.error(f"Error extracting frames: {e}")
            return None

    def process_game_video(self, youtube_url: str) -> Union[Dict, None]:
        """
        Orchestrates the entire data ingestion pipeline for a game video.

        Args:
            youtube_url (str): The URL of the YouTube game video.

        Returns:
            Dict: A dictionary containing all relevant paths and data, or None on failure.
        """
        logging.info(f"--- Starting V2 Game Data Pipeline for URL: {youtube_url} ---")

        video_path = self.download_video(youtube_url)
        if not video_path:
            return None

        audio_path = self.extract_audio(video_path)
        if not audio_path:
            return None # Cleanup of video file is handled by the caller or GC

        transcription_result = self.transcribe_audio(audio_path)
        if not transcription_result:
            return None

        frames_dir = self.extract_game_frames(video_path)
        if not frames_dir:
            return None

        logging.info("--- V2 Game Data Pipeline Finished Successfully ---")
        return {
            "video_path": video_path,
            "audio_path": audio_path,
            "frames_dir": frames_dir,
            "transcription_result": transcription_result
        }