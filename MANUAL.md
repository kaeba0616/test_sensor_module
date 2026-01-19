# IoT 센서 모듈 매뉴얼

농업용 토양/환경 센서 데이터 수집 및 AI 분석 서버 업로드 시스템

---

## 목차
1. [시스템 구성](#시스템-구성)
2. [빠른 설치](#빠른-설치)
3. [수동 실행](#수동-실행)
4. [자동 실행 설정](#자동-실행-설정)
5. [설정 변경](#설정-변경)
6. [문제 해결](#문제-해결)
7. [유틸리티](#유틸리티)

---

## 시스템 구성

### 하드웨어
- 미니PC (Linux)
- ESP32C3 마이크로컨트롤러
- 토양 센서 (USB 시리얼, VID:PID = 1A86:7523)
- 환경 센서 (USB 시리얼, VID:PID = 303A:1001)
- USB 카메라 (선택사항)

### 데이터 흐름
```
[토양센서] --9600baud--> [ESP32C3] --USB--> [미니PC] --HTTP--> [SaaS 서버]
[환경센서] --115200baud-->                      |
[카메라] ----------------------------------------+
```

### 센서 명령어
| 명령어 | 센서 | 용도 | 서버 업로드 |
|--------|------|------|-------------|
| A | 토양 센서 | AI 분석 | O (이미지 포함) |
| B | 환경 센서 | 모니터링 | X |

---

## 빠른 설치

### 새 미니PC 설치 (자동)
```bash
# 1. 코드 다운로드
git clone <repository-url> ~/test_sensor_module
cd ~/test_sensor_module

# 2. 자동 설치 (한 줄)
./install.sh
```

설치 완료 후 4시간마다 자동으로 센서 데이터를 수집합니다.

---

## 수동 실행

### 대화형 모드 (테스트/디버깅용)
```bash
cd ~/test_sensor_module
python3 main.py
```

실행 후 `A` 또는 `B`를 입력하여 센서 데이터 수집:
- `A`: 토양 센서 + 이미지 + 서버 업로드 (AI 분석)
- `B`: 환경 센서 데이터만 표시 (모니터링)

### 디버그 모드 (서버 업로드 없음)
```bash
python3 main_debug.py
```

---

## 자동 실행 설정

### 서비스 상태 확인
```bash
sudo systemctl status sensor-module
```

### 실시간 로그 확인
```bash
journalctl -u sensor-module -f
```

### 서비스 제어
```bash
# 중지
sudo systemctl stop sensor-module

# 시작
sudo systemctl start sensor-module

# 재시작
sudo systemctl restart sensor-module

# 부팅 시 자동 시작 비활성화
sudo systemctl disable sensor-module

# 부팅 시 자동 시작 활성화
sudo systemctl enable sensor-module
```

### 서비스 완전 삭제
```bash
sudo systemctl stop sensor-module
sudo systemctl disable sensor-module
sudo rm /etc/systemd/system/sensor-module.service
sudo systemctl daemon-reload
```

---

## 설정 변경

### main_auto.py 설정 (자동 실행)
```python
INTERVAL_HOURS = 4   # 실행 간격 (시간). 4=하루6번, 6=하루4번
TEST_MODE = True     # True: 테스트 이미지 사용, False: 카메라 사용
CAM_INDEX = 1        # 카메라 인덱스 (0, 1, 2...)
```

### main.py 설정 (수동 실행)
```python
TEST_MODE = True     # True: strawberry.jpg 사용, False: 카메라 사용
CAM_INDEX = 1        # 카메라 인덱스
```

### 서버 URL 변경
`main.py` 또는 `main_auto.py`에서:
```python
SERVER_URL_SOIL = "http://서버주소:포트/v1/iot/sensor-data-with-image"
```

---

## 문제 해결

### 센서 연결 안 될 때 (단계별 확인)

#### 1단계: USB 물리적 연결 확인
```bash
# 연결된 USB 장치 목록 확인
lsusb
```
센서가 목록에 없으면 → USB 케이블 교체 또는 다른 포트에 연결

#### 2단계: 포트 인식 확인
```bash
python3 port_list.py
```

정상 출력 예시:
```
[1] COM4 (또는 /dev/ttyUSB0)
    VID:PID: 1A86:7523  # 토양 센서
[2] COM5 (또는 /dev/ttyUSB1)
    VID:PID: 303A:1001  # 환경 센서
```

포트가 안 보이면 → 3단계로

#### 3단계: 권한 문제 해결 (Linux)
```bash
# 현재 사용자에게 시리얼 포트 권한 부여
sudo usermod -a -G dialout $USER

# 재로그인 필요 (또는 재부팅)
logout
```

#### 4단계: VID:PID가 다른 경우
새 센서의 VID:PID가 기존과 다르면 `serial_client.py` 수정:
```python
# 토양 센서 VID:PID (16진수)
SOIL_SENSOR_VID_PID = (0x1A86, 0x7523)  # 여기 수정

# 환경 센서 VID:PID (16진수)
ENV_SENSOR_VID_PID = (0x303A, 0x1001)   # 여기 수정
```

VID:PID 확인 방법:
```bash
python3 port_list.py
# 출력에서 VID:PID 값 확인 (예: 1A86:7523)
```

#### 5. 드라이버 문제 (Windows)
CH340/CH341 드라이버 설치 필요:
- https://www.wch.cn/download/CH341SER_EXE.html

### 센서 응답 없음
```bash
# 포트별 통신 테스트
python3 test_ports.py
```

### 카메라가 인식되지 않음
```bash
# 사용 가능한 카메라 목록
python3 list_cameras.py

# 카메라 미리보기 (SPACE: 캡처, ESC: 종료)
python3 preview_capture.py
```

### 서비스가 시작되지 않음
```bash
# 상세 로그 확인
journalctl -u sensor-module -n 50

# 수동으로 스크립트 실행하여 에러 확인
python3 main_auto.py
```

### Python 모듈 에러
```bash
# 의존성 재설치
pip3 install opencv-python pyserial requests
```

---

## 유틸리티

| 파일 | 설명 |
|------|------|
| `port_list.py` | 연결된 시리얼 포트 상세 정보 |
| `list_cameras.py` | 사용 가능한 카메라 목록 |
| `preview_capture.py` | 카메라 미리보기 및 수동 캡처 |
| `test_ports.py` | 포트별 통신 테스트 (다양한 baud rate) |
| `debug_serial.py` | 환경 센서 디버깅 |

---

## 파일 구조

```
test_sensor_module/
├── main.py              # 수동 실행 (대화형)
├── main_auto.py         # 자동 실행 (타이머 기반)
├── main_debug.py        # 디버그 모드 (업로드 없음)
├── install.sh           # 자동 설치 스크립트
├── sensor-module.service# systemd 서비스 파일
├── serial_client.py     # 시리얼 통신 모듈
├── camera.py            # 카메라 모듈
├── strawberry.jpg       # 테스트 이미지
├── data/
│   └── images/          # 캡처된 이미지 저장
└── MANUAL.md            # 이 문서
```

---

## 지원

문제 발생 시 로그와 함께 문의:
```bash
journalctl -u sensor-module -n 100 > sensor_log.txt
```
