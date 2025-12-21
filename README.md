# AETHER SENTRY // Autonomous AI Security System

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Computer Vision](https://img.shields.io/badge/Vision-OpenCV-5C3EE8?logo=opencv&logoColor=white)
![Voice Synthesis](https://img.shields.io/badge/Voice-PyTTSx3-FF9900)
![UI Framework](https://img.shields.io/badge/UI-NiceGUI-orange)
![License](https://img.shields.io/badge/License-MIT-green)

**AETHER SENTRY** is an advanced evolution of the Aether Core system. It transforms your workstation into an active AI security terminal. Beyond simple monitoring, it now features **Motion Vector Tracking**, **Threaded Voice Synthesis**, and **Dynamic Threat Assessment**—all running asynchronously in a real-time Cyberpunk HUD.

---

## ⚡ Key Features

* **🗣️ Active Voice Sentry:** The system speaks! It utilizes a dedicated background thread to verbally greet authorized users ("Welcome back") and verbally warn of intruders ("Target Lost", "Unauthorized Motion").
* **🟢 Motion Vector Tracking:** When no face is detected, the AI switches to *Sentry Mode*, calculating pixel differences to draw military-style vector graphics around moving objects in the room.
* **⚠️ Dynamic Threat Assessment:** A real-time "Threat Bar" fluctuates between **SAFE**, **CAUTION**, and **DANGER** based on presence detection and motion intensity.
* **🚀 Asynchronous Architecture:** Powered by `asyncio` for the UI and `threading` for the Voice Engine, ensuring the camera feed never freezes even while the system is speaking or writing to disk.
* **📸 Evidence Capture:** Integrated surveillance gallery that automatically logs timestamps and snaps photos upon user triggers.

## 🛠️ Tech Stack

* **Language:** Python 3.13
* **Vision Engine:** OpenCV (`cv2`) with Motion Contours
* **Audio Engine:** PyTTSx3 (Text-to-Speech)
* **Frontend/GUI:** NiceGUI (Vue.js wrapper)
* **Telemetry:** Psutil (System Interface)
* **Visualization:** Plotly Graph Objects

## 🚀 Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/yourusername/aether-sentry.git](https://github.com/yourusername/aether-sentry.git)
    cd aether-sentry
    ```

2.  **Install Dependencies**
    *(Note: We now require `pyttsx3` for voice capabilities)*
    ```bash
    pip install nicegui opencv-python psutil plotly pyttsx3
    ```

3.  **Run the System**
    ```bash
    python main.py
    ```
    *The dashboard will automatically launch in your default browser.*

## 🧩 System Architecture

**1. The Vision Pipeline (Sentry Mode):**
The system uses differential frame analysis to detect motion. It compares the current video frame against the previous one (`cv2.absdiff`) to identify changing pixels, drawing bounding boxes and vector lines around movement.

**2. The Voice Core (Threaded Daemon):**
Text-to-Speech operations are blocking by default. Aether Sentry solves this by spawning a separate `daemon thread` that listens to a queue. This allows the main AI loop to continue processing video at 30 FPS while the voice engine speaks asynchronously.

**3. The Telemetry Heartbeat:**
A non-blocking `update_loop` gathers system vitals (CPU/RAM/Net/Disk) every 30ms, rendering them into hardware-accelerated Plotly charts without UI latency.

## 📸 Screenshots

<img width="1360" height="768" alt="image" src="https://github.com/user-attachments/assets/3b92b996-a868-40d3-9c71-44617e65af2b" />


## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

---

<p align="center">
  <b>Expenza Core</b> • Created by <a href="https://github.com/pushtikadia"><b>Pushti Kadia</b></a>
</p>

