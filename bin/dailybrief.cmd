@echo off
REM bin\dailybrief.cmd -- forwards to the dbrief_cli tool via Poetry.
set "REPO_ROOT=%~dp0.."
cd /d "%REPO_ROOT%"
poetry run python "%REPO_ROOT%\dbrief_cli\main.py" %*
