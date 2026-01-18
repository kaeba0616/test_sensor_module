"""Mock 데이터로 API 호출 테스트하는 스크립트 (A: 토양, B: 환경)"""

import requests
from pathlib import Path
import sys

# 서버 URL
SERVER_URL_SOIL = "http://218.38.121.112:8000/v1/iot/sensor-data-with-image"
SERVER_URL_ENV = "http://218.38.121.112:8000/v1/iot/environment-data-with-image"
MOCK_IMAGE = "strawberry.jpg"

# Mock 토양 센서 데이터 (A 명령어)
MOCK_SOIL_DATA = {
    "address": 1,
    "temperature": 25.5,
    "humidity": 65.0,
    "ec": 1.2,
    "ph": 6.8,
    "salt": 0.5,
    "n": 120.0,
    "p": 45.0,
    "k": 180.0,
}

# Mock 환경 센서 데이터 (B 명령어)
MOCK_ENV_DATA = {
    "address": 1,
    "temperature": 24.0,      # 온도 (°C)
    "humidity": 55.0,         # 습도 (%)
    "ch2o": 0.03,             # 포름알데하드 (ug/m³)
    "tvoc": 0.15,             # 휘발성유기화합물 (ug/m³)
    "pm25": 15.0,             # 초미세먼지 PM2.5 (ug/m³)
    "pm10": 25.0,             # 미세먼지 PM10 (ug/m³)
    "co2": 450.0,             # 이산화탄소 (ppm)
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
            f"Upload failed: HTTP {r.status_code}\nResponse text: {r.text[:2000]}"
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
            f"Upload failed: HTTP {r.status_code}\nResponse text: {r.text[:2000]}"
        )

    return r.json()


def test_soil():
    """토양 센서 데이터 테스트 (A 명령어)"""
    print("=== Mock 토양 센서 (A) API 테스트 ===\n")
    print(f"Server: {SERVER_URL_SOIL}")
    print(f"Image: {MOCK_IMAGE}")
    print(f"Data: {MOCK_SOIL_DATA}\n")

    if not Path(MOCK_IMAGE).exists():
        print(f"[ERROR] Image not found: {MOCK_IMAGE}")
        return False

    print("Uploading...")
    try:
        result = upload_soil_observation(MOCK_SOIL_DATA, MOCK_IMAGE)
        print("\n[SUCCESS] Upload completed!")
        print(f"Response: {result}")
        if "ai_task_id" in result:
            print(f"AI Task ID: {result['ai_task_id']}")
        if "farm_id" in result:
            print(f"Farm ID: {result['farm_id']}")
        return True
    except Exception as e:
        print(f"\n[ERROR] Upload failed: {e}")
        return False


def test_env():
    """환경 센서 데이터 테스트 (B 명령어)"""
    print("=== Mock 환경 센서 (B) API 테스트 ===\n")
    print(f"Server: {SERVER_URL_ENV}")
    print(f"Image: {MOCK_IMAGE}")
    print(f"Data: {MOCK_ENV_DATA}\n")

    if not Path(MOCK_IMAGE).exists():
        print(f"[ERROR] Image not found: {MOCK_IMAGE}")
        return False

    print("Uploading...")
    try:
        result = upload_env_observation(MOCK_ENV_DATA, MOCK_IMAGE)
        print("\n[SUCCESS] Upload completed!")
        print(f"Response: {result}")
        if "ai_task_id" in result:
            print(f"AI Task ID: {result['ai_task_id']}")
        if "farm_id" in result:
            print(f"Farm ID: {result['farm_id']}")
        return True
    except Exception as e:
        print(f"\n[ERROR] Upload failed: {e}")
        return False


def main():
    print("=" * 50)
    print("Mock 센서 데이터 API 테스트")
    print("=" * 50)
    print()
    print("사용법:")
    print("  python main_mock.py       # 대화형 모드")
    print("  python main_mock.py A     # 토양 센서 테스트")
    print("  python main_mock.py B     # 환경 센서 테스트")
    print("  python main_mock.py all   # 둘 다 테스트")
    print()

    # 명령줄 인자 처리
    if len(sys.argv) > 1:
        cmd = sys.argv[1].upper()
        if cmd == "A":
            test_soil()
        elif cmd == "B":
            test_env()
        elif cmd == "ALL":
            print("-" * 50)
            test_soil()
            print()
            print("-" * 50)
            test_env()
        else:
            print(f"Unknown command: {cmd}")
            print("Use A, B, or ALL")
        return

    # 대화형 모드
    while True:
        print()
        cmd = input("테스트할 명령어 (A=토양, B=환경, Q=종료): ").strip().upper()

        if cmd == "Q":
            print("종료합니다.")
            break
        elif cmd == "A":
            test_soil()
        elif cmd == "B":
            test_env()
        else:
            print("A, B, 또는 Q를 입력하세요.")


if __name__ == "__main__":
    main()
