import cv2

for i in range(10):
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)  # Windows에서는 CAP_DSHOW 추천
    if cap.isOpened():
        print(f"Camera index {i}: OPENED")
        cap.release()
    else:
        print(f"Camera index {i}: not available")
