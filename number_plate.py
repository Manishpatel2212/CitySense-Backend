from ultralytics import YOLO
import cv2
import easyocr
import re
import time
from collections import Counter

# ============================================================
# CONFIG
# ============================================================

MODEL_PATH = "plate_model.pt"
VIDEO_PATH = "demo4.mp4"

# YOLO
CONFIDENCE = 0.35
IMAGE_SIZE = 416

# Run YOLO every 3rd frame
PROCESS_EVERY_N_FRAMES = 3

# OCR
OCR_SCALE = 4

# A plate must appear this many times before being accepted
MIN_CONFIRMATIONS = 2

# ============================================================
# LOAD MODELS
# ============================================================

print()
print("==========================================")
print("       citysense AI")
print("       NUMBER PLATE RECOGNITION")
print("==========================================")
print()

print("Loading plate detection model...")

model = YOLO(MODEL_PATH)

print("Plate model loaded.")
print("Classes:", model.names)

print("Loading EasyOCR...")

# IMPORTANT:
# Your RTX 4050 supports CUDA
reader = easyocr.Reader(
    ["en"],
    gpu=True,
    verbose=False
)

print("EasyOCR loaded on GPU.")

# ============================================================
# VIDEO
# ============================================================

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():

    print("ERROR: Could not open video.")
    exit()

video_fps = cap.get(cv2.CAP_PROP_FPS)

if video_fps <= 0:
    video_fps = 30

frame_width = int(
    cap.get(cv2.CAP_PROP_FRAME_WIDTH)
)

frame_height = int(
    cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
)

print()
print(
    f"Video: {frame_width}x{frame_height}"
)

print(
    f"FPS: {video_fps:.1f}"
)

print()
print("Number Plate Detection Started...")
print("Press Q to exit.")
print()

# ============================================================
# VARIABLES
# ============================================================

frame_number = 0

last_boxes = []

# Accepted plates
detected_plates = set()

# Candidate OCR results
plate_history = {}

# Last OCR result for each detection
last_plate_text = ""

last_ocr_box = None

last_ocr_time = 0

OCR_COOLDOWN = 0.7


# ============================================================
# OCR PREPROCESSING
# ============================================================

def prepare_plate(plate):

    if plate is None or plate.size == 0:

        return []

    # Resize
    plate = cv2.resize(
        plate,
        None,
        fx=OCR_SCALE,
        fy=OCR_SCALE,
        interpolation=cv2.INTER_CUBIC
    )

    # Slight blur to remove noise
    plate = cv2.bilateralFilter(
        plate,
        7,
        50,
        50
    )

    # Grayscale
    gray = cv2.cvtColor(
        plate,
        cv2.COLOR_BGR2GRAY
    )

    # Contrast enhancement
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(gray)

    # OTSU threshold
    _, otsu = cv2.threshold(
        enhanced,
        0,
        255,
        cv2.THRESH_BINARY +
        cv2.THRESH_OTSU
    )

    return [
        plate,
        enhanced,
        otsu
    ]


# ============================================================
# CLEAN OCR TEXT
# ============================================================

def clean_text(text):

    # Remove everything except A-Z and 0-9
    text = re.sub(
        r"[^A-Za-z0-9]",
        "",
        text
    ).upper()

    # Plate should contain at least 4 characters
    if len(text) < 4:
        return ""

    # Ignore extremely long OCR garbage
    if len(text) > 12:
        return ""

    return text


# ============================================================
# OCR FUNCTION
# ============================================================

def read_plate(plate):

    images = prepare_plate(plate)

    if not images:
        return ""

    candidates = []

    for img in images:

        try:

            results = reader.readtext(

                img,

                detail=1,

                paragraph=False,

                allowlist=
                "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",

                mag_ratio=1.0,

                text_threshold=0.5,

                low_text=0.3,

                link_threshold=0.3
            )

            for result in results:

                if len(result) < 2:
                    continue

                text = clean_text(
                    result[1]
                )

                if text:

                    confidence = float(
                        result[2]
                    )

                    # Keep reasonably confident OCR
                    if confidence >= 0.25:

                        candidates.append(
                            (
                                text,
                                confidence
                            )
                        )

        except Exception:
            continue

    if not candidates:
        return ""

    # --------------------------------------------------------
    # SCORE OCR CANDIDATES
    # --------------------------------------------------------

    candidate_scores = {}

    for text, confidence in candidates:

        # Longer plate text gets a slight preference
        score = (
            confidence * 0.7
            +
            min(len(text), 10)
            / 10
            * 0.3
        )

        if text not in candidate_scores:

            candidate_scores[text] = 0

        candidate_scores[text] += score

    best_text = max(
        candidate_scores,
        key=candidate_scores.get
    )

    return best_text


# ============================================================
# PLATE BOX SIMILARITY
# ============================================================

