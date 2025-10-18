import os
import argparse
import logging
import json
import shutil

# V1 Components
from viralforge.pipeline import ContentPipeline
from viralforge.recognizer import SignalRecognizer
from viralforge.curator import ClipCurator
from viralforge.editor import VideoEditor
from viralforge.hollywood_editor import HollywoodEditor

# V2 Components
from viralforge.game_pipeline import GameDataPipeline
from viralforge.observer import GameObserver
from viralforge.narrative_curator import NarrativeCurator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_v1_pipeline(youtube_url: str, output_dir: str, workspace_dir: str):
    """Runs the original V1 (audio/text-based) pipeline."""
    logging.info("--- Running V1 Standard Analysis Pipeline ---")

    pipeline = ContentPipeline(workspace_dir=workspace_dir)
    pipeline_result = pipeline.process_url(youtube_url, cleanup=False)

    if not pipeline_result or not pipeline_result.get("transcript_result"):
        logging.error("V1 Pipeline failed to process video and transcript. Exiting.")
        return

    video_path = pipeline_result["video_path"]
    audio_path = pipeline_result["audio_path"]
    transcript_result = pipeline_result["transcript_result"]

    recognizer = SignalRecognizer(transcript_result, audio_path)
    signals = recognizer.find_signals()

    curator = ClipCurator(signals, transcript_result)
    best_clips = curator.select_best_clips(top_n=5)

    if not best_clips:
        logging.warning("V1 Curator found no suitable clips.")
        return

    editor = VideoEditor(video_path, transcript_result)
    editor.produce_viral_clips(best_clips, output_dir)

def run_v2_valorant_pipeline(youtube_url: str, output_dir: str, workspace_dir: str, player_name: str):
    """Runs the V2 (gameplay computer vision-based) pipeline."""
    logging.info("--- Running V2 Valorant Analysis Pipeline ---")

    # --- V2 Phase 1: Game Data Ingestion ---
    game_pipeline = GameDataPipeline(workspace_dir=workspace_dir)
    ingestion_data = game_pipeline.process_game_video(youtube_url)
    if not ingestion_data:
        logging.error("V2 Game Data Pipeline failed. Exiting.")
        return

    video_path = ingestion_data["video_path"]
    audio_path = ingestion_data["audio_path"]
    frames_dir = ingestion_data["frames_dir"]
    transcript_result = ingestion_data["transcription_result"]
    video_resolution = ingestion_data["video_resolution"]

    # --- V2 Phase 2: Game Observation (CV) ---
    observer = GameObserver(frames_dir, video_resolution, player_name=player_name)
    game_events = observer.analyze_all_frames()

    # --- V1 Phase 2 (re-used): Audio/Text Signal Recognition ---
    recognizer = SignalRecognizer(transcript_result, audio_path)
    text_audio_events = recognizer.find_signals()

    for event in text_audio_events:
        if 'timestamp' not in event:
            event['timestamp'] = event['start']

    # --- V2 Phase 3: Narrative Curation ---
    all_events = game_events + text_audio_events

    curator = NarrativeCurator(all_events, transcript_result)
    best_narratives = curator.select_best_clips(top_n=5)

    if not best_narratives:
        logging.warning("V2 Narrative Curator found no suitable clips.")
        return

    # --- V2 Phase 4: Hollywood Editing ---
    editor = HollywoodEditor(video_path, transcript_result)
    editor.produce_valorant_clips(best_narratives, output_dir)

