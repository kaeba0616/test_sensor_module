#!/bin/bash
# 센서 모듈 자동 설치 스크립트
# 사용법: ./install.sh

set -e  # 에러 시 중단

echo "=== 센서 모듈 설치 시작 ==="

# 현재 디렉토리
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_FILE="/etc/systemd/system/sensor-module.service"

echo "설치 경로: $INSTALL_DIR"

# 1. 의존성 설치
echo ""
echo "[1/4] 의존성 설치..."
pip3 install opencv-python pyserial requests paho-mqtt

# 2. systemd 서비스 파일 생성 (경로 자동 설정)
echo ""
echo "[2/4] systemd 서비스 파일 생성..."
sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=IoT Sensor Module (MQTT)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/main_mqtt.py
Restart=always
RestartSec=10

# MQTT 및 API 설정 (필요시 수정)
Environment="MQTT_BROKER=218.38.121.112"
Environment="MQTT_PORT=1883"
Environment="FARM_ID=16e23f55-25aa-4cad-a9a8-91ddd32613b8"
Environment="SENSOR_API_KEY=sk_44373b38321d5e7f58892fb6e293a3824cd300d00edb3e225e59da7d"

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 3. 서비스 등록 및 시작
echo ""
echo "[3/4] 서비스 등록..."
sudo systemctl daemon-reload
sudo systemctl enable sensor-module
sudo systemctl start sensor-module

# 4. 상태 확인
echo ""
echo "[4/4] 서비스 상태 확인..."
sudo systemctl status sensor-module --no-pager

echo ""
echo "=== 설치 완료 ==="
echo ""
echo "유용한 명령어:"
echo "  로그 확인: journalctl -u sensor-module -f"
echo "  서비스 중지: sudo systemctl stop sensor-module"
echo "  서비스 재시작: sudo systemctl restart sensor-module"
echo "  서비스 삭제: sudo systemctl disable sensor-module && sudo rm $SERVICE_FILE"
