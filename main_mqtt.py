"""MQTT 기반 센서 데이터 수집 스크립트

서버에서 MQTT 명령을 받아 센서 데이터를 수집하고 HTTP API로 전송합니다.
기존 타이머 기반 자동 수집도 병행합니다.
"""
import os
import time
import threading
from pathlib import Path
from datetime import datetime

import requests

from serial_client import SerialClient, find_soil_sensor_port, find_env_sensor_port
from camera import capture_image, get_test_image
from mqtt_client import SensorMQTTClient

# === 설정 ===
# 수집 스케줄 설정 (서버에서 MQTT로 변경 가능)
COLLECTION_START_TIME = "00:00"  # 기본값: 00:00 (24시간 수집)
COLLECTION_END_TIME = "23:59"    # 기본값: 23:59
INTERVAL_MINUTES = 240           # 기본값: 240분 (4시간)

TEST_MODE = False   # True: strawberry.jpg 사용, False: 카메라 사용
CAM_INDEX = 0

# Baud rate (둘 다 9600)
BAUD_SOIL = 9600
BAUD_ENV = 9600

# 서버 URL (통합 엔드포인트)
SERVER_URL = "http://218.38.121.112:8000/v1/iot/sensor-data"

# API 키 설정 (환경변수 또는 직접 입력)
API_KEY = os.environ.get("SENSOR_API_KEY", "sk_44373b38321d5e7f58892fb6e293a3824cd300d00edb3e225e59da7d")

# MQTT 설정
MQTT_BROKER = os.environ.get("MQTT_BROKER", "218.38.121.112")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
# Farm ID (Spot1 기본값 - 실제 환경에서는 설정 필요)
FARM_ID = os.environ.get("FARM_ID", "16e23f55-25aa-4cad-a9a8-91ddd32613b8")
# Organization ID (센서 전송 주기 구독용)
ORG_ID = os.environ.get("ORG_ID", "eae6d5a2-4ee5-4299-832b-8ca0f0f02a50")

# 스케줄 조회 API URL (IoT 디바이스용 - API Key 인증)
SCHEDULE_API_URL = "http://218.38.121.112:8000/v1/iot/schedule"


LOG_FILE = Path(__file__).parent / "sensor_log.txt"
LOG_MAX_LINES = 5000  # 로그 파일 최대 줄 수

