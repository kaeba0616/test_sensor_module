import serial
import serial.tools.list_ports
import time

# 고정 COM 포트 설정
SOIL_SENSOR_PORT = "COM3"  # 토양 센서
ENV_SENSOR_PORT = "COM4"   # 환경 센서 (식물 센서)


def find_soil_sensor_port():
    """토양 센서 포트 (COM4)"""
    return SOIL_SENSOR_PORT


def find_env_sensor_port():
    """환경 센서 포트 (COM3)"""
    return ENV_SENSOR_PORT


class SerialClient:
    def __init__(self, port, baud=9600, timeout=5):
        self.ser = serial.Serial(port, baud, timeout=timeout)

    def send(self, msg):
        self.ser.write(f"{msg}\n".encode())

    def receive(self):
        return self.ser.readline().decode(errors="ignore").strip()

    def close(self):
        self.ser.close()
