import cv2
import math

points = []
MAX_POINTS = 500

def run(frame, results):
    h, w, _ = frame.shape

    if results.multi_hand_landmarks:
        for hand in results.multi_hand_landmarks:
            lm = hand.landmark[8]

            x = int(lm.x * w)
            y = int(lm.y * h)

            if points:
                px, py = points[-1]
                if math.hypot(x - px, y - py) < 50:
                    points.append((x, y))
            else:
                points.append((x, y))

            if len(points) > MAX_POINTS:
                points.pop(0)

            cv2.circle(frame, (x, y), 10, (255, 255, 0), -1)

    for i in range(1, len(points)):
        cv2.line(frame, points[i - 1], points[i], (255, 255, 0), 3)

    return frame