import time
from pathlib import Path

from serial_client import SerialClient
from camera import capture_image

PORT = "COM6"
BAUD = 9600
CAM_INDEX = 1


def parse_soil_csv(line: str) -> dict:
    parts = [p.strip() for p in line.split(",")]
    if len(parts) != 9:
        raise ValueError(f"Expected 9 values, got {len(parts)}: {line}")

    # ino 기준: address, temperature, huminity, ec, ph, salt, n, p, k
    address, temperature, huminity, ec, ph, salt, n, p, k = map(float, parts)
    return {
        "address": int(address),
        "temperature": temperature,
        "humidity": huminity,
        "ec": ec,
        "ph": ph,
        "salt": salt,
        "n": n,
        "p": p,
        "k": k,
        "raw": line,
    }


def main():
    sc = SerialClient(PORT, BAUD)
    print(f"[INFO] Serial: {PORT}@{BAUD}")
    print(f"[INFO] Camera index: {CAM_INDEX}")
    print("[INFO] Type A then Enter (Ctrl+C to exit)\n")

    try:
        while True:
            cmd = input("> ").strip().upper()
            if cmd != "A":
                print("[WARN] please type A\n")
                continue

            ts = int(time.time())
            device_id = "farm-01"

            # 1) 센서 요청
            sc.send("A")
            line = sc.receive()

            print("\n--- SENSOR RAW ---")
            print(line)

            if not line:
                print("[ERROR] No response\n")
                continue

            # 2) 파싱
            soil = parse_soil_csv(line)
            print("--- SENSOR PARSED ---")
            for k, v in soil.items():
                print(f"{k}: {v}")

            # 3) 사진 촬영
            filename = f"{device_id}_{ts}.jpg"
            img_path = capture_image(filename, cam_index=CAM_INDEX)
            img_abs = str(Path(img_path).resolve())

            print("\n--- IMAGE ---")
            print("file:", filename)
            print("saved_path:", img_path)
            print("abs_path  :", img_abs)
            print("exists?   :", Path(img_path).exists())
            print()

    finally:
        sc.close()
        print("[INFO] Serial closed")


if __name__ == "__main__":
    main()
