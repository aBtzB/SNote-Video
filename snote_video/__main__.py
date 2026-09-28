import argparse
import json
import logging
import os
from pathlib import Path
import sys

from .domain import MODELS
from .engines import LocalEngines
from .video import VideoEngines
from .server import make_server
from .translation import install_pack, installed


def main():
    parser = argparse.ArgumentParser(description="SNote Video — generate, translate, and review subtitles locally.")
    parser.add_argument("--data-dir", type=Path,
                        default=Path(os.environ.get("SNOTE_VIDEO_DATA_DIR", "~/.snote_video")).expanduser(),
                        help="Where to keep recordings, transcripts, and downloaded models.")
    parser.add_argument("--max-minutes", type=int, default=120, help="Video duration limit; 0 removes the limit (default: 120).")
    parser.add_argument("--max-upload-mb", type=int, default=2048, help="Maximum upload size in MiB (default: 2048).")
    commands = parser.add_subparsers(dest="command")
    serve = commands.add_parser("serve", help="Open the local notebook server (default).")
    serve.add_argument("--port", type=int, default=8766)
    preview = commands.add_parser("preview", help="Explore the sample editor before model setup.")
    preview.add_argument("--port", type=int, default=8766)
    install = commands.add_parser("install", help="Download a speech model or import your downloaded translation pack.")
    install.add_argument("--speech", choices=MODELS)
    install.add_argument("--translation", type=Path, help="Path to a manually downloaded .argosmodel file.")
    commands.add_parser("doctor", help="Check the dependency and storage configuration.")
    args = parser.parse_args()
    if args.max_minutes < 0 or args.max_upload_mb <= 0:
        parser.error("Use non-negative --max-minutes and positive --max-upload-mb values.")
    root = args.data_dir.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    if args.command == "install":
        if not (args.speech or args.translation):
            parser.error("Use --speech MODEL or --translation PATH_TO_ARGOSMODEL.")
        engines = LocalEngines(root)
        try:
            if args.speech:
                print(f"Downloading and checking the {args.speech} speech model…", flush=True)
                engines.load_speech(args.speech, download=True)
            if args.translation:
                data = install_pack(root, args.translation.expanduser())
                print(f"Installed translation pack: {data['from_code']} → {data['to_code']}")
            print("Model setup finished. Open SNote Video to use the models.")
        except Exception as exc:
            print(f"Setup failed: {exc}", file=sys.stderr)
            return 1
        return 0
    if args.command == "doctor":
        print(json.dumps({"python": sys.version.split()[0], "data_dir": str(root),
                          "translation_pairs": [f"{a} → {b}" for a, b in installed(root)],
                          **VideoEngines(root).capabilities()}, indent=2))
        print("Models are downloaded separately. See README.md for setup and the real-video smoke test.")
        return 0
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    engines = VideoEngines(root, args.max_minutes * 60)
    try:
        server = make_server(root, getattr(args, "port", 8766), engines, args.max_upload_mb * 1024 * 1024)
    except OSError as exc:
        print(f"Could not start SNote Video: {exc}. Try: python -m snote_video serve --port 8767", file=sys.stderr)
        return 1
    print(f"\nSNote Video is ready at http://127.0.0.1:{server.server_port}\n"
          "Open Models in the sidebar to choose and download models.\n"
          "Keep this terminal open. Press Ctrl+C to close SNote Video.\n", flush=True)
    try:
        server.serve_forever(poll_interval=0.3)
    except KeyboardInterrupt:
        print("\nFinishing the current model operation before closing…", flush=True)
    finally:
        server.server_close()
        server.app.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
