# SNote Video

Generate subtitles from a video's dialogue, translate them locally, and check the result while watching the clip.

SNote Video is a companion to the SNote audio notebook. It adds a video preview, editable cue times, a subtitle offset control, and reading-speed hints. You install Python and FFmpeg yourself, then choose speech and translation models in the app.

**First beta · source release · Python 3.11 or 3.12 required.** This download contains Python source and launch scripts. It is not a packaged Windows executable.

## Features

- MP4, MKV, MOV, WEBM, AVI, and M4V input, depending on the codecs in your FFmpeg build.
- Local Whisper transcription through faster-whisper.
- Optional local translation with SentencePiece Argos packs through CTranslate2.
- A Models screen with explicit downloads, progress, cancel, retry, and installed status.
- A browser-compatible video preview, with original, translated, or bilingual subtitles.
- Editable text, cue start/end times, and a global offset in seconds.
- Reading-speed and long-cue hints to help with review.
- SRT, VTT, TXT, and JSON export.
- A local queue, job cancellation, saved projects, and revision checks between browser tabs.

The app generates new subtitles from speech. It does not read text in the picture, extract existing subtitle tracks, dub voices, or burn subtitles into a video. It uses the first video track and first audio track. Subtitles are exported as separate files for a player or editor.

## Install the prerequisites

Use a Windows, macOS, or Linux computer. The program does not run directly on a phone; you can upload its release files to GitHub from a phone.

1. Install **Python 3.11 or 3.12**.
2. Install **FFmpeg with FFprobe**, including the libx264 and AAC encoders.
3. Extract the release ZIP and open a terminal in its **SNote-Video** folder.

FFmpeg's [download page](https://ffmpeg.org/download.html) links to compiled packages. On Windows, extract a build, find the folder containing both ffmpeg.exe and ffprobe.exe, and add that folder to your user PATH using **Edit environment variables for your account → Path → Edit → New**. Close and reopen the terminal afterwards.

On macOS, use an FFmpeg package that includes FFprobe; if you already use Homebrew, install its ffmpeg formula. On Ubuntu/Debian, install your distribution's ffmpeg package.

Check the tools in a new terminal:

~~~sh
ffmpeg -version
ffprobe -version
~~~

## Run the app

### Windows PowerShell

~~~powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m snote_video
~~~

Use py -3.11 instead for the first command if that is your Python version.

### macOS / Linux

~~~sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m snote_video
~~~

Use python3.11 instead if appropriate.

Open **http://127.0.0.1:8766**. Keep the terminal running. On later runs, repeat only the last command. The included **run-windows.cmd** or **bash run.sh** also starts an existing .venv environment; neither installs dependencies.

The UI can open before model setup. Its illustrative sample contains text without video and is useful for exploring the editor.

## Choose models and make subtitles

1. Open **Models**. Download **Tiny** for a modest first speech model, or choose a larger one.
2. For translation, open **Translation → Load language list**, search for a direction such as English → Spanish, and download that pack.
3. Choose **New video**, select the file, spoken language, model, and optional translation target.
4. Wait while FFmpeg makes the preview and the speech model writes subtitles.
5. Watch the preview. Switch between original, translated, bilingual, or no subtitles.
6. Correct the text and edit each cue's **In** and **Out** times in seconds. Use **Shift all cues** if every cue needs the same offset.
7. Choose **Save changes**, then export SRT or VTT for your player or video editor.

Tiny's supporting files total about 78 MB. Larger speech models can require several GB of storage and more RAM. Translation packs and Python dependencies add to the download size. Only selected models are downloaded. Opening Models does not access the model providers; loading the language list and downloading models do.

Translation packs are directional. English → Spanish does not install Spanish → English. Supported pairs depend on the catalogue; older BPE packs are not supported. The importer checks compatibility before accepting a pack. An unavailable translation route leaves the original subtitles available for editing and export.

Once installed, models work offline without an account or API key. Model downloads use Hugging Face and the official Argos catalogue. The app sends no video or dialogue to a transcription service.

## Timing and preview

The app creates an H.264/AAC MP4 preview at up to 1280 × 720. It then extracts mono 16 kHz audio from that preview, including leading silence, so recognition and playback use the same timeline. This adds a conversion step and requires extra disk space; the original video is retained unchanged.

