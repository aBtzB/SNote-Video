"""Create a source release without including user data or downloaded weights."""
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.1.0-beta.1"
TOP = {"README.md", "RELEASE_NOTES.md", "LICENSE", "pyproject.toml", "requirements.txt",
       ".gitignore", "run-windows.cmd", "run.sh"}
SUFFIXES = {".py", ".md", ".html", ".css", ".js", ".svg", ".yml", ".yaml"}
TREES = {"snote_video", "tests", "docs", "tools", ".github"}


def build():
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    destination = output / f"SNote-Video-v{VERSION}-source.zip"
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            relative = path.relative_to(ROOT)
            if not path.is_file() or "__pycache__" in relative.parts:
                continue
            if str(relative) in TOP or (relative.parts[0] in TREES and path.suffix in SUFFIXES):
                archive.write(path, Path("SNote-Video") / relative)
    checksum = hashlib.sha256(destination.read_bytes()).hexdigest()
    destination.with_suffix(".sha256").write_text(checksum + "  " + destination.name + "\n", encoding="ascii")
    print(destination)


if __name__ == "__main__":
    build()
