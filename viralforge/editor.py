import os
import logging
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.video.fx.all import crop

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
            transcript_result (dict): The full result object from Whisper.
        """
        self.video_path = video_path
        self.transcript_result = transcript_result

    def _create_base_clip(self, open_video_clip: VideoFileClip, start_time: float, end_time: float, output_width: int = 720) -> CompositeVideoClip:
        """
        Cuts a clip from an open video object and formats it to 9:16.
        This is a helper method to be called within a 'with' context.
        """
        output_height = int(output_width * 16 / 9)

        main_clip = open_video_clip.subclip(start_time, end_time)

        background_clip = main_clip.copy()
        background_clip = background_clip.set_position(('center', 'center'))
        background_clip = background_clip.resize(height=output_height)
        background_clip = crop(background_clip, width=output_width, height=output_height, x_center=background_clip.w/2, y_center=background_clip.h/2)

        main_clip = main_clip.resize(width=output_width)
        main_clip = main_clip.set_position(('center', 'center'))

        return CompositeVideoClip([background_clip, main_clip], size=(output_width, output_height))

    def _generate_subtitles(self, start_time: float, end_time: float) -> CompositeVideoClip:
        """
        Generates animated, word-by-word subtitles for the given time range.
        """
        subtitle_clips = []
        all_words = []

        for segment in self.transcript_result.get('segments', []):
            for word_info in segment.get('words', []):
                if start_time <= word_info.get('start', 0) < end_time:
                    all_words.append(word_info)

        if not all_words:
            return None

        for word_info in all_words:
            word_text = word_info.get('word', '').upper()
            word_start = word_info.get('start', 0) - start_time
            word_end = word_info.get('end', 0) - start_time

            text_clip = TextClip(
                word_text,
                fontsize=70,
                color='yellow',
                font='Impact',
                stroke_color='black',
                stroke_width=3
            )
            text_clip = text_clip.set_start(word_start).set_duration(word_end - word_start)
            text_clip = text_clip.set_position('center')

            subtitle_clips.append(text_clip)

        return CompositeVideoClip(subtitle_clips)

    def produce_viral_clips(self, clips_data: list, output_dir: str):
        """
        Produces final video files for a list of selected clips.
        """
        os.makedirs(output_dir, exist_ok=True)
        logging.info(f"--- Starting V1 Clip Production for {len(clips_data)} clips ---")

        try:
            with VideoFileClip(self.video_path) as video:
                for i, clip_info in enumerate(clips_data):
                    start = clip_info['start']
                    end = clip_info['end']

                    logging.info(f"Producing clip #{i+1}: {start:.2f}s to {end:.2f}s")

                    base_video = self._create_base_clip(video, start, end)
                    subtitles = self._generate_subtitles(start, end)

                    final_layers = [base_video]
                    if subtitles:
                        final_layers.append(subtitles.set_duration(base_video.duration))

                    final_video = CompositeVideoClip(final_layers)

                    output_filename = f"clip_{int(start)}-{int(end)}s.mp4"
                    output_path = os.path.join(output_dir, output_filename)

                    try:
                        final_video.write_videofile(
                            output_path,
                            codec='libx264',
                            audio_codec='aac',
                            temp_audiofile='temp-audio.m4a',
                            remove_temp=True,
                            preset='medium',
                            fps=24
                        )
                        logging.info(f"Successfully exported clip to {output_path}")
                    except OSError as e:
                        if "ImageMagick" in str(e):
                             logging.error(f"Failed to export clip {output_path}: ImageMagick is not installed or not found.")
                             logging.error("Please see the 'Troubleshooting' section in README.md for details.")
                        else:
                            logging.error(f"An OS-level error occurred while exporting {output_path}: {e}")
                    except Exception as e:
                        logging.error(f"An unexpected error occurred while exporting {output_path}: {e}")
        except Exception as e:
            logging.error(f"Failed to open video file {self.video_path}. Error: {e}")