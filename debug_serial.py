"""환경 센서 (B) 디버그용 스크립트"""
import time
from serial_client import SerialClient, find_env_sensor_port

PORT = find_env_sensor_port()
if not PORT:
    print("환경 센서를 찾을 수 없습니다.")
    exit(1)

print(f"환경 센서 Port: {PORT}")
sc = SerialClient(PORT, 9600, timeout=5)

# 다양한 명령어 테스트
for cmd in ["B", "b", "A", "a", ""]:
    print(f"\n--- '{cmd}' 명령어 전송 ---")
    sc.send(cmd)

    print("응답 대기중...")
    for i in range(5):
        line = sc.receive()
        if line:
            print(f"  [{i}] 응답: '{line}'")
        else:
            print(f"  [{i}] (빈 응답)")
        time.sleep(0.3)

sc.close()
