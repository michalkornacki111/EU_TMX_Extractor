#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Uruchamiacz testów E2E dla EU TMX Extractor
============================================
Uruchamia pełny zestaw testów automatycznych End-to-End:
- Kompatybilność z Windows (VT / ANSI fallback, bezpieczne kodowanie UTF-8)
- Kompatybilność z macOS i Linux (skrypty uruchomieniowe)
- Poprawność standardu TMX 1.4 XML
- Dzielenie plików dla programów CAT (ochrona pamięci RAM)
- Ekstrakcja seryjna (batch) ze wszystkich plików ZIP w folderze jeden po drugim
- Wywołania CLI i obsługa błędów

Użycie:
  python3 run_e2e_tests.py
"""

import sys
import os
import unittest

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    tests_dir = os.path.join(base_dir, "tests")

    print("=" * 72)
    print("   EU TMX EXTRACTOR - URUCHAMIANIE TESTÓW END-TO-END (E2E)")
    print("=" * 72)
    print(f"Katalog projektu: {base_dir}")
    print(f"Katalog testów:   {tests_dir}")
    print(f"Wersja Pythona:   {sys.version.split()[0]} ({sys.platform})")
    print("=" * 72)
    print()

    loader = unittest.TestLoader()
    suite = loader.discover(tests_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 72)
    if result.wasSuccessful():
        print(f" [SUKCES] Wszystkie testy E2E ({result.testsRun}) zakończone pomyślnie! OK.")
        print("=" * 72)
        sys.exit(0)
    else:
        print(f" [BLAD] Wykryto błędy: {len(result.failures)} niepowodzeń, {len(result.errors)} błędów.")
        print("=" * 72)
        sys.exit(1)

if __name__ == "__main__":
    main()
