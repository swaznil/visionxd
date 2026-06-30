import os
import time
import webbrowser

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import *

from camera import CameraThread


LIGHT_STYLE = """

QMainWindow{
background:#edf1f1;
}

QFrame{
background:#ffffff;
border:1px solid #d7dede;
}

QLabel{
font-family:Segoe UI;
color:#223030;
}

QLabel#title{
font-size:27px;
font-weight:700;
color:#162222;
}

QLabel#sub{
font-size:12px;
color:#708585;
}

QLabel#fps{
background:#f4f7f7;
border:1px solid #d7dede;
padding:6px 12px;
font-size:12px;
font-weight:600;
color:#425a5a;
}

QLabel#video{
background:black;
border:1px solid #cfd7d7;
}

QPushButton{
background:#f7f9f9;
border:1px solid #d7dede;
padding:10px 14px;
font-size:13px;
font-family:Segoe UI;
color:#223030;
min-height:20px;
}

QPushButton:hover{
background:#eef5f5;
}

QPushButton:checked{
background:#dff8f4;
border:1px solid #7fd7ca;
}

QPushButton#effect{
text-align:left;
font-size:14px;
font-weight:500;
padding-left:14px;
}

QPushButton#effect:checked{
font-weight:700;
color:#1f5050;
}

QLineEdit{
background:white;
border:1px solid #d7dede;
padding:10px;
color:#223030;
}

QCheckBox{
font-size:13px;
spacing:10px;
padding:4px;
color:#223030;
}

"""

DARK_STYLE = """

QMainWindow{
background:#101414;
}

QFrame{
background:#171d1d;
border:1px solid #2a3333;
}

QLabel{
font-family:Segoe UI;
color:#dbe7e7;
}

QLabel#title{
font-size:27px;
font-weight:700;
color:#f1ffff;
}

QLabel#sub{
font-size:12px;
color:#88a0a0;
}

QLabel#fps{
background:#1d2525;
border:1px solid #344141;
padding:6px 12px;
font-size:12px;
font-weight:600;
color:#b9e7df;
}

QLabel#video{
background:black;
border:1px solid #2d3838;
}

QPushButton{
background:#202828;
border:1px solid #364242;
padding:10px 14px;
font-size:13px;
font-family:Segoe UI;
color:#dbe7e7;
min-height:20px;
}

QPushButton:hover{
background:#263131;
}

QPushButton:checked{
background:#163d39;
border:1px solid #59d5c3;
}

QPushButton#effect{
text-align:left;
font-size:14px;
font-weight:500;
padding-left:14px;
}

QPushButton#effect:checked{
font-weight:700;
color:#a9f0e3;
}

QLineEdit{
background:#202828;
border:1px solid #364242;
padding:10px;
color:#dbe7e7;
}

QCheckBox{
font-size:13px;
spacing:10px;
padding:4px;
color:#dbe7e7;
}

"""


class EffectButton(QPushButton):

    def __init__(self, text):

        super().__init__(text)

        self.setObjectName("effect")

        self.setCursor(
            Qt.PointingHandCursor
        )

        self.setCheckable(True)

        self.setMinimumHeight(42)


class VisionWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "VisionXD"
        )

        self.resize(
            1320,
            820
        )

        self.setMinimumSize(
            1100,
            720
        )

        self.camera = CameraThread()

        self.camera.frameReady.connect(
            self.updateFrame
        )

        self.camera.fpsReady.connect(
            self.updateFPS
        )

        self.recordStart = None

        self.currentPixmap = None

        root = QWidget()

        self.setCentralWidget(root)

        layout = QVBoxLayout(root)

        layout.setContentsMargins(
            12,
            12,
            12,
            12
        )

        layout.setSpacing(10)

        top = QFrame()

        top.setFixedHeight(72)

        topLayout = QHBoxLayout(top)

        topLayout.setContentsMargins(
            14,
            10,
            14,
            10
        )

        titleWrap = QVBoxLayout()

        titleWrap.setSpacing(0)

        title = QLabel(
            "VisionXD"
        )

        title.setObjectName("title")

        sub = QLabel(
            "realtime camera toolkit"
        )

        sub.setObjectName("sub")

        titleWrap.addWidget(title)

        titleWrap.addWidget(sub)

        topLayout.addLayout(titleWrap)

        topLayout.addStretch()

        self.recLabel = QLabel("")

        self.recLabel.hide()

        self.recLabel.setStyleSheet("""

color:#ff5f57;
font-weight:700;
font-size:13px;

""")

        topLayout.addWidget(
            self.recLabel
        )

        self.shotBtn = QPushButton(
            "Screenshot"
        )

        self.shotBtn.clicked.connect(
            self.takeScreenshot
        )

        topLayout.addWidget(
            self.shotBtn
        )

        self.recordBtn = QPushButton(
            "Record"
        )

        self.recordBtn.setCheckable(True)

        self.recordBtn.clicked.connect(
            self.toggleRecording
        )

        topLayout.addWidget(
            self.recordBtn
        )

        self.pageBtn = QPushButton(
            "Settings"
        )

        self.pageBtn.clicked.connect(
            self.togglePage
        )

        topLayout.addWidget(
            self.pageBtn
        )

        self.fps = QLabel(
            "0 fps"
        )

        self.fps.setObjectName(
            "fps"
        )

        topLayout.addWidget(
            self.fps
        )

        layout.addWidget(top)

        body = QHBoxLayout()

        body.setSpacing(10)

        side = QFrame()

        side.setFixedWidth(190)

        sideLayout = QVBoxLayout(side)

        sideLayout.setContentsMargins(
            10,
            10,
            10,
            10
        )

        sideLayout.setSpacing(8)

        self.buttons = {}

        for effect in [

            "Draw",
            "Box",
            "Cuboid",
            "Fluid"

        ]:

            btn = EffectButton(effect)

            btn.clicked.connect(

                lambda checked,
                name=effect:

                self.changeEffect(name)

            )

            sideLayout.addWidget(btn)

            self.buttons[effect] = btn

        self.buttons["Draw"].setChecked(
            True
        )

        sideLayout.addStretch()

        body.addWidget(side)

        self.pages = QStackedWidget()

        self.cameraPage = QWidget()

        camLayout = QVBoxLayout(
            self.cameraPage
        )

        camLayout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.video = QLabel()

        self.video.setObjectName(
            "video"
        )

        self.video.setAlignment(
            Qt.AlignCenter
        )

        self.video.setMinimumSize(
            640,
            480
        )

        camLayout.addWidget(
            self.video
        )

        self.pages.addWidget(
            self.cameraPage
        )

        self.settingsPage = QWidget()

        settingsLayout = QVBoxLayout(
            self.settingsPage
        )

        settingsLayout.setContentsMargins(
            24,
            24,
            24,
            24
        )

        settingsLayout.setSpacing(18)

        settingsTitle = QLabel(
            "Settings"
        )

        settingsTitle.setStyleSheet("""

font-size:26px;
font-weight:700;

""")

        settingsLayout.addWidget(
            settingsTitle
        )

        self.darkMode = QCheckBox(
            "Dark mode"
        )

        self.darkMode.stateChanged.connect(
            self.applyTheme
        )

        settingsLayout.addWidget(
            self.darkMode
        )

        self.showFPS = QCheckBox(
            "Show FPS counter"
        )

        self.showFPS.setChecked(True)

        self.showFPS.stateChanged.connect(
            self.toggleFPS
        )

        settingsLayout.addWidget(
            self.showFPS
        )

        folderLabel = QLabel(
            "Save folder"
        )

        settingsLayout.addWidget(
            folderLabel
        )

        folderRow = QHBoxLayout()

        self.pathBox = QLineEdit(
            os.path.abspath(
                "captures"
            )
        )

        browse = QPushButton(
            "Browse"
        )

        browse.clicked.connect(
            self.selectFolder
        )

        folderRow.addWidget(
            self.pathBox
        )

        folderRow.addWidget(
            browse
        )

        settingsLayout.addLayout(
            folderRow
        )

        repo = QPushButton(
            "Open Github Repo"
        )

        repo.clicked.connect(

            lambda:

            webbrowser.open(
                "https://github.com/"
            )

        )

        settingsLayout.addWidget(
            repo
        )

        about = QLabel(

            "VisionXD is a realtime "
            "computer vision toolkit "
            "built using OpenCV, "
            "MediaPipe and PySide6."

        )

        about.setWordWrap(True)

        about.setStyleSheet("""

line-height:20px;
color:#7a8f8f;

""")

        settingsLayout.addWidget(
            about
        )

        settingsLayout.addStretch()

        self.pages.addWidget(
            self.settingsPage
        )

        body.addWidget(
            self.pages,
            1
        )

        layout.addLayout(
            body,
            1
        )

        self.setStyleSheet(
            DARK_STYLE
        )

        self.darkMode.setChecked(True)

        self.camera.start()

    def togglePage(self):

        if self.pages.currentIndex() == 0:

            self.pages.setCurrentIndex(1)

            self.pageBtn.setText(
                "Camera"
            )

        else:

            self.pages.setCurrentIndex(0)

            self.pageBtn.setText(
                "Settings"
            )

    def applyTheme(self):

        if self.darkMode.isChecked():

            self.setStyleSheet(
                DARK_STYLE
            )

        else:

            self.setStyleSheet(
                LIGHT_STYLE
            )

    def toggleFPS(self):

        self.fps.setVisible(
            self.showFPS.isChecked()
        )

    def selectFolder(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder"
        )

        if folder:

            self.pathBox.setText(
                folder
            )

            self.camera.setOutputFolder(
                folder
            )

    def toggleRecording(self):

        if self.recordBtn.isChecked():

            self.camera.startRecording()

            self.recordBtn.setText(
                "Stop"
            )

            self.recordStart = time.time()

            self.recLabel.show()

        else:

            self.camera.stopRecording()

            self.recordBtn.setText(
                "Record"
            )

            self.recLabel.hide()

    def takeScreenshot(self):

        self.camera.saveScreenshot()

    def changeEffect(self, name):

        for b in self.buttons.values():

            b.setChecked(False)

        self.buttons[name].setChecked(
            True
        )

        self.camera.setEffect(name)

    def updateFPS(self, fps):

        self.fps.setText(
            f"{fps} fps"
        )

        if self.camera.recording:

            elapsed = int(
                time.time()
                - self.recordStart
            )

            mins = elapsed // 60

            secs = elapsed % 60

            self.recLabel.setText(

                f"● REC  {mins:02}:{secs:02}"

            )

    def updateFrame(self, image):

        pix = QPixmap.fromImage(
            image
        )

        self.currentPixmap = pix

        scaled = pix.scaled(

            self.video.size(),

            Qt.KeepAspectRatio,

            Qt.SmoothTransformation

        )

        self.video.setPixmap(
            scaled
        )

    def resizeEvent(self, event):

        super().resizeEvent(event)

        if self.currentPixmap:

            scaled = self.currentPixmap.scaled(

                self.video.size(),

                Qt.KeepAspectRatio,

                Qt.SmoothTransformation

            )

            self.video.setPixmap(
                scaled
            )

    def closeEvent(self, event):

        self.camera.stop()

        event.accept()