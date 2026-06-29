import cv2
import math

NEON = (255, 255, 0)


def glow_line(frame, p1, p2, color, thickness=2):
    cv2.line(frame, p1, p2, color, thickness + 8)
    cv2.line(frame, p1, p2, color, thickness + 4)
    cv2.line(frame, p1, p2, color, thickness)


def glow_circle(frame, pos, radius, color):
    cv2.circle(frame, pos, radius + 10, color, 2)
    cv2.circle(frame, pos, radius + 5, color, 2)
    cv2.circle(frame, pos, radius, color, -1)


def corner(frame, x, y, size=20):

    glow_line(frame, (x, y), (x + size, y), NEON)
    glow_line(frame, (x, y), (x, y + size), NEON)


def run(frame, results):

    h, w, _ = frame.shape

    if results.multi_hand_landmarks and len(results.multi_hand_landmarks) >= 2:

        hand1 = results.multi_hand_landmarks[0]
        hand2 = results.multi_hand_landmarks[1]

        i1 = hand1.landmark[8]
        i2 = hand2.landmark[8]

        t1 = hand1.landmark[4]
        t2 = hand2.landmark[4]

        points = [
            (int(i1.x * w), int(i1.y * h)),
            (int(t1.x * w), int(t1.y * h)),
            (int(i2.x * w), int(i2.y * h)),
            (int(t2.x * w), int(t2.y * h)),
        ]

        xs = [p[0] for p in points]
        ys = [p[1] for p in points]

        x1 = min(xs)
        y1 = min(ys)

        x2 = max(xs)
        y2 = max(ys)

        glow_line(frame, (x1, y1), (x2, y1), NEON)
        glow_line(frame, (x2, y1), (x2, y2), NEON)
        glow_line(frame, (x2, y2), (x1, y2), NEON)
        glow_line(frame, (x1, y2), (x1, y1), NEON)

        corner(frame, x1, y1)
        corner(frame, x2 - 20, y1)
        corner(frame, x1, y2 - 20)
        corner(frame, x2 - 20, y2 - 20)

        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        glow_circle(frame, (cx, cy), 10, NEON)

        cv2.putText(
            frame,
            "HeHe",
            (x1, y1 - 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            NEON,
            2
        )

    return frame
