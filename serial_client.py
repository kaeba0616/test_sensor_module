import serial


class SerialClient:
    def __init__(self, port, baud=9600):
        self.ser = serial.Serial(port, baud, timeout=1)

    def send(self, msg):
        self.ser.write(f"{msg}\n".encode())

    def receive(self):
        return self.ser.readline().decode(errors="ignore").strip()

    def close(self):
        self.ser.close()
