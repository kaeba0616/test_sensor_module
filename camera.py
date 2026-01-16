from pathlib import Path
import time
import cv2

IMAGE_DIR = Path("data/images")
IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def capture_image(filename: str, cam_index: int = 1, warmup_frames: int = 5) -> str:
    cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError(
            f"Camera open failed (index={cam_index}). Close apps using camera and try again."
        )

    # warmup
    for _ in range(warmup_frames):
        cap.read()
        time.sleep(0.02)

    ret, frame = cap.read()
    cap.release()
    if not ret or frame is None:
        raise RuntimeError("Camera capture failed")

    path = IMAGE_DIR / filename
    ok = cv2.imwrite(str(path), frame)
    if not ok:
        raise RuntimeError(f"Failed to write image: {path}")

    return str(path)
