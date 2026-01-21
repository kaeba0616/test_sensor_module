@echo off
chcp 65001 >nul
echo === 센서 모듈 Windows 서비스 설치 ===
echo.

:: 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 관리자 권한으로 실행해주세요.
    echo 이 파일을 우클릭 후 "관리자 권한으로 실행" 선택
    pause
    exit /b 1
)

set INSTALL_DIR=%~dp0
set SERVICE_NAME=SensorModule
set NSSM_PATH=%INSTALL_DIR%nssm.exe

:: NSSM 존재 확인
if not exist "%NSSM_PATH%" (
    echo [오류] nssm.exe가 없습니다.
    echo.
    echo 다운로드 방법:
    echo   1. https://nssm.cc/download 접속
    echo   2. nssm-2.24.zip 다운로드
    echo   3. 압축 해제 후 win64\nssm.exe를 이 폴더에 복사
    echo.
    pause
    exit /b 1
)

:: Python 경로 찾기
for /f "tokens=*" %%i in ('where py 2^>nul') do set PYTHON_PATH=%%i
if "%PYTHON_PATH%"=="" (
    echo [오류] Python을 찾을 수 없습니다.
    pause
    exit /b 1
)
echo Python 경로: %PYTHON_PATH%

:: 기존 서비스 제거 (있으면)
echo.
echo [1/3] 기존 서비스 확인...
%NSSM_PATH% status %SERVICE_NAME% >nul 2>&1
if %errorLevel% equ 0 (
    echo 기존 서비스 제거 중...
    %NSSM_PATH% stop %SERVICE_NAME% >nul 2>&1
    %NSSM_PATH% remove %SERVICE_NAME% confirm
)

:: 서비스 설치
echo.
echo [2/3] 서비스 설치...
%NSSM_PATH% install %SERVICE_NAME% "%PYTHON_PATH%" "%INSTALL_DIR%main_mqtt.py"
%NSSM_PATH% set %SERVICE_NAME% AppDirectory "%INSTALL_DIR%"
%NSSM_PATH% set %SERVICE_NAME% DisplayName "IoT Sensor Module"
%NSSM_PATH% set %SERVICE_NAME% Description "농업용 센서 데이터 수집 모듈"
%NSSM_PATH% set %SERVICE_NAME% Start SERVICE_AUTO_START
%NSSM_PATH% set %SERVICE_NAME% AppStdout "%INSTALL_DIR%logs\service.log"
%NSSM_PATH% set %SERVICE_NAME% AppStderr "%INSTALL_DIR%logs\error.log"
%NSSM_PATH% set %SERVICE_NAME% AppRotateFiles 1
%NSSM_PATH% set %SERVICE_NAME% AppRotateBytes 1048576

:: 로그 폴더 생성
if not exist "%INSTALL_DIR%logs" mkdir "%INSTALL_DIR%logs"

:: 서비스 시작
echo.
echo [3/3] 서비스 시작...
%NSSM_PATH% start %SERVICE_NAME%

echo.
echo === 설치 완료 ===
echo.
echo 서비스 관리 명령어:
echo   상태 확인: nssm status %SERVICE_NAME%
echo   로그 확인: type logs\service.log
echo   중지: nssm stop %SERVICE_NAME%
echo   시작: nssm start %SERVICE_NAME%
echo   재시작: nssm restart %SERVICE_NAME%
echo   제거: nssm remove %SERVICE_NAME%
echo.
pause
