import os
import cv2
import time
import datetime
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

        self.cap.set(
            cv2.CAP_PROP_BUFFERSIZE,
            1
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_WIDTH,
            1280
        )

        self.cap.set(
            cv2.CAP_PROP_FRAME_HEIGHT,
            720
        )

        self.cap.set(
            cv2.CAP_PROP_FPS,
            60
        )

        self.mpHands = mp.solutions.hands

        self.hands = self.mpHands.Hands(

            max_num_hands=2,

            min_detection_confidence=0.7,

            min_tracking_confidence=0.7

        )

        self.recording = False

        self.writer = None

        self.currentFrame = None

        self.outputFolder = "captures"

        self.fpsHistory = []

        os.makedirs(
            self.outputFolder,
            exist_ok=True
        )

    def setEffect(self, name):

        if name in effects:

            self.current_effect = name

    def setOutputFolder(self, path):

        self.outputFolder = path

        os.makedirs(
            self.outputFolder,
            exist_ok=True
        )

    def startRecording(self):

        if self.recording:
            return

        width = int(
            self.cap.get(
                cv2.CAP_PROP_FRAME_WIDTH
            )
        )

        height = int(
            self.cap.get(
                cv2.CAP_PROP_FRAME_HEIGHT
            )
        )

        filename = os.path.join(

            self.outputFolder,

            datetime.datetime.now().strftime(
                "recording_%Y%m%d_%H%M%S.mp4"
            )

        )

        fourcc = cv2.VideoWriter_fourcc(
            *"mp4v"
        )

        self.writer = cv2.VideoWriter(

            filename,

            fourcc,

            30,

            (width, height)

        )

        self.recording = True

    def stopRecording(self):

        self.recording = False

        if self.writer:

            self.writer.release()

            self.writer = None

    def saveScreenshot(self):

        if self.currentFrame is None:
            return

        filename = os.path.join(

            self.outputFolder,

            datetime.datetime.now().strftime(
                "screenshot_%Y%m%d_%H%M%S.png"
            )

        )

        cv2.imwrite(
            filename,
            self.currentFrame
        )

    def stop(self):

        self.running = False

        self.wait()

    def run(self):

        timer = cv2.TickMeter()

        timer.start()

        while self.running:

            ok, frame = self.cap.read()

            if not ok:
                continue

            frame = cv2.flip(
                frame,
                1
            )

            rgb = cv2.cvtColor(

                frame,

                cv2.COLOR_BGR2RGB

            )

            results = self.hands.process(
                rgb
            )

            frame = effects[
                self.current_effect
            ].run(

                frame,
                results

            )

            self.currentFrame = frame.copy()

            if self.recording and self.writer:

                self.writer.write(frame)

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

            self.frameReady.emit(
                img.copy()
            )

            timer.stop()

            elapsed = timer.getTimeSec()

            if elapsed > 0:

                fps = 1 / elapsed

                self.fpsHistory.append(
                    fps
                )

                if len(self.fpsHistory) > 20:

                    self.fpsHistory.pop(0)

                smoothFPS = int(

                    sum(self.fpsHistory)
                    / len(self.fpsHistory)

                )

                self.fpsReady.emit(
                    smoothFPS
                )

            timer.reset()

            timer.start()

        self.cap.release()