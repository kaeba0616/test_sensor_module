import cv2
import time

CAM_INDEX = 1

cap = cv2.VideoCapture(CAM_INDEX)
if not cap.isOpened():
    raise RuntimeError(f"Camera open failed (index={CAM_INDEX}). Try 1 or 2.")

print("Press SPACE to capture, ESC to exit.")
while True:
    ret, frame = cap.read()
    if not ret:
        continue

    cv2.imshow("camera", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == 27:  # ESC
        break
    if key == 32:  # SPACE
        ts = int(time.time())
        filename = f"capture_{ts}.jpg"
        cv2.imwrite(filename, frame)
        print("saved:", filename)

cap.release()
cv2.destroyAllWindows()
