@echo off
cd /d "%~dp0"
echo [debug] console visible; close this window to stop the server.
python game_ui.py
pause