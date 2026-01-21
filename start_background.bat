@echo off
chcp 65001 >nul
echo 센서 모듈 백그라운드 실행 시작...
cd /d %~dp0
start /min "" py main_mqtt.py
echo 백그라운드에서 실행 중입니다.
echo 종료하려면 작업 관리자에서 python 프로세스를 종료하세요.
