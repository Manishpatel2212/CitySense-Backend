from flask import Flask, render_template, Response, jsonify
import cv2
import supervision as sv
from ultralytics import YOLO
import time
import pyresearch

# Flask App Initialization
app = Flask(__name__)

# PyResearch Configuration Constants
PR_MODEL_PATH = "best.pt"

PR_DISPLAY_CONFIG = {
    "window_title": "PyResearch - Pothole Computer Vision Project",
    "window_size": (1280, 720),
    "color_scheme": "PR_DARK_BLUE",
    "fps_display": True
}

# Global variables
detection_count = 0
unique_pothole_ids = set()


class PyResearchVisualizer:
    """PyResearch Standard Visualization Engine"""

    def __init__(self):
        self.model = YOLO(PR_MODEL_PATH)

        self.box_annotator = sv.BoxAnnotator(
            thickness=2,
            color=sv.Color.from_hex("#0055FF")
        )

        self.label_annotator = sv.LabelAnnotator(
            text_scale=0.7,
            text_thickness=1,
            text_color=sv.Color.WHITE,
            text_padding=10
        )

    def process_frame(self, frame):
        """PyResearch Standard Processing Pipeline"""

        global detection_count, unique_pothole_ids

        # YOLO tracking
        results = self.model.track(
            frame,
            conf=0.25,
            imgsz=640,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False
        )[0]

        detections = sv.Detections.from_ultralytics(results)

        # Count unique potholes
        if detections.tracker_id is not None:
            for track_id, class_id in zip(
                detections.tracker_id,
                detections.class_id
            ):
                class_name = self.model.names[int(class_id)]

                if class_name == "pothole":
                    unique_pothole_ids.add(int(track_id))

        # Total unique potholes detected
        detection_count = len(unique_pothole_ids)

        # Draw bounding boxes
        annotated_frame = self.box_annotator.annotate(
            scene=frame,
            detections=detections
        )

        # Draw labels
        annotated_frame = self.label_annotator.annotate(
            scene=annotated_frame,
            detections=detections
        )

        return annotated_frame


def generate_frames():
    visualizer = PyResearchVisualizer()

    cap = cv2.VideoCapture("demo2.mp4")

    while cap.isOpened():
        success, frame = cap.read()

        if not success:
            break

        output_frame = visualizer.process_frame(frame)

        _, buffer = cv2.imencode(".jpg", output_frame)

        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes
            + b"\r\n"
        )

    cap.release()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/detection_count")
def get_detection_count():
    return jsonify({
        "detections": detection_count
    })


if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
