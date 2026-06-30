# upgraded fluid.py
# keeps original aesthetic/style
# MUCH faster
# supports both hands
# smoother motion
# lower CPU usage
# better particle handling

import cv2
import math
import random
import numpy as np

NEON = (255, 255, 0)

GRID = 22

FLOW_DECAY = 0.965

FLOW_FORCE = 0.13

PARTICLE_FORCE = 0.13

PARTICLE_DRAG = 0.972

MAX_PARTICLES = 2200

velocity = None

particles = []

last_points = {}


class Particle:

    __slots__ = (

        "x",
        "y",
        "vx",
        "vy",
        "life"

    )

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.vx = random.uniform(
            -1,
            1
        )

        self.vy = random.uniform(
            -1,
            1
        )

        self.life = random.randint(
            40,
            90
        )

    def update(self):

        self.x += self.vx
        self.y += self.vy

        self.life -= 1

    def alive(self, w, h):

        return (

            self.life > 0 and

            -30 < self.x < w + 30 and
            -30 < self.y < h + 30

        )


def glow_line(frame, p1, p2, thickness=1):

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


def glow_dot(frame, pos, radius=3):

    cv2.circle(

        frame,

        pos,

        radius + 4,

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


def init_field(w, h):

    global velocity

    cols = w // GRID
    rows = h // GRID

    velocity = np.zeros(

        (rows, cols, 2),

        dtype=np.float32

    )


def disturb(x, y, dx, dy):

    global velocity

    rows, cols, _ = velocity.shape

    gx = int(x / GRID)
    gy = int(y / GRID)

    radius = 3

    for yy in range(-radius, radius + 1):

        ny = gy + yy

        if ny < 0 or ny >= rows:
            continue

        for xx in range(-radius, radius + 1):

            nx = gx + xx

            if nx < 0 or nx >= cols:
                continue

            dist = xx * xx + yy * yy

            if dist > radius * radius:
                continue

            power = 1 - (
                math.sqrt(dist)
                / radius
            )

            velocity[ny, nx, 0] += (
                dx
                * power
                * FLOW_FORCE
            )

            velocity[ny, nx, 1] += (
                dy
                * power
                * FLOW_FORCE
            )


def update_field():

    global velocity

    velocity *= FLOW_DECAY

    velocity = cv2.blur(

        velocity,

        (3, 3)

    )


def draw_field(frame):

    rows, cols, _ = velocity.shape

    for gy in range(rows):

        py = gy * GRID

        for gx in range(cols):

            vx, vy = velocity[gy, gx]

            mag = abs(vx) + abs(vy)

            if mag < 0.18:
                continue

            px = gx * GRID

            ex = int(px + vx * 12)
            ey = int(py + vy * 12)

            glow_line(

                frame,

                (px, py),

                (ex, ey),

                1

            )


def update_particles(frame, w, h):

    global particles

    rows, cols, _ = velocity.shape

    alive = []

    for p in particles:

        gx = int(p.x / GRID)
        gy = int(p.y / GRID)

        if (

            0 <= gx < cols and
            0 <= gy < rows

        ):

            flow = velocity[gy, gx]

            p.vx += (
                flow[0]
                * PARTICLE_FORCE
            )

            p.vy += (
                flow[1]
                * PARTICLE_FORCE
            )

        p.vx *= PARTICLE_DRAG
        p.vy *= PARTICLE_DRAG

        p.update()

        if p.alive(w, h):

            glow_dot(

                frame,

                (
                    int(p.x),
                    int(p.y)
                ),

                2

            )

            alive.append(p)

    particles = alive[-MAX_PARTICLES:]


def hud(frame):

    h, _, _ = frame.shape

    cv2.rectangle(

        frame,

        (12, h - 54),

        (340, h - 12),

        (0, 0, 0),

        -1

    )

    cv2.putText(

        frame,

        "INTERACTIVE FLUID FIELD",

        (22, h - 27),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.68,

        NEON,

        2,

        cv2.LINE_AA

    )


def run(frame, results):

    global velocity
    global last_points

    h, w, _ = frame.shape

    if velocity is None:
        init_field(w, h)

    overlay = frame.copy()

    if results.multi_hand_landmarks:

        active = {}

        for hand_id, hand in enumerate(

            results.multi_hand_landmarks

        ):

            lm = hand.landmark[8]

            x = int(lm.x * w)
            y = int(lm.y * h)

            current = (x, y)

            active[hand_id] = current

            if hand_id in last_points:

                prev = last_points[hand_id]

                dx = current[0] - prev[0]
                dy = current[1] - prev[1]

                disturb(
                    x,
                    y,
                    dx,
                    dy
                )

                speed = math.hypot(
                    dx,
                    dy
                )

                if speed > 1.5:

                    count = min(
                        14,
                        int(speed * 0.45)
                    )

                    for _ in range(count):

                        particles.append(

                            Particle(
                                x,
                                y
                            )

                        )

            glow_dot(
                overlay,
                current,
                6
            )

        last_points = active

    else:

        last_points.clear()

    update_field()

    draw_field(overlay)

    update_particles(
        overlay,
        w,
        h
    )

    frame = cv2.addWeighted(

        overlay,
        0.82,

        frame,
        0.18,

        0

    )

    hud(frame)

    return frame