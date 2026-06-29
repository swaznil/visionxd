import sys

from PySide6.QtWidgets import QApplication

from ui import VisionWindow

app = QApplication(sys.argv)

app.setApplicationName("VisionXD")
app.setStyle("Fusion")

window = VisionWindow()
window.show()

sys.exit(app.exec())