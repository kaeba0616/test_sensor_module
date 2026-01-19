import serial
import serial.tools.list_ports

# 센서 공통 VID:PID (CH340 USB-Serial)
SENSOR_VID_PID = (0x1A86, 0x7523)


def find_sensors_by_response():
    """명령어 응답으로 센서 포트 자동 구분

    같은 VID:PID를 가진 포트들에 실제 명령을 보내서
    응답으로 토양 센서와 환경 센서를 구분합니다.
    """
    # 같은 VID:PID를 가진 모든 포트 찾기
    ports = [p.device for p in serial.tools.list_ports.comports()
             if p.vid == SENSOR_VID_PID[0] and p.pid == SENSOR_VID_PID[1]]

    print(f"🔍 감지된 포트: {ports}")

    soil_port = None
    env_port = None

    for port in ports:
        try:
            ser = serial.Serial(port, 9600, timeout=2)

            # A 명령 테스트 (토양 센서)
            ser.write(b'A\n')
            response = ser.readline().decode(errors='ignore').strip()
            if response and len(response.split(',')) == 9:
                print(f"✅ 토양 센서 발견: {port}")
                soil_port = port
                ser.close()
                continue

            # B 명령 테스트 (환경 센서)
            ser.write(b'B\n')
            response = ser.readline().decode(errors='ignore').strip()
            if response and len(response.split(',')) == 9:
                print(f"✅ 환경 센서 발견: {port}")
                env_port = port

            ser.close()
        except Exception as e:
            print(f"⚠️ 포트 {port} 테스트 실패: {e}")

    return soil_port, env_port


def find_soil_sensor_port():
    """토양 센서 포트 찾기 (A 명령어용)"""
    soil, _ = find_sensors_by_response()
    return soil


def find_env_sensor_port():
    """환경 센서 포트 찾기 (B 명령어용)"""
    _, env = find_sensors_by_response()
    return env


class SerialClient:
    def __init__(self, port, baud=9600, timeout=3):
        self.ser = serial.Serial(port, baud, timeout=timeout)

    def send(self, msg):
        self.ser.write(f"{msg}\n".encode())

    def receive(self):
        return self.ser.readline().decode(errors="ignore").strip()

    def close(self):
        self.ser.close()
