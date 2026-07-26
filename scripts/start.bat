@echo off
setlocal EnableExtensions

REM Resolve repo root as the parent of this script's directory (scripts\ -> repo root).
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%.."
set "REPO_ROOT=%CD%\"
cd /d "%REPO_ROOT%"

REM Fully-qualified so this never depends on PATH/CWD resolution order --
REM see the timeout.exe PATH-shadowing issue this pipeline already hit once.
set "PING_EXE=%SystemRoot%\System32\ping.exe"

REM Docker Desktop may still be starting up (e.g. we were launched at login
REM alongside it), so poll the engine until it responds instead of failing
REM immediately.
set "DOCKER_WAIT_ELAPSED=0"
set "DOCKER_WAIT_MAX_SECS=180"
set "DOCKER_WAIT_STEP_SECS=3"

echo Waiting for Docker Engine to be ready...
:wait_for_docker
docker info >nul 2>&1
if not errorlevel 1 goto docker_ready

if %DOCKER_WAIT_ELAPSED% GEQ %DOCKER_WAIT_MAX_SECS% (
    echo Docker Engine did not become ready within %DOCKER_WAIT_MAX_SECS% seconds -- is Docker Desktop installed and starting? 1>&2
    exit /b 1
)

REM timeout.exe refuses to run at all ("Input redirection is not supported")
REM when stdin isn't an interactive console -- which is exactly the case
REM when this script is launched headlessly via start-hidden.vbs. Use the
REM standard ping-based sleep instead, which works in both contexts.
set /a DOCKER_WAIT_PING_COUNT=%DOCKER_WAIT_STEP_SECS%+1
"%PING_EXE%" -n %DOCKER_WAIT_PING_COUNT% 127.0.0.1 >nul
set /a DOCKER_WAIT_ELAPSED+=%DOCKER_WAIT_STEP_SECS%
goto wait_for_docker

:docker_ready
echo Docker Engine is ready.

echo Starting dash-services (docker compose)...
docker compose up -d
if errorlevel 1 (
    echo docker compose up failed with error %errorlevel% 1>&2
    exit /b 1
)

REM Give the backend a moment to come up before the GUI's first fetch.
"%PING_EXE%" -n 7 127.0.0.1 >nul

REM Kel-dash.exe does not call load_dotenv() in production, so load .env
REM into THIS process's environment -- the exe inherits it when launched.
REM Keep this block AFTER the ping/Docker-wait section above: .env is
REM user-writable, and a poisoned SystemRoot=/PING_EXE= line in it must not
REM be able to reach PING_EXE's resolution before those calls run.
if exist "%REPO_ROOT%.env" (
    for /f "usebackq eol=# tokens=1,2 delims==" %%A in ("%REPO_ROOT%.env") do (
        if not "%%A"=="" set "%%A=%%B"
    )
)
set "ENV=production"

set "KEL_DASH_EXE=%REPO_ROOT%dist\Kel-dash\Kel-dash.exe"
if not exist "%KEL_DASH_EXE%" (
    echo Kel-dash.exe not found at "%KEL_DASH_EXE%". 1>&2
    echo Build it first: powershell -File scripts\build-gui-exe.ps1 1>&2
    exit /b 1
)

echo Launching Kel-dash...
start "" "%KEL_DASH_EXE%"

endlocal
exit /b 0
