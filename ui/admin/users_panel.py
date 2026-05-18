from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QMessageBox, QDialog, QFormLayout)
from PyQt6.QtCore import Qt
from widgets.modern_table import ModernTable
from widgets.modern_button import ModernButton
from widgets.modern_input import ModernInput
from widgets.empty_state import EmptyState

class UserDialog(QDialog):
    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter un utilisateur" if not user else "Modifier l'utilisateur")
        self.user = user
        self.setFixedWidth(400)
        self._setup_ui()
        
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()
        
        self.prenom_input = ModernInput()
        self.nom_input = ModernInput()
        self.email_input = ModernInput()
        self.password_input = ModernInput(is_password=True)
        
        if self.user:
            self.prenom_input.setText(self.user[1])
            self.nom_input.setText(self.user[2])
            self.email_input.setText(self.user[3])
            self.password_input.setPlaceholderText("Laisser vide pour ne pas changer")
            
        self.form_layout.addRow("Prénom:", self.prenom_input)
        self.form_layout.addRow("Nom:", self.nom_input)
        self.form_layout.addRow("Email:", self.email_input)
        self.form_layout.addRow("Mot de passe:", self.password_input)
        
        self.buttons_layout = QHBoxLayout()
        self.save_btn = ModernButton("Enregistrer", "primary")
        self.cancel_btn = ModernButton("Annuler", "secondary")
        
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.buttons_layout.addWidget(self.save_btn)
        self.buttons_layout.addWidget(self.cancel_btn)
        
        self.layout.addLayout(self.form_layout)
        self.layout.addLayout(self.buttons_layout)
        
    def get_data(self):
        return {
            'prenom': self.prenom_input.text().strip(),
            'nom': self.nom_input.text().strip(),
            'email': self.email_input.text().strip(),
            'password': self.password_input.text()
        }

class UsersPanel(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self._setup_ui()
        self.refresh()
        
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(16)
        
        # Header
        self.header_layout = QHBoxLayout()
        self.title = QLabel("Gestion des Utilisateurs")
        self.title.setObjectName("title")
        
        self.add_btn = ModernButton("+ Ajouter un utilisateur", "primary")
        self.add_btn.clicked.connect(self._add_user)
        
        self.header_layout.addWidget(self.title)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.add_btn)
        
        # Table
        self.table = ModernTable()
        # Columns: ID, Prénom, Nom, Email, Actif, Créé le
        self.table.itemDoubleClicked.connect(self._edit_user)
        
        self.empty_state = EmptyState(
            "Aucun utilisateur", 
            "Cliquez sur 'Ajouter un utilisateur' pour commencer."
        )
        self.empty_state.hide()
        
        self.layout.addLayout(self.header_layout)
        self.layout.addWidget(self.table)
        self.layout.addWidget(self.empty_state)
        
    def refresh(self):
        users = self.controller.get_users()
        if not users:
            self.table.hide()
            self.empty_state.show()
        else:
            self.empty_state.hide()
            self.table.show()
            headers = ["ID", "Prénom", "Nom", "Email", "Actif", "Créé le"]
            # Convert Dict to list of lists for ModernTable
            data = [
                [u['id'], u['prenom'], u['nom'], u['email'], u['actif'], u['created_at']]
                for u in users
            ]
            self.table.set_data(headers, data)
            
    def _add_user(self):
        dialog = UserDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            res = self.controller.add_user(data['prenom'], data['nom'], data['email'], data['password'])
            if res['ok']:
                self.refresh()
            else:
                QMessageBox.warning(self, "Erreur", res['erreur'])
                
    def _edit_user(self, item):
        row = item.row()
        user_id = int(self.table.item(row, 0).text())
        prenom = self.table.item(row, 1).text()
        nom = self.table.item(row, 2).text()
        email = self.table.item(row, 3).text()
        
        dialog = UserDialog(self, user=(user_id, prenom, nom, email))
        if dialog.exec():
            data = dialog.get_data()
            res = self.controller.edit_user(user_id, data['prenom'], data['nom'], data['email'], data['password'])
            if res['ok']:
                self.refresh()
            else:
                QMessageBox.warning(self, "Erreur", res['erreur'])
