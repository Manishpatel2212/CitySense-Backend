from ultralytics import YOLO
import cv2
import time

# ============================================================
# CONFIG
# ============================================================

MODEL_PATH = "best.pt"
VIDEO_PATH = "demo1.mp4"

CONFIDENCE = 0.25
IMAGE_SIZE = 416

# Run AI every 3rd frame
PROCESS_EVERY_N_FRAMES = 3


# ============================================================
# SEVERITY CALCULATION
# ============================================================

def calculate_severity(
    x1,
    y1,
    x2,
    y2,
    confidence,
    frame_width,
    frame_height
):

    box_width = x2 - x1
    box_height = y2 - y1

    box_area = box_width * box_height

    frame_area = frame_width * frame_height

    area_percentage = (
        box_area / frame_area
    ) * 100

    # Area contribution
    area_score = min(
        area_percentage * 8,
        70
    )

    # Confidence contribution
    confidence_score = confidence * 30

    score = area_score + confidence_score

    score = min(
        max(score, 0),
        100
    )

    if score < 30:

        severity = "LOW"

    elif score < 60:

        severity = "MEDIUM"

    else:

        severity = "HIGH"

    return severity, int(score), area_percentage


# ============================================================
# LOAD MODEL
# ============================================================

print()
print("==========================================")
print("       citysense AI")
print("       ROAD DAMAGE ANALYSIS")
print("==========================================")
print()

print("Loading model...")

model = YOLO(MODEL_PATH)

print("Model loaded successfully.")
print("Classes:", model.names)
print("GPU: NVIDIA RTX 4050")

# ============================================================
# OPEN VIDEO
# ============================================================

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():

    print("ERROR: Video open nahi hua")
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

total_video_frames = int(
    cap.get(cv2.CAP_PROP_FRAME_COUNT)
)

video_duration = (
    total_video_frames / video_fps
)

print(
    f"Video Resolution: "
    f"{frame_width}x{frame_height}"
)

print(
    f"Video FPS: {video_fps:.1f}"
)

print(
    f"Video Duration: "
    f"{video_duration:.1f} seconds"
)

print()
print("Road Damage Detection Started...")
print("Press Q to stop.")
print()

# ============================================================
# LIVE VARIABLES
# ============================================================

frame_number = 0

last_detections = []

last_status = "ROAD OK"

last_severity = "NONE"

last_damage_score = 0


# ============================================================
# REPORT VARIABLES
# ============================================================

total_detections = 0

max_potholes_in_frame = 0

highest_damage_score = 0

damage_score_sum = 0

damage_score_count = 0

low_count = 0

medium_count = 0

high_count = 0

damaged_frames = 0

road_ok_frames = 0


