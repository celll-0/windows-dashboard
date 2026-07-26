' start-hidden.vbs
' Runs start.bat (same folder) with window style 0 (hidden), so no console
' ever flashes -- including for the `docker compose up -d` step. This is
' what the "Kel-dash" scheduled task actually invokes at logon.
Dim shell, fso, scriptDir, batPath
Set shell = CreateObject("WScript.Shell")
Set fso   = CreateObject("Scripting.FileSystemObject")
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
batPath   = scriptDir & "\start.bat"
shell.Run """" & batPath & """", 0, True
