"""센서 모듈 메인 스크립트 (A: 토양, B: 환경)

API 키 인증 방식 사용 - 센서 등록 시 발급받은 API 키 필요
.env 파일에서 FARM_ID, SENSOR_API_KEY 설정 필요
"""
import time
import os
from pathlib import Path

from dotenv import load_dotenv
import requests

# .env 파일 로드
load_dotenv()

from serial_client import SerialClient, find_soil_sensor_port, find_env_sensor_port
from camera import capture_image, get_test_image

PORT_SOIL = find_soil_sensor_port()
PORT_ENV = find_env_sensor_port()

if not PORT_SOIL:
    print("토양 센서를 찾을 수 없습니다. USB 연결을 확인하세요.")
if not PORT_ENV:
    print("환경 센서를 찾을 수 없습니다. USB 연결을 확인하세요.")
if not PORT_SOIL and not PORT_ENV:
    exit(1)

BAUD_SOIL = 9600      # 토양 센서 baud rate
BAUD_ENV = 115200     # 환경 센서 baud rate
CAM_INDEX = 1
TEST_MODE = True  # 테스트 시 True (strawberry.jpg 사용), 실제 운영 시 False (카메라 사용)

# 서버 URL (통합 엔드포인트)
SERVER_URL = "http://218.38.121.112:8000/v1/iot/sensor-data"

# 환경변수에서 설정 로드 (.env 파일 또는 시스템 환경변수)
FARM_ID = os.environ.get("FARM_ID", "")
API_KEY = os.environ.get("SENSOR_API_KEY", "")


def parse_soil_csv(line: str) -> dict:
    """A 명령어 응답 파싱: 토양 센서 데이터 (9개 값)

    순서: address, temperature, humidity, ec, ph, salt, n, p, k
    """
    parts = [p.strip() for p in line.split(",")]
    if len(parts) != 9:
        raise ValueError(f"Expected 9 values, got {len(parts)}: {line}")

    # ino 기준: address, temperature, huminity, ec, ph, salt, n, p, k
    address, temperature, huminity, ec, ph, salt, n, p, k = map(float, parts)
    return {
        "address": int(address),
        "temperature": temperature,
        "humidity": huminity,  # huminity(오타)지만 의미는 humidity
        "ec": ec,
        "ph": ph,
        "salt": salt,
        "n": n,
        "p": p,
        "k": k,
        "raw": line,
    }


