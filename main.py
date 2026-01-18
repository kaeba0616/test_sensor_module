import time
from pathlib import Path

import requests

from serial_client import SerialClient, find_sensor_port
from camera import capture_image

PORT = find_sensor_port()
if not PORT:
    print("센서를 찾을 수 없습니다. USB 연결을 확인하세요.")
    exit(1)
BAUD = 9600
CAM_INDEX = 1

# 서버 URL (A: 토양센서, B: 환경센서)
SERVER_URL_SOIL = "http://218.38.121.112:8000/v1/iot/sensor-data-with-image"
SERVER_URL_ENV = "http://218.38.121.112:8000/v1/iot/environment-data-with-image"


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


def upload_soil_observation(soil_data: dict, image_path: str) -> dict:
    """토양 센서 데이터와 이미지를 서버에 업로드 (A 명령어)"""

    form_data = {
        "device_address": str(soil_data["address"]),
        "temp": float(soil_data["temperature"]),
        "humi": float(soil_data["humidity"]),
        "ec": float(soil_data["ec"]),
        "ph": float(soil_data["ph"]),
        "salt": float(soil_data["salt"]),
        "n": float(soil_data["n"]),
        "p": float(soil_data["p"]),
        "k": float(soil_data["k"]),
    }

    img_path = Path(image_path)

    with open(img_path, "rb") as f:
        files = {"image": (img_path.name, f, "image/jpeg")}
        r = requests.post(
            SERVER_URL_SOIL,
            data=form_data,
            files=files,
            timeout=30,
        )

    if not r.ok:
        raise RuntimeError(
            f"Upload failed: HTTP {r.status_code}\n" f"Response text: {r.text[:2000]}"
        )

    return r.json()


def upload_env_observation(env_data: dict, image_path: str) -> dict:
    """환경 센서 데이터와 이미지를 서버에 업로드 (B 명령어)"""

    form_data = {
        "device_address": str(env_data["address"]),
        "temp": float(env_data["temperature"]),
        "humi": float(env_data["humidity"]),
        "ch2o": float(env_data["ch2o"]),
        "tvoc": float(env_data["tvoc"]),
        "pm25": float(env_data["pm25"]),
        "pm10": float(env_data["pm10"]),
        "co2": float(env_data["co2"]),
    }

    img_path = Path(image_path)

    with open(img_path, "rb") as f:
        files = {"image": (img_path.name, f, "image/jpeg")}
        r = requests.post(
            SERVER_URL_ENV,
            data=form_data,
            files=files,
            timeout=30,
        )

    if not r.ok:
        raise RuntimeError(
            f"Upload failed: HTTP {r.status_code}\n" f"Response text: {r.text[:2000]}"
        )

    return r.json()


def main():
    sc = SerialClient(PORT, BAUD)
    print("Ready. Type A (토양) or B (환경) then Enter. (Ctrl+C to exit)")
    print(f"- Serial: {PORT}@{BAUD}")
    print(f"- Camera index: {CAM_INDEX}")
    print(f"- Server (A/토양): {SERVER_URL_SOIL}")
    print(f"- Server (B/환경): {SERVER_URL_ENV}")
    print()
    print("Commands:")
    print("  A - 토양 센서 데이터 (temp, humi, ec, ph, salt, n, p, k)")
    print("  B - 환경 센서 데이터 (temp, humi, ch2o, tvoc, pm25, pm10, co2)")
    print()

    try:
        while True:
            cmd = input("> ").strip().upper()

            if cmd not in ["A", "B"]:
                print("Type A (토양센서) or B (환경센서)")
                continue

            ts = int(time.time())
            device_id = "farm-01"

            # 1) 센서 요청
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

            # 3) 이미지 촬영
            img_filename = f"{device_id}_{ts}.jpg"
            img_path = capture_image(img_filename, cam_index=CAM_INDEX)
            img_abs = str(Path(img_path).resolve())

            print("\n--- IMAGE ---")
            print("file:", img_filename)
            print("saved_path:", img_path)
            print("abs_path  :", img_abs)
            print("exists?   :", Path(img_path).exists())

            # 4) 업로드
            print(f"\n--- UPLOAD ({data_type}) ---")
            try:
                if cmd == "A":
                    result = upload_soil_observation(sensor_data, img_path)
                else:  # cmd == "B"
                    result = upload_env_observation(sensor_data, img_path)

                print("✅ uploaded:", result)
                print(f"   AI Task ID: {result.get('ai_task_id')}")
                print(f"   Farm ID: {result.get('farm_id')}")
            except Exception as e:
                print("❌ upload error:", e)

            print()  # 줄바꿈

    finally:
        sc.close()
        print("[INFO] Serial closed")


if __name__ == "__main__":
    main()
