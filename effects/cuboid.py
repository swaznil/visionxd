import cv2
import math
import numpy as np

NEON = (255, 255, 0)

ROT_SMOOTH = 0.18
MOVE_SMOOTH = 0.2
SCALE_SMOOTH = 0.15

rot_x = 0
rot_y = 0

target_rot_x = 0
target_rot_y = 0

cube_scale = 1.0
target_scale = 1.0

center_x = 0
center_y = 0

smooth_center = None

last_pinch = None


def lerp(a, b, t):
    return a + (b - a) * t


def smooth_point(old, new, t):

    return (
        int(lerp(old[0], new[0], t)),
        int(lerp(old[1], new[1], t))
    )


def dist(a, b):

    return math.hypot(
        a[0] - b[0],
        a[1] - b[1]
    )


def glow_line(frame, p1, p2, thickness=2):

    cv2.line(
        frame,
        p1,
        p2,
        NEON,
        thickness + 12,
        cv2.LINE_AA
    )

    cv2.line(
        frame,
        p1,
        p2,
        NEON,
        thickness + 5,
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
        radius,
        (255, 255, 255),
        -1,
        cv2.LINE_AA
    )


def rotate_x(point, angle):

    x, y, z = point

    c = math.cos(angle)
    s = math.sin(angle)

    y2 = y * c - z * s
    z2 = y * s + z * c

    return (x, y2, z2)


def rotate_y(point, angle):

    x, y, z = point

    c = math.cos(angle)
    s = math.sin(angle)

    x2 = x * c + z * s
    z2 = -x * s + z * c

    return (x2, y, z2)


def project(point, center, scale):

    x, y, z = point

    z += 5

    factor = 320 / z

    px = int(center[0] + x * factor * scale)
    py = int(center[1] + y * factor * scale)

    return (px, py)


VERTICES = [
    (-1, -1, -1),
    ( 1, -1, -1),
    ( 1,  1, -1),
    (-1,  1, -1),

    (-1, -1,  1),
    ( 1, -1,  1),
    ( 1,  1,  1),
    (-1,  1,  1),
]

EDGES = [
    (0,1),(1,2),(2,3),(3,0),
    (4,5),(5,6),(6,7),(7,4),
    (0,4),(1,5),(2,6),(3,7)
]


def energy_core(frame, center):

    for r in range(20, 90, 12):

        cv2.circle(
            frame,
            center,
            r,
            NEON,
            1,
            cv2.LINE_AA
        )

    cv2.circle(
        frame,
        center,
        8,
        (255, 255, 255),
        -1,
        cv2.LINE_AA
    )


def hud(frame):

    h, w, _ = frame.shape

    cv2.rectangle(
        frame,
        (12, h - 58),
        (460, h - 12),
        (0, 0, 0),
        -1
    )

    cv2.putText(
        frame,
        "AR HOLOGRAM CUBE",
        (24, h - 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.72,
        NEON,
        2,
        cv2.LINE_AA
    )


def run(frame, results):

    global rot_x
    global rot_y

    global target_rot_x
    global target_rot_y

    global cube_scale
    global target_scale

    global smooth_center
    global last_pinch

    h, w, _ = frame.shape

    if smooth_center is None:
        smooth_center = (w // 2, h // 2)

    if results.multi_hand_landmarks:

        hand = results.multi_hand_landmarks[0]

        lm = hand.landmark

        ix = int(lm[8].x * w)
        iy = int(lm[8].y * h)

        tx = int(lm[4].x * w)
        ty = int(lm[4].y * h)

        mx = int(lm[9].x * w)
        my = int(lm[9].y * h)

        wrist_x = int(lm[0].x * w)
        wrist_y = int(lm[0].y * h)

        target_rot_y = (ix - mx) * 0.02
        target_rot_x = (iy - wrist_y) * 0.015

        pinch = dist(
            (ix, iy),
            (tx, ty)
        )

        target_scale = max(
            0.5,
            min(3.0, pinch / 55)
        )

        smooth_center = smooth_point(
            smooth_center,
            (mx, my),
            MOVE_SMOOTH
        )

        glow_dot(frame, (ix, iy), 6)
        glow_dot(frame, (tx, ty), 6)

        glow_line(
            frame,
            (ix, iy),
            (tx, ty),
            2
        )

        cv2.circle(
            frame,
            smooth_center,
            int(target_scale * 70),
            NEON,
            1,
            cv2.LINE_AA
        )

    rot_x = lerp(
        rot_x,
        target_rot_x,
        ROT_SMOOTH
    )

    rot_y = lerp(
        rot_y,
        target_rot_y,
        ROT_SMOOTH
    )

    cube_scale = lerp(
        cube_scale,
        target_scale,
        SCALE_SMOOTH
    )

    projected = []

    depth = []

    for v in VERTICES:

        r = rotate_x(v, rot_x)
        r = rotate_y(r, rot_y)

        depth.append(r[2])

        p = project(
            r,
            smooth_center,
            cube_scale
        )

        projected.append(p)

    edge_depth = []

    for edge in EDGES:

        z = (
            depth[edge[0]] +
            depth[edge[1]]
        ) / 2

        edge_depth.append((z, edge))

    edge_depth.sort(reverse=True)

    for _, edge in edge_depth:

        p1 = projected[edge[0]]
        p2 = projected[edge[1]]

        glow_line(frame, p1, p2, 2)

    for p in projected:

        glow_dot(frame, p, 4)

    energy_core(
        frame,
        smooth_center
    )

    for p in projected:

        glow_line(
            frame,
            smooth_center,
            p,
            1
        )

    hud(frame)

    return frame