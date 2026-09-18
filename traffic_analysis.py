from ultralytics import YOLO
import cv2
import os
import time
import threading
import queue
from datetime import datetime, timezone

# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = "yolo11n.pt"
VIDEO_PATH = "demo3.mp4"

# Detection settings
CONFIDENCE = 0.25
IMAGE_SIZE = 320

# Run YOLO every Nth frame
# 3 = better detection frequency
# 5 = smoother video
PROCESS_EVERY_N_FRAMES = 4

# Backend
BACKEND_URL = os.getenv(
    "URBANPULSE_BACKEND_URL",
    "http://localhost:5000/api/detections"
)

BUS_ID = "BUS-12"
CAMERA_ID = "CAM-FRONT"

# Send backend data once every second
BACKEND_INTERVAL = 1.0

# ============================================================
# VEHICLE CLASSES - YOLO COCO
# ============================================================

VEHICLE_CLASSES = {
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck"
}

# ============================================================
# BACKEND ASYNC QUEUE
# ============================================================

backend_queue = queue.Queue(maxsize=2)


def backend_worker():

    while True:

        event = backend_queue.get()

        if event is None:
            break

        try:

            import requests

            response = requests.post(
                BACKEND_URL,
                json=event,
                timeout=0.5
            )

            if response.status_code not in [200, 201]:
                print(
                    "BACKEND ERROR:",
                    response.status_code
                )

        except Exception:
            # Backend failure should NEVER stop video
            pass

        finally:
            backend_queue.task_done()


backend_thread = threading.Thread(
    target=backend_worker,
    daemon=True
)

backend_thread.start()

# ============================================================
# LOAD YOLO
# ============================================================

print()
print("==========================================")
print("       URBANPULSE AI TRAFFIC SYSTEM")
print("==========================================")
print()

print("Loading YOLO model...")

model = YOLO(MODEL_PATH)

print("Model loaded successfully.")
print("Using GPU: NVIDIA RTX 4050")

# ============================================================
# OPEN VIDEO
# ============================================================

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():

    print("ERROR: Could not open video.")
    exit()

# Video properties
video_fps = cap.get(cv2.CAP_PROP_FPS)

if video_fps <= 0:
    video_fps = 30

video_width = int(
    cap.get(cv2.CAP_PROP_FRAME_WIDTH)
)

video_height = int(
    cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
)

print(f"Video resolution: {video_width}x{video_height}")
print(f"Video FPS: {video_fps:.1f}")
print()
print("Starting traffic analysis...")
print("Press Q to quit.")
print()

# ============================================================
# VARIABLES
# ============================================================

frame_number = 0

last_results = None

last_counts = {
    "Car": 0,
    "Motorcycle": 0,
    "Bus": 0,
    "Truck": 0
}

last_total = 0

last_congestion = "LOW"

last_backend_time = 0

# FPS calculation
fps_counter = 0
fps_timer = time.time()
display_fps = 0

# ============================================================
# MAIN LOOP
# ============================================================

