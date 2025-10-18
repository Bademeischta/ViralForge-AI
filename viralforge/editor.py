import os
import logging
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, vfx
from moviepy.video.fx.all import crop

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class VideoEditor:
    """
    Creates final video clips with formatting and animated subtitles.
    """

    def __init__(self, video_path: str, transcript_result: dict):
        """
        Initializes the VideoEditor.

        Args:
            video_path (str): The file path to the original video file.
            transcript_result (dict): The full result object from Whisper, including word-level timestamps.
        """
        self.video_path = video_path
        self.transcript_result = transcript_result

    def create_clip(self, start_time: float, end_time: float, output_width: int = 720) -> CompositeVideoClip:
        """
        Cuts a clip from the original video and formats it to a 9:16 aspect ratio.

        Args:
            start_time (float): The start time of the clip in seconds.
            end_time (float): The end time of the clip in seconds.
            output_width (int): The width of the output video.

        Returns:
            CompositeVideoClip: The formatted 9:16 video clip.
        """
        output_height = int(output_width * 16 / 9)

        with VideoFileClip(self.video_path) as video:
            # Create the main clip, cropped from the original
            main_clip = video.subclip(start_time, end_time)

            # Create a blurred, scaled background
            background_clip = main_clip.copy()
            background_clip = background_clip.set_position(('center', 'center'))
            background_clip = background_clip.resize(height=output_height)
            background_clip = crop(background_clip, width=output_width, height=output_height, x_center=background_clip.w/2, y_center=background_clip.h/2)
            # In moviepy 1.0.3, the gaussian blur is not directly available.
            # A common workaround is to use a different scaling or visual effect.
            # For simplicity, we will skip the blur effect to maintain compatibility.
            # background_clip = background_clip.fx(vfx.blur, 20) # This line is removed.

            # Center the main clip on top of the background
            main_clip = main_clip.resize(width=output_width)
            main_clip = main_clip.set_position(('center', 'center'))

            # Combine background and main clip
            final_clip = CompositeVideoClip([background_clip, main_clip], size=(output_width, output_height))
            return final_clip

    def generate_subtitles(self, start_time: float, end_time: float) -> CompositeVideoClip:
        """
        Generates animated, word-by-word subtitles for the given time range.

        Args:
            start_time (float): The start time of the clip.
            end_time (float): The end time of the clip.

        Returns:
            CompositeVideoClip: A clip containing only the animated subtitles.
        """
        subtitle_clips = []
        all_words = []

        # Collect all words within the clip's time range
        for segment in self.transcript_result['segments']:
            for word_info in segment.get('words', []):
                if start_time <= word_info['start'] < end_time:
                    all_words.append(word_info)

        if not all_words:
            return None

        # Create a TextClip for each word
        for i, word_info in enumerate(all_words):
            word_text = word_info['word'].upper()
            word_start = word_info['start'] - start_time # Adjust to clip's timeline
            word_end = word_info['end'] - start_time

            # Create the main text (highlighted)
            text_clip = TextClip(
                word_text,
                fontsize=70,
                color='yellow',
                font='Impact',
                stroke_color='black',
                stroke_width=3
            )
            text_clip = text_clip.set_start(word_start).set_duration(word_end - word_start)

            # Position this word clip based on its position in the sentence
            # This is a simple implementation: we center each word.
            # A more advanced version could calculate sentence position.
            text_clip = text_clip.set_position('center')

            subtitle_clips.append(text_clip)

        return CompositeVideoClip(subtitle_clips)


    def produce_viral_clips(self, clips_data: list, output_dir: str):
        """
        Produces final video files for a list of selected clips.

        Args:
            clips_data (list): A list of clip dictionaries from ClipCurator.
            output_dir (str): The directory to save the final .mp4 files.
        """
        os.makedirs(output_dir, exist_ok=True)
        logging.info(f"Starting production of {len(clips_data)} clips...")

        for i, clip_info in enumerate(clips_data):
            start = clip_info['start']
            end = clip_info['end']

            logging.info(f"Producing clip #{i+1}: {start:.2f}s to {end:.2f}s")

            # 1. Create the formatted video clip
            formatted_video = self.create_clip(start, end)
            if not formatted_video:
                logging.warning(f"Skipping clip #{i+1} due to video creation error.")
                continue

            # 2. Generate animated subtitles
            subtitles = self.generate_subtitles(start, end)

            # 3. Combine video and subtitles
            if subtitles:
                final_video = CompositeVideoClip([formatted_video, subtitles.set_duration(formatted_video.duration)])
            else:
                final_video = formatted_video

            # 4. Export the final video
            output_filename = f"clip_{int(start)}-{int(end)}s.mp4"
            output_path = os.path.join(output_dir, output_filename)

            try:
                # Use a preset for faster encoding, suitable for social media
                final_video.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile='temp-audio.m4a',
                    remove_temp=True,
                    preset='medium', # 'ultrafast' is faster, 'medium' is good quality/size balance
                    fps=24
                )
                logging.info(f"Successfully exported clip to {output_path}")
            except OSError as e:
                if "No such file or directory" in str(e) and "ImageMagick" in str(e):
                     logging.error(f"Failed to export clip {output_path}: ImageMagick is not installed or not found.")
                     logging.error("Please install ImageMagick and ensure it's in your system's PATH.")
                     logging.error("See the 'Troubleshooting' section in README.md for details.")
                else:
                    logging.error(f"An OS-level error occurred while exporting {output_path}: {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred while exporting {output_path}: {e}")
            finally:
                # Close clips to free up resources
                formatted_video.close()
                if subtitles:
                    subtitles.close()
                final_video.close()