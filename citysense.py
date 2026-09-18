from ultralytics import YOLO
import cv2
import easyocr
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

VIDEO_PATH = str(BASE_DIR / os.getenv("URBANPULSE_VIDEO", "demo3.mp4"))

POTHOLE_MODEL = str(BASE_DIR / "best.pt")
VEHICLE_MODEL = str(BASE_DIR / "yolo11n.pt")
PLATE_MODEL = str(BASE_DIR / "plate_model.pt")

BUS_ID = "BUS-12"
CAMERA_ID = "CAM-FRONT"

CONFIDENCE = 0.25
TRAFFIC_POST_INTERVAL_FRAMES = int(os.getenv("URBANPULSE_TRAFFIC_INTERVAL_FRAMES", "30"))
VEHICLE_POST_INTERVAL_FRAMES = int(os.getenv("URBANPULSE_VEHICLE_INTERVAL_FRAMES", "15"))
POTHOLE_POST_INTERVAL_FRAMES = int(os.getenv("URBANPULSE_POTHOLE_INTERVAL_FRAMES", "30"))
MAX_FRAMES = int(os.getenv("URBANPULSE_MAX_FRAMES", "0"))
DISPLAY_WINDOW = os.getenv("URBANPULSE_DISPLAY_WINDOW", "1") != "0"

# Backend endpoint
BACKEND_URL = os.getenv(
    "URBANPULSE_BACKEND_URL",
    "http://localhost:5000/api/detections"
)

# Save all generated events locally
JSON_OUTPUT = "citysense_events.json"


# ============================================================
# VEHICLE CLASSES
# ============================================================

VEHICLE_CLASSES = {
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck"
}


# ============================================================
# LOAD MODELS
# ============================================================

print("Loading UrbanPulse AI models...")

pothole_model = YOLO(POTHOLE_MODEL)

vehicle_model = YOLO(VEHICLE_MODEL)

plate_model = YOLO(PLATE_MODEL)

# OCR
reader = easyocr.Reader(
    ["en"],
    gpu=False
)

print("All models loaded.")
print("Pothole classes:", pothole_model.names)
print("Vehicle model loaded.")
print("Plate classes:", plate_model.names)


# ============================================================
# VIDEO
# ============================================================

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():

    print("ERROR: Could not open video.")

    exit()


print()
print("========================================")
print("       CITYSENSE AI STARTED")
print("========================================")
print("Video:", VIDEO_PATH)
print("Bus:", BUS_ID)
print("Camera:", CAMERA_ID)
print()


# ============================================================
# EVENT STORAGE
# ============================================================

all_events = []

detected_plates = set()

frame_number = 0

backend_success_count = 0
backend_failure_count = 0
pothole_signatures = {}
vehicle_signatures = {}


# ============================================================
# OCR FUNCTION
# ============================================================

def read_plate(plate):

    if plate is None or plate.size == 0:
        return ""

    try:

        # Resize
        plate = cv2.resize(
            plate,
            None,
            fx=3,
            fy=3,
            interpolation=cv2.INTER_CUBIC
        )

        # Grayscale
        gray = cv2.cvtColor(
            plate,
            cv2.COLOR_BGR2GRAY
        )

        # Contrast
        gray = cv2.equalizeHist(gray)

        versions = []

        versions.append(plate)
        versions.append(gray)

        # OTSU
        _, thresh = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        versions.append(thresh)

        # Adaptive threshold
        adaptive = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )

        versions.append(adaptive)

        candidates = []

        for image in versions:

            results = reader.readtext(
                image,
                detail=1,
                paragraph=False,
                allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            )

            for result in results:

                text = result[1]

                text = re.sub(
                    r"[^A-Za-z0-9]",
                    "",
                    text
                ).upper()

                if len(text) >= 4:

                    candidates.append(text)

        if not candidates:
            return ""

        candidates.sort(
            key=len,
            reverse=True
        )

        return candidates[0]

    except Exception as e:

        print("OCR ERROR:", e)

        return ""


# ============================================================
# CREATE BASE JSON
# ============================================================

def create_base_event():

    return {
        "busId": BUS_ID,

        "cameraId": CAMERA_ID,

        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),

        "location": {
            "latitude": None,
            "longitude": None
        }
    }


