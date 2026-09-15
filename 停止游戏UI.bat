@echo off
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process | Where-Object { ($_.Name -eq 'python.exe' -or $_.Name -eq 'pythonw.exe') -and $_.CommandLine -like '*game_ui.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo Stopped local web UI server (if it was running).
ping -n 3 127.0.0.1 >nul