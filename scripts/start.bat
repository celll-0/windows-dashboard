@echo off
setlocal EnableExtensions EnableDelayedExpansion

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

REM Load .env, then .env.prod on top (same layering as the "widget" poe
REM task's envfile = [".env", ".env.prod"] -- .env.prod wins on shared keys
REM like GUI_HOST). Done into THIS process's environment for two reasons:
REM DailyBrief.exe does not call load_dotenv() in production, so it inherits
REM these when launched below; and `docker compose up` needs SERVICES_PORT
REM in its own environment too, since docker-compose.yml's `ports:` mapping
REM is `${SERVICES_PORT:-8002}:${SERVICES_PORT:-8002}` -- Compose does NOT
REM read .env.prod on its own (only the container gets it, via env_file,
REM which is too late for port mapping resolved at "up" time), so without
REM this the exposed port silently falls back to 8002 regardless of what
REM .env.prod says. Keep this block AFTER the ping/Docker-wait section above:
REM .env/.env.prod are user-writable, and a poisoned SystemRoot=/PING_EXE=
REM line in one must not be able to reach PING_EXE's resolution before those
REM calls run.
REM Values in these files may be wrapped in single/double quotes (e.g.
REM SERVICES_PORT='8070') the way dotenv-style loaders expect -- strip them
REM here too, since `for /f` does not, and a quoted port string would
REM otherwise reach docker compose's ${SERVICES_PORT:-8002} substitution
REM literally (producing an invalid "'8070'" container port).
if exist "%REPO_ROOT%.env" (
    for /f "usebackq eol=# tokens=1,2 delims==" %%A in ("%REPO_ROOT%.env") do (
        if not "%%A"=="" (
            set "_val=%%B"
            set "_val=!_val:'=!"
            set "_val=!_val:"=!"
            set "%%A=!_val!"
        )
    )
)
if exist "%REPO_ROOT%.env.prod" (
    for /f "usebackq eol=# tokens=1,2 delims==" %%A in ("%REPO_ROOT%.env.prod") do (
        if not "%%A"=="" (
            set "_val=%%B"
            set "_val=!_val:'=!"
            set "_val=!_val:"=!"
            set "%%A=!_val!"
        )
    )
)
set "ENV=production"

echo Starting dash-services (docker compose)...
docker compose up -d
if errorlevel 1 (
    echo docker compose up failed with error %errorlevel% 1>&2
    exit /b 1
)

REM Give the backend a moment to come up before the GUI's first fetch.
"%PING_EXE%" -n 7 127.0.0.1 >nul

set "DAILYBRIEF_EXE=%REPO_ROOT%dist\DailyBrief\DailyBrief.exe"
if not exist "%DAILYBRIEF_EXE%" (
    echo DailyBrief.exe not found at "%DAILYBRIEF_EXE%". 1>&2
    echo Build it first: powershell -File scripts\build-gui-exe.ps1 1>&2
    exit /b 1
)

echo Launching DailyBrief...
start "" "%DAILYBRIEF_EXE%"

endlocal
exit /b 0
