@echo off
chcp 65001 >nul
title Ekstraktor Pamieci Tlumaczeniowych UE (DGT-TM)
color 0B
cls

echo ======================================================================
echo       EKSTRAKTOR PAMIECI TLUMACZENIOWYCH UE (DGT-TM) v2.1
echo       Autor: Michal Kornacki (w Antigravity, 2026) - Licencja MIT
echo ======================================================================
echo.

set "PY_CMD="

where py >nul 2>nul
if not errorlevel 1 set "PY_CMD=py"

if not defined PY_CMD (
    where python >nul 2>nul
    if not errorlevel 1 set "PY_CMD=python"
)

if not defined PY_CMD (
    where python3 >nul 2>nul
    if not errorlevel 1 set "PY_CMD=python3"
)

if defined PY_CMD (
    %PY_CMD% "%~dp0tmx_extractor.py"
    goto finish
)

color 0C
echo.
echo ======================================================================
echo  [UWAGA] Nie znaleziono zainstalowanego Pythona na Twoim komputerze!
echo ======================================================================
echo.
echo Aby program dzialal, potrzebujesz bezplatnego srodowiska Python:
echo.
echo 1. Otworz przegladarke i wejdz na:
echo    https://www.python.org/downloads/
echo.
echo 2. Pobierz i uruchom instalator (np. Python 3.12 lub nowszy).
echo.
echo 3. [BARDZO WAZNE!] Na pierwszym ekranie instalatora zaznacz ptaszek:
echo    [X] Add python.exe to PATH (lub 'Add Python to environment variables')
echo.
echo 4. Kliknij 'Install Now'. Po zakonczeniu kliknij ten plik ponownie.
echo.
echo Szczegolowa instrukcje krok po kroku znajdziesz w pliku: INSTRUKCJA.html
echo ======================================================================
echo.
pause
exit /b 1

:finish
echo.
echo ----------------------------------------------------------------------
echo Program zakonczyl dzialanie. Nacisnij dowolny klawisz, aby zamknac to okno...
pause >nul
