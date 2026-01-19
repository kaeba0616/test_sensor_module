"""
MQTT Client for Sensor Module
Subscribes to command topics and executes callbacks
"""

import json
import logging
from typing import Callable, Optional
from datetime import datetime

import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SensorMQTTClient:
    """MQTT Client for receiving commands from server"""

    def __init__(
        self,
        broker_host: str,
        broker_port: int = 1883,
        farm_id: str = None,
        client_id: str = None
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.farm_id = farm_id
        self.client_id = client_id or f"sensor-{farm_id or 'unknown'}"
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.command_callback: Optional[Callable] = None

    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            logger.info(f"✅ MQTT 브로커 연결 성공: {self.broker_host}:{self.broker_port}")
            self.connected = True

            # Subscribe to command topic for this farm
            if self.farm_id:
                topic = f"farm/{self.farm_id}/command"
                client.subscribe(topic, qos=1)
                logger.info(f"📡 토픽 구독: {topic}")
        else:
            logger.error(f"❌ MQTT 연결 실패, 코드: {rc}")
            self.connected = False

    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        self.connected = False
        if rc != 0:
            logger.warning(f"⚠️ MQTT 연결 끊김 (예상치 못함), 코드: {rc}")
        else:
            logger.info("👋 MQTT 연결 종료")

    def on_message(self, client, userdata, msg):
        """Callback when a message is received"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())

            logger.info(f"📥 메시지 수신: {topic}")
            logger.info(f"   내용: {json.dumps(payload, ensure_ascii=False)}")

            action = payload.get("action")
            request_id = payload.get("request_id")
            farm_id = payload.get("farm_id")
            timestamp = payload.get("timestamp")

            if not action:
                logger.warning("⚠️ 'action' 필드가 없습니다")
                return

            # Call the registered callback
            if self.command_callback:
                self.command_callback(action, payload)
            else:
                logger.warning("⚠️ 명령 콜백이 등록되지 않았습니다")

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 파싱 오류: {e}")
        except Exception as e:
            logger.error(f"❌ 메시지 처리 오류: {e}")

    def on_command(self, callback: Callable[[str, dict], None]):
        """Register a callback for command messages

        Args:
            callback: Function that takes (action: str, payload: dict)
        """
        self.command_callback = callback
        logger.info("📝 명령 콜백 등록 완료")

    def connect(self):
        """Connect to MQTT broker"""
        logger.info(f"🚀 MQTT 브로커 연결 시도: {self.broker_host}:{self.broker_port}")

        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            logger.info("✅ MQTT 클라이언트 시작됨")
        except Exception as e:
            logger.error(f"❌ MQTT 연결 실패: {e}")
            raise

    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            logger.info("🛑 MQTT 연결 종료 중...")
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("✅ MQTT 연결 종료됨")

    def publish_status(self, status: str, details: dict = None):
        """Publish status message to server

        Args:
            status: Status string (e.g., "online", "collecting", "error")
            details: Additional details dictionary
        """
        if not self.client or not self.connected:
            logger.warning("⚠️ MQTT 연결되지 않음, 상태 전송 실패")
            return

        topic = f"farm/{self.farm_id}/status"
        message = {
            "status": status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "farm_id": self.farm_id,
        }
        if details:
            message["details"] = details

        try:
            payload = json.dumps(message)
            self.client.publish(topic, payload, qos=1)
            logger.info(f"📤 상태 전송: {topic} | {status}")
        except Exception as e:
            logger.error(f"❌ 상태 전송 실패: {e}")


def main():
    """Test the MQTT client"""
    import time

    # Test configuration
    BROKER_HOST = "218.38.121.112"  # Server IP
    BROKER_PORT = 1883
    FARM_ID = "16e23f55-25aa-4cad-a9a8-91ddd32613b8"  # Spot1 farm ID

    def handle_command(action: str, payload: dict):
        """Handle incoming commands"""
        print(f"\n🎯 명령 수신: {action}")
        print(f"   Payload: {payload}")

        if action == "collect_soil":
            print("   → 토양 센서 데이터 수집 시작...")
        elif action == "collect_env":
            print("   → 환경 센서 데이터 수집 시작...")
        elif action == "collect_all":
            print("   → 전체 센서 데이터 수집 시작...")
        elif action == "status":
            print("   → 상태 보고...")
        else:
            print(f"   → 알 수 없는 명령: {action}")

    # Create client and connect
    client = SensorMQTTClient(
        broker_host=BROKER_HOST,
        broker_port=BROKER_PORT,
        farm_id=FARM_ID
    )
    client.on_command(handle_command)

    try:
        client.connect()
        print("\n명령 대기 중... (Ctrl+C로 종료)")

        # Send online status
        client.publish_status("online")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n종료합니다...")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