# ============================================================
# FPS VARIABLES
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
    # YOLO DETECTION
    # ========================================================

    if frame_number % PROCESS_EVERY_N_FRAMES == 0:

        results = model.predict(

            source=frame,

            conf=CONFIDENCE,

            imgsz=IMAGE_SIZE,

            device=0,

            half=True,

            verbose=False,

            max_det=30

        )[0]

        detections = []

        # ====================================================
        # PROCESS DETECTIONS
        # ====================================================

        if results.boxes is not None:

            for box in results.boxes:

                confidence = float(
                    box.conf[0]
                )

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0]
                )

                severity, score, area_percentage = (
                    calculate_severity(

                        x1,
                        y1,
                        x2,
                        y2,

                        confidence,

                        frame_width,
                        frame_height
                    )
                )

                detections.append({

                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,

                    "confidence":
                        confidence,

                    "severity":
                        severity,

                    "score":
                        score,

                    "area":
                        area_percentage
                })

        # ====================================================
        # SAVE CURRENT DETECTIONS
        # ====================================================

        last_detections = detections

        current_potholes = len(
            detections
        )

        # ====================================================
        # REPORT STATISTICS
        # ====================================================

        total_detections += (
            current_potholes
        )

        max_potholes_in_frame = max(
            max_potholes_in_frame,
            current_potholes
        )

        if current_potholes > 0:

            damaged_frames += 1

        else:

            road_ok_frames += 1

        # ----------------------------------------------------
        # INDIVIDUAL SEVERITY COUNTS
        # ----------------------------------------------------

        for detection in detections:

            severity = detection[
                "severity"
            ]

            score = detection[
                "score"
            ]

            damage_score_sum += score

            damage_score_count += 1

            highest_damage_score = max(
                highest_damage_score,
                score
            )

            if severity == "LOW":

                low_count += 1

            elif severity == "MEDIUM":

                medium_count += 1

            elif severity == "HIGH":

                high_count += 1

        # ====================================================
        # OVERALL ROAD CONDITION
        # ====================================================

        if current_potholes == 0:

            last_status = "ROAD OK"

            last_severity = "NONE"

            last_damage_score = 0

        else:

            last_status = "ROAD DAMAGED"

            # Average score
            frame_score = sum(
                d["score"]
                for d in detections
            ) / current_potholes

            # Extra penalty for multiple potholes
            frame_score += (
                current_potholes - 1
            ) * 10

            last_damage_score = int(
                min(frame_score, 100)
            )

            if last_damage_score < 30:

                last_severity = "LOW"

            elif last_damage_score < 60:

                last_severity = "MEDIUM"

            else:

                last_severity = "HIGH"


    # ========================================================
    # DRAW DETECTIONS
    # ========================================================

    for detection in last_detections:

        x1 = detection["x1"]
        y1 = detection["y1"]
        x2 = detection["x2"]
        y2 = detection["y2"]

        confidence = detection[
            "confidence"
        ]

        severity = detection[
            "severity"
        ]

        score = detection[
            "score"
        ]

        # ----------------------------------------------------
        # BOX
        # ----------------------------------------------------

        cv2.rectangle(

            frame,

            (x1, y1),

            (x2, y2),

            (0, 0, 255),

            3
        )

        # ----------------------------------------------------
        # LABEL
        # ----------------------------------------------------

        label = (
            f"Pothole | "
            f"{severity} | "
            f"{score}/100"
        )

        cv2.putText(

            frame,

            label,

            (
                x1,
                max(y1 - 10, 25)
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.55,

            (0, 0, 255),

            2
        )

        # Confidence

        cv2.putText(

            frame,

            f"Conf: {confidence:.2f}",

            (
                x1,
                min(
                    y2 + 20,
                    frame_height - 10
                )
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.45,

            (255, 255, 255),

            1
        )


    # ========================================================
    # FPS
    # ========================================================

    fps_counter += 1

    if time.time() - fps_timer >= 1.0:

        elapsed = (
            time.time() - fps_timer
        )

        display_fps = (
            fps_counter / elapsed
        )

        fps_counter = 0

        fps_timer = time.time()


    # ========================================================
    # DASHBOARD
    # ========================================================

    cv2.rectangle(

        frame,

        (10, 10),

        (450, 225),

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

        (320, 38),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.5,

        (0, 255, 0),

        2
    )

    # Road status

    cv2.putText(

        frame,

        f"ROAD: {last_status}",

        (20, 72),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.6,

        (0, 255, 255),

        2
    )

    # Potholes

    cv2.putText(

        frame,

        f"POTHOLES: {len(last_detections)}",

        (20, 105),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.55,

        (255, 255, 255),

        2
    )

    # Severity

    cv2.putText(

        frame,

        f"SEVERITY: {last_severity}",

        (20, 138),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.6,

        (0, 165, 255),

        2
    )

    # Score

    cv2.putText(

        frame,

        f"DAMAGE SCORE: {last_damage_score}/100",

        (20, 171),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.55,

        (255, 255, 255),

        2
    )

    # AI status

    cv2.putText(

        frame,

        "AI: ACTIVE",

        (20, 204),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.5,

        (0, 255, 0),

        2
    )


    # ========================================================
    # DISPLAY
    # ========================================================

    cv2.imshow(

        "UrbanPulse AI - Road Damage",

        frame
    )

    # ========================================================
    # QUIT
    # ========================================================

    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


# ============================================================
# FINAL REPORT
# ============================================================

cap.release()

cv2.destroyAllWindows()


# ============================================================
# CALCULATE FINAL STATISTICS
# ============================================================

if damage_score_count > 0:

    average_damage_score = (
        damage_score_sum /
        damage_score_count
    )

else:

    average_damage_score = 0


# Overall road score
overall_score = (
    average_damage_score
)

# Add damage density
if frame_number > 0:

    damage_percentage = (
        damaged_frames /
        max(
            damaged_frames +
            road_ok_frames,
            1
        )
    ) * 100

else:

    damage_percentage = 0


# Combine score and damage frequency
overall_score = (
    overall_score * 0.7
    +
    min(damage_percentage, 100)
    * 0.3
)

overall_score = int(
    min(overall_score, 100)
)


# ============================================================
# FINAL ROAD CONDITION
# ============================================================

if total_detections == 0:

    final_condition = "GOOD"

    final_severity = "NONE"

elif overall_score < 30:

    final_condition = "DAMAGED"

    final_severity = "LOW"

elif overall_score < 60:

    final_condition = "DAMAGED"

    final_severity = "MEDIUM"

else:

    final_condition = "SEVERELY DAMAGED"

    final_severity = "HIGH"


# ============================================================
# PRINT FINAL REPORT
# ============================================================

print()
print()
print("================================================")
print("           URBANPULSE AI ROAD REPORT")
print("================================================")

print()

print(
    f"Video File              : {VIDEO_PATH}"
)

print(
    f"Video Duration          : "
    f"{video_duration:.1f} seconds"
)

print(
    f"Frames Analyzed         : "
    f"{frame_number}"
)

print()

print(
    f"Total Pothole Detections: "
    f"{total_detections}"
)

print(
    f"Maximum Potholes/Frame  : "
    f"{max_potholes_in_frame}"
)

print(
    f"Frames With Damage      : "
    f"{damaged_frames}"
)

print(
    f"Damage Coverage         : "
    f"{damage_percentage:.1f}%"
)

print()

print(
    f"LOW Severity            : "
    f"{low_count}"
)

print(
    f"MEDIUM Severity         : "
    f"{medium_count}"
)

print(
    f"HIGH Severity           : "
    f"{high_count}"
)

print()

print(
    f"Average Damage Score    : "
    f"{average_damage_score:.1f}/100"
)

print(
    f"Highest Damage Score    : "
    f"{highest_damage_score}/100"
)

print()

print(
    "------------------------------------------------"
)

print(
    f"FINAL ROAD CONDITION    : "
    f"{final_condition}"
)

print(
    f"FINAL SEVERITY          : "
    f"{final_severity}"
)

print(
    f"OVERALL DAMAGE SCORE    : "
    f"{overall_score}/100"
)

print(
    "------------------------------------------------"
)

print()
print("              ANALYSIS COMPLETE")
print("================================================")