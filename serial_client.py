import serial
import serial.tools.list_ports

# 토양 센서 (A 명령어)
SOIL_SENSOR_VID_PID = (0x1A86, 0x7523)
# 환경 센서 (B 명령어)
ENV_SENSOR_VID_PID = (0x303A, 0x1001)


def find_port_by_vid_pid(vid_pid):
    """특정 VID:PID로 포트 찾기"""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if port.vid and port.pid:
            if (port.vid, port.pid) == vid_pid:
                return port.device
    return None


def find_soil_sensor_port():
    """토양 센서 포트 찾기 (A 명령어용)"""
    return find_port_by_vid_pid(SOIL_SENSOR_VID_PID)


def find_env_sensor_port():
    """환경 센서 포트 찾기 (B 명령어용)"""
    return find_port_by_vid_pid(ENV_SENSOR_VID_PID)


class SerialClient:
    def __init__(self, port, baud=9600, timeout=3):
        self.ser = serial.Serial(port, baud, timeout=timeout)

    def send(self, msg):
        self.ser.write(f"{msg}\n".encode())

    def receive(self):
        return self.ser.readline().decode(errors="ignore").strip()

    def close(self):
        self.ser.close()
