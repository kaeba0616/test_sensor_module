from serial_client import SerialClient


def parse_soil_csv(line: str) -> dict:
    parts = [p.strip() for p in line.split(",")]
    if len(parts) != 9:
        raise ValueError(f"Expected 9 values, got {len(parts)}: {line}")

    address, temperature, huminity, ec, ph, salt, n, p, k = map(float, parts)
    return {
        "address": int(address),
        "temperature": temperature,
        "humidity": huminity,
        "ec": ec,
        "ph": ph,
        "salt": salt,
        "n": n,
        "p": p,
        "k": k,
        "raw": line,
    }


def main():
    sc = SerialClient("COM6", baud=9600)
    try:
        sc.send("A")  # ESP32C3에 A 전송

        line = sc.receive()
        print("raw:", line)

        data = parse_soil_csv(line)
        print("parsed:", data)

    finally:
        sc.close()


if __name__ == "__main__":
    main()
