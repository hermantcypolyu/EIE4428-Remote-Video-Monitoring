from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SCREENSHOT_DIR = BASE_DIR / "screenshots"
RECORDING_DIR = BASE_DIR / "recordings"
EVENT_DIR = BASE_DIR / "event_media"
for folder in (SCREENSHOT_DIR, RECORDING_DIR, EVENT_DIR):
    folder.mkdir(exist_ok=True)

CAMERA_INDEX = 0
HOST = "0.0.0.0"
PORT = 5001
SECRET_KEY = "eie4428-local-demo-key"
PROFILES = {
    "low": {"width": 320, "height": 240, "fps": 10, "jpeg_quality": 40},
    "balanced": {"width": 640, "height": 480, "fps": 15, "jpeg_quality": 65},
    "high": {"width": 1280, "height": 720, "fps": 20, "jpeg_quality": 85},
}
DEFAULT_PROFILE = "balanced"
DEFAULT_SENSITIVITY = "medium"
SENSITIVITY = {
    "low": {"threshold": 35, "min_area": 3500},
    "medium": {"threshold": 25, "min_area": 1800},
    "high": {"threshold": 16, "min_area": 700},
}
EVENT_TAIL_SECONDS = 5
