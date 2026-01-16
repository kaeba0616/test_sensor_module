import time
from pathlib import Path

import requests

from serial_client import SerialClient
from camera import capture_image

PORT = "COM7"
BAUD = 9600
CAM_INDEX = 1

SERVER_URL = "http://218.38.121.112:8000/v1/iot/sensor-data-with-image"


def parse_soil_csv(line: str) -> dict:
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


def upload_observation(soil_data: dict, image_path: str) -> dict:
    """센서 데이터와 이미지를 서버에 업로드 (서버 스펙: form-data + image)"""

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
            data=form_data,  # ✅ meta가 아니라 form field로 보냄
            files=files,
            timeout=30,
        )

    # 실패 시 본문 출력(서버가 500만 주는 경우에도 확인용)
    if not r.ok:
        raise RuntimeError(
            f"Upload failed: HTTP {r.status_code}\n" f"Response text: {r.text[:2000]}"
        )

    # 서버가 JSON을 준다고 했으니 json() 파싱
    return r.json()


def main():
    sc = SerialClient(PORT, BAUD)
    print("Ready. Type A then Enter. (Ctrl+C to exit)")
    print(f"- Serial: {PORT}@{BAUD}")
    print(f"- Camera index: {CAM_INDEX}")
    print(f"- Server: {SERVER_URL}")

    try:
        while True:
            cmd = input("> ").strip().upper()
            if cmd != "A":
                print("Type only A for now.")
                continue

            ts = int(time.time())
            device_id = "farm-01"

            # 1) 센서 요청
            sc.send("A")
            line = sc.receive()

            print("\n--- SENSOR RAW ---")
            print(line)

            if not line:
                print("[ERROR] No sensor response\n")
                continue

            # 2) 파싱
            try:
                soil = parse_soil_csv(line)
            except Exception as e:
                print("[ERROR] Parse failed:", e, "\n")
                continue

            print("--- SENSOR PARSED ---")
            for k, v in soil.items():
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

            # 4) 업로드 (서버 스펙대로)
            print("\n--- UPLOAD ---")
            try:
                result = upload_observation(soil, img_path)
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
