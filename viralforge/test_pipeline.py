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

        # 1. Check if the transcription is not None and is a list
        self.assertIsNotNone(transcription)
        self.assertIsInstance(transcription, list)

        # 2. Check if the transcription list is not empty
        self.assertGreater(len(transcription), 0)

        # 3. Check the structure of the first segment
        first_segment = transcription[0]
        self.assertIn('start', first_segment)
        self.assertIn('end', first_segment)
        self.assertIn('text', first_segment)

        # 4. Check the content of the transcription (optional but good)
        full_text = " ".join(seg['text'] for seg in transcription).lower()
        self.assertIn("elephants", full_text)
        self.assertIn("cool", full_text)

if __name__ == '__main__':
    unittest.main()