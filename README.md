# AETHER CORE // Advanced Biometric Telemetry System

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Computer Vision](https://img.shields.io/badge/Computer_Vision-OpenCV-5C3EE8?logo=opencv&logoColor=white)
![UI Framework](https://img.shields.io/badge/UI-NiceGUI-orange)
![License](https://img.shields.io/badge/License-MIT-green)

**AETHER CORE** is a futuristic, full-stack biometric dashboard that unifies real-time computer vision with high-frequency system telemetry. Built with a "Cyberpunk" design philosophy, it demonstrates how Python can handle concurrent media streams and heavy data visualization simultaneously in a browser-based interface.

---

## ⚡ Key Features

* **Real-Time Target Locking:** Utilizes OpenCV Haarcascades to detect user presence, rendering a dynamic "Head-Up Display" (HUD) overlay with scanner animations.
* **Asynchronous Architecture:** Powered by Python's `asyncio` to handle video processing and system monitoring (CPU/RAM/Net/Disk) on parallel threads without UI latency.
* **Reactive "Glass" UI:** Features a responsive, dark-mode interface with hardware-accelerated sparklines (Plotly) and conditional styling that reacts to camera states.
* **Surveillance Gallery:** Integrated capture system allows users to snap, timestamp, and archive high-resolution surveillance frames instantly.
* **Adaptive State Management:** The system dynamically shifts between `SEARCHING` (Red/Warning) and `LOCKED` (Cyan/Secure) modes based on biometric input.

## 🛠️ Tech Stack

* **Language:** Python 3.13
* **Vision Engine:** OpenCV (`cv2`)
* **Frontend/GUI:** NiceGUI (Vue.js wrapper for Python)
* **Telemetry:** Psutil (System Interface)
* **Visualization:** Plotly Graph Objects

## 🚀 Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/yourusername/aether-core.git](https://github.com/yourusername/aether-core.git)
    cd aether-core
    ```

2.  **Install Dependencies**
    ```bash
    pip install nicegui opencv-python psutil plotly
    ```

3.  **Run the System**
    ```bash
    python main.py
    ```
    *The dashboard will automatically launch in your default browser at http://localhost:8080*

## 🧩 System Architecture

**1. The Vision Pipeline:**
The system captures video frames at ~30 FPS. Frames are processed in a grayscale buffer to optimize detection speed. A mathematical "Scanner Line" animation is rendered frame-by-frame using coordinate geometry.

**2. The Async Heartbeat:**
Unlike traditional blocking scripts, AETHER CORE utilizes a non-blocking `update_loop`. This ensures that heavy I/O operations (like writing to the disk or fetching network packets) never interrupt the smoothness of the video feed.

## 📸 Screenshot
<img width="1360" height="768" alt="image" src="https://github.com/user-attachments/assets/39ba5ba3-f1d9-449b-8676-ccaa3c3865f1" />



## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

---
<p align="center">
  <b>Expenza Core</b> • Created by <a href="https://github.com/pushtikadia"><b>Pushti Kadia</b></a>
</p>
