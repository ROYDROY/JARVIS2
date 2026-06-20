Set WshShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run chr(34) & strPath & "\lanzar_jarvis.bat" & Chr(34), 0
Set WshShell = Nothing
