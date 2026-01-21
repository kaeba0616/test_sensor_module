@echo off
chcp 65001 >nul
echo 시작 프로그램 바로가기 생성...

set INSTALL_DIR=%~dp0

:: PowerShell로 바로가기 생성 (현재 폴더에)
powershell -ExecutionPolicy Bypass -File "%INSTALL_DIR%create_shortcut.ps1"

echo.
echo 시작 프로그램으로 등록하려면:
echo   1. Win + R 키
echo   2. shell:startup 입력 후 Enter
echo   3. SensorModule.lnk 파일을 해당 폴더로 이동
echo.
pause
