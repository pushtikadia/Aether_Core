import asyncio
import base64
import cv2
import psutil
import time
import threading
import queue
import pyttsx3
import numpy as np
import plotly.graph_objects as go
from collections import deque
from datetime import datetime
from nicegui import ui, app

# --- CONFIGURATION ---
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# --- VOICE CORE (THREADED) ---
# We use a separate thread so the voice doesn't freeze the camera
voice_queue = queue.Queue()

def voice_worker():
    engine = pyttsx3.init()
    engine.setProperty('rate', 160) # Speed of speech
    while True:
        text = voice_queue.get()
        if text is None: break
        try:
            engine.say(text)
            engine.runAndWait()
        except: pass
        voice_queue.task_done()

threading.Thread(target=voice_worker, daemon=True).start()

def speak(text):
    # Only queue if not full to prevent lag
    if voice_queue.qsize() < 2:
        voice_queue.put(text)

# --- STATE MANAGEMENT ---
history_len = 50
cpu_history = deque([0]*history_len, maxlen=history_len)
ram_history = deque([0]*history_len, maxlen=history_len)
net_history = deque([0]*history_len, maxlen=history_len)
logs = deque([], maxlen=8)
gallery = [] 

cap = cv2.VideoCapture(0)
last_net_bytes = psutil.net_io_counters().bytes_recv

# Global State
prev_gray = None
is_target_locked = False
scan_line_pos = 0
last_speak_time = 0
motion_detected = False

