from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon

class ToastNotification(QWidget):
    def __init__(self, message, type="info", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.ToolTip)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # UI
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(16, 12, 16, 12)
        
        self.label = QLabel(message)
        self.label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        
        self.layout.addWidget(self.label)
        
        bg_color = "#3B82F6" # info
        if type == "success": bg_color = "#10B981"
        elif type == "error": bg_color = "#EF4444"
        elif type == "warning": bg_color = "#F59E0B"
            
        self.setStyleSheet(f"""
            ToastNotification {{
                background-color: {bg_color};
                border-radius: 8px;
            }}
        """)
        
        # Animations
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)
        
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.hide_toast)
        self.timer.setSingleShot(True)

    def show_toast(self, parent_widget):
        # Position at bottom right
        if parent_widget:
            x = parent_widget.width() - self.width() - 20
            y = parent_widget.height() - self.height() - 20
            self.move(x, y)
            
        self.show()
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()
        self.timer.start(3000)

    def hide_toast(self):
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.close)
        self.animation.start()
