import socket
import threading
from contextlib import contextmanager
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request, send_from_directory

from camera import camera
from config import EVENT_DIR, HOST, PORT, RECORDING_DIR, SCREENSHOT_DIR, SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY
client_lock = threading.Lock()
active_clients = 0


def local_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def api_ok(message, **data):
    return jsonify(ok=True, message=message, **data)


def api_error(error, status=400):
    return jsonify(ok=False, error=str(error)), status


@app.get("/")
def index():
    return render_template("index.html", server_url=f"http://{local_ip()}:{PORT}")


@app.get("/video_feed")
def video_feed():
    def counted_stream():
        global active_clients
        with client_lock:
            active_clients += 1
        try:
            yield from camera.frames()
        finally:
            with client_lock:
                active_clients = max(0, active_clients - 1)
    return Response(counted_stream(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.get("/api/status")
def status():
    with client_lock:
        count = active_clients
    return jsonify(camera.metrics(count))


@app.post("/api/snapshot")
def snapshot():
    try:
        return api_ok("Screenshot saved.", filename=camera.snapshot())
    except Exception as exc:
        return api_error(exc, 503)


@app.post("/api/record/start")
def record_start():
    try:
        return api_ok("Recording started.", filename=camera.start_manual_recording())
    except Exception as exc:
        return api_error(exc, 503)


@app.post("/api/record/stop")
def record_stop():
    return api_ok("Recording stopped.", filename=camera.stop_manual_recording())


@app.post("/api/profile")
def profile():
    try:
        camera.set_profile((request.get_json(silent=True) or {}).get("profile", ""))
        return api_ok("Video profile updated.")
    except Exception as exc:
        return api_error(exc)


@app.post("/api/sensitivity")
def sensitivity():
    try:
        camera.set_sensitivity((request.get_json(silent=True) or {}).get("sensitivity", ""))
        return api_ok("Motion sensitivity updated.")
    except Exception as exc:
        return api_error(exc)


@app.post("/api/motion")
def motion():
    camera.motion_enabled = bool((request.get_json(silent=True) or {}).get("enabled", True))
    if not camera.motion_enabled:
        camera.motion = False
        camera.background = None
    return api_ok("Motion detection updated.")


@app.post("/api/roi")
def roi():
    try:
        body = request.get_json(silent=True) or {}
        camera.set_roi(body.get("roi"))
        return api_ok("Detection zone updated.")
    except Exception as exc:
        return api_error(exc)


@app.get("/media/<kind>/<path:name>")
def media(kind, name):
    folders = {"screenshots": SCREENSHOT_DIR, "recordings": RECORDING_DIR, "events": EVENT_DIR}
    folder = folders.get(kind)
    if folder is None:
        return api_error("Invalid media type.", 404)
    return send_from_directory(folder, name, as_attachment=True)


@app.get("/health")
def health():
    return jsonify(ok=True, service="EIE4428 Remote Video Monitoring")


if __name__ == "__main__":
    print(f"Local dashboard: http://127.0.0.1:{PORT}")
    print(f"Remote dashboard: http://{local_ip()}:{PORT}")
    try:
        from waitress import serve
        serve(app, host=HOST, port=PORT, threads=8)
    except ImportError:
        app.run(host=HOST, port=PORT, threaded=True, debug=False)
