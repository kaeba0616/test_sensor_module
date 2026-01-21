$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$PSScriptRoot\SensorModule.lnk")
$Shortcut.TargetPath = "$PSScriptRoot\start_background.bat"
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.WindowStyle = 7
$Shortcut.Save()
Write-Host "SensorModule.lnk 생성 완료: $PSScriptRoot\SensorModule.lnk"