def store_event(event):

    global backend_success_count, backend_failure_count

    all_events.append(event)

    try:

        request = urllib.request.Request(
            BACKEND_URL,
            data=json.dumps(event).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(
            request,
            timeout=1.5
        ) as response:

            status_code = response.getcode()

        if status_code in (200, 201, 409):

            backend_success_count += 1

        else:

            backend_failure_count += 1

            print(
                "BACKEND ERROR:",
                status_code
            )

    except urllib.error.HTTPError as e:

        if e.code == 409:

            backend_success_count += 1

            return

        backend_failure_count += 1

        print(
            "BACKEND ERROR:",
            e.code,
            e.read().decode("utf-8", errors="ignore")[:120]
        )

    except urllib.error.URLError as e:

        backend_failure_count += 1

        if backend_failure_count <= 3:

            print(
                "BACKEND UNAVAILABLE:",
                e
            )


def should_send_signature(cache, key, frame_interval):

    last_frame = cache.get(key)

    if last_frame is not None and frame_number - last_frame < frame_interval:

        return False

    cache[key] = frame_number

    return True


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame_number += 1

    display_frame = frame.copy()

    if MAX_FRAMES and frame_number > MAX_FRAMES:
        break


    # ========================================================
    # 1. POTHOLE DETECTION
    # ========================================================

    pothole_results = pothole_model(
        frame,
        conf=0.35,
        imgsz=640,
        device="cpu",
        classes=[0],
        verbose=False
    )[0]

    if pothole_results.boxes is not None:

        for box in pothole_results.boxes:

            confidence = float(
                box.conf[0]
            )

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            width = x2 - x1
            height = y2 - y1
            pothole_key = (
                round(x1 / 25),
                round(y1 / 25),
                round(width / 25),
                round(height / 25)
            )

            # Draw
            cv2.rectangle(
                display_frame,
                (x1, y1),
                (x2, y2),
                (0, 0, 255),
                2
            )

            cv2.putText(
                display_frame,
                f"POTHOLE {confidence:.2f}",
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2
            )

            # JSON
            event = create_base_event()

            event["detection"] = {
                "type": "pothole",
                "confidence": round(
                    confidence,
                    3
                ),
                "severity": "high"
            }

            event["boundingBox"] = {
                "x": x1,
                "y": y1,
                "width": width,
                "height": height
            }

            event["frameNumber"] = frame_number

            if should_send_signature(
                pothole_signatures,
                pothole_key,
                POTHOLE_POST_INTERVAL_FRAMES
            ):

                store_event(event)


    # ========================================================
    # 2. VEHICLE DETECTION
    # ========================================================

    vehicle_results = vehicle_model(
        frame,
        conf=CONFIDENCE,
        imgsz=640,
        device="cpu",
        classes=list(
            VEHICLE_CLASSES.keys()
        ),
        verbose=False
    )[0]


    counts = {
        "Car": 0,
        "Motorcycle": 0,
        "Bus": 0,
        "Truck": 0
    }


    if vehicle_results.boxes is not None:

        for box in vehicle_results.boxes:

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

            counts[class_name] += 1

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            width = x2 - x1
            height = y2 - y1
            vehicle_key = (
                class_name,
                round(x1 / 40),
                round(y1 / 40),
                round(width / 40),
                round(height / 40)
            )


            # Draw vehicle
            cv2.rectangle(
                display_frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            cv2.putText(
                display_frame,
                f"{class_name} {confidence:.2f}",
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )


            # Vehicle JSON
            event = create_base_event()

            event["detection"] = {
                "type": "vehicle",
                "confidence": round(
                    confidence,
                    3
                ),
                "severity": None
            }

            event["boundingBox"] = {
                "x": x1,
                "y": y1,
                "width": width,
                "height": height
            }

            event["vehicle"] = {
                "type": class_name
            }

            event["frameNumber"] = frame_number

            if should_send_signature(
                vehicle_signatures,
                vehicle_key,
                VEHICLE_POST_INTERVAL_FRAMES
            ):

                store_event(event)


    # ========================================================
    # 3. TRAFFIC ANALYSIS
    # ========================================================

    total_vehicles = sum(
        counts.values()
    )


    if total_vehicles <= 8:

        congestion = "LOW"

    elif total_vehicles <= 15:

        congestion = "MEDIUM"

    else:

        congestion = "HIGH"


    # Traffic JSON
    traffic_event = create_base_event()

    traffic_event["detection"] = {

        "type": "traffic",

        "confidence": None,

        "severity": congestion.lower()

    }

    traffic_event["boundingBox"] = {

        "x": 0,

        "y": 0,

        "width": 0,

        "height": 0

    }

    traffic_event["traffic"] = {

        "totalVehicles": total_vehicles,

        "cars": counts["Car"],

        "motorcycles": counts["Motorcycle"],

        "buses": counts["Bus"],

        "trucks": counts["Truck"],

        "congestion": congestion

    }

    traffic_event["frameNumber"] = frame_number

    if frame_number == 1 or frame_number % TRAFFIC_POST_INTERVAL_FRAMES == 0:

        store_event(
            traffic_event
        )


    # ========================================================
    # 4. NUMBER PLATE DETECTION + OCR
    # ========================================================

    plate_results = plate_model(
        frame,
        conf=0.25,
        imgsz=640,
        device="cpu",
        verbose=False
    )[0]


    if plate_results.boxes is not None:

        for box in plate_results.boxes:

            confidence = float(
                box.conf[0]
            )

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            x1 = max(
                0,
                x1
            )

            y1 = max(
                0,
                y1
            )

            x2 = min(
                frame.shape[1],
                x2
            )

            y2 = min(
                frame.shape[0],
                y2
            )

            plate = frame[
                y1:y2,
                x1:x2
            ]

            if plate.size == 0:
                continue


            # OCR
            plate_text = read_plate(
                plate
            )


            # Draw
            cv2.rectangle(
                display_frame,
                (x1, y1),
                (x2, y2),
                (255, 0, 0),
                2
            )


            label = "LICENSE PLATE"
            new_plate_detected = False

            if plate_text:

                label = plate_text

                if plate_text not in detected_plates:

                    new_plate_detected = True

                    detected_plates.add(
                        plate_text
                    )

                    print(
                        "PLATE:",
                        plate_text
                    )


            cv2.putText(
                display_frame,
                label,
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 0, 0),
                2
            )


            # Plate JSON
            event = create_base_event()

            event["detection"] = {

                "type": "number_plate",

                "confidence": round(
                    confidence,
                    3
                ),

                "severity": None

            }

            event["boundingBox"] = {

                "x": x1,

                "y": y1,

                "width": x2 - x1,

                "height": y2 - y1

            }

            event["plateNumber"] = plate_text

            event["frameNumber"] = frame_number

            if new_plate_detected:

                store_event(
                    event
                )


    # ========================================================
    # DASHBOARD
    # ========================================================

    cv2.rectangle(
        display_frame,
        (10, 10),
        (380, 190),
        (0, 0, 0),
        -1
    )


    cv2.putText(
        display_frame,
        "CITYSENSE AI",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )


    cv2.putText(
        display_frame,
        f"Vehicles: {total_vehicles}",
        (20, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )


    cv2.putText(
        display_frame,
        f"Cars: {counts['Car']}",
        (20, 95),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        2
    )


    cv2.putText(
        display_frame,
        f"Bus: {counts['Bus']}",
        (150, 95),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        2
    )


    cv2.putText(
        display_frame,
        f"Truck: {counts['Truck']}",
        (220, 95),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        2
    )


    cv2.putText(
        display_frame,
        f"Traffic: {congestion}",
        (20, 125),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 255),
        2
    )


    cv2.putText(
        display_frame,
        f"Frame: {frame_number}",
        (20, 155),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        2
    )


    cv2.putText(
        display_frame,
        f"Events: {len(all_events)}",
        (20, 180),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        2
    )


    # ========================================================
    # SHOW
    # ========================================================

    if DISPLAY_WINDOW:

        cv2.imshow(
            "CitySense AI - UrbanPulse",
            display_frame
        )


    if DISPLAY_WINDOW and cv2.waitKey(1) & 0xFF == ord("q"):

        break


# ============================================================
# CLEANUP
# ============================================================

cap.release()

cv2.destroyAllWindows()


# ============================================================
# SAVE JSON
# ============================================================

with open(
    JSON_OUTPUT,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        all_events,
        file,
        indent=2
    )


print()
print("========================================")
print("       CITYSENSE AI COMPLETE")
print("========================================")

print(
    "Total JSON events:",
    len(all_events)
)

print(
    "JSON saved:",
    JSON_OUTPUT
)

print(
    "Unique plates:",
    len(detected_plates)
)

print(
    "Backend events accepted:",
    backend_success_count
)

print(
    "Backend events failed:",
    backend_failure_count
)

print("========================================")
