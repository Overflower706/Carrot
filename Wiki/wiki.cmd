@echo off
rem Double-click: starts the wiki server and opens the doc list.
rem Close the "Wiki Server" window to stop it.
start "Wiki Server" /min cmd /c "python "%~dp0serve.py" || pause"
ping -n 3 127.0.0.1 >nul
start "" http://127.0.0.1:8765/index.html
