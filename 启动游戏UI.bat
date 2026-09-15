@echo off
cd /d "%~dp0"
if exist "runtime\pythonw.exe" (
  start "" "runtime\pythonw.exe" game_ui.py
  exit /b
)
where pythonw >nul 2>nul
if %errorlevel%==0 (
  start "" pythonw game_ui.py
) else (
  python game_ui.py
  pause
)