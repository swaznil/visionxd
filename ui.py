from PySide6.QtCore import Qt
from PySide6.QtCore import QSize

from PySide6.QtGui import QAction
from PySide6.QtGui import QPixmap

from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QMainWindow

from camera import CameraThread


class EffectButton(QPushButton):

    def __init__(self, text):

        super().__init__(text)

        self.setCursor(Qt.PointingHandCursor)

        self.setMinimumHeight(52)

        self.setCheckable(True)


class VisionWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("VisionXD")

        self.resize(1450, 900)

        self.setMinimumSize(1100, 700)

        self.camera = CameraThread()

        self.camera.frameReady.connect(
            self.updateFrame
        )

        self.camera.fpsReady.connect(
            self.updateFPS
        )

        root = QWidget()

        self.setCentralWidget(root)

        rootLayout = QVBoxLayout(root)

        rootLayout.setContentsMargins(16, 16, 16, 16)

        rootLayout.setSpacing(12)

        title = QHBoxLayout()

        logo = QLabel("VisionXD")

        logo.setObjectName("title")

        self.fps = QLabel("0 FPS")

        self.fps.setObjectName("fps")

        title.addWidget(logo)

        title.addStretch()

        title.addWidget(self.fps)

        rootLayout.addLayout(title)

        self.video = QLabel()

        self.video.setAlignment(Qt.AlignCenter)

        self.video.setObjectName("video")

        rootLayout.addWidget(
            self.video,
            1
        )

        dock = QFrame()

        dock.setObjectName("dock")

        dockLayout = QHBoxLayout(dock)

        dockLayout.setContentsMargins(
            18,
            18,
            18,
            18
        )

        self.buttons = {}

        for effect in [

            "Draw",

            "Box",

            "Cuboid",

            "Fluid",

        ]:

            btn = EffectButton(effect)

            btn.clicked.connect(

                lambda checked,
                name=effect:

                self.changeEffect(name)

            )

            dockLayout.addWidget(btn)

            self.buttons[effect] = btn

        self.buttons["Draw"].setChecked(True)

        rootLayout.addWidget(dock)

        self.setStyleSheet("""

QMainWindow{

background:#111;

}

QLabel#title{

font-size:30px;

font-weight:700;

color:white;

}

QLabel#fps{

color:#00ffff;

font-size:15px;

}

QLabel#video{

background:#1b1b1b;

border-radius:22px;

border:2px solid #2b2b2b;

}

QFrame#dock{

background:#181818;

border-radius:20px;

border:1px solid #2f2f2f;

}

QPushButton{

background:#202020;

border:none;

border-radius:14px;

font-size:16px;

color:white;

padding:14px;

}

QPushButton:hover{

background:#2b2b2b;

}

QPushButton:checked{

background:#00d7ff;

color:black;

font-weight:bold;

}

""")

        self.camera.start()

    def changeEffect(self, name):

        for b in self.buttons.values():
            b.setChecked(False)

        self.buttons[name].setChecked(True)

        self.camera.setEffect(name)

    def updateFPS(self, fps):

        self.fps.setText(f"{fps} FPS")

    def updateFrame(self, image):

        pix = QPixmap.fromImage(image)

        pix = pix.scaled(

            self.video.size(),

            Qt.KeepAspectRatio,

            Qt.SmoothTransformation

        )

        self.video.setPixmap(pix)

    def closeEvent(self, event):

        self.camera.stop()

        event.accept()