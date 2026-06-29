import cv2
import math

NEON = (255, 255, 0)

smooth_nodes = None
SMOOTH = 0.35


def lerp(a, b, t):
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t)
    )


def glow_line(frame, p1, p2, thickness=2):

    cv2.line(
        frame,
        p1,
        p2,
        NEON,
        thickness + 10,
        cv2.LINE_AA
    )

    cv2.line(
        frame,
        p1,
        p2,
        NEON,
        thickness + 4,
        cv2.LINE_AA
    )

    cv2.line(
        frame,
        p1,
        p2,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA
    )


def glow_dot(frame, pos, radius=5):

    cv2.circle(
        frame,
        pos,
        radius + 8,
        NEON,
        2,
        cv2.LINE_AA
    )

    cv2.circle(
        frame,
        pos,
        radius + 3,
        NEON,
        2,
        cv2.LINE_AA
    )

    cv2.circle(
        frame,
        pos,
        radius,
        (255, 255, 255),
        -1,
        cv2.LINE_AA
    )


def smooth(points):

    global smooth_nodes

    if smooth_nodes is None:
        smooth_nodes = points
        return points

    out = []

    for old, new in zip(smooth_nodes, points):
        out.append(lerp(old, new, SMOOTH))

    smooth_nodes = out

    return out


def hud(frame, active):

    h, w, _ = frame.shape

    text = (
        "Show 2 finger of each hand to create shape"
        if not active else
        "LIVE SHAPE TRACKING"
    )

    width = 400
    height = 34

    x = 18
    y = h - 55

    cv2.rectangle(
        frame,
        (x, y),
        (x + width, y + height),
        (0, 0, 0),
        -1
    )

    cv2.rectangle(
        frame,
        (x, y),
        (x + width, y + height),
        NEON,
        1
    )

    cv2.putText(
        frame,
        text,
        (x + 12, y + 22),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        NEON,
        1,
        cv2.LINE_AA
    )


def run(frame, results):

    global smooth_nodes

    h, w, _ = frame.shape

    if not results.multi_hand_landmarks:
        smooth_nodes = None
        hud(frame, False)
        return frame

    hands = results.multi_hand_landmarks

    if len(hands) < 2:
        smooth_nodes = None
        hud(frame, False)
        return frame

    hand1 = hands[0]
    hand2 = hands[1]

    pts = []

    ids = [
        (hand1, 8),
        (hand1, 4),
        (hand2, 8),
        (hand2, 4)
    ]

    for hand, idx in ids:

        lm = hand.landmark[idx]

        x = int(lm.x * w)
        y = int(lm.y * h)

        pts.append((x, y))

    pts = smooth(pts)

    center_x = sum(p[0] for p in pts) // 4
    center_y = sum(p[1] for p in pts) // 4

    ordered = sorted(
        pts,
        key=lambda p: math.atan2(
            p[1] - center_y,
            p[0] - center_x
        )
    )

    for i in range(len(ordered)):

        p1 = ordered[i]
        p2 = ordered[(i + 1) % len(ordered)]

        glow_line(frame, p1, p2, 2)

    for p in ordered:
        glow_dot(frame, p, 5)

    glow_dot(frame, (center_x, center_y), 4)

    for p in ordered:

        dx = p[0] - center_x
        dy = p[1] - center_y

        length = math.hypot(dx, dy)

        if length < 1:
            continue

        ex = int(center_x + dx * 1.18)
        ey = int(center_y + dy * 1.18)

        cv2.line(
            frame,
            p,
            (ex, ey),
            NEON,
            1,
            cv2.LINE_AA
        )

    hud(frame, True)

    return frame