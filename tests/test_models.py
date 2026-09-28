"""Optional real-model test: see docs/validation.md for the environment variables."""

import os
from pathlib import Path
import tempfile
import threading
import unittest

from snote_video.video import VideoEngines


@unittest.skipUnless(os.environ.get("SNOTE_VIDEO_TEST_VIDEO"), "Real-video test needs SNOTE_VIDEO_TEST_VIDEO and installed models")
class RealModelTests(unittest.TestCase):
    def test_recording_produces_expected_words_and_a_translation(self):
        root = Path(os.environ.get("SNOTE_VIDEO_DATA_DIR", "~/.snote_video")).expanduser()
        engines = VideoEngines(root)
        stop = threading.Event()
        lines, language = [], []
        with tempfile.TemporaryDirectory() as directory:
            playback = Path(directory) / "playback.wav"
            duration, peaks = engines.prepare(Path(os.environ["SNOTE_VIDEO_TEST_VIDEO"]), playback, stop)
            self.assertGreater(duration, 0)
            self.assertEqual(len(peaks), 96)
            engines.transcribe(playback, os.environ.get("SNOTE_VIDEO_TEST_MODEL", "tiny"),
                               os.environ.get("SNOTE_VIDEO_TEST_SOURCE", "en"), stop,
                               language.append, lambda start, end, text: lines.append(text))
        self.assertTrue(lines, "No speech was detected in the supplied recording")
        text = " ".join(lines)
        expected = os.environ.get("SNOTE_VIDEO_EXPECT_TEXT", "")
        if expected:
            self.assertIn(expected.casefold(), text.casefold())
        translator = engines.translator(language[0], os.environ.get("SNOTE_VIDEO_TEST_TARGET", "es"))
        translated = translator(text)
        self.assertTrue(translated.strip())
        print(f"\nRecognized: {text}\nTranslated: {translated}\n")


if __name__ == "__main__":
    unittest.main()
