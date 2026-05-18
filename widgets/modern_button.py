from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QCursor

class ModernButton(QPushButton):
    def __init__(self, text, button_type="primary", parent=None):
        super().__init__(text, parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Le type peut être "primary", "secondary" ou "danger"
        # Il servira d'identifiant objet pour le style QSS
        if button_type != "primary":
            self.setObjectName(button_type)
            
        self.setMinimumHeight(36)
