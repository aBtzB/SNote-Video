"""Local video preparation. The recognition audio is extracted from the preview.

Using one media timeline for playback and recognition avoids losing leading
silence when an audio stream starts later than the video stream.
"""
from array import array
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import wave

from .domain import MAX_DURATION
from .engines import LocalEngines, checkpoint


def run_process(args, stop, *, timeout=None, progress_file=None, on_progress=None, duration=0):
    """Drain output to temporary files and terminate children on cancellation."""
    checkpoint(stop)
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        process = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        started = time.monotonic()
        last_progress = None
        try:
            while process.poll() is None:
                checkpoint(stop)
                if timeout and time.monotonic() - started > timeout:
                    raise RuntimeError("The media probe timed out. Try another video file.")
                if progress_file and progress_file.is_file() and on_progress and duration:
                    try:
                        with progress_file.open("rb") as progress:
                            progress.seek(0, 2)
                            progress.seek(max(0, progress.tell() - 4096))
                            values = progress.read().decode("utf-8", errors="replace").splitlines()
                        times = [int(line.split("=", 1)[1]) for line in values if line.startswith("out_time_us=")]
                        if times:
                            value = max(0, min(99, round(100 * times[-1] / 1_000_000 / duration)))
                            if value != last_progress:
                                on_progress(value)
                                last_progress = value
                    except (OSError, ValueError):
                        pass
                stop.wait(0.15)
            checkpoint(stop)
            if process.returncode:
                err.seek(0, 2)
                err.seek(max(0, err.tell() - 3000))
                details = err.read().decode("utf-8", errors="replace").strip()
                raise RuntimeError("Video processing failed. " + (details or "Check your FFmpeg installation."))
            out.seek(0)
            return out.read(2 * 1024 * 1024)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def probe(path, stop):
    tool = shutil.which("ffprobe")
    if not tool:
        raise RuntimeError("FFprobe is missing. Install FFmpeg and add its bin folder to PATH, then restart.")
    data = run_process([tool, "-v", "error", "-protocol_whitelist", "file,pipe",
        "-show_entries", "stream=index,codec_type,codec_name,duration,width,height:format=duration",
        "-of", "json", str(path)], stop, timeout=30)
    try:
        return json.loads(data)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("Could not read this video's metadata.") from exc


def video_duration(info):
    streams = info.get("streams", [])
    videos = [stream for stream in streams if stream.get("codec_type") == "video"]
    if not videos:
        raise ValueError("This file has no video track. Choose a video with sound.")
    if not any(stream.get("codec_type") == "audio" for stream in streams):
        raise ValueError("This video has no audio track to transcribe.")
    duration = videos[0].get("duration") or info.get("format", {}).get("duration")
    try:
        duration = float(duration)
    except (TypeError, ValueError):
        raise ValueError("The video duration could not be determined. Try converting it to MP4.") from None
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("The video has no usable duration.")
    return duration


def waveform(path, stop):
    """Summarize PCM in constant memory, including an hour-long recording."""
    peaks = []
    with wave.open(str(path), "rb") as stream:
        frames, rate = stream.getnframes(), stream.getframerate()
        if stream.getnchannels() != 1 or stream.getsampwidth() != 2 or rate != 16000 or not frames:
            raise ValueError("The prepared audio is not valid mono 16 kHz PCM.")
        for index in range(96):
            remaining = frames * (index + 1) // 96 - frames * index // 96
            maximum = 0
            while remaining:
                checkpoint(stop)
                amount = min(remaining, 16000)
                values = array("h", stream.readframes(amount))
                if sys.byteorder != "little":
                    values.byteswap()
                if len(values) != amount:
                    raise ValueError("The prepared audio was incomplete.")
                maximum = max(maximum, max(map(abs, values), default=0))
                remaining -= amount
            peaks.append(round(maximum / 32768, 3))
    return frames / rate, peaks


class VideoEngines(LocalEngines):
    def __init__(self, root, max_duration=MAX_DURATION):
        super().__init__(root)
        self.max_duration = max_duration

    def capabilities(self):
        return {**super().capabilities(),
                "media_installed": bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))}

    def prepare(self, source, destination, stop, on_progress=None):
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg or not shutil.which("ffprobe"):
            raise RuntimeError("Install FFmpeg with FFprobe and add its bin folder to PATH, then restart SNote Video.")
        report = on_progress or (lambda message, progress: None)
        report("Checking the video and its audio track…", 0)
        duration = video_duration(probe(source, stop))
        if self.max_duration and duration > self.max_duration + 0.05:
            raise ValueError(f"This video exceeds the {self.max_duration / 60:g}-minute limit. "
                             "Restart with a larger --max-minutes value to allow it.")
        if shutil.disk_usage(destination.parent).free < duration * 32000 + 20 * 1024 * 1024:
            raise ValueError("Not enough free disk space for the extracted audio and video preview.")
        with tempfile.TemporaryDirectory(prefix=".prepare-", dir=destination.parent) as temporary:
            folder = Path(temporary)
            preview = folder / "preview.mp4"
            pcm = folder / "playback.wav"
            progress = folder / "progress.txt"
            report("Creating a video preview…", 1)
            run_process([ffmpeg, "-hide_banner", "-v", "error", "-nostdin", "-y",
                "-protocol_whitelist", "file,pipe", "-i", str(source),
                "-map", "0:v:0", "-map", "0:a:0", "-sn", "-dn",
                "-vf", "scale=w='min(1280,iw)':h='min(720,ih)':force_original_aspect_ratio=decrease:force_divisible_by=2,setsar=1",
                "-af", "aresample=async=1:first_pts=0,apad",
                "-t", str(duration), "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
                "-pix_fmt", "yuv420p", "-threads", "2", "-c:a", "aac", "-b:a", "128k",
                "-movflags", "+faststart", "-progress", str(progress), str(preview)], stop,
                progress_file=progress, duration=duration,
                on_progress=lambda value: report(f"Creating a video preview… {value}%", round(value * 0.13)))
            # Extract from exactly what the user will watch, preserving silence
            # before late audio starts and after a short audio stream ends.
            duration = video_duration(probe(preview, stop))
            report("Extracting audio on the video timeline…", 14)
            run_process([ffmpeg, "-hide_banner", "-v", "error", "-nostdin", "-y",
                "-protocol_whitelist", "file,pipe", "-i", str(preview),
                "-map", "0:a:0", "-vn", "-af", "aresample=16000:async=1:first_pts=0,apad",
                "-t", str(duration), "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
                str(pcm)], stop)
            result = waveform(pcm, stop)
            checkpoint(stop)
            pcm.replace(destination)
            preview.replace(destination.parent / "preview.mp4")
            return result
