"""센서 포트 디버깅 스크립트

USB 시리얼 포트를 스캔하고 각 포트에 명령어를 보내서
센서 응답을 확인합니다.
"""
import serial
import serial.tools.list_ports
import time

def debug_ports():
    print("=" * 60)
    print("USB 시리얼 포트 디버깅")
    print("=" * 60)

    # 1. 모든 COM 포트 나열
    print("\n[1] 감지된 모든 COM 포트:")
    all_ports = list(serial.tools.list_ports.comports())

    if not all_ports:
        print("   ❌ COM 포트가 감지되지 않았습니다!")
        return

    for p in all_ports:
        print(f"   - {p.device}")
        print(f"     VID:PID = {hex(p.vid) if p.vid else 'None'}:{hex(p.pid) if p.pid else 'None'}")
        print(f"     설명: {p.description}")
        print(f"     제조사: {p.manufacturer}")
        print()

    # 2. CH340 포트 (1A86:7523) 필터링
    print("\n[2] CH340 USB-Serial 포트 (VID:PID = 1A86:7523):")
    ch340_ports = [p.device for p in all_ports
                   if p.vid == 0x1A86 and p.pid == 0x7523]

    if not ch340_ports:
        print("   ❌ CH340 포트가 감지되지 않았습니다!")
        print("   → 센서 USB 케이블이 연결되어 있는지 확인하세요.")
        return

    for port in ch340_ports:
        print(f"   ✅ {port}")

    # 3. 각 포트에 명령어 테스트
    print("\n[3] 각 포트에 명령어 테스트:")

    for port in ch340_ports:
        print(f"\n   --- {port} 테스트 ---")
        try:
            ser = serial.Serial(port, 9600, timeout=3)
            time.sleep(0.5)  # 연결 안정화 대기

            # 버퍼 클리어
            ser.reset_input_buffer()
            ser.reset_output_buffer()

            # A 명령 테스트
            print(f"   [A 명령 전송]")
            ser.write(b'A\n')
            time.sleep(0.5)
            response_a = ser.readline().decode(errors='ignore').strip()
            print(f"   응답: '{response_a}'")
            if response_a:
                parts = response_a.split(',')
                print(f"   값 개수: {len(parts)}")
                if len(parts) == 9:
                    print(f"   ✅ 토양 센서로 판단됨!")
            else:
                print(f"   ⚠️ 응답 없음")

            time.sleep(0.5)
            ser.reset_input_buffer()

            # B 명령 테스트
            print(f"   [B 명령 전송]")
            ser.write(b'B\n')
            time.sleep(0.5)
            response_b = ser.readline().decode(errors='ignore').strip()
            print(f"   응답: '{response_b}'")
            if response_b:
                parts = response_b.split(',')
                print(f"   값 개수: {len(parts)}")
                if len(parts) == 9:
                    print(f"   ✅ 환경 센서로 판단됨!")
            else:
                print(f"   ⚠️ 응답 없음")

            ser.close()

        except serial.SerialException as e:
            print(f"   ❌ 포트 열기 실패: {e}")
        except Exception as e:
            print(f"   ❌ 오류: {e}")

    print("\n" + "=" * 60)
    print("디버깅 완료")
    print("=" * 60)


if __name__ == "__main__":
    debug_ports()
