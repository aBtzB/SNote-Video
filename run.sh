#!/usr/bin/env bash
set -e
cd -- "$(dirname -- "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "Create the Python environment and install requirements first. See README.md."
  exit 1
fi
exec .venv/bin/python -m snote_video "$@"
