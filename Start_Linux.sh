#!/usr/bin/env bash
# Skrót do uruchomienia ekstraktora w trybie asystenta
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$DIR/tmx_extractor.py"
