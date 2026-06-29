import cv2
import math
import time

NEON = (255, 255, 0)

points = []
MAX_POINTS = 10000

smoothed = None
last_point = None
last_seen = None

fist_start = None
pinch_start = None

stable_gesture = "NONE"
pending_gesture = None
pending_since = None

GESTURE_DEBOUNCE = 0.08
HAND_TIMEOUT = 0.3

PINCH_HOLD = 0.12
FIST_HOLD = 0.55

ERASE_RADIUS_FRAC = 0.05
PINCH_FRAC = 0.06

SMOOTH_ALPHA = 0.38


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def lerp(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t))


def gesture(hand):
    lm = hand.landmark
    m = 0.02

    index_up = lm[8].y < lm[6].y - m
    middle_up = lm[12].y < lm[10].y - m
    ring_up = lm[16].y < lm[14].y - m
    pinky_up = lm[20].y < lm[18].y - m

    if index_up and not (middle_up or ring_up or pinky_up):
        return "DRAW"

    if not (index_up or middle_up or ring_up or pinky_up):
        return "CLEAR"

    return "IDLE"


def run(frame, results):
    global points, smoothed, last_point, last_seen
    global fist_start, pinch_start
    global stable_gesture, pending_gesture, pending_since

    h, w, _ = frame.shape
    now = time.time()
    diag = math.hypot(w, h)
    erase_radius = diag * ERASE_RADIUS_FRAC
    pinch_thresh = diag * PINCH_FRAC

    if results.multi_hand_landmarks:
        hand = results.multi_hand_landmarks[0]
        lm = hand.landmark

        ix, iy = int(lm[8].x * w), int(lm[8].y * h)
        tx, ty = int(lm[4].x * w), int(lm[4].y * h)
        raw = (ix, iy)

        if smoothed is None or now - (last_seen or 0) > HAND_TIMEOUT:
            smoothed = raw
        else:
            smoothed = lerp(smoothed, raw, SMOOTH_ALPHA)

        current = smoothed
        last_seen = now

        g_raw = gesture(hand)
        if g_raw == stable_gesture:
            pending_gesture = None
        else:
            if pending_gesture != g_raw:
                pending_gesture = g_raw
                pending_since = now
            elif now - pending_since >= GESTURE_DEBOUNCE:
                stable_gesture = g_raw
                pending_gesture = None
        g = stable_gesture

        # pinch is checked independent of gesture state so an open hand
        # pinching (thumb+index together, other fingers relaxed) still
        # triggers erase, not just a strict "DRAW" pose
        pinch = dist((ix, iy), (tx, ty))
        is_pinching = pinch < pinch_thresh

        if is_pinching:
            pinch_start = pinch_start or now
            erasing = now - pinch_start > PINCH_HOLD
        else:
            pinch_start = None
            erasing = False

        if erasing:
            last_point = None
            fist_start = None
            points = [p for p in points if dist(p, current) >= erase_radius]
            cv2.circle(frame, current, int(erase_radius), NEON, 2)

        elif g == "DRAW":
            fist_start = None
            if last_point is None:
                last_point = current
            d = dist(last_point, current)
            if d > 1:
                steps = max(1, int(d / 2))
                for i in range(steps):
                    points.append(lerp(last_point, current, i / steps))
                points.append(current)
                last_point = current

        elif g == "CLEAR":
            last_point = None
            fist_start = fist_start or now
            if now - fist_start > FIST_HOLD:
                points.clear()
                fist_start = None

        else:
            last_point = None
            fist_start = None

        cv2.circle(frame, current, 6, NEON, -1)

        if len(points) > MAX_POINTS:
            points = points[-MAX_POINTS:]

    else:
        last_point = None
        fist_start = None
        pinch_start = None

    for i in range(1, len(points)):
        p1, p2 = points[i - 1], points[i]
        speed = dist(p1, p2)
        thickness = max(2, min(8, int(speed / 4)))
        cv2.line(frame, p1, p2, NEON, thickness)

    cv2.rectangle(frame, (10, h - 50), (260, h - 10), (0, 0, 0), -1)
    cv2.putText(frame, f"MODE: {stable_gesture}",
                (20, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, NEON, 2)
    cv2.putText(frame, "INDEX draw | FIST clear | PINCH erase",
                (20, h - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, NEON, 1)

    return frame