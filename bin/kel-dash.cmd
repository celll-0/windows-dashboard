@echo off
REM bin\kel-dash.cmd -- forwards to the dash-cli tool via Poetry.
set "REPO_ROOT=%~dp0.."
cd /d "%REPO_ROOT%"
poetry run python "%REPO_ROOT%\dash-cli\main.py" %*
