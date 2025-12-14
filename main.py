import asyncio
import base64
import cv2
import psutil
import time
import plotly.graph_objects as go
from collections import deque
from datetime import datetime
from nicegui import ui, app

# --- CONFIGURATION ---
# Using standard Haarcascades for 100% compatibility with Python 3.13
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# --- STATE MANAGEMENT ---
history_len = 50
cpu_history = deque([0] * history_len, maxlen=history_len)
ram_history = deque([0] * history_len, maxlen=history_len)
net_history = deque([0] * history_len, maxlen=history_len)
logs = deque([], maxlen=7)
gallery = []

cap = cv2.VideoCapture(0)
last_net_bytes = psutil.net_io_counters().bytes_recv

# Global Variables for Animation
is_target_locked = False
scan_line_pos = 0


def process_frame():
    global is_target_locked, scan_line_pos
    success, frame = cap.read()
    if not success: return None

    # 1. Flip & Grayscale for AI
    frame = cv2.flip(frame, 1)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    height, width, _ = frame.shape

    # 2. Detect Faces
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    is_target_locked = len(faces) > 0

    # 3. Dynamic Theme Colors (Cyan = Safe/Lock, Red = Searching)
    color = (255, 255, 0) if is_target_locked else (0, 0, 255)  # BGR

    # 4. Sci-Fi Scanner Line Animation
    scan_line_pos = (scan_line_pos + 4) % height
    cv2.line(frame, (0, scan_line_pos), (width, scan_line_pos), color, 1)

    # 5. Draw HUD Elements
    for (x, y, w, h) in faces:
        d = int(w * 0.2)
        thick = 2
        # Top-Left
        cv2.line(frame, (x, y), (x + d, y), color, thick)
        cv2.line(frame, (x, y), (x, y + d), color, thick)
        # Top-Right
        cv2.line(frame, (x + w, y), (x + w - d, y), color, thick)
        cv2.line(frame, (x + w, y), (x + w, y + d), color, thick)
        # Bottom-Left
        cv2.line(frame, (x, y + h), (x + d, y + h), color, thick)
        cv2.line(frame, (x, y + h), (x, y + h - d), color, thick)
        # Bottom-Right
        cv2.line(frame, (x + w, y + h), (x + w - d, y + h), color, thick)
        cv2.line(frame, (x + w, y + h), (x + w, y + h - d), color, thick)

        cv2.putText(frame, 'ID: AETHER-USR', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    # 6. Encode for Browser
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
    # UI Theme: Cyberpunk Black & Cyan
    ui.colors(primary='#00f0ff', secondary='#000000', accent='#ff003c')

    with ui.column().classes('w-full min-h-screen bg-black text-[#00f0ff] p-2 gap-2 font-mono overflow-hidden'):

        # --- HEADER ---
        with ui.row().classes('w-full justify-between items-center border-b border-[#00f0ff]/30 pb-2 px-2'):
            with ui.row().classes('items-center gap-3'):
                ui.icon('hub', size='28px').classes('animate-pulse')
                ui.label('AETHER // CORE').classes('text-2xl font-bold tracking-[0.15em] text-white')

            status_badge = ui.label('INITIALIZING...').classes('text-xs font-bold px-3 py-1 rounded border')

        # --- MAIN GRID ---
        with ui.grid(columns=12).classes('w-full gap-4 h-[70vh]'):
            # LEFT: TELEMETRY
            with ui.column().classes('col-span-3 gap-3 h-full'):
                def stat_card(title, color):
                    with ui.card().classes(f'w-full bg-black border border-{color} p-3 shadow-lg'):
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

                cpu_plot, cpu_lbl = stat_card('CPU THREADS', 'cyan-400')
                ram_plot, ram_lbl = stat_card('RAM BUFFER', 'purple-400')
                net_plot, net_lbl = stat_card('UPLINK (MB/s)', 'green-400')

                with ui.card().classes('w-full bg-black border border-orange-400 p-3'):
                    with ui.row().classes('w-full justify-between'):
                        ui.label('DRIVE STATUS').classes('text-orange-400 text-[10px] font-bold')
                        disk_lbl = ui.label('0%').classes('text-white text-xs')
                    disk_bar = ui.linear_progress(value=0).classes(
                        'h-1 rounded-none text-orange-400 track-color-gray-900 mt-2')

            # CENTER: VISION FEED
            with ui.card().classes(
                    'col-span-6 bg-black border-2 border-[#00f0ff] p-0 relative overflow-hidden flex items-center justify-center'):
                video_feed = ui.image().classes('w-full h-full object-cover opacity-90')
                # Visual Flash for Snapshot
                flash = ui.element('div').classes(
                    'absolute inset-0 bg-white opacity-0 pointer-events-none transition-opacity duration-200')

            # RIGHT: LOGS & CONTROL
            with ui.column().classes('col-span-3 gap-3 h-full'):
                with ui.card().classes('w-full flex-1 bg-black border border-gray-700 p-2 overflow-hidden'):
                    ui.label('KERNEL LOGS').classes('text-gray-500 text-[10px] mb-2')
                    log_container = ui.column().classes('w-full text-[10px] font-mono gap-1')

                def take_snapshot():
                    flash.classes(remove='opacity-0', add='opacity-50')
                    ui.timer(0.1, lambda: flash.classes(remove='opacity-50', add='opacity-0'))

                    ts = datetime.now().strftime("%H:%M:%S")
                    gallery.insert(0, {'time': ts, 'src': video_feed.source})
                    logs.append(f"[REC] FRAME CAPTURED: {ts}")
                    render_gallery()

                ui.button('CAPTURE FRAME', on_click=take_snapshot, icon='camera').classes(
                    'w-full bg-[#00f0ff]/10 border border-[#00f0ff] text-[#00f0ff] hover:bg-[#00f0ff]/20')
                ui.button('TERMINATE', on_click=app.shutdown, icon='power_settings_new').classes(
                    'w-full bg-red-900/20 border border-red-500 text-red-500 hover:bg-red-900/40')

        # --- GALLERY SECTION ---
        ui.label('ENCRYPTED ARCHIVE').classes('text-xs text-gray-500 mt-2 px-2')
        gallery_row = ui.row().classes('w-full h-24 overflow-x-auto gap-2 px-2 pb-2')

        def render_gallery():
            gallery_row.clear()
            with gallery_row:
                for img in list(gallery)[:6]:  # Show last 6 images
                    with ui.column().classes('relative shrink-0'):
                        ui.image(img['src']).classes('w-32 h-20 border border-gray-700 rounded')
                        ui.label(img['time']).classes(
                            'absolute bottom-0 right-0 bg-black/80 text-[9px] px-1 text-[#00f0ff]')

    # --- MAIN LOOP ---
    async def update_loop():
        while True:
            # 1. Video & AI
            frame = process_frame()
            if frame: video_feed.set_source(frame)

            # 2. Dynamic UI Updates
            if is_target_locked:
                status_badge.classes(replace='text-[#00f0ff] border-[#00f0ff] bg-[#00f0ff]/10')
                status_badge.set_text('TARGET LOCKED')
            else:
                status_badge.classes(replace='text-red-500 border-red-500 bg-red-500/10')
                status_badge.set_text('SCANNING SECTOR...')

            # 3. Telemetry Updates
            c, r, n, d = get_metrics()

            cpu_lbl.set_text(f'{c}%')
            cpu_plot.update_figure(
                {'data': [go.Scatter(y=list(cpu_history), mode='lines', line={'color': '#00f0ff'}, fill='tozeroy')]})

            ram_lbl.set_text(f'{r}%')
            ram_plot.update_figure(
                {'data': [go.Scatter(y=list(ram_history), mode='lines', line={'color': '#a855f7'}, fill='tozeroy')]})

            net_lbl.set_text(f'{n:.1f}')
            net_plot.update_figure(
                {'data': [go.Scatter(y=list(net_history), mode='lines', line={'color': '#4ade80'}, fill='tozeroy')]})

            disk_lbl.set_text(f'{d}%')
            disk_bar.set_value(d / 100)

            # 4. Logs
            if c > 60: logs.append(f"[WARN] HIGH LOAD: {c}%")
            if not is_target_locked and len(logs) == 0: logs.append("[SYS] IDLE...")

            log_container.clear()
            with log_container:
                for log in list(logs)[-7:]:
                    color = 'text-red-400' if 'WARN' in log else 'text-gray-500'
                    ui.label(log).classes(f'{color} text-[10px]')

            await asyncio.sleep(0.03)  # ~30 FPS

    ui.timer(0, update_loop, once=True)


ui.run(title='AETHER CORE', dark=True, frameless=False)