while True:

    loop_start = time.time()

    ret, frame = cap.read()

    if not ret:
        break

    frame_number += 1

    # ========================================================
    # YOLO DETECTION
    # ========================================================

    if frame_number % PROCESS_EVERY_N_FRAMES == 0:

        results = model.predict(

            source=frame,

            conf=CONFIDENCE,

            imgsz=IMAGE_SIZE,

            device=0,

            classes=list(
                VEHICLE_CLASSES.keys()
            ),

            verbose=False,

            half=True,

            max_det=30

        )[0]

        last_results = results

        # ----------------------------------------------------
        # RESET COUNTS
        # ----------------------------------------------------

        counts = {
            "Car": 0,
            "Motorcycle": 0,
            "Bus": 0,
            "Truck": 0
        }

        # ----------------------------------------------------
        # COUNT VEHICLES
        # ----------------------------------------------------

        if results.boxes is not None:

            for box in results.boxes:

                class_id = int(
                    box.cls[0]
                )

                class_name = VEHICLE_CLASSES.get(
                    class_id
                )

                if class_name is None:
                    continue

                counts[class_name] += 1

        # ----------------------------------------------------
        # SAVE COUNTS
        # ----------------------------------------------------

        last_counts = counts

        last_total = sum(
            counts.values()
        )

        # ----------------------------------------------------
        # CONGESTION
        # ----------------------------------------------------

        if last_total <= 8:

            last_congestion = "LOW"

        elif last_total <= 15:

            last_congestion = "MEDIUM"

        else:

            last_congestion = "HIGH"

    # ========================================================
    # DRAW LAST DETECTION BOXES
    # ========================================================

    if last_results is not None:

        if last_results.boxes is not None:

            for box in last_results.boxes:

                class_id = int(
                    box.cls[0]
                )

                confidence = float(
                    box.conf[0]
                )

                class_name = VEHICLE_CLASSES.get(
                    class_id
                )

                if class_name is None:
                    continue

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0]
                )

                # Bounding box
                cv2.rectangle(

                    frame,

                    (x1, y1),

                    (x2, y2),

                    (0, 255, 0),

                    2

                )

                # Label
                label = (
                    f"{class_name} "
                    f"{confidence:.2f}"
                )

                cv2.putText(

                    frame,

                    label,

                    (
                        x1,
                        max(y1 - 10, 20)
                    ),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.55,

                    (0, 255, 0),

                    2

                )

    # ========================================================
    # SEND DATA TO BACKEND
    # ========================================================

    current_time = time.time()

    if (
        current_time -
        last_backend_time
        >= BACKEND_INTERVAL
    ):

        event = {

            "busId": BUS_ID,

            "cameraId": CAMERA_ID,

            "timestamp":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            "location": {

                "latitude": None,

                "longitude": None

            },

            "detection": {

                "type": "traffic",

                "confidence": None,

                "severity":
                    last_congestion.lower()

            },

            "traffic": {

                "totalVehicles":
                    last_total,

                "cars":
                    last_counts["Car"],

                "motorcycles":
                    last_counts["Motorcycle"],

                "buses":
                    last_counts["Bus"],

                "trucks":
                    last_counts["Truck"],

                "congestion":
                    last_congestion

            }

        }

        # ----------------------------------------------------
        # NON-BLOCKING BACKEND REQUEST
        # ----------------------------------------------------

        try:

            if not backend_queue.full():

                backend_queue.put_nowait(
                    event
                )

        except queue.Full:

            pass

        last_backend_time = current_time

    # ========================================================
    # FPS CALCULATION
    # ========================================================

    fps_counter += 1

    if time.time() - fps_timer >= 1.0:

        display_fps = fps_counter / (
            time.time() - fps_timer
        )

        fps_counter = 0

        fps_timer = time.time()

    # ========================================================
    # DASHBOARD PANEL
    # ========================================================

    panel_height = 225

    cv2.rectangle(

        frame,

        (10, 10),

        (380, panel_height),

        (0, 0, 0),

        -1

    )

    # Title
    cv2.putText(

        frame,

        "URBANPULSE AI",

        (20, 38),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.7,

        (255, 255, 255),

        2

    )

    # FPS
    cv2.putText(

        frame,

        f"FPS: {display_fps:.1f}",

        (20, 68),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.55,

        (255, 255, 255),

        2

    )

    # Total
    cv2.putText(

        frame,

        f"VEHICLES: {last_total}",

        (20, 100),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.65,

        (255, 255, 255),

        2

    )

    # Cars
    cv2.putText(

        frame,

        f"Cars: {last_counts['Car']}",

        (20, 128),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.5,

        (255, 255, 255),

        2

    )

    # Motorcycles
    cv2.putText(

        frame,

        f"Motorcycles: {last_counts['Motorcycle']}",

        (20, 153),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.5,

        (255, 255, 255),

        2

    )

    # Buses
    cv2.putText(

        frame,

        f"Buses: {last_counts['Bus']}",

        (20, 178),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.5,

        (255, 255, 255),

        2

    )

    # Trucks
    cv2.putText(

        frame,

        f"Trucks: {last_counts['Truck']}",

        (190, 128),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.5,

        (255, 255, 255),

        2

    )

    # Congestion
    cv2.putText(

        frame,

        f"TRAFFIC: {last_congestion}",

        (190, 153),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.6,

        (0, 255, 255),

        2

    )

    # AI status
    cv2.putText(

        frame,

        "AI: ACTIVE",

        (190, 178),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.5,

        (0, 255, 0),

        2

    )

    # ========================================================
    # DISPLAY
    # ========================================================

    cv2.imshow(

        "citysense AI - Traffic Analysis",

        frame

    )

    # ========================================================
    # KEYBOARD
    # ========================================================

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):

        break


# ============================================================
# CLEANUP
# ============================================================

cap.release()

cv2.destroyAllWindows()

# Stop backend worker
try:

    backend_queue.put_nowait(None)

except Exception:

    pass

print()
print("==========================================")
print("       TRAFFIC ANALYSIS COMPLETE")
print("==========================================")