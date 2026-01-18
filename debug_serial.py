"""B 명령어 디버그용 스크립트"""
import time
from serial_client import SerialClient, find_sensor_port

PORT = find_sensor_port()
if not PORT:
    print("센서를 찾을 수 없습니다.")
    exit(1)

print(f"Port: {PORT}")
sc = SerialClient(PORT, 9600, timeout=5)

print("\n--- B 명령어 전송 ---")
sc.send("B")

# 여러 줄 응답 확인
print("응답 대기중 (5초)...")
for i in range(10):
    line = sc.receive()
    if line:
        print(f"  [{i}] 응답: '{line}'")
    else:
        print(f"  [{i}] (빈 응답)")
    time.sleep(0.5)

sc.close()
