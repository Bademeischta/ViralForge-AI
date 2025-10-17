import os
import argparse
import logging
from viralforge.pipeline import ContentPipeline
from viralforge.recognizer import SignalRecognizer
from viralforge.curator import ClipCurator
from viralforge.editor import VideoEditor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main(youtube_url: str, output_dir: str = "output_clips"):
    """
    Runs the full ViralForge AI pipeline on a single YouTube URL.

    1.  Downloads the video.
    2.  Extracts and transcribes the audio.
    3.  Analyzes the content for signals.
    4.  Curates the best moments.
    5.  Edits and exports the final clips.
    """
    logging.info(f"Starting ViralForge AI pipeline for URL: {youtube_url}")

    # --- Phase 1: Content Pipeline ---
    logging.info("--- Phase 1: Running Content Pipeline ---")
    # We create a persistent workspace to inspect intermediate files if needed.
    workspace_dir = "viralforge_workspace"
    content_pipeline = ContentPipeline(workspace_dir=workspace_dir)

    video_path = content_pipeline.download_video(youtube_url)
    if not video_path:
        logging.error("Failed to download video. Exiting pipeline.")
        return

    audio_path = content_pipeline.extract_audio(video_path)
    if not audio_path:
        logging.error("Failed to extract audio. Exiting pipeline.")
        return

    transcript_result = content_pipeline.transcribe_audio(audio_path)
    if not transcript_result or not transcript_result.get('segments'):
        logging.error("Failed to transcribe audio. Exiting pipeline.")
        return

    logging.info("Content pipeline completed. Transcript and audio are ready.")

    # --- Phase 2: Signal Recognition ---
    logging.info("--- Phase 2: Recognizing Signals ---")
    recognizer = SignalRecognizer(transcript_result, audio_path)
    signals = recognizer.find_signals()
    if not signals:
        logging.warning("No signals were recognized. No clips will be produced.")
        return
    logging.info(f"Signal recognition completed. Found {len(signals)} signals.")

    # --- Phase 3: Clip Curation ---
    logging.info("--- Phase 3: Curating Best Clips ---")
    curator = ClipCurator(signals, transcript_result)
    best_clips = curator.select_best_clips(top_n=5) # Select top 5 clips
    if not best_clips:
        logging.warning("No suitable clips were curated. Exiting.")
        return
    logging.info(f"Curation completed. Selected {len(best_clips)} clips for production.")
    for i, clip in enumerate(best_clips):
        logging.info(f"  - Clip #{i+1}: {clip['start']:.2f}s to {clip['end']:.2f}s (Score: {clip['score']})")

    # --- Phase 4: Video Editing ---
    logging.info("--- Phase 4: Producing Final Videos ---")
    editor = VideoEditor(video_path, transcript_result)
    editor.produce_viral_clips(best_clips, output_dir)

    logging.info(f"--- Pipeline Finished ---")
    logging.info(f"Final clips are available in the '{output_dir}' directory.")
    # Note: Intermediate files in 'viralforge_workspace' are not deleted by default
    # in this script, allowing for inspection. You can delete the folder manually.

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ViralForge AI: Automatically create short-form viral clips from YouTube videos.")
    parser.add_argument("youtube_url", type=str, help="The full URL of the YouTube video to process.")
    parser.add_argument("--output_dir", type=str, default="output_clips", help="The directory to save the final video clips.")

    args = parser.parse_args()

    main(args.youtube_url, args.output_dir)