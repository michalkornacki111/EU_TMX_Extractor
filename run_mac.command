#!/usr/bin/env bash
# EU Translation Memory Extractor (macOS launcher)

export PATH="/Library/Frameworks/Python.framework/Versions/Current/bin:/usr/local/bin:/opt/homebrew/bin:$PATH"
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
clear

echo "======================================================================"
echo "      EU TRANSLATION MEMORY EXTRACTOR (DGT-TM) v2.5"
echo "      Author: Michał Kornacki (in Antigravity, 2026) - MIT License"
echo "======================================================================"
echo ""

if command -v python3 &>/dev/null; then
    python3 "$DIR/tmx_extractor.py" "$@"
elif command -v python &>/dev/null; then
    python "$DIR/tmx_extractor.py" "$@"
else
    echo "======================================================================"
    echo " [WARNING] Python was not found on your Mac!"
    echo "======================================================================"
    echo ""
    echo "1. Go to: https://www.python.org/downloads/macos/"
    echo "2. Download the macOS 64-bit universal2 installer (.pkg)"
    echo "3. Run the installer, then double-click this file again."
    echo ""
    echo "Detailed instructions are available in: INSTRUCTIONS.html"
    echo "======================================================================"
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

echo ""
echo "----------------------------------------------------------------------"
read -p "Program finished. Press Enter to close this window..."
