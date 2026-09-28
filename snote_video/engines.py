"""Speech and translation adapters; video preparation lives in video.py."""

import importlib.util


class Cancelled(Exception):
    pass


def checkpoint(stop):
    if stop.is_set():
        raise Cancelled()


class LocalEngines:
    def __init__(self, root):
        self.root = root
        self.model = None
        self.model_name = None
        self.translation_route = None
        self.translation_models = []

    def capabilities(self):
        return {
            "speech_installed": importlib.util.find_spec("faster_whisper") is not None,
            "translation_installed": all(importlib.util.find_spec(name) is not None
                                         for name in ("sentencepiece", "ctranslate2")),
        }

    def load_speech(self, name, download=False):
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("Speech dependencies are missing. Run: python -m pip install -r requirements.txt") from exc
        if self.model_name != name:
            self.model = None  # Do not retain several large models in memory.
            self.model_name = None
            try:
                from .models import speech_folder
                local = speech_folder(self.root, name)
                self.model = WhisperModel(
                    str(local) if local else name, device="cpu", compute_type="int8",
                    download_root=str(self.root / "models" / "whisper"),
                    local_files_only=not download,
                )
            except Exception as exc:
                raise RuntimeError(f"Could not load the {name} speech model. Open Models and install it, or run: python -m snote_video install --speech {name}") from exc
            self.model_name = name
        return self.model

    def transcribe(self, path, name, language, stop, on_language, on_segment):
        checkpoint(stop)
        model = self.load_speech(name)
        checkpoint(stop)
        segments, info = model.transcribe(
            str(path), language=None if language == "auto" else language,
            task="transcribe", beam_size=5, vad_filter=True,
            condition_on_previous_text=False,
        )
        on_language(info.language)
        for segment in segments:
            checkpoint(stop)
            if segment.text.strip():
                on_segment(segment.start, segment.end, segment.text.strip())
        checkpoint(stop)

    def translator(self, source, target):
        if source == target:
            return lambda text: text
        from .translation import PairTranslator, installed, route
        paths = tuple(route(installed(self.root), source, target))
        if paths != self.translation_route:
            self.translation_models = []
            self.translation_route = None
            self.translation_models = [PairTranslator(path) for path in paths]
            self.translation_route = paths

        def translate(text):
            for model in self.translation_models:
                text = model(text)
            return text

        return translate