def process_frame():
    global is_target_locked, scan_line_pos, prev_gray, last_speak_time, motion_detected
    success, frame = cap.read()
    if not success: return None
    
    # 1. Flip & Pre-process
    frame = cv2.flip(frame, 1)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    height, width, _ = frame.shape
    
    # 2. Motion Detection (Military Vector Style)
    if prev_gray is None: prev_gray = gray
    diff = cv2.absdiff(prev_gray, gray)
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    motion_contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    prev_gray = gray
    
    motion_detected = False
    for c in motion_contours:
        if cv2.contourArea(c) > 500: # Ignore small movements
            motion_detected = True
            (mx, my, mw, mh) = cv2.boundingRect(c)
            # Draw "Motion Vectors" (Green Brackets)
            cv2.rectangle(frame, (mx, my), (mx+mw, my+mh), (0, 255, 0), 1)
            cv2.line(frame, (mx, my), (mx+10, my), (0, 255, 0), 2)
            cv2.line(frame, (mx, my), (mx, my+10), (0, 255, 0), 2)

    # 3. Face Detection (Target Lock)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    # 4. Logic & Voice Triggers
    now = time.time()
    if len(faces) > 0:
        if not is_target_locked and (now - last_speak_time > 5):
            speak("Target confirmed. Welcome back.")
            last_speak_time = now
        is_target_locked = True
        color = (255, 255, 0) # Cyan
    else:
        if is_target_locked and (now - last_speak_time > 5):
            speak("Target lost. Engaging Sentry Mode.")
            last_speak_time = now
        is_target_locked = False
        color = (0, 0, 255) # Red

    # 5. Scanner Animation
    scan_line_pos = (scan_line_pos + 4) % height
    cv2.line(frame, (0, scan_line_pos), (width, scan_line_pos), color, 1)
    cv2.putText(frame, 'AETHER SENTRY', (10, scan_line_pos - 5), cv2.FONT_HERSHEY_PLAIN, 1, color, 1)

    # 6. Draw HUD
    for (x, y, w, h) in faces:
        # Fancy corners
        cv2.line(frame, (x, y), (x + 20, y), color, 2)
        cv2.line(frame, (x, y), (x, y + 20), color, 2)
        cv2.line(frame, (x+w, y), (x+w-20, y), color, 2)
        cv2.line(frame, (x+w, y), (x+w, y+20), color, 2)
        cv2.line(frame, (x, y+h), (x+20, y+h), color, 2)
        cv2.line(frame, (x, y+h), (x, y+h-20), color, 2)
        cv2.line(frame, (x+w, y+h), (x+w-20, y+h), color, 2)
        cv2.line(frame, (x+w, y+h), (x+w, y+h-20), color, 2)
        
        cv2.putText(frame, 'BIOMETRIC MATCH', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    # Encode
    _, buffer = cv2.imencode('.jpg', frame)
    b64 = base64.b64encode(buffer).decode('utf-8')
    return f'data:image/jpeg;base64,{b64}'

def get_metrics():
    global last_net_bytes
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    
    curr_net = psutil.net_io_counters().bytes_recv
    net_speed = (curr_net - last_net_bytes) / 1024 / 1024 
    last_net_bytes = curr_net
    
    cpu_history.append(cpu)
    ram_history.append(ram)
    net_history.append(net_speed)
    
    return cpu, ram, net_speed, disk

@ui.page('/')
def dashboard():
    ui.colors(primary='#00f0ff', secondary='#000000', accent='#ff003c')
    
    with ui.column().classes('w-full min-h-screen bg-black text-[#00f0ff] p-2 gap-2 font-mono overflow-hidden'):
        
        # HEADER
        with ui.row().classes('w-full justify-between items-center border-b border-[#00f0ff]/30 pb-2 px-2'):
            with ui.row().classes('items-center gap-3'):
                ui.icon('security', size='28px').classes('animate-pulse text-red-500')
                ui.label('AETHER // SENTRY').classes('text-2xl font-bold tracking-[0.15em] text-white')
            
            status_badge = ui.label('SYSTEM ARMED').classes('text-xs font-bold px-3 py-1 rounded border')

        # GRID
        with ui.grid(columns=12).classes('w-full gap-4 h-[70vh]'):
            
            # LEFT (STATS)
            with ui.column().classes('col-span-3 gap-3 h-full'):
                def stat_card(title, color):
                    with ui.card().classes(f'w-full bg-black border border-{color} p-3 shadow-[0_0_10px_rgba(0,0,0,0.5)]'):
                        ui.label(title).classes(f'text-{color} text-[10px] font-bold tracking-widest')
                        chart = ui.plotly({
                            'layout': {
                                'paper_bgcolor': 'rgba(0,0,0,0)', 'plot_bgcolor': 'rgba(0,0,0,0)',
                                'margin': {'l': 0, 'r': 0, 't': 5, 'b': 0},
                                'xaxis': {'visible': False, 'fixedrange': True},
                                'yaxis': {'visible': False, 'fixedrange': True, 'range': [0, 100]},
                                'showlegend': False
                            }
                        }).classes('h-12 w-full')
                        lbl = ui.label('0').classes('text-lg font-bold absolute top-2 right-3 text-white')
                    return chart, lbl

                cpu_plot, cpu_lbl = stat_card('CORE PROCESSING', 'cyan-400')
                ram_plot, ram_lbl = stat_card('MEMORY MATRIX', 'purple-400')
                net_plot, net_lbl = stat_card('DATA STREAM', 'green-400')
                
                with ui.card().classes('w-full bg-black border border-red-500 p-3'):
                    with ui.row().classes('w-full justify-between'):
                        ui.label('THREAT LEVEL').classes('text-red-500 text-[10px] font-bold')
                        threat_lbl = ui.label('LOW').classes('text-white text-xs')
                    threat_bar = ui.linear_progress(value=0.1).classes('h-1 rounded-none text-red-500 track-color-gray-900 mt-2')

            # CENTER (VIDEO)
            with ui.card().classes('col-span-6 bg-black border-2 border-[#00f0ff] p-0 relative overflow-hidden flex items-center justify-center'):
                video_feed = ui.image().classes('w-full h-full object-cover opacity-90')
                # Holographic Grid Overlay
                ui.element('div').classes('absolute inset-0 bg-[linear-gradient(rgba(0,240,255,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(0,240,255,0.1)_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none opacity-20')
                flash = ui.element('div').classes('absolute inset-0 bg-white opacity-0 pointer-events-none transition-opacity duration-200')

            # RIGHT (LOGS)
            with ui.column().classes('col-span-3 gap-3 h-full'):
                with ui.card().classes('w-full flex-1 bg-black border border-gray-700 p-2 overflow-hidden'):
                    ui.label('SENTRY LOGS').classes('text-gray-500 text-[10px] mb-2')
                    log_container = ui.column().classes('w-full text-[10px] font-mono gap-1')

                def take_snapshot():
                    flash.classes(remove='opacity-0', add='opacity-50')
                    ui.timer(0.1, lambda: flash.classes(remove='opacity-50', add='opacity-0'))
                    speak("Snapshot captured.")
                    ts = datetime.now().strftime("%H:%M:%S")
                    gallery.insert(0, {'time': ts, 'src': video_feed.source})
                    logs.append(f"[REC] EVIDENCE SAVED: {ts}")
                    render_gallery()

                ui.button('MANUAL SNAPSHOT', on_click=take_snapshot, icon='camera_alt').classes('w-full bg-[#00f0ff]/10 border border-[#00f0ff] text-[#00f0ff] hover:bg-[#00f0ff]/20')
                ui.button('DEACTIVATE', on_click=app.shutdown, icon='power_off').classes('w-full bg-red-900/20 border border-red-500 text-red-500 hover:bg-red-900/40')

        # GALLERY
        ui.label('CAPTURED INTELLIGENCE').classes('text-xs text-gray-500 mt-2 px-2')
        gallery_row = ui.row().classes('w-full h-24 overflow-x-auto gap-2 px-2 pb-2')

        def render_gallery():
            gallery_row.clear()
            with gallery_row:
                for img in list(gallery)[:6]:
                    with ui.column().classes('relative shrink-0'):
                        ui.image(img['src']).classes('w-32 h-20 border border-gray-700 rounded')
                        ui.label(img['time']).classes('absolute bottom-0 right-0 bg-black/80 text-[9px] px-1 text-[#00f0ff]')

    # --- LOOP ---
    async def update_loop():
        while True:
            frame = process_frame()
            if frame: video_feed.set_source(frame)
            
            c, r, n, d = get_metrics()
            
            # Logic Updates
            if is_target_locked:
                status_badge.classes(replace='text-[#00f0ff] border-[#00f0ff] bg-[#00f0ff]/10')
                status_badge.set_text('AUTHORIZED USER DETECTED')
                threat_lbl.set_text('SAFE')
                threat_bar.set_value(0)
            elif motion_detected:
                status_badge.classes(replace='text-yellow-400 border-yellow-400 bg-yellow-400/10')
                status_badge.set_text('UNAUTHORIZED MOTION')
                threat_lbl.set_text('CAUTION')
                threat_bar.set_value(0.5)
            else:
                status_badge.classes(replace='text-red-500 border-red-500 bg-red-500/10')
                status_badge.set_text('SENTRY MODE ACTIVE')
                threat_lbl.set_text('MONITORING')
                threat_bar.set_value(0.2)

            # Chart Updates
            cpu_lbl.set_text(f'{c}%')
            cpu_plot.update_figure({'data': [go.Scatter(y=list(cpu_history), mode='lines', line={'color': '#00f0ff', 'width': 2}, fill='tozeroy')]})
            ram_lbl.set_text(f'{r}%')
            ram_plot.update_figure({'data': [go.Scatter(y=list(ram_history), mode='lines', line={'color': '#a855f7', 'width': 2}, fill='tozeroy')]})
            net_lbl.set_text(f'{n:.1f}')
            net_plot.update_figure({'data': [go.Scatter(y=list(net_history), mode='lines', line={'color': '#4ade80', 'width': 2}, fill='tozeroy')]})

            # Auto Logs
            if motion_detected and not is_target_locked:
                if len(logs) == 0 or "MOTION" not in logs[-1]:
                    logs.append(f"[ALERT] MOVEMENT IN SECTOR {int(time.time())%100}")

            log_container.clear()
            with log_container:
                for log in list(logs)[-7:]:
                    color = 'text-red-400' if 'ALERT' in log else 'text-gray-400'
                    ui.label(log).classes(f'{color} text-[10px]')

            await asyncio.sleep(0.03)

    ui.timer(0, update_loop, once=True)

ui.run(title='AETHER SENTRY', dark=True, frameless=False)


