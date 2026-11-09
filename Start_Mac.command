#!/usr/bin/env bash
# Ekstraktor Pamięci Tłumaczeniowych UE (macOS launcher)
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
clear

echo "======================================================================"
echo "      EKSTRAKTOR PAMIĘCI TŁUMACZENIOWYCH UE (DGT-TM) v2.1"
echo "      Autor: Michał Kornacki (w Antigravity, 2026) - Licencja MIT"
echo "======================================================================"
echo ""

if command -v python3 &>/dev/null; then
    python3 "$DIR/tmx_extractor.py"
elif command -v python &>/dev/null; then
    python "$DIR/tmx_extractor.py"
else
    echo "======================================================================"
    echo " [UWAGA] Nie znaleziono zainstalowanego Pythona na Twoim komputerze Mac!"
    echo "======================================================================"
    echo ""
    echo "1. Wejdź na stronę: https://www.python.org/downloads/macos/"
    echo "2. Pobierz instalator macOS 64-bit universal2 installer (.pkg)"
    echo "3. Zainstaluj pakiet, a następnie uruchom ten plik ponownie."
    echo ""
    echo "Szczegółowa instrukcja znajduje się w pliku: INSTRUKCJA.html"
    echo "======================================================================"
    echo ""
    read -p "Naciśnij Enter, aby zamknąć..."
    exit 1
fi

echo ""
echo "----------------------------------------------------------------------"
read -p "Program zakończył działanie. Naciśnij Enter, aby zamknąć to okno..."
