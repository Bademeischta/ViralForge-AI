import unittest
import os
import shutil
from viralforge.pipeline import ContentPipeline

class TestContentPipeline(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory for testing."""
        self.test_workspace = "test_workspace"
        os.makedirs(self.test_workspace, exist_ok=True)

    def tearDown(self):
        """Clean up the temporary directory after tests."""
        if os.path.exists(self.test_workspace):
            shutil.rmtree(self.test_workspace)

    def test_full_pipeline(self):
        """
        Test the full process_url pipeline from download to transcription.
        We use a very short, well-known video to make the test quick.
        "Me at the zoo" - The first video on YouTube.
        """
        # This URL is for "Me at the zoo", which is only 18 seconds long.
        youtube_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"

        # Initialize the pipeline with our test-specific workspace
        pipeline = ContentPipeline(workspace_dir=self.test_workspace)

        # Process the URL, but keep the files for inspection if needed
        transcription = pipeline.process_url(youtube_url, cleanup=True)

        # 1. Check if the result is not None and is a dict
        self.assertIsNotNone(transcription)
        self.assertIsInstance(transcription, dict)

        # 2. Check for all expected keys
        self.assertIn('video_path', transcription)
        self.assertIn('audio_path', transcription)
        self.assertIn('transcript_result', transcription)

        # 3. Check the transcript part
        transcript_result = transcription['transcript_result']
        self.assertIn('segments', transcript_result)
        self.assertGreater(len(transcript_result['segments']), 0)
        self.assertIn("elephants", transcript_result['text'].lower())

if __name__ == '__main__':
    unittest.main()