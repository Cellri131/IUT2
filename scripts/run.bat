@echo off
REM Launcher pour crawler.py (double-clic directement sur ce fichier)

setlocal enabledelayedexpansion

cd /d "%~dp0"

python run.py

pause
