from PySide6.QtCore import Qt

from PySide6.QtGui import QPixmap

from PySide6.QtWidgets import QWidget
from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QPushButton
from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QMainWindow
from PySide6.QtWidgets import QSizePolicy

from camera import CameraThread


class EffectButton(QPushButton):

    def __init__(self, text):

        super().__init__(text)

        self.setCursor(
            Qt.PointingHandCursor
        )

        self.setCheckable(True)

        self.setMinimumHeight(46)

        self.setObjectName("effect")


class VisionWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "VisionXD"
        )

        self.resize(1320, 840)

        self.setMinimumSize(
            1020,
            700
        )

        self.camera = CameraThread()

        self.camera.frameReady.connect(
            self.updateFrame
        )

        self.camera.fpsReady.connect(
            self.updateFPS
        )

        root = QWidget()

        self.setCentralWidget(root)

        layout = QVBoxLayout(root)

        layout.setContentsMargins(
            18,
            18,
            18,
            18
        )

        layout.setSpacing(14)

        top = QFrame()

        top.setObjectName("top")

        topLayout = QHBoxLayout(top)

        topLayout.setContentsMargins(
            16,
            14,
            16,
            14
        )

        titleWrap = QVBoxLayout()

        titleWrap.setSpacing(1)

        title = QLabel(
            "VisionXD"
        )

        title.setObjectName("title")

        sub = QLabel(
            "camera experiments"
        )

        sub.setObjectName("sub")

        titleWrap.addWidget(title)

        titleWrap.addWidget(sub)

        self.fps = QLabel("0 fps")

        self.fps.setObjectName("fps")

        topLayout.addLayout(titleWrap)

        topLayout.addStretch()

        topLayout.addWidget(self.fps)

        layout.addWidget(top)

        body = QHBoxLayout()

        body.setSpacing(14)

        side = QFrame()

        side.setObjectName("side")

        side.setFixedWidth(200)

        sideLayout = QVBoxLayout(side)

        sideLayout.setContentsMargins(
            12,
            12,
            12,
            12
        )

        sideLayout.setSpacing(10)

        sideTitle = QLabel(
            "effects"
        )

        sideTitle.setObjectName("sideTitle")

        sideLayout.addWidget(sideTitle)

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

            sideLayout.addWidget(btn)

            self.buttons[effect] = btn

        self.buttons["Draw"].setChecked(True)

        sideLayout.addStretch()

        self.status = QLabel(
            "camera active"
        )

        self.status.setObjectName("status")

        sideLayout.addWidget(self.status)

        body.addWidget(side)

        videoWrap = QFrame()

        videoWrap.setObjectName("videoWrap")

        videoLayout = QVBoxLayout(videoWrap)

        videoLayout.setContentsMargins(
            10,
            10,
            10,
            10
        )

        self.video = QLabel()

        self.video.setAlignment(
            Qt.AlignCenter
        )

        self.video.setObjectName("video")

        self.video.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        videoLayout.addWidget(
            self.video
        )

        body.addWidget(
            videoWrap,
            1
        )

        layout.addLayout(
            body,
            1
        )

        self.setStyleSheet("""

QMainWindow{

background:#d7dfdf;

}

QFrame#top{

background:#eef4f4;

border:1px solid #adc0c0;

}

QFrame#side{

background:#eef4f4;

border:1px solid #adc0c0;

}

QFrame#videoWrap{

background:#eef4f4;

border:1px solid #adc0c0;

}

QLabel#title{

font-size:29px;

font-weight:600;

color:#294040;

font-family:Tahoma;

}

QLabel#sub{

font-size:12px;

color:#6a8181;

font-family:Verdana;

}

QLabel#fps{

background:#def7f3;

border:1px solid #8fd1c8;

padding:7px 15px;

font-size:13px;

font-weight:600;

color:#2b5b59;

font-family:Tahoma;

}

QLabel#sideTitle{

font-size:13px;

font-weight:bold;

color:#547070;

padding-bottom:4px;

font-family:Verdana;

}

QLabel#status{

font-size:12px;

color:#537575;

padding:10px;

background:#e5f5f4;

border:1px solid #b5d8d4;

font-family:Verdana;

}

QPushButton#effect{

background:#dde7e7;

border:1px solid #b2c6c6;

padding:12px;

text-align:left;

font-size:14px;

color:#314848;

font-family:Tahoma;

}

QPushButton#effect:hover{

background:#e8f5f3;

border:1px solid #79d2c4;

}

QPushButton#effect:checked{

background:#d6fbf5;

border:1px solid #61d9ca;

color:#204f4f;

font-weight:600;

}

QLabel#video{

background:black;

border:2px solid #9fb7b7;

}

""")

        self.camera.start()

    def changeEffect(self, name):

        for b in self.buttons.values():

            b.setChecked(False)

        self.buttons[name].setChecked(True)

        self.camera.setEffect(name)

        self.status.setText(
            f"{name.lower()} mode active"
        )

    def updateFPS(self, fps):

        self.fps.setText(
            f"{fps} fps"
        )

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