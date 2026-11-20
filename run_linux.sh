#!/usr/bin/env bash
# Shortcut to launch EU TMX Extractor in interactive wizard mode
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
python3 "$DIR/tmx_extractor.py" "$@"
