from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QSpacerItem, QSizePolicy, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from widgets.modern_button import ModernButton
from widgets.modern_input import ModernInput
from widgets.modern_card import ModernCard
from controllers.auth_controller import AuthController

class LoginWindow(QWidget):
    login_success = pyqtSignal(str, dict) # role ('admin' or 'user'), data
    switch_to_admin_setup = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_controller = AuthController()
        self.is_admin_mode = False
        self._setup_ui()
        
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Main Card
        self.card = ModernCard()
        self.card.setFixedWidth(400)
        
        # Title
        self.title = QLabel("Connexion à votre espace")
        self.title.setObjectName("title")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # App Name
        app_name = QLabel("QueryAI")
        app_name.setStyleSheet("font-size: 28px; font-weight: bold; color: #2563EB; margin-bottom: 20px;")
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Inputs
        self.email_input = ModernInput(placeholder="Email")
        self.password_input = ModernInput(placeholder="Mot de passe", is_password=True)
        
        # Login Button
        self.login_btn = ModernButton("Connexion Utilisateur", "primary")
        self.login_btn.clicked.connect(self._handle_login)
        
        # Divider
        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #E5E7EB; margin: 20px 0px;")
        
        # Admin Section
        self.admin_label = QLabel("Vous êtes admin d'une entreprise ?")
        self.admin_label.setObjectName("subtitle")
        self.admin_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.toggle_mode_btn = ModernButton("Accéder à l'espace Admin", "secondary")
        self.toggle_mode_btn.clicked.connect(self._toggle_mode)
        
        # Assemble Card
        self.card.addWidget(app_name)
        self.card.addWidget(self.title)
        self.card.layout.addSpacing(20)
        self.card.addWidget(self.email_input)
        self.card.addWidget(self.password_input)
        self.card.layout.addSpacing(10)
        self.card.addWidget(self.login_btn)
        self.card.addWidget(divider)
        self.card.addWidget(self.admin_label)
        self.card.addWidget(self.toggle_mode_btn)
        
        self.layout.addWidget(self.card)

    def _toggle_mode(self):
        self.is_admin_mode = not self.is_admin_mode
        if self.is_admin_mode:
            self.title.setText("Connexion Administrateur")
            self.login_btn.setText("Connexion Admin")
            self.admin_label.setText("Pas de compte admin ?")
            self.toggle_mode_btn.setText("Créer un compte Admin")
            self.toggle_mode_btn.clicked.disconnect()
            self.toggle_mode_btn.clicked.connect(self.switch_to_admin_setup.emit)
        else:
            self.title.setText("Connexion à votre espace")
            self.login_btn.setText("Connexion Utilisateur")
            self.admin_label.setText("Vous êtes admin d'une entreprise ?")
            self.toggle_mode_btn.setText("Accéder à l'espace Admin")
            self.toggle_mode_btn.clicked.disconnect()
            self.toggle_mode_btn.clicked.connect(self._toggle_mode)

    def _handle_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if self.is_admin_mode:
            res = self.auth_controller.login_admin(email, password)
            if res['ok']:
                self.login_success.emit('admin', res['admin'])
            else:
                QMessageBox.warning(self, "Erreur", res['erreur'])
        else:
            res = self.auth_controller.login_user(email, password)
            if res['ok']:
                self.login_success.emit('user', res['utilisateur'])
            else:
                QMessageBox.warning(self, "Erreur", res['erreur'])
