@echo off
chcp 65001 >nul
echo === 센서 모듈 설치 시작 ===
echo.

set INSTALL_DIR=%~dp0
echo 설치 경로: %INSTALL_DIR%

:: 1. 의존성 설치
echo.
echo [1/3] 의존성 설치...
py -m pip install opencv-python pyserial requests paho-mqtt python-dotenv
echo 패키지 설치 완료

:: 2. .env 파일 생성
echo.
echo [2/3] 환경변수 설정...
if not exist "%INSTALL_DIR%.env" (
    copy "%INSTALL_DIR%.env.example" "%INSTALL_DIR%.env"
    echo .env 파일이 생성되었습니다.
    echo *** 중요: .env 파일을 열어 FARM_ID와 SENSOR_API_KEY를 설정하세요! ***
) else (
    echo .env 파일이 이미 존재합니다.
)

:: 3. 완료
echo.
echo [3/3] 설치 완료
echo.
echo === 설치 완료 ===
echo.
echo 사용 방법:
echo   1. .env 파일을 열어 다음 값 설정:
echo      - FARM_ID (농장 ID)
echo      - SENSOR_API_KEY_SOIL (토양 센서 API 키)
echo      - SENSOR_API_KEY_PLANT (식물 센서 API 키)
echo      - ORG_ID (조직 ID)
echo   2. 테스트 실행: py main.py
echo   3. MQTT 실행: py main_mqtt.py
echo.
echo 백그라운드 자동 실행 설정:
echo   - install_service.bat 실행 (NSSM 서비스 등록)
echo   - 또는 start_background.bat 실행
echo.
pause
