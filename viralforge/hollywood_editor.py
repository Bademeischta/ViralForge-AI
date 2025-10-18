import os
import logging
from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip, vfx
from viralforge.editor import VideoEditor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HollywoodEditor(VideoEditor):
    """
    An advanced editor that creates highly dynamic and stylized game clips
    by applying context-aware visual effects based on narrative events.
    """

    def produce_valorant_clips(self, narrative_clips: list, output_dir: str):
        """
        Produces final, stylized Valorant clips with dynamic effects.
        """
        os.makedirs(output_dir, exist_ok=True)
        logging.info(f"--- Starting Hollywood Editor Production for {len(narrative_clips)} clips ---")

        try:
            with VideoFileClip(self.video_path) as video:
                for i, clip_info in enumerate(narrative_clips):
                    start = clip_info['start']
                    end = clip_info['end']
                    narrative_type = clip_info['type']
                    events = clip_info['events']

                    logging.info(f"Producing narrative clip #{i+1} ({narrative_type}): {start:.2f}s to {end:.2f}s")

                    # 1. Create the base formatted video clip using the open video object
                    base_clip = self._create_base_clip(video, start, end)

                    # 2. Apply dynamic effects
                    final_fx_clip = base_clip
                    kill_events = [e for e in events if e.get('event') == 'kill']
                    for kill_event in kill_events:
                        kill_time = kill_event['timestamp']

                        effect_start = kill_time - start - 0.5
                        effect_end = kill_time - start + 0.5

                        if effect_start < 0 or effect_end > final_fx_clip.duration:
                            continue

                        if kill_event.get('details', {}).get('type') == 'headshot':
                            logging.info(f"  - Applying Slomo effect for headshot at {kill_time:.2f}s")
                            final_fx_clip = final_fx_clip.fx(vfx.speedx, factor=0.5, start_t=effect_start, end_t=effect_end)

                    # 3. Generate subtitles
                    subtitles = self._generate_subtitles(start, end)

                    # 4. Add context overlays
                    overlay_clips = [final_fx_clip]
                    if subtitles:
                        overlay_clips.append(subtitles.set_duration(final_fx_clip.duration))

                    if narrative_type == 'multi_kill':
                        logging.info("  - Adding 'MULTI-KILL' overlay")
                        multi_kill_text = TextClip("MULTI-KILL", fontsize=100, color='red', font='Impact', stroke_color='white', stroke_width=2)
                        multi_kill_text = multi_kill_text.set_position(('center', 'top')).set_duration(3).set_start(0.5)
                        overlay_clips.append(multi_kill_text)

                    if narrative_type == 'reaction_kill':
                        logging.info("  - Adding 'REACTION!' overlay")
                        reaction_text = TextClip("REACTION!", fontsize=100, color='yellow', font='Impact', stroke_color='black', stroke_width=3)
                        reaction_text = reaction_text.set_position(('center', 'top')).set_duration(2.5).set_start(0.5)
                        overlay_clips.append(reaction_text)

                    # 5. Combine all layers and export
                    final_video = CompositeVideoClip(overlay_clips)

                    output_filename = f"valorant_clip_{i+1}_{narrative_type}_{int(start)}-{int(end)}s.mp4"
                    output_path = os.path.join(output_dir, output_filename)

                    try:
                        final_video.write_videofile(output_path, codec='libx264', audio_codec='aac', temp_audiofile='temp-audio.m4a', remove_temp=True, preset='medium', fps=24)
                        logging.info(f"Successfully exported stylized clip to {output_path}")
                    except OSError as e:
                        if "ImageMagick" in str(e):
                            logging.error(f"Failed to export clip {output_path}: ImageMagick is not installed or not found.")
                            logging.error("Please see the 'Troubleshooting' section in README.md for details.")
                        else:
                            logging.error(f"An OS-level error occurred while exporting {output_path}: {e}")
                    except Exception as e:
                        logging.error(f"An unexpected error occurred while exporting {output_path}: {e}")

        except Exception as e:
            logging.error(f"Failed to open video file {self.video_path} for Hollywood editing. Error: {e}")