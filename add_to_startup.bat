@echo off
chcp 65001 >nul
echo 시작 프로그램 바로가기 생성...

set INSTALL_DIR=%~dp0
set SHORTCUT_NAME=SensorModule.lnk

:: VBScript로 바로가기 생성 (현재 폴더에)
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%INSTALL_DIR%%SHORTCUT_NAME%" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%INSTALL_DIR%start_background.bat" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> CreateShortcut.vbs
echo oLink.WindowStyle = 7 >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs

cscript //nologo CreateShortcut.vbs
del CreateShortcut.vbs

echo.
echo 바로가기가 생성되었습니다: %INSTALL_DIR%%SHORTCUT_NAME%
echo.
echo 시작 프로그램으로 등록하려면:
echo   1. Win + R 키
echo   2. shell:startup 입력 후 Enter
echo   3. %SHORTCUT_NAME% 파일을 해당 폴더로 이동
echo.
pause
