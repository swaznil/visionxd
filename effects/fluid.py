import cv2
import math
import random
import numpy as np

NEON = (255, 255, 0)

GRID = 18

particles = []

velocity = None


class Particle:

    def __init__(self, x, y):

        self.x = x
        self.y = y

        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-1, 1)

        self.life = random.randint(40, 90)

    def update(self):

        self.x += self.vx
        self.y += self.vy

        self.life -= 1

    def alive(self):

        return self.life > 0


def glow_line(frame, p1, p2, thickness=1):

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


def glow_dot(frame, pos, radius=3):

    cv2.circle(
        frame,
        pos,
        radius + 5,
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

    radius = 4

    for yy in range(-radius, radius + 1):
        for xx in range(-radius, radius + 1):

            nx = gx + xx
            ny = gy + yy

            if (
                0 <= nx < cols and
                0 <= ny < rows
            ):

                d = math.hypot(xx, yy)

                if d > radius:
                    continue

                power = 1 - d / radius

                velocity[ny, nx, 0] += dx * power * 0.15
                velocity[ny, nx, 1] += dy * power * 0.15


def update_field():

    global velocity

    velocity *= 0.96

    velocity = cv2.blur(
        velocity,
        (3, 3)
    )


last = None


def run(frame, results):

    global velocity
    global last

    h, w, _ = frame.shape

    if velocity is None:
        init_field(w, h)

    overlay = frame.copy()

    if results.multi_hand_landmarks:

        hand = results.multi_hand_landmarks[0]

        lm = hand.landmark[8]

        x = int(lm.x * w)
        y = int(lm.y * h)

        current = (x, y)

        if last is not None:

            dx = current[0] - last[0]
            dy = current[1] - last[1]

            disturb(x, y, dx, dy)

            speed = math.hypot(dx, dy)

            count = int(speed * 0.8)

            for _ in range(count):

                particles.append(
                    Particle(x, y)
                )

        last = current

        glow_dot(frame, current, 7)

    else:
        last = None

    update_field()

    rows, cols, _ = velocity.shape

    for y in range(rows):

        for x in range(cols):

            vx, vy = velocity[y, x]

            px = x * GRID
            py = y * GRID

            ex = int(px + vx * 12)
            ey = int(py + vy * 12)

            mag = math.hypot(vx, vy)

            if mag > 0.2:

                glow_line(
                    overlay,
                    (px, py),
                    (ex, ey),
                    1
                )

    alive = []

    for p in particles:

        gx = int(p.x / GRID)
        gy = int(p.y / GRID)

        if (
            0 <= gx < cols and
            0 <= gy < rows
        ):

            flow = velocity[gy, gx]

            p.vx += flow[0] * 0.15
            p.vy += flow[1] * 0.15

        p.vx *= 0.97
        p.vy *= 0.97

        p.update()

        if p.alive():

            glow_dot(
                overlay,
                (int(p.x), int(p.y)),
                2
            )

            alive.append(p)

    particles[:] = alive

    frame = cv2.addWeighted(
        overlay,
        0.82,
        frame,
        0.18,
        0
    )

    cv2.rectangle(
        frame,
        (12, h - 55),
        (390, h - 12),
        (0, 0, 0),
        -1
    )

    cv2.putText(
        frame,
        "INTERACTIVE FLUID FIELD",
        (22, h - 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        NEON,
        2,
        cv2.LINE_AA
    )

    return frame