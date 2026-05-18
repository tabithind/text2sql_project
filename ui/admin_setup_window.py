from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from widgets.modern_button import ModernButton
from widgets.modern_input import ModernInput
from widgets.modern_card import ModernCard
from controllers.auth_controller import AuthController

class AdminSetupWindow(QWidget):
    setup_success = pyqtSignal(dict) # admin data
    back_to_login = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_controller = AuthController()
        self._setup_ui()
        
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.card = ModernCard()
        self.card.setFixedWidth(400)
        
        self.title = QLabel("Création de compte Administrateur")
        self.title.setObjectName("title")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.prenom_input = ModernInput("Prénom")
        self.nom_input = ModernInput("Nom")
        self.entreprise_input = ModernInput("Nom de l'entreprise")
        self.email_input = ModernInput("Email")
        self.password_input = ModernInput("Mot de passe", is_password=True)
        
        self.register_btn = ModernButton("Créer le compte", "primary")
        self.register_btn.clicked.connect(self._handle_register)
        
        self.back_btn = ModernButton("Retour à la connexion", "secondary")
        self.back_btn.clicked.connect(self.back_to_login.emit)
        
        self.card.addWidget(self.title)
        self.card.layout.addSpacing(20)
        self.card.addWidget(self.prenom_input)
        self.card.addWidget(self.nom_input)
        self.card.addWidget(self.entreprise_input)
        self.card.addWidget(self.email_input)
        self.card.addWidget(self.password_input)
        self.card.layout.addSpacing(10)
        self.card.addWidget(self.register_btn)
        self.card.addWidget(self.back_btn)
        
        self.layout.addWidget(self.card)

    def _handle_register(self):
        res = self.auth_controller.register_admin(
            self.prenom_input.text().strip(),
            self.nom_input.text().strip(),
            self.email_input.text().strip(),
            self.password_input.text(),
            self.entreprise_input.text().strip()
        )
        if res['ok']:
            # Log them in automatically or just signal success with admin_id
            # To properly return admin data, we need to fetch it. For now, just a basic struct
            admin_data = {
                'id': res['admin_id'],
                'prenom': self.prenom_input.text().strip(),
                'nom': self.nom_input.text().strip(),
                'email': self.email_input.text().strip(),
                'entreprise': self.entreprise_input.text().strip()
            }
            self.setup_success.emit(admin_data)
        else:
            QMessageBox.warning(self, "Erreur", res['erreur'])
