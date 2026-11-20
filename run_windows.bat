@echo off
chcp 65001 >nul
title EU Translation Memory Extractor (DGT-TM)
color 0B
cls

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo ======================================================================
echo       EU TRANSLATION MEMORY EXTRACTOR (DGT-TM) v2.4
echo       Author: Michal Kornacki (in Antigravity, 2026) - MIT License
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
    %PY_CMD% "%~dp0tmx_extractor.py" %*
    goto finish
)

color 0C
echo.
echo ======================================================================
echo  [WARNING] Python was not found on your computer!
echo ======================================================================
echo.
echo To run this application, you need the free Python runtime:
echo.
echo 1. Open your browser and go to:
echo    https://www.python.org/downloads/
echo.
echo 2. Download and run the installer (e.g. Python 3.12 or newer).
echo.
echo 3. [CRITICAL STEP!] On the very first installer screen, check:
echo    [X] Add python.exe to PATH (or 'Add Python to environment variables')
echo.
echo 4. Complete the installation and double-click this file again.
echo.
echo Detailed instructions can be found in the INSTRUCTIONS.html file.
echo ======================================================================
echo.
pause
exit /b 1

:finish
if errorlevel 1 (
    echo.
    echo [An error occurred during program execution.]
    pause
)
