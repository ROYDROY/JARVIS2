@echo off
title JARVIS 4.0
cd /d "%~dp0"
call venv\Scripts\activate.bat
python jarvis_app.py
