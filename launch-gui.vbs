Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\ouyangjiahong\codes\MinerU"
WshShell.Run "cmd /c C:\Users\ouyangjiahong\.local\bin\uv.exe run --extra gui pythonw mineru/cli/gui.py 2>C:\Users\ouyangjiahong\codes\MinerU\gui-launch.log", 0, False
Set WshShell = Nothing
