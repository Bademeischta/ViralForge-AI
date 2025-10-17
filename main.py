import pprint
from viralforge.content_pipeline import ContentPipeline

def main():
    """
    Example usage of the ContentPipeline class.
    """
    # A short, well-known video for testing purposes.
    # Rick Astley - Never Gonna Give You Up (Official Music Video)
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    # Initialize the pipeline
    pipeline = ContentPipeline(workspace_dir="temp_workspace")

    # Process the URL to get the transcription
    print(f"Processing URL: {youtube_url}")
    transcription = pipeline.process_url(youtube_url, cleanup=True)

    if transcription:
        print("\n--- Transcription Result ---")
        pprint.pprint(transcription)
        print("\n--- End of Transcription ---")
    else:
        print("Failed to process the video.")

if __name__ == "__main__":
    main()