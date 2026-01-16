# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an IoT sensor module for agricultural monitoring. It reads soil sensor data via serial connection from an ESP32C3 microcontroller, captures images using a USB camera, and uploads both to a remote server.

## Dependencies

- Python 3.x
- `opencv-python` (cv2) - camera capture
- `pyserial` - serial communication with ESP32C3
- `requests` - HTTP uploads

Install with: `pip install opencv-python pyserial requests`

## Running the Application

```bash
# Main application (with server upload)
python main.py

# Debug mode (local only, no upload)
python main_debug.py
```

Both scripts run an interactive loop. Type `A` and press Enter to trigger a sensor reading and image capture.

## Utility Scripts

```bash
# List available serial ports
python port_list.py

# List available cameras (indices 0-9)
python list_cameras.py

# Interactive camera preview with manual capture (SPACE to capture, ESC to exit)
python preview_capture.py
```

## Architecture

The system follows a simple pipeline:

1. **SerialClient** (`serial_client.py`) - Wraps pyserial for communication with ESP32C3. Sends commands and receives CSV sensor data.

2. **Camera Module** (`camera.py`) - Captures images via OpenCV. Images are saved to `data/images/`.

3. **Main Loop** (`main.py`) - Orchestrates the workflow:
   - Sends "A" command to ESP32C3
   - Parses 9-field CSV response: `address, temperature, humidity, ec, ph, salt, n, p, k`
   - Captures image with timestamp filename
   - Uploads sensor data + image to server via multipart form POST

## Configuration

Serial port and camera index are hardcoded at the top of `main.py` and `main_debug.py`:
- `PORT` - Serial port (e.g., "COM6", "COM7", "/dev/ttyUSB0")
- `CAM_INDEX` - Camera index (typically 0 or 1)
- `SERVER_URL` - API endpoint for uploads

## Data Storage

- `data/images/` - Captured images (`{device_id}_{timestamp}.jpg`)
- `data/failed/` - Failed upload data stored as JSON for retry
