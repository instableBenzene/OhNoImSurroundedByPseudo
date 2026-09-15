' Launch the local web UI with NO visible window.
' Prefers a bundled runtime (runtime\pythonw.exe) so no system Python is needed.
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = base
If fso.FileExists(base & "\runtime\pythonw.exe") Then
  sh.Run "cmd /c runtime\pythonw.exe game_ui.py", 0, False
Else
  sh.Run "cmd /c where pythonw >nul 2>nul && pythonw game_ui.py || python game_ui.py", 0, False
End If