def parse_env_csv(line: str) -> dict:
    """B 명령어 응답 파싱: 환경 센서 데이터 (9개 값)

    순서: address, temp, hum, ch2o, tvoc, pm25, pm10, co2, 0
    단위: 온도°C, 습도%, 포름알데하드ug/m³, 휘발성환경물질ug/m³, 초미세먼지ug/m³, 미세먼지ug/m³, 이산화탄소ppm, 0
    """
    parts = [p.strip() for p in line.split(",")]
    if len(parts) != 9:
        raise ValueError(f"Expected 9 values, got {len(parts)}: {line}")

    address, temp, hum, ch2o, tvoc, pm25, pm10, co2, _ = map(float, parts)
    return {
        "address": int(address),
        "temperature": temp,
        "humidity": hum,
        "ch2o": ch2o,        # 포름알데하드 (ug/m³)
        "tvoc": tvoc,        # 휘발성유기화합물 (ug/m³)
        "pm25": pm25,        # 초미세먼지 PM2.5 (ug/m³)
        "pm10": pm10,        # 미세먼지 PM10 (ug/m³)
        "co2": co2,          # 이산화탄소 (ppm)
        "raw": line,
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
        raise RuntimeError(
            f"Upload failed: HTTP {r.status_code}\n" f"Response text: {r.text[:2000]}"
        )

    return r.json()


def main():
    sc_soil = SerialClient(PORT_SOIL, BAUD_SOIL) if PORT_SOIL else None
    sc_env = SerialClient(PORT_ENV, BAUD_ENV) if PORT_ENV else None

    print("Ready. Type A (토양) or B (환경) then Enter. (Ctrl+C to exit)")
    print(f"- 토양 센서 (A): {PORT_SOIL or '미연결'}@{BAUD_SOIL}")
    print(f"- 환경 센서 (B): {PORT_ENV or '미연결'}@{BAUD_ENV}")
    print(f"- Test mode: {TEST_MODE} {'(strawberry.jpg 사용)' if TEST_MODE else '(카메라 사용)'}")
    print(f"- Camera index: {CAM_INDEX}")
    print(f"- Server: {SERVER_URL}")
    print(f"- Farm ID: {FARM_ID or '미설정'}")
    print(f"- API Key: {API_KEY[:15]}..." if len(API_KEY) > 15 else f"- API Key: {API_KEY or '미설정'}")
    print()

    # 환경변수 확인
    if not API_KEY or not FARM_ID:
        print("[WARNING] 환경변수가 설정되지 않았습니다!")
        print(".env 파일을 생성하고 다음 값을 설정하세요:")
        print("  FARM_ID=your-farm-id")
        print("  SENSOR_API_KEY=sk_your_api_key")
        print("또는 .env.example 파일을 참고하세요.")
        print()

    print("Commands:")
    print("  A - 토양 센서 데이터 (temp, humi, ec, ph, salt, n, p, k) + 이미지 업로드")
    print("  B - 환경 센서 데이터 (temp, humi, ch2o, tvoc, pm25, pm10, co2) + 업로드")
    print()

    try:
        while True:
            cmd = input("> ").strip().upper()

            if cmd not in ["A", "B"]:
                print("Type A (토양센서) or B (환경센서)")
                continue

            # 센서 연결 확인
            if cmd == "A" and not sc_soil:
                print("[ERROR] 토양 센서가 연결되지 않았습니다.\n")
                continue
            if cmd == "B" and not sc_env:
                print("[ERROR] 환경 센서가 연결되지 않았습니다.\n")
                continue

            ts = int(time.time())
            device_id = "farm-01"

            # 1) 센서 요청 (각 센서별 포트 사용)
            sc = sc_soil if cmd == "A" else sc_env
            sc.send(cmd)
            line = sc.receive()

            print(f"\n--- SENSOR RAW ({cmd}) ---")
            print(line)

            if not line:
                print("[ERROR] No sensor response\n")
                continue

            # 2) 파싱
            try:
                if cmd == "A":
                    sensor_data = parse_soil_csv(line)
                    data_type = "토양"
                else:  # cmd == "B"
                    sensor_data = parse_env_csv(line)
                    data_type = "환경"
            except Exception as e:
                print("[ERROR] Parse failed:", e, "\n")
                continue

            print(f"--- SENSOR PARSED ({data_type}) ---")
            for k, v in sensor_data.items():
                if k != "raw":
                    print(f"{k}: {v}")

            # 3) 이미지 촬영/테스트 이미지 사용 (A 명령어만)
            img_path = None
            if cmd == "A":
                img_filename = f"{device_id}_{ts}.jpg"
                if TEST_MODE:
                    img_path = get_test_image(img_filename)
                else:
                    img_path = capture_image(img_filename, cam_index=CAM_INDEX)
                img_abs = str(Path(img_path).resolve())

                print("\n--- IMAGE ---")
                print("file:", img_filename)
                print("saved_path:", img_path)
                print("abs_path  :", img_abs)
                print("exists?   :", Path(img_path).exists())

            # 4) 업로드 (A: 이미지 포함, B: 센서 데이터만)
            print(f"\n--- UPLOAD ({data_type}) ---")
            try:
                result = upload_sensor_data(cmd, sensor_data, img_path)
                print("✅ uploaded:", result)
                if result.get('ai_task_id'):
                    print(f"   AI Task ID: {result.get('ai_task_id')}")
                print(f"   Farm ID: {result.get('farm_id')}")
                print(f"   Records Created: {result.get('records_created')}")
            except Exception as e:
                print("❌ upload error:", e)

            print()  # 줄바꿈

    finally:
        if sc_soil:
            sc_soil.close()
        if sc_env:
            sc_env.close()
        print("[INFO] Serial closed")


if __name__ == "__main__":
    main()