The preview uses your current edits. Exports use saved edits. Source-text changes invalidate an unchanged translation; timing changes clear that cue's review mark. Saving rejects overlapping, reversed, non-finite, or out-of-range times.

Reading-speed hints flag cues above 20 characters per second and text longer than 84 characters. These are review prompts, not language-specific subtitle standards. This version does not split or merge cues automatically.

Generated timestamps can still need correction. Check exported subtitles against the original video, particularly files with unusual timestamps or variable frame rates.

## File and duration limits

Defaults are **2 GiB per file** and **120 minutes per video**. They are application limits, not Whisper limits. To change them, place the options before any subcommand:

~~~sh
python -m snote_video --max-minutes 240 --max-upload-mb 4096
~~~

To remove the duration limit:

~~~sh
python -m snote_video --max-minutes 0 --max-upload-mb 4096
~~~

Here, python means the Python executable in your virtual environment. Longer videos take more CPU time and disk space; the full original, preview, and extracted WAV are retained. The app processes one video at a time and queues up to eight jobs.

## Data and troubleshooting

Data is saved under **~/.snote_video**. This is separate from SNote's audio workspace. Deleting a project removes its source video, preview, WAV, and database entry; models stay installed.

~~~sh
python -m snote_video doctor
python -m snote_video --data-dir ./video-data serve --port 8767
~~~

| Problem | Check |
| --- | --- |
| New video is disabled | Install the Python requirements and FFmpeg/FFprobe, restart, then download a speech model |
| Preview conversion fails | Read the terminal message; check FFmpeg includes libx264 and AAC and the disk has space |
| No audio track | Choose a video containing dialogue; silent videos cannot produce a transcript |
| Translation is missing | Install the correct directional pack and translate again |
| Subtitles drift | Review the cue times or apply an offset; an offset cannot repair changing drift |
| Video is too long or large | Change the documented limits when starting the app |
| Browser cannot connect | Keep the terminal open and use the printed localhost URL |
| Model download fails | Check the connection and free space, then retry |
| Port 8766 is occupied | Close the previous instance or start on a different port with a separate data directory |

Use one process per data directory. The app is for a single local user, with no account system or encrypted storage. CPU inference is the supported baseline. Names, accents, overlapping speech, and mixed-language dialogue need human review.

## Development

~~~sh
python -m unittest discover -s tests -v
node --check snote_video/static/app.js
~~~

FFmpeg media tests generate small clips with tones. No speech models are downloaded by the test suite. See [validation](docs/validation.md) for what was checked and the optional real-video model test.

The backend uses Python's standard HTTP server and SQLite. The frontend is plain HTML, CSS, and JavaScript. See [architecture](docs/architecture.md) for the pipeline and [project notes](docs/portfolio.md) for ideas you can investigate.

## Releases

The upload-ready release notes are in **RELEASE_NOTES.md**. [Publishing instructions](docs/releasing.md) include the tag, title, asset filename, and phone-friendly upload steps. [GitHub text](docs/GITHUB.md) includes an About description and topics.

To rebuild a clean source asset without packaging local recordings or models:

~~~sh
python tools/package_release.py
~~~

The ZIP and its SHA-256 file appear in dist/. This source release needs Python and FFmpeg installed separately. It includes no model weights, dependency binaries, or compiled executable.

## Acknowledgments

Inspired by the video-to-subtitles workflow in [Blue-B/WhisperSubTranslate](https://github.com/Blue-B/WhisperSubTranslate). This is an independent implementation built on SNote's local review engine. No source files, branding, or UI assets from that repository were copied, and this release does not claim its full feature set.

Speech recognition uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper), based on [OpenAI Whisper](https://github.com/openai/whisper), and [CTranslate2](https://github.com/OpenNMT/CTranslate2). Translation uses [Argos](https://github.com/argosopentech/argos-translate) models and [SentencePiece](https://github.com/google/sentencepiece). Video preparation uses [FFmpeg](https://ffmpeg.org/). The Tiny size estimate comes from its [model file listing](https://huggingface.co/Systran/faster-whisper-tiny/tree/main).

Application source: MIT license. Dependencies and downloaded models retain their own licenses.
