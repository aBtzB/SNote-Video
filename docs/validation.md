# Validation

## Automated checks

~~~sh
python -m unittest discover -s tests -v
node --check snote_video/static/app.js
~~~

The current suite has **53 tests: 52 passed and one optional real-model test skipped** in the development environment. Six media tests use the actual installed FFmpeg/FFprobe. They generate small videos with pictures and tones, including a three-second video whose audio starts one second late.

The real media checks cover preview encoding, leading/trailing silence, duration alignment, cancellation, missing audio, configurable limits, and the HTTP upload → preview → timed subtitle export path. Speech and translation in that HTTP test are deterministic substitutes, not model inference.

Other tests cover model-download byte counts, checksums, cache/retry behavior, archive validation, HTTP origin checks, queue behavior, revisions, edit validation, and exports. Download tests use local byte streams and do not contact the actual model hosts.

JavaScript syntax and HTML element references were checked. No browser executable or model dependencies were available here, so rendered layout, native video subtitle playback, real model downloads, speech/translation quality, and Windows/macOS installation still need checking on the target computer. This beta makes no accuracy or speed claim.

## Real-model smoke test

Install the dependencies, FFmpeg/FFprobe, Tiny, and English → Spanish. Record a short English video with the words “This is a test recording.”

macOS/Linux, using the virtual environment's Python:

~~~sh
export SNOTE_VIDEO_TEST_VIDEO="/absolute/path/to/clip.mp4"
export SNOTE_VIDEO_EXPECT_TEXT="test recording"
.venv/bin/python -m unittest discover -s tests -p test_models.py -v
~~~

Windows PowerShell:

~~~powershell
$env:SNOTE_VIDEO_TEST_VIDEO = "C:\path\to\clip.mp4"
$env:SNOTE_VIDEO_EXPECT_TEXT = "test recording"
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_models.py -v
~~~

Optional variables: SNOTE_VIDEO_DATA_DIR (default ~/.snote_video), SNOTE_VIDEO_TEST_MODEL (tiny), SNOTE_VIDEO_TEST_SOURCE (en), SNOTE_VIDEO_TEST_TARGET (es).

The smoke test prepares the video, runs real recognition, checks the expected phrase if supplied, and requests a non-empty translation. Review the printed text yourself; non-empty output does not establish translation accuracy.

## Browser and release checks

1. Start with a fresh data directory. Verify that opening Models makes no external request until a download or catalogue load is requested.
2. Download Tiny and a translation pair; test cancelling another download and retrying it.
3. Upload a short video and check preview playback and seeking from cue buttons.
4. Toggle original, translated, bilingual, and off modes, including fullscreen.
5. Edit text and cue timing; save and reopen the project.
6. Apply positive and negative offsets. Confirm offsets outside the video are rejected.
7. Change source text and confirm that its unchanged translation is cleared on save.
8. Test two tabs saving different revisions.
9. Export SRT/VTT and compare their timing with the original video in a player or editor.
10. Try a narrow window, keyboard navigation, long subtitles, and RTL text if relevant.
11. Disconnect the network after model setup and process another video.
12. Check installation and the launch scripts on each operating system you intend to claim as tested.

Mark the release as a pre-release while these target-machine checks remain outstanding. The packaged source is not a compiled or signed desktop executable.
