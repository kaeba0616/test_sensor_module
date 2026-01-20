@echo off
chcp 65001 >nul
echo Windows 시작 시 자동 실행 등록...

set INSTALL_DIR=%~dp0
set SHORTCUT_NAME=SensorModule.lnk
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

:: VBScript로 바로가기 생성
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%STARTUP_FOLDER%\%SHORTCUT_NAME%" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%INSTALL_DIR%start_background.bat" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> CreateShortcut.vbs
echo oLink.WindowStyle = 7 >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

cscript //nologo CreateShortcut.vbs
del CreateShortcut.vbs

echo.
echo 시작 프로그램에 등록되었습니다.
echo 위치: %STARTUP_FOLDER%\%SHORTCUT_NAME%
echo.
echo 제거하려면 해당 파일을 삭제하세요.
pause
