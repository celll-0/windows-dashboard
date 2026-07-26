#requires -Version 5.1
<#
.SYNOPSIS
  Registers the "Kel-dash" scheduled task: runs start-hidden.vbs at this
  user's logon, fully headless (no console/window ever flashes).
  Run this once manually per machine. No admin rights required.
#>
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot   # scripts/ -> repo root
$vbsPath  = Join-Path $PSScriptRoot "start-hidden.vbs"   # lives alongside this script

if (-not (Test-Path $vbsPath)) {
    throw "start-hidden.vbs not found at $vbsPath"
}

$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$vbsPath`"" -WorkingDirectory $RepoRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"

# Interactive + LeastPrivilege: the GUI must run in the interactive user
# session (running "whether user is logged on or not" would make any window
# invisible anyway), and no elevated rights are required for `docker
# compose` under a normal Docker Desktop install.
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive -RunLevel Limited

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName "Kel-dash" `
    -Action $action -Trigger $trigger -Principal $principal -Settings $settings `
    -Description "Starts dash-services (Docker) and launches Kel-dash.exe headlessly at logon." `
    -Force

Write-Host "Registered scheduled task 'Kel-dash'. Verify with: Get-ScheduledTask -TaskName Kel-dash"
