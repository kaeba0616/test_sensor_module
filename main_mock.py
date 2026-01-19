"""Mock 데이터로 API 호출 테스트하는 스크립트 (A: 토양, B: 환경)

API 키 인증 방식 사용 - 센서 등록 시 발급받은 API 키 필요
"""

import requests
from pathlib import Path
import sys
import os

# 서버 URL (통합 엔드포인트)
SERVER_URL = "http://218.38.121.112:8000/v1/iot/sensor-data"
MOCK_IMAGE = "strawberry.jpg"

# API 키 설정 (환경변수 또는 직접 입력)
# 센서 등록 후 발급받은 API 키를 여기에 입력하거나 환경변수로 설정
API_KEY = os.environ.get("SENSOR_API_KEY", "sk_44373b38321d5e7f58892fb6e293a3824cd300d00edb3e225e59da7d")

# Mock 토양 센서 데이터 (A 명령어)
MOCK_SOIL_DATA = {
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
    "temperature": 24.0,      # 온도 (°C)
    "humidity": 55.0,         # 습도 (%)
    "ch2o": 0.03,             # 포름알데하드 (ug/m³)
    "tvoc": 0.15,             # 휘발성유기화합물 (ug/m³)
    "pm25": 15.0,             # 초미세먼지 PM2.5 (ug/m³)
    "pm10": 25.0,             # 미세먼지 PM10 (ug/m³)
    "co2": 450.0,             # 이산화탄소 (ppm)
}


def upload_sensor_data(command: str, sensor_data: dict, image_path: str = None, api_key: str = None) -> dict:
    """센서 데이터를 서버에 업로드 (통합 엔드포인트)

    Args:
        command: 'A' (토양센서) 또는 'B' (환경센서)
        sensor_data: 센서 데이터 딕셔너리
        image_path: 이미지 파일 경로 (선택)
        api_key: API 키 (지정하지 않으면 전역 API_KEY 사용)

    Returns:
        서버 응답 JSON
    """
    key = api_key or API_KEY

    # 헤더에 API 키 설정
    headers = {
        "X-API-Key": key
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
            f"Upload failed: HTTP {r.status_code}\nResponse text: {r.text[:2000]}"
        )

    return r.json()


def test_soil(api_key: str = None):
    """토양 센서 데이터 테스트 (A 명령어)"""
    key = api_key or API_KEY

    print("=== Mock 토양 센서 (A) API 테스트 ===\n")
    print(f"Server: {SERVER_URL}")
    print(f"API Key: {key[:15]}..." if len(key) > 15 else f"API Key: {key}")
    print(f"Image: {MOCK_IMAGE}")
    print(f"Data: {MOCK_SOIL_DATA}\n")

    if not Path(MOCK_IMAGE).exists():
        print(f"[WARNING] Image not found: {MOCK_IMAGE}")
        print("이미지 없이 센서 데이터만 전송합니다.\n")
        image_path = None
    else:
        image_path = MOCK_IMAGE

    print("Uploading...")
    try:
        result = upload_sensor_data('A', MOCK_SOIL_DATA, image_path, key)
        print("\n[SUCCESS] Upload completed!")
        print(f"Response: {result}")
        if "ai_task_id" in result and result["ai_task_id"]:
            print(f"AI Task ID: {result['ai_task_id']}")
        if "farm_id" in result:
            print(f"Farm ID: {result['farm_id']}")
        if "records_created" in result:
            print(f"Records Created: {result['records_created']}")
        return True
    except Exception as e:
        print(f"\n[ERROR] Upload failed: {e}")
        return False


def test_env(api_key: str = None):
    """환경 센서 데이터 테스트 (B 명령어)"""
    key = api_key or API_KEY

    print("=== Mock 환경 센서 (B) API 테스트 ===\n")
    print(f"Server: {SERVER_URL}")
    print(f"API Key: {key[:15]}..." if len(key) > 15 else f"API Key: {key}")
    print(f"Image: {MOCK_IMAGE}")
    print(f"Data: {MOCK_ENV_DATA}\n")

    if not Path(MOCK_IMAGE).exists():
        print(f"[WARNING] Image not found: {MOCK_IMAGE}")
        print("이미지 없이 센서 데이터만 전송합니다.\n")
        image_path = None
    else:
        image_path = MOCK_IMAGE

    print("Uploading...")
    try:
        result = upload_sensor_data('B', MOCK_ENV_DATA, image_path, key)
        print("\n[SUCCESS] Upload completed!")
        print(f"Response: {result}")
        if "ai_task_id" in result and result["ai_task_id"]:
            print(f"AI Task ID: {result['ai_task_id']}")
        if "farm_id" in result:
            print(f"Farm ID: {result['farm_id']}")
        if "records_created" in result:
            print(f"Records Created: {result['records_created']}")
        return True
    except Exception as e:
        print(f"\n[ERROR] Upload failed: {e}")
        return False


def main():
    print("=" * 50)
    print("Mock 센서 데이터 API 테스트 (API 키 인증)")
    print("=" * 50)
    print()
    print("사용법:")
    print("  python main_mock.py                  # 대화형 모드")
    print("  python main_mock.py A                # 토양 센서 테스트")
    print("  python main_mock.py B                # 환경 센서 테스트")
    print("  python main_mock.py all              # 둘 다 테스트")
    print("  python main_mock.py A <API_KEY>      # 특정 API 키로 테스트")
    print()
    print("API 키 설정 방법:")
    print("  1. 환경변수: export SENSOR_API_KEY=sk_xxx...")
    print("  2. 명령줄 인자: python main_mock.py A sk_xxx...")
    print("  3. 코드 수정: API_KEY 변수 직접 수정")
    print()

    # API 키 확인
    if API_KEY.startswith("sk_여기에"):
        print("[WARNING] API 키가 설정되지 않았습니다!")
        print("관리자 페이지에서 센서 등록 후 발급받은 API 키를 설정하세요.")
        print()

    # 명령줄 인자 처리
    if len(sys.argv) > 1:
        cmd = sys.argv[1].upper()
        api_key = sys.argv[2] if len(sys.argv) > 2 else None

        if cmd == "A":
            test_soil(api_key)
        elif cmd == "B":
            test_env(api_key)
        elif cmd == "ALL":
            print("-" * 50)
            test_soil(api_key)
            print()
            print("-" * 50)
            test_env(api_key)
        else:
            print(f"Unknown command: {cmd}")
            print("Use A, B, or ALL")
        return

    # 대화형 모드
    custom_api_key = None

    while True:
        print()
        cmd = input("테스트할 명령어 (A=토양, B=환경, K=API키설정, Q=종료): ").strip().upper()

        if cmd == "Q":
            print("종료합니다.")
            break
        elif cmd == "K":
            custom_api_key = input("API 키 입력: ").strip()
            if custom_api_key:
                print(f"API 키 설정됨: {custom_api_key[:15]}...")
            else:
                custom_api_key = None
                print("API 키 초기화됨 (기본값 사용)")
        elif cmd == "A":
            test_soil(custom_api_key)
        elif cmd == "B":
            test_env(custom_api_key)
        else:
            print("A, B, K, 또는 Q를 입력하세요.")


if __name__ == "__main__":
    main()
