@echo off
chcp 65001 >nul
echo === 센서 모듈 서비스 제거 ===
echo.

:: 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 관리자 권한으로 실행해주세요.
    pause
    exit /b 1
)

set INSTALL_DIR=%~dp0
set SERVICE_NAME=SensorModule
set NSSM_PATH=%INSTALL_DIR%nssm.exe

%NSSM_PATH% stop %SERVICE_NAME% >nul 2>&1
%NSSM_PATH% remove %SERVICE_NAME% confirm

echo.
echo 서비스가 제거되었습니다.
pause