def pre_flight_check(mode: str):
    """
    Performs a "pre-flight check" to ensure all required system dependencies
    and user-provided assets are in place before starting the pipeline.
    """
    # 1. Check for universal system dependencies
    dependencies = {'ffmpeg': 'ffmpeg'}
    # MoviePy often uses 'convert' for legacy ImageMagick, but 'magick' for newer versions.
    if not shutil.which('convert') and not shutil.which('magick'):
        dependencies['ImageMagick'] = 'convert/magick'

    if mode == 'valorant':
        dependencies['Tesseract OCR'] = 'tesseract'

    missing_deps = [name for name, cmd in dependencies.items() if not shutil.which(cmd.split('/')[0])]

    if missing_deps:
        logging.error("="*20 + " FEHLER: KRITISCHE ABHÄNGIGKEITEN FEHLEN " + "="*20)
        logging.error("Die folgenden Programme wurden nicht in Ihrem System-PATH gefunden:")
        for dep in missing_deps:
            logging.error(f"  - {dep}")
        logging.error("\nBitte installieren Sie die fehlenden Programme.")
        logging.error("Eine detaillierte Anleitung finden Sie in der Datei: INSTALL.md")
        logging.error("="*72)
        return False

    # 2. Check for V2-specific user-provided templates
    if mode == 'valorant':
        agents_path = "assets/templates/valorant/agents/"
        icons_path = "assets/templates/valorant/icons/"

        agents_ok = os.path.exists(agents_path) and any(f.endswith('.png') for f in os.listdir(agents_path))
        icons_ok = os.path.exists(icons_path) and any(f.endswith('.png') for f in os.listdir(icons_path))

        if not agents_ok or not icons_ok:
            logging.error("\n" + "="*24 + " WICHTIGE AKTION ERFORDERLICH " + "="*25 +
                          "\nFEHLER: Die Template-Bilder für die Valorant-Analyse fehlen!" +
                          "\n\nDamit das Programm Kills erkennen kann, musst du ihm zeigen, wonach es suchen soll." +
                          "\n\nANLEITUNG:" +
                          "\n1. Mache Screenshots von den folgenden Elementen im Spiel (in 1080p-Auflösung):" +
                          "\n   - Dem Porträt jedes einzelnen Agenten im Killfeed." +
                          "\n   - Dem normalen Kill-Symbol (Fadenkreuz)." +
                          "\n   - Dem Headshot-Symbol." +
                          "\n\n2. Schneide diese Screenshots exakt zu, sodass nur noch das Symbol/Porträt ohne Hintergrund zu sehen ist." +
                          "\n\n3. Speichere die Bilder als .png-Dateien in den folgenden Ordnern:" +
                          f"\n   - Agenten-Porträts -> in den Ordner: {os.path.abspath(agents_path)}" +
                          f"\n   - Kill-Symbole      -> in den Ordner: {os.path.abspath(icons_path)}" +
                          "\n\nDas Programm wird erst funktionieren, wenn diese Bilder hinzugefügt wurden." +
                          "\n" + "="*80)
            return False

    return True

def main():
    parser = argparse.ArgumentParser(description="ViralForge AI: Automatically create short-form viral clips from YouTube videos.")
    parser.add_argument("youtube_url", type=str, help="The full URL of the YouTube video to process.")
    parser.add_argument("--mode", type=str, default="v1", choices=["v1", "valorant"], help="The analysis mode to use ('v1' for general, 'valorant' for V2 CV analysis).")
    parser.add_argument("--player-name", type=str, help="The in-game name of the player for V2 analysis.")
    parser.add_argument("--output_dir", type=str, default="output_clips", help="The directory to save the final video clips.")
    parser.add_argument("--workspace_dir", type=str, default="viralforge_workspace", help="A directory to store intermediate files.")

    args = parser.parse_args()

    if not pre_flight_check(args.mode):
        return

    if args.mode == 'valorant' and not args.player_name:
        logging.error("FEHLER: Das Argument --player-name ist für den 'valorant'-Modus erforderlich.")
        return

    os.makedirs(args.workspace_dir, exist_ok=True)

    if args.mode == "valorant":
        run_v2_valorant_pipeline(args.youtube_url, args.output_dir, args.workspace_dir, args.player_name)
    else:
        run_v1_pipeline(args.youtube_url, args.output_dir, args.workspace_dir)

    logging.info(f"--- Pipeline Finished ---")
    logging.info(f"Final clips are available in the '{args.output_dir}' directory.")

if __name__ == "__main__":
    main()