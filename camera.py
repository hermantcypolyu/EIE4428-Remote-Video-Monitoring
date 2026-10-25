import atexit
import json
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from config import (CAMERA_INDEX, DEFAULT_PROFILE, DEFAULT_SENSITIVITY,
                    EVENT_DIR, EVENT_TAIL_SECONDS, PROFILES, RECORDING_DIR,
                    SCREENSHOT_DIR, SENSITIVITY)


class CameraService:
    def __init__(self):
        self.lock = threading.RLock()
        self.condition = threading.Condition(self.lock)
        self.capture = None
        self.running = False
        self.thread = None
        self.frame = None
        self.encoded = None
        self.frame_id = 0
        self.profile_name = DEFAULT_PROFILE
        self.sensitivity_name = DEFAULT_SENSITIVITY
        self.motion_enabled = True
        self.motion = False
        self.motion_since = None
        self.last_motion_at = 0.0
        self.background = None
        self.roi = None
        self.manual_writer = None
        self.manual_recording = False
        self.manual_path = None
        self.event_writer = None
        self.event_path = None
        self.event_started = None
        self.event_count = 0
        self.events = deque(maxlen=100)
        self.started_at = None
        self.fps_actual = 0.0
        self.avg_jpeg_bytes = 0.0
        self._fps_frames = 0
        self._fps_mark = time.monotonic()
        self._jpeg_samples = deque(maxlen=50)
        self.error = None
        atexit.register(self.stop)

    @property
    def profile(self):
        return PROFILES[self.profile_name]

    def start(self):
        with self.lock:
            if self.running:
                return
            backend = cv2.CAP_DSHOW if hasattr(cv2, "CAP_DSHOW") else 0
            self.capture = cv2.VideoCapture(CAMERA_INDEX, backend)
            if not self.capture.isOpened():
                self.capture = cv2.VideoCapture(CAMERA_INDEX)
            if not self.capture.isOpened():
                self.error = "Cannot open camera. Close Teams/Zoom and check camera permission."
                raise RuntimeError(self.error)
            self._apply_profile_locked()
            self.running = True
            self.started_at = time.time()
            self.error = None
            self.thread = threading.Thread(target=self._loop, daemon=True, name="camera-loop")
            self.thread.start()

    def _apply_profile_locked(self):
        p = self.profile
        if self.capture:
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, p["width"])
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, p["height"])
            self.capture.set(cv2.CAP_PROP_FPS, p["fps"])

    def stop(self):
        with self.lock:
            self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        with self.lock:
            self._close_writer("manual")
            self._close_writer("event")
            if self.capture:
                self.capture.release()
                self.capture = None

    def _new_writer(self, path: Path, frame):
        h, w = frame.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        return cv2.VideoWriter(str(path), fourcc, max(5.0, float(self.profile["fps"])), (w, h))

    def _close_writer(self, kind):
        attr = "manual_writer" if kind == "manual" else "event_writer"
        writer = getattr(self, attr)
        if writer:
            writer.release()
            setattr(self, attr, None)
        if kind == "manual":
            self.manual_recording = False

    def _motion_boxes(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        h, w = gray.shape
        x1, y1, x2, y2 = (0, 0, w, h)
        if self.roi:
            rx1, ry1, rx2, ry2 = self.roi
            x1, y1, x2, y2 = int(rx1*w), int(ry1*h), int(rx2*w), int(ry2*h)
        region = gray[y1:y2, x1:x2]
        if region.size == 0:
            self.background = None
            return []
        if self.background is None or self.background.shape != region.shape:
            self.background = region.astype("float")
            return []
        cv2.accumulateWeighted(region, self.background, 0.04)
        delta = cv2.absdiff(region, cv2.convertScaleAbs(self.background))
        cfg = SENSITIVITY[self.sensitivity_name]
        thresh = cv2.threshold(delta, cfg["threshold"], 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
        boxes = []
        for contour in contours:
            if cv2.contourArea(contour) < cfg["min_area"]:
                continue
            bx, by, bw, bh = cv2.boundingRect(contour)
            boxes.append((bx+x1, by+y1, bw, bh))
        return boxes

    def _start_event(self, clean_frame):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_name = f"event_{stamp}.jpg"
        video_name = f"event_{stamp}.mp4"
        image_path = EVENT_DIR / image_name
        video_path = EVENT_DIR / video_name
        cv2.imwrite(str(image_path), clean_frame)
        self.event_writer = self._new_writer(video_path, clean_frame)
        self.event_path = video_path
        self.event_started = time.time()
        self.event_count += 1
        self.events.appendleft({
            "id": self.event_count,
            "time": datetime.now().isoformat(timespec="seconds"),
            "snapshot": image_name,
            "recording": video_name,
        })

    def _loop(self):
        while True:
            with self.lock:
                if not self.running:
                    break
                cap = self.capture
                target_delay = 1.0 / max(1, self.profile["fps"])
            started = time.monotonic()
            ok, clean = cap.read()
            if not ok:
                with self.lock:
                    self.error = "Camera frame capture failed."
                time.sleep(0.2)
                continue
            clean = cv2.resize(clean, (self.profile["width"], self.profile["height"]))
            display = clean.copy()
            now = time.time()
            with self.lock:
                boxes = self._motion_boxes(clean) if self.motion_enabled else []
                self.motion = bool(boxes)
                if self.motion:
                    self.last_motion_at = now
                    if self.motion_since is None:
                        self.motion_since = now
                        self._start_event(clean)
                elif self.motion_since is not None and now - self.last_motion_at > EVENT_TAIL_SECONDS:
                    self.motion_since = None
                    self._close_writer("event")

                for x, y, w, h in boxes:
                    cv2.rectangle(display, (x, y), (x+w, y+h), (0, 0, 255), 2)
                if self.roi:
                    h, w = display.shape[:2]
                    x1, y1, x2, y2 = self.roi
                    cv2.rectangle(display, (int(x1*w), int(y1*h)), (int(x2*w), int(y2*h)), (255, 180, 0), 2)

                stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                status = "MOTION DETECTED" if self.motion else "MONITORING"
                color = (0, 0, 255) if self.motion else (0, 210, 0)
                cv2.rectangle(display, (0, 0), (display.shape[1], 58), (20, 20, 20), -1)
                cv2.putText(display, stamp, (12, 23), cv2.FONT_HERSHEY_SIMPLEX, .58, (255,255,255), 1, cv2.LINE_AA)
                cv2.putText(display, status, (12, 48), cv2.FONT_HERSHEY_SIMPLEX, .62, color, 2, cv2.LINE_AA)

                if self.manual_recording:
                    cv2.circle(display, (display.shape[1]-20, 19), 8, (0,0,255), -1)
                if self.manual_writer:
                    self.manual_writer.write(display)
                if self.event_writer:
                    self.event_writer.write(display)

                params = [int(cv2.IMWRITE_JPEG_QUALITY), self.profile["jpeg_quality"]]
                success, encoded = cv2.imencode(".jpg", display, params)
                if success:
                    self.frame = clean
                    self.encoded = encoded.tobytes()
                    self.frame_id += 1
                    self._jpeg_samples.append(len(self.encoded))
                    self.avg_jpeg_bytes = sum(self._jpeg_samples) / len(self._jpeg_samples)
                    self._fps_frames += 1
                    interval = time.monotonic() - self._fps_mark
                    if interval >= 1.0:
                        self.fps_actual = self._fps_frames / interval
                        self._fps_frames = 0
                        self._fps_mark = time.monotonic()
                    self.condition.notify_all()
            elapsed = time.monotonic() - started
            if elapsed < target_delay:
                time.sleep(target_delay - elapsed)

    def frames(self):
        self.start()
        last = -1
        while True:
            with self.condition:
                self.condition.wait_for(lambda: self.frame_id != last or not self.running, timeout=2)
                if not self.running:
                    break
                last = self.frame_id
                image = self.encoded
            if image:
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + image + b"\r\n"

    def snapshot(self):
        with self.lock:
            if self.frame is None:
                raise RuntimeError("No camera frame is available yet.")
            name = datetime.now().strftime("snapshot_%Y%m%d_%H%M%S.jpg")
            cv2.imwrite(str(SCREENSHOT_DIR / name), self.frame)
            return name

    def start_manual_recording(self):
        with self.lock:
            if self.frame is None:
                raise RuntimeError("No camera frame is available yet.")
            if self.manual_recording:
                return self.manual_path.name
            name = datetime.now().strftime("recording_%Y%m%d_%H%M%S.mp4")
            self.manual_path = RECORDING_DIR / name
            self.manual_writer = self._new_writer(self.manual_path, self.frame)
            self.manual_recording = True
            return name

    def stop_manual_recording(self):
        with self.lock:
            name = self.manual_path.name if self.manual_path else None
            self._close_writer("manual")
            return name

    def set_profile(self, name):
        if name not in PROFILES:
            raise ValueError("Invalid profile.")
        with self.lock:
            self.profile_name = name
            self.background = None
            self._apply_profile_locked()

    def set_sensitivity(self, name):
        if name not in SENSITIVITY:
            raise ValueError("Invalid sensitivity.")
        with self.lock:
            self.sensitivity_name = name
            self.background = None

    def set_roi(self, values):
        if values is None:
            with self.lock:
                self.roi = None
                self.background = None
            return
        if len(values) != 4 or any(v < 0 or v > 1 for v in values):
            raise ValueError("ROI values must be between 0 and 1.")
        x1, y1, x2, y2 = values
        if x1 >= x2 or y1 >= y2:
            raise ValueError("ROI must have positive width and height.")
        with self.lock:
            self.roi = tuple(values)
            self.background = None

    def metrics(self, clients=0):
        with self.lock:
            bitrate = self.avg_jpeg_bytes * self.fps_actual * 8 / 1_000_000
            return {
                "online": self.running and self.error is None,
                "error": self.error,
                "profile": self.profile_name,
                "resolution": f"{self.profile['width']}x{self.profile['height']}",
                "jpeg_quality": self.profile["jpeg_quality"],
                "fps": round(self.fps_actual, 1),
                "avg_frame_kb": round(self.avg_jpeg_bytes / 1024, 1),
                "bitrate_mbps": round(bitrate, 2),
                "motion_enabled": self.motion_enabled,
                "motion": self.motion,
                "sensitivity": self.sensitivity_name,
                "recording": self.manual_recording,
                "event_count": self.event_count,
                "clients": clients,
                "uptime_s": int(time.time() - self.started_at) if self.started_at else 0,
                "roi": self.roi,
                "events": list(self.events)[:10],
            }

camera = CameraService()
