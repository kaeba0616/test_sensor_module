"""USB 시리얼 포트 상세 정보 출력"""

import serial.tools.list_ports


def list_ports():
    """연결된 시리얼 포트의 상세 정보 출력"""
    ports = serial.tools.list_ports.comports()

    if not ports:
        print("연결된 시리얼 포트가 없습니다.")
        return

    print(f"=== 연결된 시리얼 포트 ({len(ports)}개) ===\n")

    for i, port in enumerate(ports, 1):
        print(f"[{i}] {port.device}")
        print(f"    Description : {port.description}")
        print(f"    HWID        : {port.hwid}")

        # VID:PID (USB Vendor/Product ID)
        if port.vid and port.pid:
            print(f"    VID:PID     : {port.vid:04X}:{port.pid:04X}")
        else:
            print(f"    VID:PID     : N/A")

        print(f"    Serial No.  : {port.serial_number or 'N/A'}")
        print(f"    Manufacturer: {port.manufacturer or 'N/A'}")
        print(f"    Product     : {port.product or 'N/A'}")
        print()


if __name__ == "__main__":
    list_ports()
