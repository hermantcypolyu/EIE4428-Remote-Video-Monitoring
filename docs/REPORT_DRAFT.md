# Smart Remote Video Monitoring and Event Alert System

**Subject:** EIE4428 Multimedia Communications  
**Students:** [STUDENT 1 NAME / ID], [STUDENT 2 NAME / ID]  
**Group:** [GROUP NUMBER]  
**Submission date:** 29 November 2026

> PRE-SUBMISSION NOTE: This draft accurately describes the included implementation, but the bracketed identity fields, screenshots, measured results, contribution details and references must be completed using the group's real evidence before submission.

## Abstract
This project implements a browser-based remote video monitoring system using Python, OpenCV and Flask. A video server captures frames from a webcam, processes monitoring overlays, compresses each frame as JPEG and sends an MJPEG stream over the local network. A remote user can access the live feed using a standard web browser. The system adds adjustable streaming profiles, motion detection, selectable monitoring zones, manual screenshots, manual recording, motion-triggered event recording, event history, multi-client access and real-time performance indicators. [ADD ONE SENTENCE SUMMARIZING YOUR ACTUAL TEST RESULTS.]

## 1. Introduction
The aim is to integrate multimedia capture, compression and network transmission in a usable remote monitoring system. The server must provide stable real-time viewing from a remote PC while maintaining acceptable quality and a clear interface. Beyond the basic requirement, this implementation emphasizes event-based monitoring and measurable quality/bandwidth trade-offs.

## 2. Requirements
### 2.1 Functional requirements
- Capture live video from the server laptop webcam.
- JPEG-compress and stream frames to remote standard browsers.
- Support configurable quality profiles.
- Show timestamp and monitoring status.
- Detect motion, display bounding boxes and support a Region of Interest.
- Save screenshots and manual/event recordings.
- Display recent events and performance information.

### 2.2 Non-functional requirements
- Stable operation over a 30-minute trial.
- Responsive interface on laptop and mobile browsers.
- Safe reconnection after browser refresh.
- One shared capture pipeline for concurrent clients.

## 3. System Architecture
Insert a clean figure showing:

`Webcam -> OpenCV capture -> Resize/process -> JPEG encoding -> Flask MJPEG endpoint -> Wi-Fi/LAN -> Browser dashboard`

The capture service runs in one background thread. Every connected browser reads the latest encoded frame. This avoids opening the physical webcam separately for each client.

## 4. Technology Selection
OpenCV was selected for webcam access, image processing, JPEG encoding and video writing. Flask provides HTTP routes, REST-style controls and browser delivery. MJPEG was selected because each frame can be processed independently before transmission and displayed by ordinary browsers without a custom client. Its main limitation is higher bandwidth than inter-frame video codecs, which is evaluated through the measured compressed frame size and bitrate.

## 5. Implementation
### 5.1 Capture and compression
The server reads a webcam frame, resizes it according to the selected quality profile, overlays timestamp/status information and JPEG-encodes it. JPEG quality values of 40, 65 and 85 are used for Low, Balanced and High profiles. The browser receives a multipart MJPEG response.

### 5.2 Quality profiles
- Low: 320x240, target 10 FPS, JPEG quality 40.
- Balanced: 640x480, target 15 FPS, JPEG quality 65.
- High: 1280x720, target 20 FPS, JPEG quality 85.

Actual FPS may differ because of camera and computer limitations. The interface therefore reports measured FPS rather than claiming the target value.

### 5.3 Motion detection
Frames are converted to grayscale and blurred to reduce noise. An adaptive background is updated by weighted accumulation. Absolute frame-background difference, thresholding and dilation produce candidate regions. Contours smaller than the sensitivity-dependent minimum area are ignored. A detected event creates a timestamped snapshot and video. Recording ends after motion has been absent for five seconds.

### 5.4 Region of Interest
The browser converts the user's drag selection into normalized coordinates between zero and one. The server applies motion analysis only inside that region, allowing doorways or other important areas to be monitored while ignoring irrelevant movement.

### 5.5 Recording and media management
Manual screenshots are stored in `screenshots/`; manual recordings in `recordings/`; event outputs in `event_media/`. File names include date and time. Recording writers are released on Stop or server shutdown so that files remain playable.

### 5.6 Monitoring metrics
The system reports actual FPS, moving-average JPEG frame size and estimated stream bitrate. The estimate is:

`bitrate = average JPEG bytes x actual frames per second x 8`

This estimate excludes HTTP/TCP/IP overhead and should be described as an application-payload estimate.

## 6. User Interface
[INSERT FULL DASHBOARD SCREENSHOT]

Explain the live feed, color-coded camera/motion/recording indicators, quality controls, motion controls, media buttons, server URL, event history and responsive layout.

## 7. Experimental Setup
- Server computer: [MODEL / CPU / RAM / OS]
- Client computer: [MODEL / OS / BROWSER]
- Additional client: [PHONE / BROWSER]
- Webcam: [MODEL OR BUILT-IN]
- Network: [ROUTER / WIFI BAND / APPROXIMATE DISTANCE]
- Test date and environment: [DETAILS]

## 8. Results and Discussion
Import the completed values from `TEST_RESULTS_TEMPLATE.csv` and include charts for:
1. Profile versus average JPEG size and estimated bitrate.
2. Client count versus actual FPS or observed delay.
3. Motion sensitivity versus true/false detections.

Do not invent data. Discuss why higher resolution/JPEG quality generally increases frame size and bandwidth, and whether added clients affected processing or network performance.

## 9. Stability and Error Handling
Describe the 30-minute test, reconnection test, camera-busy handling and firewall test. Report all observed failures truthfully and explain fixes.

## 10. Limitations
- MJPEG does not exploit inter-frame redundancy and can use substantial bandwidth.
- Motion detection can be affected by sudden illumination changes.
- The current prototype is intended for a trusted LAN and has no authentication or encryption.
- MP4 codec support can vary across platforms.
- Actual frame rate depends on webcam and computer capability.

## 11. Division of Effort
| Task | Student 1 contribution | Student 2 contribution | Evidence |
|---|---|---|---|
| Architecture | [TRUTHFUL DETAILS] | [TRUTHFUL DETAILS] | [COMMITS/NOTES] |
| Capture/streaming | [DETAILS] | [DETAILS] | [EVIDENCE] |
| Motion/events | [DETAILS] | [DETAILS] | [EVIDENCE] |
| Dashboard | [DETAILS] | [DETAILS] | [EVIDENCE] |
| Testing/report | [DETAILS] | [DETAILS] | [EVIDENCE] |

## 12. Conclusion
The system integrates capture, per-frame compression, network streaming and browser reception in a single monitoring platform. [ADD ACTUAL EVIDENCE: stability duration, remote clients, measured quality modes and motion-detection result.] Future work may include HTTPS authentication, WebRTC or H.264 transport, push notifications and multiple cameras.

## References
[ADD THE EXACT DOCUMENTATION, tutorials and libraries actually used, using one consistent citation style.]
