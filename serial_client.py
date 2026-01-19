import serial
import serial.tools.list_ports
import time

# 고정 COM 포트 설정
SOIL_SENSOR_PORT = "COM4"  # 토양 센서
ENV_SENSOR_PORT = "COM3"   # 환경 센서 (식물 센서)


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
        self.ser.reset_input_buffer()  # 버퍼 클리어
        self.ser.write(f"{msg}\n".encode())
        time.sleep(0.5)  # 센서 응답 준비 시간

    def receive(self, retries=3):
        """응답 수신 (처음 2번 버리고 3번째 사용)"""
        response = ""
        for i in range(retries):
            line = self.ser.readline().decode(errors="ignore").strip()
            print(f"   [DEBUG] Read #{i+1}: '{line}'")
            response = line
            if i < retries - 1:
                time.sleep(0.3)  # 다음 응답 대기
        return response

    def close(self):
        self.ser.close()
