@echo off
chcp 65001 >nul
echo === 절전 모드 완전 비활성화 (관리자 권한 필요) ===
echo.

:: 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 관리자 권한으로 실행해주세요.
    echo 이 파일을 우클릭 후 "관리자 권한으로 실행" 선택
    pause
    exit /b 1
)

echo [1/4] 절전 모드 비활성화...
powercfg -change -standby-timeout-ac 0
powercfg -change -standby-timeout-dc 0

echo [2/4] 최대 절전 모드 비활성화...
powercfg -change -hibernate-timeout-ac 0
powercfg -change -hibernate-timeout-dc 0

echo [3/4] 화면 끄기 비활성화 (항상 켜짐)...
powercfg -change -monitor-timeout-ac 0
powercfg -change -monitor-timeout-dc 0

echo [4/4] 고성능 전원 관리 옵션 활성화...
powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c

echo.
echo === 완료 ===
echo - 절전 모드: 사용 안 함
echo - 최대 절전 모드: 사용 안 함
echo - 화면 끄기: 사용 안 함 (항상 켜짐)
echo - 전원 관리: 고성능
echo.
echo 컴퓨터와 화면이 계속 켜져있습니다.
pause