def log(msg: str):
    """타임스탬프 포함 로그 출력 (콘솔 + 파일)"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{ts}] {msg}"
    print(log_line, flush=True)

    # 파일에도 기록
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")

        # 로그 파일 크기 관리 (5000줄 초과 시 오래된 줄 삭제)
        if LOG_FILE.exists() and LOG_FILE.stat().st_size > 500000:  # ~500KB 초과시
            lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
            if len(lines) > LOG_MAX_LINES:
                # 최근 3000줄만 유지
                LOG_FILE.write_text("\n".join(lines[-3000:]) + "\n", encoding="utf-8")
    except Exception:
        pass  # 파일 쓰기 실패 시 무시


def fetch_schedule_from_server() -> bool:
    """서버에서 현재 수집 스케줄을 가져옴

    Returns:
        True if successful, False otherwise
    """
    global COLLECTION_START_TIME, COLLECTION_END_TIME, INTERVAL_MINUTES

    log(f"📡 서버에서 수집 스케줄 조회 중...")

    try:
        headers = {"X-API-Key": API_KEY}
        response = requests.get(SCHEDULE_API_URL, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            COLLECTION_START_TIME = data.get("start_time", COLLECTION_START_TIME)
            COLLECTION_END_TIME = data.get("end_time", COLLECTION_END_TIME)
            INTERVAL_MINUTES = data.get("interval_minutes", INTERVAL_MINUTES)

            log(f"✅ 스케줄 조회 성공: {COLLECTION_START_TIME} ~ {COLLECTION_END_TIME}, {INTERVAL_MINUTES}분 간격")
            return True
        else:
            log(f"⚠️ 스케줄 조회 실패 (HTTP {response.status_code}): 기본값 사용")
            return False

    except requests.exceptions.ConnectionError:
        log(f"⚠️ 서버 연결 실패: 기본값 사용 ({COLLECTION_START_TIME}~{COLLECTION_END_TIME}, {INTERVAL_MINUTES}분)")
        return False
    except requests.exceptions.Timeout:
        log(f"⚠️ 서버 응답 시간 초과: 기본값 사용")
        return False
    except Exception as e:
        log(f"⚠️ 스케줄 조회 오류: {e}")
        return False


def parse_soil_csv(line: str) -> dict:
    """토양 센서 데이터 파싱 (9개 값)"""
    parts = [p.strip() for p in line.split(",")]
    if len(parts) != 9:
        raise ValueError(f"Expected 9 values, got {len(parts)}: {line}")

    address, temperature, humidity, ec, ph, salt, n, p, k = map(float, parts)
    return {
        "address": int(address),
        "temperature": temperature / 10,  # 센서 데이터가 10배로 들어옴
        "humidity": humidity / 10,        # 센서 데이터가 10배로 들어옴
        "ec": ec,
        "ph": ph,
        "salt": salt,
        "n": n,
        "p": p,
        "k": k,
    }


def parse_env_csv(line: str) -> dict:
    """환경 센서 데이터 파싱 (9개 값)"""
    parts = [p.strip() for p in line.split(",")]
    if len(parts) != 9:
        raise ValueError(f"Expected 9 values, got {len(parts)}: {line}")

    address, temp, hum, ch2o, tvoc, pm25, pm10, co2, _ = map(float, parts)
    return {
        "address": int(address),
        "temperature": temp,
        "humidity": hum,
        "ch2o": ch2o,
        "tvoc": tvoc,
        "pm25": pm25,
        "pm10": pm10,
        "co2": co2,
    }


def upload_sensor_data(command: str, sensor_data: dict, image_path: str = None) -> dict:
    """센서 데이터를 서버에 업로드 (통합 엔드포인트)"""
    headers = {"X-API-Key": API_KEY}

    form_data = {
        "command": command.upper(),
        "temp": float(sensor_data["temperature"]),
        "humi": float(sensor_data["humidity"]),
    }

    if command.upper() == 'A':
        form_data.update({
            "ec": float(sensor_data["ec"]),
            "ph": float(sensor_data["ph"]),
            "salt": float(sensor_data["salt"]),
            "n": float(sensor_data["n"]),
            "p": float(sensor_data["p"]),
            "k": float(sensor_data["k"]),
        })
    else:
        form_data.update({
            "ch2o": float(sensor_data["ch2o"]),
            "tvoc": float(sensor_data["tvoc"]),
            "pm25": float(sensor_data["pm25"]),
            "pm10": float(sensor_data["pm10"]),
            "co2": float(sensor_data["co2"]),
        })

    files = None
    if image_path and Path(image_path).exists():
        img_path = Path(image_path)
        f = open(img_path, "rb")
        files = {"image": (img_path.name, f, "image/jpeg")}

    try:
        r = requests.post(
            SERVER_URL,
            headers=headers,
            data=form_data,
            files=files,
            timeout=30,
        )
    finally:
        if files:
            files["image"][1].close()

    if not r.ok:
        raise RuntimeError(f"Upload failed: HTTP {r.status_code}\n{r.text[:500]}")

    return r.json()


class SensorCollector:
    """센서 데이터 수집기"""

    def __init__(self):
        self.sc_soil = None
        self.sc_env = None
        self.collecting = False
        self.lock = threading.Lock()

    def initialize(self):
        """시리얼 포트 초기화"""
        port_soil = find_soil_sensor_port()
        port_env = find_env_sensor_port()

        if port_soil:
            self.sc_soil = SerialClient(port_soil, BAUD_SOIL)
            log(f"✅ 토양 센서 연결: {port_soil}")
        else:
            log("⚠️ 토양 센서 미연결")

        if port_env:
            self.sc_env = SerialClient(port_env, BAUD_ENV)
            log(f"✅ 환경 센서 연결: {port_env}")
        else:
            log("⚠️ 환경 센서 미연결")

        return port_soil or port_env

    def close(self):
        """시리얼 포트 닫기"""
        if self.sc_soil:
            self.sc_soil.close()
        if self.sc_env:
            self.sc_env.close()
        log("시리얼 연결 종료")

    def collect_soil(self, with_image: bool = True) -> bool:
        """토양 센서 데이터 수집 및 업로드"""
        if not self.sc_soil:
            log("❌ 토양 센서가 연결되지 않았습니다")
            return False

        with self.lock:
            if self.collecting:
                log("⚠️ 이미 수집 중입니다")
                return False
            self.collecting = True

        try:
            log("🌱 토양 센서(A) 데이터 수집 시작...")
            self.sc_soil.send("A")
            line = self.sc_soil.receive()

            if not line:
                log("❌ 토양 센서 응답 없음")
                return False

            log(f"   [RAW] 센서 응답: '{line}'")
            soil_data = parse_soil_csv(line)
            log(f"   데이터: temp={soil_data['temperature']}, humidity={soil_data['humidity']}, ec={soil_data['ec']}, ph={soil_data['ph']}")

            # 이미지 촬영
            img_path = None
            if with_image:
                ts = int(time.time())
                img_filename = f"farm_{ts}.jpg"
                if TEST_MODE:
                    img_path = get_test_image(img_filename)
                else:
                    img_path = capture_image(img_filename, cam_index=CAM_INDEX)
                log(f"   이미지: {img_path}")

            # 서버 업로드
            result = upload_sensor_data('A', soil_data, img_path)
            log(f"✅ 토양 데이터 업로드 완료: records={result.get('records_created')}")
            if result.get('ai_task_id'):
                log(f"   AI 분석 시작: task_id={result.get('ai_task_id')}")
            return True

        except Exception as e:
            log(f"❌ 토양 센서 처리 실패: {e}")
            return False
        finally:
            self.collecting = False

    def collect_env(self) -> bool:
        """환경 센서 데이터 수집 및 업로드"""
        if not self.sc_env:
            log("❌ 환경 센서가 연결되지 않았습니다")
            return False

        with self.lock:
            if self.collecting:
                log("⚠️ 이미 수집 중입니다")
                return False
            self.collecting = True

        try:
            log("🌿 환경 센서(B) 데이터 수집 시작...")
            self.sc_env.send("B")
            line = self.sc_env.receive()

            if not line:
                log("❌ 환경 센서 응답 없음")
                return False

            env_data = parse_env_csv(line)
            log(f"   데이터: temp={env_data['temperature']}, humidity={env_data['humidity']}, co2={env_data['co2']}, pm25={env_data['pm25']}")

            # 서버 업로드 (이미지 없음)
            result = upload_sensor_data('B', env_data)
            log(f"✅ 환경 데이터 업로드 완료: records={result.get('records_created')}")
            return True

        except Exception as e:
            log(f"❌ 환경 센서 처리 실패: {e}")
            return False
        finally:
            self.collecting = False

    def collect_all(self) -> bool:
        """전체 센서 데이터 수집"""
        log("📡 전체 센서 데이터 수집 시작...")
        soil_ok = self.collect_soil(with_image=True)
        time.sleep(1)  # 잠시 대기
        env_ok = self.collect_env()
        return soil_ok or env_ok


def is_within_collection_window() -> bool:
    """현재 시간이 수집 시간대 내인지 확인"""
    now = datetime.now().time()
    start = datetime.strptime(COLLECTION_START_TIME, "%H:%M").time()
    end = datetime.strptime(COLLECTION_END_TIME, "%H:%M").time()

    if start <= end:
        # 일반적인 경우: 09:00 ~ 18:00
        return start <= now <= end
    else:
        # 자정을 넘기는 경우: 22:00 ~ 06:00
        return now >= start or now <= end


def main():
    global COLLECTION_START_TIME, COLLECTION_END_TIME, INTERVAL_MINUTES

    log("=" * 50)
    log("MQTT 기반 센서 데이터 수집 시작")
    log("=" * 50)
    log(f"서버: {SERVER_URL}")
    log(f"MQTT 브로커: {MQTT_BROKER}:{MQTT_PORT}")
    log(f"Farm ID: {FARM_ID}")
    log(f"Organization ID: {ORG_ID}")
    log(f"API Key: {API_KEY[:15]}...")
    log("")

    # 서버에서 현재 수집 스케줄 가져오기
    fetch_schedule_from_server()

    log(f"적용된 수집 스케줄: {COLLECTION_START_TIME} ~ {COLLECTION_END_TIME}, {INTERVAL_MINUTES}분 간격")
    log("")

    # 센서 초기화
    collector = SensorCollector()
    if not collector.initialize():
        log("❌ 연결된 센서가 없습니다")
        return

    # MQTT 명령 핸들러
    def handle_command(action: str, payload: dict):
        """MQTT 명령 처리"""
        log(f"🎯 MQTT 명령 수신: {action}")

        if action == "collect_soil":
            collector.collect_soil(with_image=True)
        elif action == "collect_env":
            collector.collect_env()
        elif action == "collect_all":
            collector.collect_all()
        elif action == "status":
            mqtt_client.publish_status("online", {
                "soil_connected": collector.sc_soil is not None,
                "env_connected": collector.sc_env is not None,
                "schedule": {
                    "start_time": COLLECTION_START_TIME,
                    "end_time": COLLECTION_END_TIME,
                    "interval_minutes": INTERVAL_MINUTES
                }
            })
        else:
            log(f"⚠️ 알 수 없는 명령: {action}")

    # 수집 스케줄 업데이트 핸들러
    def handle_schedule_update(start_time: str, end_time: str, interval_minutes: int, payload: dict):
        """서버에서 수집 스케줄 변경 시 처리"""
        global COLLECTION_START_TIME, COLLECTION_END_TIME, INTERVAL_MINUTES

        # 변경 전 값 저장
        old_start = COLLECTION_START_TIME
        old_end = COLLECTION_END_TIME
        old_interval = INTERVAL_MINUTES

        # 새 값 적용
        COLLECTION_START_TIME = start_time
        COLLECTION_END_TIME = end_time
        INTERVAL_MINUTES = interval_minutes

        # 변경 사항 확인
        time_changed = (old_start != start_time) or (old_end != end_time)
        interval_changed = old_interval != interval_minutes

        # 눈에 띄는 로그 출력
        log("")
        log("=" * 60)
        log("🔔 서버에서 수집 스케줄 변경 알림 수신")
        log("=" * 60)

        if time_changed:
            log(f"   📅 수집 시간대: {old_start} ~ {old_end}  →  {start_time} ~ {end_time}")
        else:
            log(f"   📅 수집 시간대: {start_time} ~ {end_time} (변경 없음)")

        if interval_changed:
            # 간격을 읽기 쉽게 변환
            old_label = f"{old_interval // 60}시간 {old_interval % 60}분" if old_interval >= 60 else f"{old_interval}분"
            new_label = f"{interval_minutes // 60}시간 {interval_minutes % 60}분" if interval_minutes >= 60 else f"{interval_minutes}분"
            if old_interval >= 60 and old_interval % 60 == 0:
                old_label = f"{old_interval // 60}시간"
            if interval_minutes >= 60 and interval_minutes % 60 == 0:
                new_label = f"{interval_minutes // 60}시간"
            log(f"   ⏱️  수집 간격: {old_label}  →  {new_label}")
        else:
            log(f"   ⏱️  수집 간격: {interval_minutes}분 (변경 없음)")

        log("-" * 60)
        log(f"   ✅ 변경된 설정이 즉시 적용되었습니다")
        log(f"   📡 다음 자동 수집은 현재 설정에 따라 실행됩니다")
        log("=" * 60)
        log("")

        # MQTT 상태 업데이트 발행
        mqtt_client.publish_status("schedule_updated", {
            "old_schedule": {
                "start_time": old_start,
                "end_time": old_end,
                "interval_minutes": old_interval
            },
            "new_schedule": {
                "start_time": start_time,
                "end_time": end_time,
                "interval_minutes": interval_minutes
            }
        })

    # MQTT 클라이언트 시작
    mqtt_client = SensorMQTTClient(
        broker_host=MQTT_BROKER,
        broker_port=MQTT_PORT,
        farm_id=FARM_ID,
        organization_id=ORG_ID
    )
    mqtt_client.on_command(handle_command)
    mqtt_client.on_schedule_update(handle_schedule_update)

    try:
        mqtt_client.connect()
        mqtt_client.publish_status("online", {
            "soil_connected": collector.sc_soil is not None,
            "env_connected": collector.sc_env is not None,
            "schedule": {
                "start_time": COLLECTION_START_TIME,
                "end_time": COLLECTION_END_TIME,
                "interval_minutes": INTERVAL_MINUTES
            }
        })

        log("")
        log("🟢 MQTT 명령 대기 중... (Ctrl+C로 종료)")
        log(f"   수집 스케줄: {COLLECTION_START_TIME} ~ {COLLECTION_END_TIME}")
        log(f"   수집 간격: {INTERVAL_MINUTES}분")
        log(f"   스케줄 토픽: organization/{ORG_ID}/settings/schedule")
        log("")

        # 메인 루프: 스케줄 기반 자동 수집 + MQTT 명령 대기
        last_auto_collect = time.time()
        was_in_window = is_within_collection_window()

        if was_in_window:
            log(f"   현재 수집 시간대 내입니다. 첫 수집: {INTERVAL_MINUTES}분 후")
        else:
            log(f"   현재 수집 시간대 외입니다. {COLLECTION_START_TIME}에 수집이 시작됩니다.")

        while True:
            current_time = time.time()
            in_window = is_within_collection_window()

            # 수집 시간대 진입 감지
            if in_window and not was_in_window:
                log(f"📅 수집 시간대 시작: {COLLECTION_START_TIME}")
                last_auto_collect = current_time  # 즉시 수집하지 않고 다음 간격에 수집

            # 수집 시간대 종료 감지
            if not in_window and was_in_window:
                log(f"📅 수집 시간대 종료: {COLLECTION_END_TIME}")

            was_in_window = in_window

            # 수집 시간대 내에서만 자동 수집
            if in_window:
                # 간격 체크 (분 단위)
                if current_time - last_auto_collect >= INTERVAL_MINUTES * 60:
                    log("⏰ 스케줄 기반 자동 수집 실행")
                    collector.collect_all()
                    last_auto_collect = current_time
                    log(f"   다음 수집: {INTERVAL_MINUTES}분 후")

            time.sleep(30)  # 30초마다 체크

    except KeyboardInterrupt:
        log("\n사용자에 의해 종료됨")
    finally:
        mqtt_client.publish_status("offline")
        mqtt_client.disconnect()
        collector.close()


if __name__ == "__main__":
    main()
