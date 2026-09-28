"""Real media checks use generated pictures and tones, not speech-model output."""
from array import array
from copy import deepcopy
import http.client
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
import wave

from snote_video.domain import Problem, apply_edits, sample_project
from snote_video.engines import Cancelled
from snote_video.server import make_server
from snote_video.video import VideoEngines, probe, run_process, video_duration


class TimingTests(unittest.TestCase):
    def test_timing_correction_clears_review_without_discarding_translation(self):
        project = sample_project()
        rows = deepcopy(project["segments"])
        rows[0]["end"] -= 0.1
        translation = rows[0]["translation"]
        apply_edits(project, {"segments": rows})
        self.assertFalse(project["segments"][0]["reviewed"])
        self.assertEqual(project["segments"][0]["translation"], translation)

    def test_metadata_rejects_missing_tracks_and_invalid_duration(self):
        valid = {"streams": [{"codec_type": "video", "duration": "3"}, {"codec_type": "audio"}]}
        self.assertEqual(video_duration(valid), 3)
        for invalid in ({}, {"streams": [{"codec_type": "video"}]},
                        {"streams": [{"codec_type": "audio"}]},
                        {"streams": [{"codec_type": "video", "duration": "nan"}, {"codec_type": "audio"}]}):
            with self.subTest(info=invalid), self.assertRaises(ValueError):
                video_duration(invalid)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "Media checks need FFmpeg and FFprobe")
class VideoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = tempfile.TemporaryDirectory()
        cls.clip = Path(cls.fixtures.name) / "delayed.mkv"
        # A three-second picture with one second of tone starting at t=1.
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
            "testsrc2=size=320x180:rate=10:duration=3", "-f", "lavfi", "-i",
            "sine=frequency=440:sample_rate=16000:duration=1", "-filter_complex",
            "[1:a]asetpts=PTS+1/TB[late]", "-map", "0:v:0", "-map", "[late]",
            "-c:v", "libx264", "-threads", "1", "-c:a", "pcm_s16le", str(cls.clip)],
            check=True, capture_output=True)
        cls.silent = Path(cls.fixtures.name) / "no-audio.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(cls.clip),
                        "-an", "-c:v", "copy", str(cls.silent)], check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        cls.fixtures.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.engine = VideoEngines(self.root)
        self.stop = threading.Event()

    def tearDown(self):
        self.temp.cleanup()

    def test_real_preview_and_recognition_audio_keep_leading_and_trailing_silence(self):
        messages = []
        wav = self.root / "playback.wav"
        duration, peaks = self.engine.prepare(self.clip, wav, self.stop,
            lambda message, progress: messages.append((message, progress)))
        preview = self.root / "preview.mp4"
        info = probe(preview, self.stop)
        self.assertTrue(any(stream["codec_name"] == "h264" for stream in info["streams"]))
        self.assertTrue(any(stream["codec_name"] == "aac" for stream in info["streams"]))
        self.assertAlmostEqual(duration, 3, delta=0.15)
        self.assertAlmostEqual(video_duration(info), duration, delta=0.15)
        self.assertEqual(len(peaks), 96)
        with wave.open(str(wav)) as audio:
            self.assertEqual((audio.getnchannels(), audio.getframerate()), (1, 16000))
            samples = array("h", audio.readframes(audio.getnframes()))
        first = next(index for index, value in enumerate(samples) if abs(value) > 100)
        self.assertAlmostEqual(first / 16000, 1, delta=0.08)
        self.assertLess(max(map(abs, samples[int(2.3 * 16000):])), 100)
        self.assertTrue(messages)
        self.assertFalse(list(self.root.glob(".prepare-*")))

    def test_video_without_audio_is_rejected_without_publishing_preview(self):
        with self.assertRaisesRegex(ValueError, "no audio"):
            self.engine.prepare(self.silent, self.root / "playback.wav", self.stop)
        self.assertFalse((self.root / "preview.mp4").exists())

    def test_configured_duration_limit_is_enforced_before_conversion(self):
        engine = VideoEngines(self.root, max_duration=2)
        with self.assertRaisesRegex(ValueError, "--max-minutes"):
            engine.prepare(self.clip, self.root / "playback.wav", self.stop)
        self.assertFalse((self.root / "preview.mp4").exists())

    def test_cancel_stops_a_running_media_process(self):
        timer = threading.Timer(0.25, self.stop.set)
        timer.start()
        started = time.monotonic()
        try:
            with self.assertRaises(Cancelled):
                run_process(["ffmpeg", "-v", "error", "-re", "-i", str(self.clip),
                             "-f", "null", "-"], self.stop)
        finally:
            timer.cancel()
        self.assertLess(time.monotonic() - started, 2)

    def test_pre_cancelled_job_does_not_publish_files(self):
        self.stop.set()
        with self.assertRaises(Cancelled):
            self.engine.prepare(self.clip, self.root / "playback.wav", self.stop)
        self.assertFalse(list(self.root.glob(".prepare-*")))
        self.assertFalse((self.root / "preview.mp4").exists())

    def test_http_video_upload_preview_seek_timing_edit_and_subtitle_export(self):
        class TestModels(VideoEngines):
            def capabilities(self):
                return {"media_installed": True, "speech_installed": True, "translation_installed": True}
            def transcribe(self, path, name, language, stop, on_language, on_segment):
                on_language("en")
                on_segment(1, 1.8, "Fixture dialogue.")
            def translator(self, source, target):
                return lambda text: "Texto de prueba."

        server = make_server(self.root, 0, TestModels(self.root))
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
        thread.start()
        def request(method, path, data=None, payload=None, headers=None):
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            request_headers = {"X-SNote-Video-Request": "1", **(headers or {})}
            if payload is not None:
                request_headers["Content-Type"] = "application/json"
                data = json.dumps(payload).encode()
            try:
                connection.request(method, path, body=data, headers=request_headers)
                response = connection.getresponse()
                body = response.read()
                if response.getheader("Content-Type", "").startswith("application/json"):
                    body = json.loads(body)
                return response.status, body, dict(response.getheaders())
            finally:
                connection.close()
        try:
            code, project, _ = request("POST", "/api/projects?filename=delayed.mkv&target=es",
                                      data=self.clip.read_bytes())
            self.assertEqual(code, 202, project)
            path = "/api/projects/" + project["id"]
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                project = request("GET", path)[1]
                if project["status"] == "ready":
                    break
                self.assertNotIn(project["status"], {"error", "cancelled"}, project)
                time.sleep(0.05)
            self.assertEqual(project["status"], "ready", project)
            self.assertTrue(project["has_video"])
            code, data, headers = request("GET", path + "/video", headers={"Range": "bytes=0-31"})
            self.assertEqual(code, 206)
            self.assertEqual(headers["Content-Type"], "video/mp4")
            self.assertEqual(len(data), 32)
            self.assertIn(b"ftyp", data)
            project["segments"][0].update(start=1.1, end=1.9, reviewed=True)
            code, saved, _ = request("PATCH", path, payload={
                "revision": project["revision"], "segments": project["segments"]})
            self.assertEqual(code, 200, saved)
            self.assertFalse(saved["segments"][0]["reviewed"])
            code, subtitles, _ = request("GET", path + "/export?format=srt&content=both")
            self.assertEqual(code, 200)
            self.assertIn(b"00:00:01,100 --> 00:00:01,900", subtitles)
            self.assertIn(b"Texto de prueba.", subtitles)
            server.app.max_upload = 4
            self.assertEqual(request("POST", "/api/projects?filename=too-large.mp4", data=b"12345")[0], 413)
        finally:
            server.shutdown()
            server.server_close()
            server.app.close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
