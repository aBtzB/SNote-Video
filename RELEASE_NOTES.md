## SNote Video v0.1.0-beta.1

First beta of SNote Video, a local tool for generating, translating, and reviewing subtitles from video.

### Included
- Video input: MP4, MKV, MOV, WEBM, AVI, and M4V.
- Local Whisper transcription and optional translation using downloaded language packs.
- In-app model selection, download progress, cancellation, and retry.
- Video preview with original, translated, or bilingual subtitles.
- Editable subtitle text and cue times, a global timing offset, and reading-speed hints.
- SRT, VTT, TXT, and JSON exports.
- Saved projects and a local processing queue.

### Download and run
Download **SNote-Video-v0.1.0-beta.1-source.zip** from Assets and extract it.

Install **Python 3.11 or 3.12** and **FFmpeg with FFprobe**, then follow README.md to install requirements and start the app. Open **http://127.0.0.1:8766** and choose your models in **Models**.

This is a **source release with launch scripts**. It does not include a Windows executable, Python, FFmpeg, or model weights.

### Limits and beta status
- Defaults: 2 GiB per file and 120 minutes. Both limits are configurable; the duration cap can be disabled.
- Uses the first video and audio tracks; CPU inference.
- Exports separate subtitle files. No OCR, dubbing, subtitle-track extraction, or burned-in video export.
- Automated application checks and real FFmpeg conversion/synchronization tests passed. Live model downloads, real speech/translation quality, and browser/OS checks still need local verification.

Inspired by WhisperSubTranslate; implemented independently with a focus on subtitle review and timing.
