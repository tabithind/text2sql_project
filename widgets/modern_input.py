from PyQt6.QtWidgets import QLineEdit

class ModernInput(QLineEdit):
    def __init__(self, placeholder="", is_password=False, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        if is_password:
            self.setEchoMode(QLineEdit.EchoMode.Password)
        self.setMinimumHeight(36)
