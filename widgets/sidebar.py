from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QButtonGroup, QSpacerItem, QSizePolicy
from PyQt6.QtCore import pyqtSignal

class Sidebar(QWidget):
    item_selected = pyqtSignal(int)
    
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(250)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 24, 12, 24)
        self.layout.setSpacing(8)
        
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.button_group.idClicked.connect(self._on_button_clicked)
        
        for idx, (icon, text) in enumerate(items):
            btn = QPushButton(f"  {text}")
            btn.setObjectName("sidebar_btn")
            btn.setCheckable(True)
            # Placeholder for actual icon implementation if needed
            self.button_group.addButton(btn, idx)
            self.layout.addWidget(btn)
            
            if idx == 0:
                btn.setChecked(True)
                
        # Push everything to the top
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.layout.addSpacerItem(spacer)

    def _on_button_clicked(self, id):
        self.item_selected.emit(id)