def box_distance(box1, box2):

    if box1 is None or box2 is None:

        return 99999

    x1, y1, x2, y2 = box1

    a1, b1, a2, b2 = box2

    cx1 = (x1 + x2) / 2
    cy1 = (y1 + y2) / 2

    cx2 = (a1 + a2) / 2
    cy2 = (b1 + b2) / 2

    return (
        (cx1 - cx2) ** 2
        +
        (cy1 - cy2) ** 2
    ) ** 0.5


# ============================================================
# FPS
# ============================================================

fps_counter = 0

fps_timer = time.time()

display_fps = 0


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame_number += 1

    # ========================================================
    # YOLO PLATE DETECTION
    # ========================================================

    if (
        frame_number %
        PROCESS_EVERY_N_FRAMES
        == 0
    ):

        results = model.predict(

            source=frame,

            conf=CONFIDENCE,

            imgsz=IMAGE_SIZE,

            device=0,

            half=True,

            verbose=False,

            max_det=10

        )[0]

        new_boxes = []

        if results.boxes is not None:

            for box in results.boxes:

                confidence = float(
                    box.conf[0]
                )

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0]
                )

                # Safety
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

                if x2 <= x1 or y2 <= y1:
                    continue

                new_boxes.append({

                    "box": (
                        x1,
                        y1,
                        x2,
                        y2
                    ),

                    "confidence":
                        confidence,

                    "text":
                        ""
                })

        last_boxes = new_boxes


    # ========================================================
    # OCR
    # ========================================================

    for detection in last_boxes:

        box = detection["box"]

        x1, y1, x2, y2 = box

        # ----------------------------------------------------
        # OCR COOLDOWN
        # ----------------------------------------------------

        current_time = time.time()

        if (
            current_time -
            last_ocr_time
            < OCR_COOLDOWN
        ):

            continue

        plate = frame[
            y1:y2,
            x1:x2
        ]

        if plate.size == 0:
            continue

        # ----------------------------------------------------
        # OCR
        # ----------------------------------------------------

        text = read_plate(
            plate
        )

        if not text:
            continue

        # ----------------------------------------------------
        # TEMPORAL CONFIRMATION
        # ----------------------------------------------------

        if text not in plate_history:

            plate_history[text] = []

        plate_history[text].append(
            time.time()
        )

        # Keep only recent confirmations
        plate_history[text] = [

            t for t in
            plate_history[text]

            if time.time() - t < 3
        ]

        confirmations = len(
            plate_history[text]
        )

        # ----------------------------------------------------
        # ACCEPT PLATE
        # ----------------------------------------------------

        if (
            confirmations >=
            MIN_CONFIRMATIONS
        ):

            if text not in detected_plates:

                detected_plates.add(
                    text
                )

                print(
                    "PLATE DETECTED:",
                    text
                )

            last_plate_text = text

        last_ocr_box = box

        last_ocr_time = time.time()


    # ========================================================
    # DRAW PLATE
    # ========================================================

    for detection in last_boxes:

        x1, y1, x2, y2 = (
            detection["box"]
        )

        confidence = (
            detection["confidence"]
        )

        # Plate box
        cv2.rectangle(

            frame,

            (x1, y1),

            (x2, y2),

            (0, 255, 0),

            2
        )

        # ----------------------------------------------------
        # ONLY NUMBER PLATE TEXT
        # ----------------------------------------------------

        label = "PLATE"

        if (
            last_ocr_box is not None
            and
            box_distance(
                detection["box"],
                last_ocr_box
            ) < 80
            and
            last_plate_text
        ):

            label = last_plate_text

        cv2.putText(

            frame,

            label,

            (
                x1,
                max(
                    y1 - 10,
                    25
                )
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.7,

            (0, 255, 0),

            2
        )


    # ========================================================
    # FPS
    # ========================================================

    fps_counter += 1

    if (
        time.time() -
        fps_timer
        >= 1.0
    ):

        elapsed = (
            time.time()
            -
            fps_timer
        )

        display_fps = (
            fps_counter /
            elapsed
        )

        fps_counter = 0

        fps_timer = time.time()


    # ========================================================
    # MINIMAL DISPLAY
    # ========================================================

    cv2.putText(

        frame,

        f"FPS: {display_fps:.1f}",

        (20, 35),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.6,

        (0, 255, 0),

        2
    )

    # ========================================================
    # SHOW
    # ========================================================

    cv2.imshow(

        "UrbanPulse AI - Number Plate",

        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


# ============================================================
# CLEANUP
# ============================================================

cap.release()

cv2.destroyAllWindows()


# ============================================================
# SUMMARY
# ============================================================

print()
print("==========================================")
print("       NUMBER PLATE SUMMARY")
print("==========================================")

if detected_plates:

    for plate in sorted(
        detected_plates
    ):

        print(
            plate
        )

else:

    print(
        "No readable plate detected."
    )

print("==========================================")
print("DONE")
print("==========================================")