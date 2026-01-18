"""시리얼 포트 테스트 스크립트 (포트 1~5, 다양한 baud rate)"""
import serial
import time

# 테스트할 포트 목록 (COM1 ~ COM6)
PORTS = [f"COM{i}" for i in range(1, 7)]

# 테스트할 baud rate
BAUD_RATES = [9600, 115200]

# 테스트할 명령어
COMMANDS = ["A", "B"]


def test_port(port, baud, timeout=3):
    """특정 포트/baud rate 조합 테스트"""
    try:
        ser = serial.Serial(port, baud, timeout=timeout)
        time.sleep(0.5)  # 포트 안정화 대기

        results = []
        for cmd in COMMANDS:
            ser.write(f"{cmd}\n".encode())
            time.sleep(0.5)
            response = ser.readline().decode(errors="ignore").strip()
            results.append((cmd, response))

        ser.close()
        return results
    except serial.SerialException as e:
        return None  # 포트 열기 실패


def main():
    print("=" * 60)
    print("시리얼 포트 테스트")
    print("=" * 60)

    for port in PORTS:
        print(f"\n[{port}]")

        for baud in BAUD_RATES:
            results = test_port(port, baud)

            if results is None:
                print(f"  {baud:6} baud: 포트 열기 실패")
            else:
                print(f"  {baud:6} baud:")
                for cmd, resp in results:
                    if resp:
                        print(f"    {cmd} -> '{resp[:50]}{'...' if len(resp) > 50 else ''}'")
                    else:
                        print(f"    {cmd} -> (응답 없음)")


if __name__ == "__main__":
    main()
