# EIE4428 Smart Remote Video Monitoring System

A complete pre-submission implementation for the EIE4428 mini-project. It captures a webcam, JPEG-compresses every frame, streams MJPEG to standard browsers, and adds monitoring functions.

## Included functions
- Browser-based remote live stream over LAN
- One shared camera-processing thread for multiple clients
- Low / Balanced / High quality profiles
- Timestamp, camera status, FPS, average JPEG size and estimated bitrate
- Motion detection with bounding boxes
- Adjustable motion sensitivity
- Browser-selected Region of Interest (drag on the live video)
- Manual screenshots and MP4 recording
- Automatic motion-event snapshot and recording
- Event history and media download links
- Responsive dark monitoring dashboard
- Health endpoint and clean camera shutdown

## Quick start (Windows)
1. Close Teams, Zoom and other webcam applications.
2. Double-click `run_windows.bat`.
3. Allow Python through Windows Firewall on **Private networks** when prompted.
4. On this computer, open `http://127.0.0.1:5001`.
5. On a second device connected to the same Wi-Fi, open the `Remote dashboard` URL printed in the terminal.

## macOS / Linux
```bash
./run_mac_linux.sh
```
Allow camera access when the operating system asks.

## Manual launch
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Demo flow
1. Start server and open dashboard from second laptop.
2. Move in front of camera to prove the feed is live.
3. Drag a detection zone on the feed.
4. Move inside and outside the zone to show selective detection.
5. Show auto-created event snapshot and recording.
6. Switch Low, Balanced and High profiles; explain frame-size/bitrate trade-off.
7. Connect a phone to show concurrent browser access.
8. Start and stop manual recording; take a screenshot.

## Output folders
- `screenshots/`: manual screenshots
- `recordings/`: manual recordings
- `event_media/`: automatic event images and videos

## Important pre-submission steps
Read `PRE_SUBMISSION_CHECKLIST.md`. Replace all student placeholders in `docs/REPORT_DRAFT.md`, run the real experiments, insert your own results/screenshots, and export the report as PDF. Do not submit invented test data.

## Troubleshooting
- **Camera cannot open:** close Teams/Zoom, confirm OS camera permission, or change `CAMERA_INDEX` in `config.py` to 1.
- **Port 5001 already in use:** change `PORT` in `config.py` to another value (e.g., 5002).
- **macOS port conflict:** if you see "Address already in use" on port 5000, macOS AirPlay Receiver uses it by default. The app now uses port 5001 instead.
- **Remote device cannot connect:** both devices must be on the same network; use the printed LAN IP; allow TCP port 5001 through the firewall; avoid guest Wi-Fi with client isolation.
- **MP4 does not play:** install a media player that supports `mp4v`, or change the writer codec for your platform.
- **False motion alerts:** select a smaller ROI or use Low sensitivity.
- **High profile is slow:** webcam hardware may not support 1280x720 at 20 FPS; use Balanced and record the actual measured FPS.

## Academic integrity
Understand and be able to explain every module. Add the real group members, contribution record, experimental results and references required by your class.
