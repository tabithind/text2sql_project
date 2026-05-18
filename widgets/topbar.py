from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

class Topbar(QWidget):
    logout_clicked = pyqtSignal()
    
    def __init__(self, title="QueryAI", parent=None):
        super().__init__(parent)
        self.setObjectName("surface")
        self.setFixedHeight(64)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(24, 0, 24, 0)
        
        # Title
        self.title_label = QLabel(title)
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setStyleSheet("color: #2563EB;")
        
        # Info label (e.g. connected database)
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #6B7280; font-size: 14px; margin-left: 20px;")
        
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        self.logout_btn = QPushButton("Déconnexion")
        self.logout_btn.setObjectName("secondary")
        self.logout_btn.clicked.connect(self.logout_clicked.emit)
        
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.info_label)
        self.layout.addSpacerItem(spacer)
        self.layout.addWidget(self.logout_btn)
        
    def set_info(self, text):
        self.info_label.setText(text)
