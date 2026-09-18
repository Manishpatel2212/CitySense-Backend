import cv2
import math
from ultralytics import YOLO
import json
from datetime import datetime

# =========================
# CONFIG
# =========================

MODEL_PATH = "best.pt"
VIDEO_PATH = "demo2.mp4"

BUS_ID = "BUS-12"
CAMERA_ID = "CAM-FRONT"

CONFIDENCE = 0.35
MIN_FRAMES = 3

# Re-identification
MAX_LOST_FRAMES = 30
POSITION_DISTANCE = 100
MIN_AREA_SIMILARITY = 0.50


# =========================
# HELPER FUNCTIONS
# =========================

def get_center(box):
    x1, y1, x2, y2 = box
    return (
        (x1 + x2) / 2,
        (y1 + y2) / 2
    )


def get_area(box):
    x1, y1, x2, y2 = box

    width = max(0, x2 - x1)
    height = max(0, y2 - y1)

    return width * height


def get_distance(box1, box2):
    c1 = get_center(box1)
    c2 = get_center(box2)

    return math.sqrt(
        (c1[0] - c2[0]) ** 2 +
        (c1[1] - c2[1]) ** 2
    )


def get_area_similarity(box1, box2):
    area1 = get_area(box1)
    area2 = get_area(box2)

    if area1 == 0 or area2 == 0:
        return 0

    return min(area1, area2) / max(area1, area2)

def create_pothole_event(bus_id, camera_id, confidence, box):
    x1, y1, x2, y2 = box

    event = {
        "busId": bus_id,
        "cameraId": camera_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",

        "location": {
            "latitude": None,
            "longitude": None
        },

        "detection": {
            "type": "pothole",
            "confidence": round(float(confidence), 2),
            "severity": "high"
        },

        "boundingBox": {
            "x": int(x1),
            "y": int(y1),
            "width": int(x2 - x1),
            "height": int(y2 - y1)
        }
    }

    return event
# =========================
# LOAD MODEL
# =========================

print("Loading model...")

model = YOLO(MODEL_PATH)

print("Model loaded.")
print("Classes:", model.names)


# =========================
# LOAD VIDEO
# =========================

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("ERROR: Could not open video.")
    exit()

print("Video opened.")


# =========================
# TRACKING DATA
# =========================

# Active BoT-SORT tracks
#
# track_id:
# {
#     "pothole_id": int or None,
#     "frames": int,
#     "last_frame": int,
#     "last_box": [...],
#     "confirmed": bool
# }
active_tracks = {}


# Recently lost CONFIRMED potholes
#
# pothole_id:
# {
#     "last_frame": int,
#     "last_box": [...]
# }
recently_lost = {}


