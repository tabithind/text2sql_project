from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen

class LoadingSpinner(QLabel):
    def __init__(self, parent=None, size=32, color="#3B82F6"):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.color = color
        self.angle = 0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.setInterval(30)
        self.hide()

    def start(self):
        self.show()
        self.timer.start()

    def stop(self):
        self.hide()
        self.timer.stop()

    def rotate(self):
        self.angle = (self.angle + 10) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(QColor(self.color))
        pen.setWidth(int(self.width() * 0.1))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # Draw arc
        rect = self.rect().adjusted(pen.width(), pen.width(), -pen.width(), -pen.width())
        painter.drawArc(rect, -self.angle * 16, 270 * 16)
