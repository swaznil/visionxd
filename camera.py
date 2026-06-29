import cv2
import mediapipe as mp

from PySide6.QtCore import QThread
from PySide6.QtCore import Signal

from PySide6.QtGui import QImage

from effects import effects


class CameraThread(QThread):

    frameReady = Signal(QImage)

    fpsReady = Signal(int)

    def __init__(self):

        super().__init__()

        self.running = True

        self.current_effect = "Draw"

        self.cap = cv2.VideoCapture(0)

        self.mpHands = mp.solutions.hands

        self.hands = self.mpHands.Hands(
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

    def setEffect(self, name):

        if name in effects:
            self.current_effect = name

    def stop(self):

        self.running = False

        self.wait()

    def run(self):

        timer = cv2.TickMeter()

        while self.running:

            ok, frame = self.cap.read()

            if not ok:
                continue

            frame = cv2.flip(frame, 1)

            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            results = self.hands.process(rgb)

            frame = effects[self.current_effect].run(
                frame,
                results
            )

            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            h, w, c = rgb.shape

            img = QImage(
                rgb.data,
                w,
                h,
                c * w,
                QImage.Format_RGB888
            )

            self.frameReady.emit(img.copy())

            timer.stop()

            if timer.getTimeSec() > 0:
                fps = int(1 / timer.getTimeSec())
                self.fpsReady.emit(fps)

            timer.reset()
            timer.start()

        self.cap.release()