import requests

SERVER_URL = "http://218.38.121.112:8000/v1/api/sensor-data"
API_KEY = "DEVICE_API_KEY"


def upload_observation(meta: dict, image_path: str):
    files = {"image": open(image_path, "rb")}

    headers = {"Authorization": f"Bearer {API_KEY}"}

    response = requests.post(
        SERVER_URL, data={"meta": meta}, files=files, headers=headers, timeout=10
    )

    response.raise_for_status()
