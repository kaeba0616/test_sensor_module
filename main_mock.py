"""Mock 데이터로 API 호출 테스트하는 스크립트"""

import requests
from pathlib import Path

SERVER_URL = "http://218.38.121.112:8000/v1/iot/sensor-data-with-image"
MOCK_IMAGE = "strawberry.jpg"

# Mock 토양 센서 데이터
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


def upload_observation(soil_data: dict, image_path: str) -> dict:
    """센서 데이터와 이미지를 서버에 업로드"""

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
            SERVER_URL,
            data=form_data,
            files=files,
            timeout=30,
        )

    if not r.ok:
        raise RuntimeError(
            f"Upload failed: HTTP {r.status_code}\nResponse text: {r.text[:2000]}"
        )

    return r.json()


def main():
    print("=== Mock 데이터 API 테스트 ===\n")
    print(f"Server: {SERVER_URL}")
    print(f"Image: {MOCK_IMAGE}")
    print(f"Soil data: {MOCK_SOIL_DATA}\n")

    # 이미지 파일 존재 확인
    if not Path(MOCK_IMAGE).exists():
        print(f"[ERROR] Image not found: {MOCK_IMAGE}")
        return

    print("Uploading...")
    try:
        result = upload_observation(MOCK_SOIL_DATA, MOCK_IMAGE)
        print("\n[SUCCESS] Upload completed!")
        print(f"Response: {result}")
        if "ai_task_id" in result:
            print(f"AI Task ID: {result['ai_task_id']}")
        if "farm_id" in result:
            print(f"Farm ID: {result['farm_id']}")
    except Exception as e:
        print(f"\n[ERROR] Upload failed: {e}")


if __name__ == "__main__":
    main()
