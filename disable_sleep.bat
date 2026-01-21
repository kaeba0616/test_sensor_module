@echo off
chcp 65001 >nul
echo === 절전 모드 비활성화 (관리자 권한 필요) ===
echo.

:: 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 관리자 권한으로 실행해주세요.
    echo 이 파일을 우클릭 후 "관리자 권한으로 실행" 선택
    pause
    exit /b 1
)

echo [1/3] 절전 모드 비활성화...
powercfg -change -standby-timeout-ac 0
powercfg -change -standby-timeout-dc 0

echo [2/3] 최대 절전 모드 비활성화...
powercfg -change -hibernate-timeout-ac 0
powercfg -change -hibernate-timeout-dc 0

echo [3/3] 화면 끄기 시간 설정 (10분 후)...
powercfg -change -monitor-timeout-ac 10
powercfg -change -monitor-timeout-dc 10

echo.
echo === 완료 ===
echo - 절전 모드: 사용 안 함
echo - 최대 절전 모드: 사용 안 함
echo - 화면 끄기: 10분 후
echo.
echo 컴퓨터가 계속 실행되며 센서 모듈이 정상 작동합니다.
pause
