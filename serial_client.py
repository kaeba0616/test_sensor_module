import serial
import serial.tools.list_ports

SENSOR_VID_PID = [
    (0x1A86, 0x7523),
    (0x303A, 0x1001),
]


def find_sensor_port():
    """VID:PID로 센서 포트 자동 감지"""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if port.vid and port.pid:
            if (port.vid, port.pid) in SENSOR_VID_PID:
                return port.device
    return None


class SerialClient:
    def __init__(self, port, baud=9600):
        self.ser = serial.Serial(port, baud, timeout=1)

    def send(self, msg):
        self.ser.write(f"{msg}\n".encode())

    def receive(self):
        return self.ser.readline().decode(errors="ignore").strip()

    def close(self):
        self.ser.close()
