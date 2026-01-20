"""타이머 기반 자동 실행 스크립트 (하루 3~5번)

API 키 인증 방식 사용 - 센서 등록 시 발급받은 API 키 필요
.env 파일에서 FARM_ID, SENSOR_API_KEY 설정 필요
"""
import time
import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
import requests

# .env 파일 로드
load_dotenv()

from serial_client import SerialClient, find_soil_sensor_port, find_env_sensor_port
from camera import capture_image, get_test_image

# === 설정 ===
INTERVAL_HOURS = 4  # 실행 간격 (시간). 4시간 = 하루 6번, 6시간 = 하루 4번
TEST_MODE = True    # True: strawberry.jpg 사용, False: 카메라 사용
CAM_INDEX = 1

# Baud rate
BAUD_SOIL = 9600
BAUD_ENV = 115200

# 서버 URL (통합 엔드포인트)
SERVER_URL = "http://218.38.121.112:8000/v1/iot/sensor-data"

# 환경변수에서 설정 로드 (.env 파일 또는 시스템 환경변수)
FARM_ID = os.environ.get("FARM_ID", "")
API_KEY = os.environ.get("SENSOR_API_KEY", "")


def parse_soil_csv(line: str) -> dict:
    """토양 센서 데이터 파싱 (9개 값)"""
    parts = [p.strip() for p in line.split(",")]
    if len(parts) != 9:
        raise ValueError(f"Expected 9 values, got {len(parts)}: {line}")

    address, temperature, humidity, ec, ph, salt, n, p, k = map(float, parts)
    return {
        "address": int(address),
        "temperature": temperature,
        "humidity": humidity,
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
    """센서 데이터를 서버에 업로드 (통합 엔드포인트)

    Args:
        command: 'A' (토양센서) 또는 'B' (환경센서)
        sensor_data: 센서 데이터 딕셔너리
        image_path: 이미지 파일 경로 (선택)

    Returns:
        서버 응답 JSON
    """
    # 헤더에 API 키 설정
    headers = {
        "X-API-Key": API_KEY
    }

    # 기본 폼 데이터 (공통 필드 + 명령어)
    form_data = {
        "command": command.upper(),
        "temp": float(sensor_data["temperature"]),
        "humi": float(sensor_data["humidity"]),
    }

    # 명령어에 따라 추가 필드 설정
    if command.upper() == 'A':
        # 토양 센서 데이터
        form_data.update({
            "ec": float(sensor_data["ec"]),
            "ph": float(sensor_data["ph"]),
            "salt": float(sensor_data["salt"]),
            "n": float(sensor_data["n"]),
            "p": float(sensor_data["p"]),
            "k": float(sensor_data["k"]),
        })
    else:
        # 환경 센서 데이터
        form_data.update({
            "ch2o": float(sensor_data["ch2o"]),
            "tvoc": float(sensor_data["tvoc"]),
            "pm25": float(sensor_data["pm25"]),
            "pm10": float(sensor_data["pm10"]),
            "co2": float(sensor_data["co2"]),
        })

    # 이미지 파일 처리
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


def log(msg: str):
    """타임스탬프 포함 로그 출력"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def run_cycle(sc_soil, sc_env):
    """한 사이클 실행: 토양 센서 + 환경 센서"""
    ts = int(time.time())
    device_id = "farm-01"

    # === 토양 센서 (A) - AI 분석용 ===
    if sc_soil:
        log("토양 센서(A) 데이터 수집 시작...")
        try:
            sc_soil.send("A")
            line = sc_soil.receive()

            if not line:
                log("[ERROR] 토양 센서 응답 없음")
            else:
                soil_data = parse_soil_csv(line)
                log(f"토양 데이터: temp={soil_data['temperature']}, humidity={soil_data['humidity']}, ec={soil_data['ec']}, ph={soil_data['ph']}")

                # 이미지 촬영
                img_filename = f"{device_id}_{ts}.jpg"
                if TEST_MODE:
                    img_path = get_test_image(img_filename)
                else:
                    img_path = capture_image(img_filename, cam_index=CAM_INDEX)

                # 서버 업로드
                result = upload_sensor_data('A', soil_data, img_path)
                log(f"토양 데이터 업로드 성공: AI Task ID={result.get('ai_task_id')}, Records={result.get('records_created')}")

        except Exception as e:
            log(f"[ERROR] 토양 센서 처리 실패: {e}")

    # === 환경 센서 (B) - 모니터링용 ===
    if sc_env:
        log("환경 센서(B) 데이터 수집 시작...")
        try:
            sc_env.send("B")
            line = sc_env.receive()

            if not line:
                log("[ERROR] 환경 센서 응답 없음")
            else:
                env_data = parse_env_csv(line)
                log(f"환경 데이터: temp={env_data['temperature']}, humidity={env_data['humidity']}, co2={env_data['co2']}, pm25={env_data['pm25']}")

                # 서버 업로드
                result = upload_sensor_data('B', env_data)
                log(f"환경 데이터 업로드 성공: Records={result.get('records_created')}")

        except Exception as e:
            log(f"[ERROR] 환경 센서 처리 실패: {e}")


def main():
    log("=== 센서 자동 실행 시작 ===")
    log(f"실행 간격: {INTERVAL_HOURS}시간 (하루 약 {24 // INTERVAL_HOURS}번)")
    log(f"서버: {SERVER_URL}")
    log(f"Farm ID: {FARM_ID or '미설정'}")
    log(f"API Key: {API_KEY[:15]}..." if len(API_KEY) > 15 else f"API Key: {API_KEY or '미설정'}")

    # 환경변수 확인
    if not API_KEY or not FARM_ID:
        log("[WARNING] 환경변수가 설정되지 않았습니다!")
        log(".env 파일을 생성하고 FARM_ID, SENSOR_API_KEY를 설정하세요.")
        log(".env.example 파일을 참고하세요.")

    # 포트 찾기
    port_soil = find_soil_sensor_port()
    port_env = find_env_sensor_port()

    if not port_soil and not port_env:
        log("[ERROR] 연결된 센서가 없습니다.")
        return

    log(f"토양 센서: {port_soil or '미연결'}")
    log(f"환경 센서: {port_env or '미연결'}")

    # 시리얼 클라이언트 생성
    sc_soil = SerialClient(port_soil, BAUD_SOIL) if port_soil else None
    sc_env = SerialClient(port_env, BAUD_ENV) if port_env else None

    try:
        while True:
            run_cycle(sc_soil, sc_env)
            log(f"다음 실행까지 {INTERVAL_HOURS}시간 대기...")
            time.sleep(INTERVAL_HOURS * 3600)

    except KeyboardInterrupt:
        log("사용자에 의해 종료됨")
    finally:
        if sc_soil:
            sc_soil.close()
        if sc_env:
            sc_env.close()
        log("시리얼 연결 종료")


if __name__ == "__main__":
    main()
