from flask import Flask, Response, send_from_directory, request
import cv2
import mediapipe as mp
import importlib

app = Flask(__name__, static_folder="web")

cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
hands_detector = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7
)

current_effect = "draw"

effects = {
    "draw": importlib.import_module("effects.draw"),
    "box": importlib.import_module("effects.box"),
}


@app.route("/")
def index():
    return send_from_directory("web", "index.html")


@app.route("/app.js")
def js():
    return send_from_directory("web", "app.js")


@app.route("/styles.css")
def css():
    return send_from_directory("web", "styles.css")


@app.route("/effect/<name>")
def set_effect(name):
    global current_effect

    if name in effects:
        current_effect = name

    return "ok"


def generate_frames():
    global current_effect

    while True:
        success, frame = cap.read()

        if not success:
            break

        frame = cv2.flip(frame, 1)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands_detector.process(rgb)

        frame = effects[current_effect].run(frame, results)

        ret, buffer = cv2.imencode(".jpg", frame)

        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes +
            b"\r\n"
        )


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":
    app.run(debug=True)