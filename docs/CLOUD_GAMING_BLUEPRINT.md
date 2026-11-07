# FoxVC Real Cloud Gaming Architecture Blueprint

> **Saved Specification & Implementation Roadmap**  
> Target: Self-hosted, low-latency (<25ms) Game Streaming Engine for Heavy Android/PC Games (e.g., Free Fire, GTA, Cyberpunk) across local devices.

---

## 1. System Architecture Diagram

```
+--------------------------------------------------------------+
|                    HOST DEVICE (Samsung / PC)                |
|                                                              |
|   +-------------------+          +-----------------------+   |
|   |   Real Game App   |          |  Hardware Encoder     |   |
|   |  (e.g. Free Fire) | -------> | (NVENC / Exynos Media)|   |
|   +-------------------+          +-----------------------+   |
|            ^                                 |               |
|            | Taps / Virtual Touch            | H.264/HEVC    |
|   +-------------------+                      v 60 FPS Stream |
|   | Input Injector    |          +-----------------------+   |
|   | (ADB/uinput/A11y) |          | WebRTC / RTSP Server  |   |
|   +-------------------+          +-----------------------+   |
+-------------^--------------------------------|---------------+
              | Low Latency UDP Input          | Video & Audio
              | (<5ms)                         | (<20ms)
+-------------|--------------------------------v---------------+
|             |          LOCAL WI-FI (LAN)                     |
+-------------|------------------------------------------------+
              |                                |
+-------------|--------------------------------v---------------+
|             |        CLIENT DEVICE (Old Phone / Web Browser) |
|   +-------------------+          +-----------------------+   |
|   | Virtual Controls  |          | Hardware Video Player |   |
|   | (D-pad, Fire, Aim)|          | (WebRTC / Canvas H264)|   |
|   +-------------------+          +-----------------------+   |
+--------------------------------------------------------------+
```

---

## 2. Core Components Required for Real 3D Gaming

### A. Host Video Capture & Encoding
* **Android Host (Samsung F34 5G):**
  * Android `MediaProjection` API captures screen buffer directly from GPU.
  * `MediaCodec` encodes frames in hardware via Exynos 1280 (H.264 Baseline, 60fps, 5-10 Mbps bitrate).
* **PC Host (Linux / Windows):**
  * Sunshine / NVENC / VAAPI for zero-copy GPU frame grabbing.

### B. Ultra-Low-Latency Transport (WebRTC / RTP over UDP)
* Traditional HTTP streaming (HLS/DASH) has 2-5 second delays (unplayable for action games).
* **Real Cloud Gaming uses WebRTC / UDP DataChannels**:
  * Latency: **8ms - 20ms** over 5GHz Wi-Fi.
  * Audio: Opus codec (stereo, 48kHz, 5ms frame size).
  * Video: H.264 / AV1 hardware decoded on the client.

### C. Touch & Gamepad Input Injection
* **Android Ingestion:**
  * **Method 1 (Wireless ADB):** Uses Android's internal `input tap x y` or raw event injection (`/dev/input/event*`) at 0ms delay.
  * **Method 2 (Accessibility Service):** Emulates gesture touches without needing root or USB cables.
* **Client Touch Overlay:**
  * Multi-touch virtual thumbsticks with analog dead-zone calculations.
  * Custom button mapping (Fire, Aim, Jump, Crouch, Sprint, Reload).

---

## 3. Implementation Roadmap for FoxVC Engine

### Phase 1: Local HTML5 Game Hub (Completed)
- [x] Lightweight HTTP + WebSocket game engine in `cloud_gaming/`.
- [x] 4 built-in games with touch controls, virtual joystick, and audio.
- [x] CLI command: `./foxvc cloud [port]`.

### Phase 2: Native Screen & Audio Streamer (Next Setup)
- [ ] Lightweight Go/Python WebRTC Daemon using `aiortc` + Android `scrcpy-server` bridge.
- [ ] Captures real Android display output to a WebRTC video track.
- [ ] Streams directly to any browser on the old phone without installing extra third-party apps.

### Phase 3: Hardware-Level Controller Mapping
- [ ] Dual-touch joystick (left thumb movement + right thumb aiming).
- [ ] Gyroscope forwarding from client phone to host for motion aiming.

---

## 4. Current Work Saved State
* **FoxVC Core Status:** 101/101 unit tests passing.
* **Repository:** Clean, synced with `origin/main`.
* **Cloud Gaming Server:** Ready in `cloud_gaming/server.py` and `run_cloud_server.py`.
