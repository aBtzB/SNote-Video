# How video becomes subtitles

## Shared timing
A video upload is streamed to a generated project directory. FFprobe verifies that it contains both video and audio and determines its duration. FFmpeg selects the first video and audio tracks and writes a temporary H.264/AAC preview at up to 1280 × 720. A second pass extracts mono 16 kHz PCM from that preview. Leading and trailing silence are retained with timestamp-aware resampling and padding.

Recognition therefore sees the timeline that the browser plays. The preview and WAV become available after preparation succeeds; cancellation removes temporary preparation files. The source is retained unchanged for retry.

This is a deliberate disk and CPU tradeoff. Re-encoding every clip gives the browser a predictable playback format but can take substantial time. It is not a lossless video export. Unusual source timestamps and recognition errors can still require cue edits.

## Components
| Module | Responsibility |
| --- | --- |
| video.py | FFprobe, cancellable FFmpeg processes, preview conversion, aligned WAV and waveform |
| engines.py | Speech model lifecycle and local translation adapter |
| models.py | Explicit model downloads, cached catalogue, validation, temporary installation |
| jobs.py | One inference worker, queue, partial transcripts, progress, recovery boundaries |
| server.py | Loopback HTTP routes, streamed uploads, byte-range media serving |
| domain.py | Cue validation, edit rules, model choices |
| store.py | SQLite documents, revision checks, interrupted-job recovery |
| exports.py | Saved text, SRT, VTT, JSON output |
| static/app.js | Video text tracks, cue editing, model UI, progress polling |

## Work and failure boundaries
One inference worker accepts up to eight active or pending jobs. Preview conversion runs in cancellable subprocesses; native model calls stop between segments or lines. Speech segments are saved progressively. Translation is committed as a whole; a failed translation leaves the source text available.

A separate single worker manages model downloads. Merely opening the app or model panel performs no network request. Explicit downloads are staged and checked before publishing model directories. Speech files are tied to a resolved repository revision and validated against provider sizes and available checksums. Translation packs are checked for safe paths, language direction, tokenizer compatibility, and model loading.

## Editing and preview
The browser uses a native video text track for draft subtitles. Export is based on saved state. Timestamps are edited in seconds and rounded to milliseconds on save. Server validation rejects invalid numbers, reversed cues, overlap, and out-of-range ends. Timing edits reset review marks. Source edits also invalidate unchanged translations.

Every saved update increments a revision. A stale browser tab receives HTTP 409 without overwriting newer work. Global offsets are applied to the draft only, with bounds checks before a save.

## Local scope
The server binds to 127.0.0.1, validates Host and Origin, and requires an application header on mutations. FFmpeg uses argument arrays rather than shell commands and restricts input protocols to local files/pipes. It does not send video to a transcription service.

The default video data directory and port are separate from the SNote audio edition. Storage is ordinary local files and SQLite, without authentication or encryption. A hosted version needs a different server, ownership model, and worker architecture.
