#requires -Version 5.1
<#
.SYNOPSIS
  Builds dist\Kel-dash\Kel-dash.exe via PyInstaller (onedir, windowed).
  Invoked manually, or automatically by the pre-push git hook.
  Exits non-zero on any failure so callers (the git hook) can abort.
#>
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot   # scripts/ -> repo root
Set-Location $RepoRoot

Write-Host "== Resolving Poetry virtualenv =="
$venvPath = (poetry env info --path 2>$null | Select-Object -Last 1)
if ($venvPath) { $venvPath = $venvPath.Trim() }

if (-not $venvPath -or -not (Test-Path $venvPath)) {
    Write-Host "No usable Poetry venv found; running 'poetry install'..."
    poetry install --with shared,shared-dev,gui,build-windows --without services,services-dev
    if ($LASTEXITCODE -ne 0) { throw "poetry install failed with exit code $LASTEXITCODE" }
    $venvPath = (poetry env info --path 2>$null | Select-Object -Last 1).Trim()
}

$pyInstaller = Join-Path $venvPath "Scripts\pyinstaller.exe"
if (-not (Test-Path $pyInstaller)) {
    Write-Host "pyinstaller.exe missing from venv; installing build-windows group..."
    poetry install --with build-windows
    if ($LASTEXITCODE -ne 0) { throw "poetry install --with build-windows failed" }
}
if (-not (Test-Path $pyInstaller)) {
    throw "pyinstaller.exe still not found at $pyInstaller after install attempt"
}

Write-Host "== Running PyInstaller (onedir, windowed) =="
& $pyInstaller "Kel-dash.spec" --noconfirm --clean
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed with exit code $LASTEXITCODE"
}

$distDir = Join-Path $RepoRoot "dist\Kel-dash"
$exePath = Join-Path $distDir "Kel-dash.exe"
if (-not (Test-Path $exePath)) {
    throw "Build reported success but $exePath was not produced"
}

Write-Host "== Seeding runtime config (first run only; never overwrites) =="
$seed = @{
    (Join-Path $RepoRoot "dash-gui\config.yml") = (Join-Path $distDir "config.yml")
    (Join-Path $RepoRoot "logging.yml")         = (Join-Path $distDir "logging.yml")
}
foreach ($src in $seed.Keys) {
    $dst = $seed[$src]
    if (-not (Test-Path $dst)) {
        Copy-Item -Path $src -Destination $dst
        Write-Host "Seeded $dst from $src"
    }
}

Write-Host "Build succeeded: $exePath"
exit 0
