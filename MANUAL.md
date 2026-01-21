# IoT 센서 모듈 설치 및 운영 매뉴얼

농업용 토양/식물 센서 데이터 수집 및 AI 분석 서버 업로드 시스템

---

## 목차
1. [시스템 요구사항](#시스템-요구사항)
2. [빠른 설치 (5분)](#빠른-설치-5분)
3. [상세 설치 가이드](#상세-설치-가이드)
4. [실행 방법](#실행-방법)
5. [백그라운드 서비스 설정](#백그라운드-서비스-설정)
6. [설정 변경](#설정-변경)
7. [문제 해결](#문제-해결)
8. [파일 구조](#파일-구조)

---

## 시스템 요구사항

### 하드웨어
- 미니PC (Windows 10/11)
- ESP32C3 마이크로컨트롤러
- **토양 센서** (USB 시리얼, VID:PID = 1A86:7523, 9600 baud)
- **식물/환경 센서** (USB 시리얼, VID:PID = 303A:1001, 9600 baud)
- USB 카메라 (토양 센서 이미지 촬영용)

### 소프트웨어
- Python 3.8 이상
- Git (코드 다운로드용)

### 데이터 흐름
```
[토양센서] --A명령--> [ESP32C3] --USB--> [미니PC] --HTTP--> [SaaS 서버]
[식물센서] --B명령-->                        |                    |
[카메라] -----------------------------------+                    v
                                                            [AI 분석]
```

### 센서 정보

| 센서 | 명령어 | Baud Rate | API 키 | 데이터 |
|------|--------|-----------|--------|--------|
| 토양 센서 | A | 9600 | SENSOR_API_KEY_SOIL | temp, humidity, ec, ph, salt, n, p, k + 이미지 |
| 식물 센서 | B | 9600 | SENSOR_API_KEY_PLANT | temp, humidity, ch2o, tvoc, pm25, pm10, co2 |

---

## 빠른 설치 (5분)

### 1단계: 코드 다운로드
```batch
cd %USERPROFILE%
git clone <repository-url> test_sensor_module
cd test_sensor_module
```

### 2단계: 설치 실행
```batch
install.bat
```

### 3단계: 환경변수 설정
`.env` 파일을 메모장으로 열어 수정:
```batch
notepad .env
```

**필수 설정값:**
```ini
# 농장 ID
FARM_ID=발급받은-농장-ID

# 토양 센서 API 키 (A 명령)
SENSOR_API_KEY_SOIL=sk_토양센서_API_키

# 식물 센서 API 키 (B 명령)
SENSOR_API_KEY_PLANT=sk_식물센서_API_키

# 조직 ID (스케줄 변경 알림용)
ORG_ID=조직-ID
```

### 4단계: 절전 모드 비활성화
```batch
disable_sleep.bat  (우클릭 → 관리자 권한으로 실행)
```

### 5단계: 테스트 실행
```batch
py main.py
```
- `A` 입력: 토양 센서 테스트
- `B` 입력: 식물 센서 테스트

### 6단계: 백그라운드 서비스 등록
[백그라운드 서비스 설정](#백그라운드-서비스-설정) 참고

---

## 상세 설치 가이드

### Python 설치 (없는 경우)
1. https://www.python.org/downloads/ 접속
2. Python 3.11 이상 다운로드
3. 설치 시 **"Add Python to PATH"** 체크 필수
4. 설치 확인:
   ```batch
   py --version
   ```

### Git 설치 (없는 경우)
1. https://git-scm.com/download/win 접속
2. 다운로드 및 설치
3. 설치 확인:
   ```batch
   git --version
   ```

### 의존성 수동 설치
`install.bat`이 실패한 경우:
```batch
py -m pip install opencv-python pyserial requests paho-mqtt python-dotenv
```

---

## 실행 방법

### 수동 실행 (테스트/디버깅)
```batch
cd %USERPROFILE%\test_sensor_module
py main.py
```

명령어:
| 입력 | 동작 |
|------|------|
| `A` | 토양 센서 데이터 수집 + 이미지 + 서버 업로드 (AI 분석) |
| `B` | 식물 센서 데이터 수집 + 서버 업로드 |
| `Ctrl+C` | 종료 |

### MQTT 기반 실행 (권장)
```batch
py main_mqtt.py
```
- 서버에서 설정한 스케줄에 따라 자동 수집
- MQTT로 서버에서 수집 명령 수신 가능
- 수집 간격/시간대 변경 시 자동 적용

---

## 백그라운드 서비스 설정

컴퓨터가 켜져있는 동안 자동으로 센서 데이터를 수집하려면 Windows 서비스로 등록합니다.

### 방법 1: NSSM 서비스 (권장)

#### 1. NSSM 다운로드
1. https://nssm.cc/download 접속
2. `nssm-2.24.zip` 다운로드
3. 압축 해제
4. `win64\nssm.exe`를 `test_sensor_module` 폴더에 복사

#### 2. 서비스 설치
```batch
install_service.bat  (우클릭 → 관리자 권한으로 실행)
```

#### 3. 서비스 관리
```batch
:: 상태 확인
nssm status SensorModule

:: 로그 확인
type logs\service.log
type sensor_log.txt

:: 중지
nssm stop SensorModule

:: 시작
nssm start SensorModule

:: 재시작
nssm restart SensorModule

:: 완전 제거
uninstall_service.bat  (관리자 권한)
```

### 방법 2: 시작 프로그램 등록 (간단)

```batch
add_to_startup.bat
```
- Windows 시작 시 자동 실행
- 백그라운드 창으로 실행됨

### 방법 3: 수동 백그라운드 실행

```batch
start_background.bat
```
- 최소화된 창으로 실행
- 작업 관리자에서 python 프로세스 종료로 중지

---

## 설정 변경

### 환경변수 (.env 파일)

```ini
# ========================================
# 필수 설정
# ========================================

# 농장 ID (관리자 페이지에서 확인)
FARM_ID=your-farm-id-here

# 토양 센서 API 키 (A 명령 - 토양 데이터 + 이미지 업로드)
SENSOR_API_KEY_SOIL=sk_your_soil_api_key_here

# 식물/환경 센서 API 키 (B 명령 - 환경 데이터 업로드)
SENSOR_API_KEY_PLANT=sk_your_plant_api_key_here

# ========================================
# MQTT 설정
# ========================================

# MQTT 브로커 주소
MQTT_BROKER=218.38.121.112

# MQTT 포트
MQTT_PORT=1883

# 조직 ID (스케줄 변경 알림 수신용)
ORG_ID=your-organization-id-here
```

### main_mqtt.py 설정

```python
# 테스트 모드 (카메라 없이 테스트)
TEST_MODE = False    # True: strawberry.jpg 사용, False: 실제 카메라

# 카메라 인덱스
CAM_INDEX = 0        # 0, 1, 2... 사용 가능한 카메라 번호

# Baud rate (센서에 맞게 설정)
BAUD_SOIL = 9600
BAUD_ENV = 9600
```

---

## 문제 해결

### 센서 연결 안 될 때

#### 1단계: USB 연결 확인
장치 관리자에서 COM 포트 확인:
1. `Win + X` → 장치 관리자
2. "포트 (COM & LPT)" 확장
3. 센서 포트 확인 (예: COM4, COM5)

#### 2단계: 포트 인식 확인
```batch
py port_list.py
```

정상 출력:
```
[1] COM4
    VID:PID: 1A86:7523  # 토양 센서
[2] COM5
    VID:PID: 303A:1001  # 식물 센서
```

#### 3단계: 드라이버 설치
CH340/CH341 드라이버 필요 시:
- https://www.wch.cn/download/CH341SER_EXE.html

#### 4단계: VID:PID가 다른 경우
`serial_client.py` 수정:
```python
SOIL_SENSOR_VID_PID = (0x1A86, 0x7523)  # 토양 센서
ENV_SENSOR_VID_PID = (0x303A, 0x1001)   # 식물 센서
```

### 센서 응답 없음
```batch
py test_ports.py
```
- 각 COM 포트별로 9600, 115200 baud rate 테스트
- 응답 오는 포트/baud rate 조합 확인

### API 키 오류
```
SENSOR_API_KEY_SOIL 환경변수가 설정되지 않았습니다
SENSOR_API_KEY_PLANT 환경변수가 설정되지 않았습니다
```
→ `.env` 파일에 API 키가 올바르게 설정되었는지 확인

### Python 모듈 에러
```batch
py -m pip install --upgrade opencv-python pyserial requests paho-mqtt python-dotenv
```

### 서비스 로그 확인
```batch
:: NSSM 서비스 로그
type logs\service.log
type logs\error.log

:: 프로그램 내부 로그
type sensor_log.txt
```

### 절전 모드로 멈춤
```batch
disable_sleep.bat  (관리자 권한)
```

---

## 파일 구조

```
test_sensor_module/
├── main.py              # 수동 실행 (테스트용)
├── main_mqtt.py         # MQTT 기반 실행 (권장, 메인)
├── main_auto.py         # 타이머 기반 자동 실행
│
├── install.bat          # 의존성 설치 + .env 생성
├── install_service.bat  # Windows 서비스 등록
├── uninstall_service.bat# Windows 서비스 제거
├── start_background.bat # 백그라운드 실행
├── add_to_startup.bat   # 시작 프로그램 등록
├── disable_sleep.bat    # 절전 모드 비활성화
│
├── .env                 # 환경변수 (비공개, git 제외)
├── .env.example         # 환경변수 예시
│
├── serial_client.py     # 시리얼 통신 모듈
├── mqtt_client.py       # MQTT 클라이언트
├── camera.py            # 카메라 모듈
├── strawberry.jpg       # 테스트 이미지
│
├── port_list.py         # 포트 목록 확인
├── test_ports.py        # 포트 통신 테스트
├── list_cameras.py      # 카메라 목록 확인
│
├── nssm.exe             # Windows 서비스 관리자 (다운로드 필요)
├── sensor_log.txt       # 프로그램 로그
├── logs/                # 서비스 로그
│   ├── service.log
│   └── error.log
│
└── data/
    └── images/          # 캡처된 이미지
```

---

## MQTT 기능

### 서버에서 수신하는 명령
- `collect_soil`: 토양 센서 데이터 수집
- `collect_env`: 식물 센서 데이터 수집
- `collect_all`: 전체 센서 데이터 수집
- `status`: 현재 상태 보고

### 스케줄 자동 변경
서버에서 수집 스케줄 변경 시 MQTT로 알림 수신:
- 토픽: `organization/{ORG_ID}/settings/schedule`
- 수집 시간대, 간격 자동 업데이트

---

## 지원

문제 발생 시 로그 파일과 함께 문의:
```batch
type logs\service.log > debug_log.txt
type logs\error.log >> debug_log.txt
type sensor_log.txt >> debug_log.txt
py port_list.py >> debug_log.txt
```
