from ultralytics import YOLO
import cv2
from collections import defaultdict

# =========================
# CONFIG
# =========================

MODEL_PATH = "yolo11n.pt"
VIDEO_PATH = "demo3.mp4"

CONFIDENCE = 0.35

# COCO classes
VEHICLE_CLASSES = {
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck"
}

# =========================
# LOAD MODEL
# =========================

model = YOLO(MODEL_PATH)

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("ERROR: Could not open video.")
    exit()

print("Video opened.")
print("Starting vehicle detection + tracking...")

# =========================
# TRACKING DATA
# =========================

seen_vehicle_ids = set()

vehicle_counts = defaultdict(int)

frame_number = 0

# =========================
# MAIN LOOP
# =========================

while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame_number += 1

    # =========================
    # YOLO + BOT-SORT
    # =========================

    results = model.track(
        frame,
        conf=CONFIDENCE,
        imgsz=640,
        device=0,
        persist=True,
        tracker="botsort.yaml",
        classes=list(VEHICLE_CLASSES.keys()),
        verbose=False
    )[0]

    # =========================
    # PROCESS DETECTIONS
    # =========================

    if results.boxes is not None:

        for box in results.boxes:

            if box.id is None:
                continue

            track_id = int(box.id[0])

            class_id = int(box.cls[0])

            confidence = float(box.conf[0])

            class_name = VEHICLE_CLASSES.get(
                class_id,
                "Vehicle"
            )

            # Bounding box
            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            # =========================
            # COUNT UNIQUE VEHICLES
            # =========================

            if track_id not in seen_vehicle_ids:

                seen_vehicle_ids.add(track_id)

                vehicle_counts[class_name] += 1

                print(
                    f"NEW VEHICLE | "
                    f"ID: {track_id} | "
                    f"Type: {class_name} | "
                    f"Confidence: {confidence:.2f} | "
                    f"Frame: {frame_number}"
                )

            # =========================
            # DRAW BOX
            # =========================

            label = (
                f"{class_name} "
                f"ID:{track_id} "
                f"{confidence:.2f}"
            )

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                label,
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

    # =========================
    # DISPLAY COUNTS
    # =========================

    total = len(seen_vehicle_ids)

    cv2.rectangle(
        frame,
        (10, 10),
        (310, 145),
        (0, 0, 0),
        -1
    )

    cv2.putText(
        frame,
        f"Vehicles: {total}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    y = 70

    for vehicle_type in [
        "Car",
        "Motorcycle",
        "Bus",
        "Truck"
    ]:

        count = vehicle_counts[vehicle_type]

        cv2.putText(
            frame,
            f"{vehicle_type}: {count}",
            (20, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        y += 20

    # =========================
    # SHOW FRAME
    # =========================

    cv2.imshow(
        "UrbanPulse AI - Vehicle Tracking",
        frame
    )

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# =========================
# CLEANUP
# =========================

cap.release()
cv2.destroyAllWindows()

print()
print("==============================")
print("VEHICLE DETECTION COMPLETE")
print("==============================")

print(f"Total unique vehicles: {total}")

print()
print("Vehicle breakdown:")

for vehicle_type in [
    "Car",
    "Motorcycle",
    "Bus",
    "Truck"
]:

    print(
        f"{vehicle_type}: "
        f"{vehicle_counts[vehicle_type]}"
    )