# Permanent pothole number
next_pothole_id = 1

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
        classes=[0],
        verbose=False
    )[0]

    # Track IDs visible in this frame
    current_track_ids = set()


    # =========================
    # PROCESS DETECTIONS
    # =========================

    if results.boxes is not None:

        for box in results.boxes:

            # Ignore detections without tracker ID
            if box.id is None:
                continue

            track_id = int(box.id[0])

            xyxy = box.xyxy[0].tolist()

            current_track_ids.add(track_id)


            # ==================================
            # EXISTING ACTIVE TRACK
            # ==================================

            if track_id in active_tracks:

                track = active_tracks[track_id]

                track["frames"] += 1
                track["last_frame"] = frame_number
                track["last_box"] = xyxy

                continue


            # ==================================
            # NEW TRACK ID
            # ==================================

            matched_pothole_id = None
            best_score = None


            # ==================================
            # SEARCH ONLY RECENTLY LOST TRACKS
            # ==================================

            for pothole_id, lost_track in recently_lost.items():

                frames_lost = (
                    frame_number -
                    lost_track["last_frame"]
                )

                # Too old
                if frames_lost > MAX_LOST_FRAMES:
                    continue


                # Position similarity
                distance = get_distance(
                    xyxy,
                    lost_track["last_box"]
                )


                # Size similarity
                area_similarity = get_area_similarity(
                    xyxy,
                    lost_track["last_box"]
                )


                # Both conditions must pass
                if (
                    distance <= POSITION_DISTANCE
                    and
                    area_similarity >= MIN_AREA_SIMILARITY
                ):

                    # Lower score = better match
                    score = (
                        distance / POSITION_DISTANCE
                        +
                        (1 - area_similarity)
                    )

                    if (
                        best_score is None
                        or
                        score < best_score
                    ):

                        best_score = score
                        matched_pothole_id = pothole_id


            # ==================================
            # RE-IDENTIFIED POTHOLE
            # ==================================

            if matched_pothole_id is not None:

                print(
                    f"RE-IDENTIFIED POTHOLE "
                    f"#{matched_pothole_id} "
                    f"| New Track ID: {track_id} "
                    f"| Frame: {frame_number}"
                )


                old_track = recently_lost[
                    matched_pothole_id
                ]


                active_tracks[track_id] = {

                    "pothole_id":
                        matched_pothole_id,

                    "frames":
                        old_track["frames"]
                        if "frames" in old_track
                        else MIN_FRAMES,

                    "last_frame":
                        frame_number,

                    "last_box":
                        xyxy,

                    "confirmed":
                        True
                }


                # Remove from recently lost
                del recently_lost[
                    matched_pothole_id
                ]


            # ==================================
            # COMPLETELY NEW TRACK
            # ==================================

            else:

                active_tracks[track_id] = {

                    "pothole_id":
                        None,

                    "frames":
                        1,

                    "last_frame":
                        frame_number,

                    "last_box":
                        xyxy,

                    "confirmed":
                        False
                }


    # =========================
    # FIND LOST TRACKS
    # =========================

    tracks_to_remove = []


    for track_id, track in active_tracks.items():

        if track_id in current_track_ids:
            continue


        frames_missing = (
            frame_number -
            track["last_frame"]
        )


        # ==================================
        # TRACK JUST DISAPPEARED
        # ==================================

        if frames_missing == 1:

            # Only confirmed potholes
            # go into re-identification pool
            if track["confirmed"]:

                pothole_id = track["pothole_id"]

                recently_lost[pothole_id] = {

                    "last_frame":
                        track["last_frame"],

                    "last_box":
                        track["last_box"],

                    "frames":
                        track["frames"]
                }


            tracks_to_remove.append(track_id)


        # ==================================
        # OLD UNCONFIRMED/ACTIVE TRACK
        # ==================================

        elif frames_missing > MAX_LOST_FRAMES:

            tracks_to_remove.append(track_id)


    # Remove disappeared tracks
    for track_id in tracks_to_remove:

        if track_id in active_tracks:
            del active_tracks[track_id]


    # =========================
    # CONFIRM NEW TRACKS
    # =========================

    for track_id, track in active_tracks.items():

        if (
            not track["confirmed"]
            and
            track["frames"] >= MIN_FRAMES
        ):

            pothole_id = next_pothole_id

            next_pothole_id += 1

            track["pothole_id"] = pothole_id
            track["confirmed"] = True

            # Get confidence for this track
            confidence = 0.0

            for box in results.boxes:
                if box.id is not None and int(box.id[0]) == track_id:
                    confidence = float(box.conf[0])
                    break

            # Create UrbanPulse JSON event
            event = create_pothole_event(
                BUS_ID,
                CAMERA_ID,
                confidence,
                track["last_box"]
            )

            print(
                f"NEW POTHOLE "
                f"#{pothole_id} "
                f"| Track ID: {track_id} "
                f"| Frame: {frame_number}"
            )

            print("\n--- URBANPULSE EVENT ---")
            print(json.dumps(event, indent=2))
            print("------------------------\n")


    # =========================
    # REMOVE OLD LOST TRACKS
    # =========================

    lost_to_remove = []


    for pothole_id, lost_track in recently_lost.items():

        if (
            frame_number -
            lost_track["last_frame"]
            >
            MAX_LOST_FRAMES
        ):

            lost_to_remove.append(
                pothole_id
            )


    for pothole_id in lost_to_remove:

        del recently_lost[pothole_id]


    # =========================
    # DISPLAY
    # =========================

    annotated_frame = results.plot()


    cv2.putText(
        annotated_frame,
        f"Frame: {frame_number}",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )


    cv2.putText(
        annotated_frame,
        f"Unique potholes: {next_pothole_id - 1}",
        (20, 75),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )


    cv2.imshow(
        "Pothole Tracking",
        annotated_frame
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
print(
    f"Unique potholes detected: "
    f"{next_pothole_id - 1}"
)
print("==============================")