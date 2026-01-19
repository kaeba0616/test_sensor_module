"""센서 데이터 업로드 유틸리티

API 키 인증 방식 사용 - 센서 등록 시 발급받은 API 키 필요
"""
import os
from pathlib import Path

import requests

# 서버 URL (통합 엔드포인트)
SERVER_URL = "http://218.38.121.112:8000/v1/iot/sensor-data"

# API 키 설정 (환경변수 또는 직접 입력)
API_KEY = os.environ.get("SENSOR_API_KEY", "sk_44373b38321d5e7f58892fb6e293a3824cd300d00edb3e225e59da7d")


def upload_sensor_data(command: str, sensor_data: dict, image_path: str = None, api_key: str = None) -> dict:
    """센서 데이터를 서버에 업로드 (통합 엔드포인트)

    Args:
        command: 'A' (토양센서) 또는 'B' (환경센서)
        sensor_data: 센서 데이터 딕셔너리
        image_path: 이미지 파일 경로 (선택)
        api_key: API 키 (지정하지 않으면 전역 API_KEY 사용)

    Returns:
        서버 응답 JSON
    """
    key = api_key or API_KEY

    # 헤더에 API 키 설정
    headers = {
        "X-API-Key": key
    }

    # 기본 폼 데이터 (공통 필드 + 명령어)
    form_data = {
        "command": command.upper(),
        "temp": float(sensor_data["temperature"]),
        "humi": float(sensor_data["humidity"]),
    }

    # 명령어에 따라 추가 필드 설정
    if command.upper() == 'A':
        # 토양 센서 데이터
        form_data.update({
            "ec": float(sensor_data["ec"]),
            "ph": float(sensor_data["ph"]),
            "salt": float(sensor_data["salt"]),
            "n": float(sensor_data["n"]),
            "p": float(sensor_data["p"]),
            "k": float(sensor_data["k"]),
        })
    else:
        # 환경 센서 데이터
        form_data.update({
            "ch2o": float(sensor_data["ch2o"]),
            "tvoc": float(sensor_data["tvoc"]),
            "pm25": float(sensor_data["pm25"]),
            "pm10": float(sensor_data["pm10"]),
            "co2": float(sensor_data["co2"]),
        })

    # 이미지 파일 처리
    files = None
    if image_path and Path(image_path).exists():
        img_path = Path(image_path)
        f = open(img_path, "rb")
        files = {"image": (img_path.name, f, "image/jpeg")}

    try:
        r = requests.post(
            SERVER_URL,
            headers=headers,
            data=form_data,
            files=files,
            timeout=30,
        )
    finally:
        if files:
            files["image"][1].close()

    r.raise_for_status()
    return r.json()
