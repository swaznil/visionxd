import cv2
import math
import time

NEON = (255, 255, 0)

MAX_POINTS = 12000

GESTURE_DEBOUNCE = 0.08
HAND_TIMEOUT = 0.25

PINCH_HOLD = 0.12
FIST_HOLD = 0.7

ERASE_RADIUS_FRAC = 0.05
PINCH_FRAC = 0.06

SMOOTH_ALPHA = 0.4
MAX_CONNECT_DIST_FRAC = 0.035

points = []

smoothed = None
last_point = None
last_seen = None

stable_gesture = "NONE"
pending_gesture = None
pending_since = None

fist_start = None
pinch_start = None

hand_present_last = False


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def lerp(a, b, t):
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t)
    )


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


def draw_progress(frame, x, y, w, h, progress):
    cv2.rectangle(frame, (x, y), (x + w, y + h), (60, 60, 60), 2)

    fill = int(w * max(0, min(1, progress)))

    if fill > 0:
        cv2.rectangle(frame, (x, y), (x + fill, y + h), NEON, -1)


def run(frame, results):
    global points
    global smoothed
    global last_point
    global last_seen

    global stable_gesture
    global pending_gesture
    global pending_since

    global fist_start
    global pinch_start

    global hand_present_last

    h, w, _ = frame.shape

    now = time.time()

    diag = math.hypot(w, h)

    erase_radius = diag * ERASE_RADIUS_FRAC
    pinch_thresh = diag * PINCH_FRAC
    max_connect_dist = diag * MAX_CONNECT_DIST_FRAC

    if results.multi_hand_landmarks:
        hand = results.multi_hand_landmarks[0]
        lm = hand.landmark

        ix = int(lm[8].x * w)
        iy = int(lm[8].y * h)

        tx = int(lm[4].x * w)
        ty = int(lm[4].y * h)

        raw = (ix, iy)

        reappeared = (
            not hand_present_last or
            last_seen is None or
            now - last_seen > HAND_TIMEOUT
        )

        if smoothed is None or reappeared:
            smoothed = raw
            last_point = None
        else:
            smoothed = lerp(smoothed, raw, SMOOTH_ALPHA)

        current = smoothed

        last_seen = now
        hand_present_last = True

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
                last_point = None

        g = stable_gesture

        pinch = dist((ix, iy), (tx, ty))

        is_pinching = g != "CLEAR" and pinch < pinch_thresh

        if is_pinching:
            pinch_start = pinch_start or now
            erasing = now - pinch_start >= PINCH_HOLD
        else:
            pinch_start = None
            erasing = False

        if erasing:
            last_point = None
            fist_start = None

            filtered = []

            for p in points:
                if p is None:
                    filtered.append(None)
                    continue

                if dist(p, current) >= erase_radius:
                    filtered.append(p)

            points = filtered

            cv2.circle(frame, current, int(erase_radius), NEON, 2)

        elif g == "DRAW":
            fist_start = None

            if last_point is None:
                last_point = current
                points.append(None)
                points.append(current)

            else:
                jump = dist(last_point, current)

                if jump > max_connect_dist:
                    points.append(None)
                    points.append(current)
                    last_point = current

                elif jump > 1:
                    steps = max(1, int(jump / 2))

                    for i in range(1, steps + 1):
                        p = lerp(last_point, current, i / steps)
                        points.append(p)

                    last_point = current
                    
        elif g == "CLEAR":

            last_point = None

            fist_start = fist_start or now

            hold = now - fist_start

            progress = hold / FIST_HOLD

            bw = 200
            bh = 18

            bx = (w - bw) // 2
            by = 26

            bg = frame.copy()

            cv2.rectangle(

                bg,

                (bx - 14, by - 34),

                (bx + bw + 14, by + bh + 14),

                (0, 0, 0),

                -1

            )

            cv2.addWeighted(

                bg,
                0.45,

                frame,
                0.55,

                0,

                frame

            )

            cv2.rectangle(

                frame,

                (bx, by),

                (bx + bw, by + bh),

                (45, 45, 45),

                1

            )

            fill = int(

                bw * max(
                    0,
                    min(1, progress)
                )

            )

            if fill > 0:

                cv2.rectangle(

                    frame,

                    (bx, by),

                    (bx + fill, by + bh),

                    NEON,

                    -1

                )

            cv2.putText(

                frame,

                "CLEARING CANVAS",

                (bx + 18, by - 10),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.52,

                NEON,

                1,

                cv2.LINE_AA

            )

            if hold >= FIST_HOLD:

                points.clear()

                fist_start = None

        else:
            last_point = None
            fist_start = None

        cv2.circle(frame, current, 6, NEON, -1)

        if len(points) > MAX_POINTS:
            points = points[-MAX_POINTS:]

    else:
        smoothed = None
        last_point = None
        fist_start = None
        pinch_start = None
        hand_present_last = False

    prev = None

    for p in points:
        if p is None:
            prev = None
            continue

        if prev is not None:
            speed = dist(prev, p)

            thickness = max(2, min(6, int(7 - speed / 6)))

            cv2.line(frame, prev, p, NEON, thickness)

        prev = p

    cv2.rectangle(frame, (10, h - 52), (300, h - 10), (0, 0, 0), -1)

    cv2.putText(
        frame,
        f"MODE: {stable_gesture}",
        (20, h - 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        NEON,
        2
    )

    cv2.putText(
        frame,
        "INDEX draw | FIST clear | PINCH erase",
        (20, h - 12),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.42,
        NEON,
        1
    )

    return frame