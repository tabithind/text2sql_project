from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QMessageBox)
from PyQt6.QtCore import Qt
from widgets.modern_table import ModernTable
from widgets.modern_button import ModernButton
from widgets.empty_state import EmptyState

class PermissionsPanel(QWidget):
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
        self.title = QLabel("Gestion des Permissions")
        self.title.setObjectName("title")
        
        self.user_combo = QComboBox()
        self.user_combo.setMinimumWidth(200)
        self.user_combo.setFixedHeight(36)
        self.user_combo.currentIndexChanged.connect(self._on_user_selected)
        
        self.header_layout.addWidget(self.title)
        self.header_layout.addStretch()
        self.header_layout.addWidget(QLabel("Sélectionner un utilisateur :"))
        self.header_layout.addWidget(self.user_combo)
        
        self.info_label = QLabel("Double-cliquez sur une ligne pour modifier l'accès de l'utilisateur à la base de données.")
        self.info_label.setObjectName("subtitle")
        
        # Table
        self.table = ModernTable()
        self.table.itemDoubleClicked.connect(self._edit_permission)
        
        self.empty_state = EmptyState(
            "Sélectionnez un utilisateur", 
            "Choisissez un utilisateur dans la liste déroulante pour gérer ses permissions."
        )
        
        self.layout.addLayout(self.header_layout)
        self.layout.addWidget(self.info_label)
        self.layout.addWidget(self.table)
        self.layout.addWidget(self.empty_state)
        
    def refresh(self):
        # Refresh users combo box
        self.user_combo.blockSignals(True)
        self.user_combo.clear()
        users = self.controller.get_users()
        for u in users:
            self.user_combo.addItem(f"{u['prenom']} {u['nom']} ({u['email']})", u['id'])
        self.user_combo.blockSignals(False)
        
        if self.user_combo.count() > 0:
            self._on_user_selected()
        else:
            self.table.hide()
            self.info_label.hide()
            self.empty_state.show()
            
    def _on_user_selected(self):
        user_id = self.user_combo.currentData()
        if not user_id: return
        
        self.empty_state.hide()
        self.table.show()
        self.info_label.show()
        
        databases = self.controller.get_databases()
        headers = ["DB ID", "Nom de la base", "Type", "Accès Actuel"]
        data = []
        
        for db in databases:
            # Check current permission
            perms = self.controller.get_user_permissions(user_id, db['id'])
            # The permission service returns a list of allowed operations. 
            # We need to map it back to the role ('lecture', 'ecriture', 'admin') or 'aucun'
            acces = "aucun"
            if 'schema' in perms: acces = "admin"
            elif 'insert' in perms: acces = "ecriture"
            elif 'select' in perms: acces = "lecture"
            
            data.append([db['id'], db['nom'], db['type'], acces])
            
        self.table.set_data(headers, data)

    def _edit_permission(self, item):
        row = item.row()
        db_id = int(self.table.item(row, 0).text())
        db_nom = self.table.item(row, 1).text()
        current_acces = self.table.item(row, 3).text()
        user_id = self.user_combo.currentData()
        
        from PyQt6.QtWidgets import QInputDialog
        items = ["aucun", "lecture", "ecriture", "admin"]
        current_index = items.index(current_acces) if current_acces in items else 0
        
        acces, ok = QInputDialog.getItem(
            self, 
            "Modifier la permission", 
            f"Niveau d'accès pour {db_nom} :", 
            items, 
            current_index, 
            False
        )
        
        if ok and acces != current_acces:
            val = acces if acces != "aucun" else None
            res = self.controller.update_permission(user_id, db_id, val)
            if res['ok']:
                self._on_user_selected()
            else:
                QMessageBox.warning(self, "Erreur", res['erreur'])
