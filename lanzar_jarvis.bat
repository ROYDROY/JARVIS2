@echo off
title JARVIS 4.0
cd /d "%~dp0"
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    call C:\JARVIS2\venv\Scripts\activate.bat
)
python jarvis_app.py
