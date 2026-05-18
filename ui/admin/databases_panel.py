from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QMessageBox, QDialog, QFormLayout, QComboBox, QStackedWidget, QScrollArea)
from PyQt6.QtCore import Qt
from widgets.modern_table import ModernTable
from widgets.modern_button import ModernButton
from widgets.modern_input import ModernInput
from widgets.empty_state import EmptyState
from config.constants import DB_FIELD_CONFIG, FIELD_DESCRIPTIONS, PORTS_DEFAUT

class DatabaseDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajouter une base de données")
        self.controller = controller
        self.setFixedWidth(550)
        self.setMinimumHeight(500)
        self.is_connected = False
        self.selected_db_type = "mysql"
        self.field_inputs = {}  # Stocke les champs dynamiquement créés
        self._setup_ui()

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(16)
        self.layout.setContentsMargins(24, 24, 24, 24)

        # Titre moderne et sobre
        title_label = QLabel("Connexion à une base de données")
        title_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #111827; margin-bottom: 4px;")
        self.layout.addWidget(title_label)

        # Nom affiché
        nom_label = QLabel("Nom affiché :")
        nom_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #4B5563;")
        self.layout.addWidget(nom_label)
        self.nom_input = ModernInput("Nom affiché (ex: Production DB)")
        self.layout.addWidget(self.nom_input)

        # Type de base de données
        type_label = QLabel("Type de base de données :")
        type_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #4B5563;")
        self.layout.addWidget(type_label)
        self.type_combo = QComboBox()
        self.type_combo.setFixedHeight(36)
        for db_type in DB_FIELD_CONFIG.keys():
            config = DB_FIELD_CONFIG[db_type]
            self.type_combo.addItem(config['nom'], db_type)
        self.type_combo.currentIndexChanged.connect(self._on_db_type_changed)
        self.layout.addWidget(self.type_combo)

        # Info box pour le type sélectionné (style épuré)
        self.info_label = QLabel()
        self.info_label.setStyleSheet(
            "background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 6px; "
            "padding: 12px; color: #1E40AF; font-size: 12px; line-height: 1.4;"
        )
        self.info_label.setWordWrap(True)
        self.layout.addWidget(self.info_label)

        # Mode (Manuel vs URL)
        mode_label = QLabel("Mode de connexion :")
        mode_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #4B5563;")
        self.layout.addWidget(mode_label)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Manuel", "URL"])
        self.mode_combo.setFixedHeight(36)
        self.mode_combo.currentIndexChanged.connect(self._change_mode_combo)
        self.layout.addWidget(self.mode_combo)

        # Stacked widget pour les deux modes
        self.stacked = QStackedWidget()

        # Mode Manuel - conteneur avec scroll
        self.manuel_scroll = QScrollArea()
        self.manuel_scroll.setWidgetResizable(True)
        self.manuel_scroll.setStyleSheet("border: none; background-color: transparent;")
        self.manuel_widget = QWidget()
        self.manuel_widget.setStyleSheet("background-color: transparent;")
        self.manuel_layout = QFormLayout(self.manuel_widget)
        self.manuel_layout.setContentsMargins(0, 0, 0, 0)
        self.manuel_layout.setSpacing(10)
        self.manuel_scroll.setWidget(self.manuel_widget)

        # Mode URL
        self.url_widget = QWidget()
        self.url_widget.setStyleSheet("background-color: transparent;")
        self.url_layout = QVBoxLayout(self.url_widget)
        self.url_layout.setContentsMargins(0, 0, 0, 0)
        self.url_layout.setSpacing(8)
        self.url_input = ModernInput("mysql://user:pass@host:3306/db")
        self.url_label = QLabel("URL de connexion :")
        self.url_label.setStyleSheet("font-size: 13px; font-weight: 500; color: #4B5563;")
        self.url_placeholder = QLabel()
        self.url_placeholder.setStyleSheet("color: #6B7280; font-size: 11px;")
        self.url_placeholder.setWordWrap(True)
        self.url_layout.addWidget(self.url_label)
        self.url_layout.addWidget(self.url_input)
        self.url_layout.addWidget(self.url_placeholder)
        self.url_layout.addStretch()

        self.stacked.addWidget(self.manuel_scroll)
        self.stacked.addWidget(self.url_widget)
        self.layout.addWidget(self.stacked)

        # Buttons
        self.buttons_layout = QHBoxLayout()
        self.test_btn = ModernButton("Tester la connexion", "secondary")
        self.save_btn = ModernButton("Enregistrer", "primary")
        self.save_btn.setEnabled(False)
        self.cancel_btn = ModernButton("Annuler", "secondary")

        self.test_btn.clicked.connect(self._test_connection)
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        self.buttons_layout.addWidget(self.test_btn)
        self.buttons_layout.addWidget(self.save_btn)
        self.buttons_layout.addWidget(self.cancel_btn)

        self.layout.addLayout(self.buttons_layout)

        # Initialiser les champs pour MySQL par défaut
        self._on_db_type_changed(0)

    def _on_db_type_changed(self, index):
        """Appelé quand le type de base de données change."""
        self.selected_db_type = self.type_combo.currentData()
        config = DB_FIELD_CONFIG[self.selected_db_type]

        # Mettre à jour l'info box (sans icône emoji)
        info_text = f"<b>{config['nom']}</b><br>{config['info']}"
        self.info_label.setText(info_text)

        # Régénérer les champs
        self._regenerate_manuel_fields()

        # Mettre à jour le placeholder de l'URL
        from config.constants import URL_PLACEHOLDERS
        placeholder = URL_PLACEHOLDERS.get(self.selected_db_type, "")
        self.url_placeholder.setText(f"Exemple : {placeholder}")

        # Réinitialiser le bouton test
        self.test_btn.setText("Tester la connexion")
        self.test_btn.setStyleSheet("")
        self.save_btn.setEnabled(False)

    def _regenerate_manuel_fields(self):
        """Régénère dynamiquement les champs du mode manuel selon le type de BD."""
        # Effacer les champs précédents
        while self.manuel_layout.rowCount():
            self.manuel_layout.removeRow(0)
        self.field_inputs.clear()

        config = DB_FIELD_CONFIG[self.selected_db_type]
        port_defaut = PORTS_DEFAUT[self.selected_db_type]

        # Champs obligatoires (titre de section propre)
        mandatory_label = QLabel("Champs obligatoires")
        mandatory_label.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #2563EB; "
            "text-transform: uppercase; letter-spacing: 0.5px; margin-top: 8px; margin-bottom: 4px;"
        )
        self.manuel_layout.addRow(mandatory_label)

        for field in config['champs_obligatoires']:
            field_config = FIELD_DESCRIPTIONS.get(field, {})
            label = field_config.get('label', field)
            placeholder = field_config.get('placeholder', '')
            is_password = field_config.get('type') == 'password'

            # Définir les valeurs par défaut
            default_value = ''
            if field == 'port':
                default_value = str(port_defaut)
            elif field == 'host' or field == 'server':
                default_value = 'localhost'

            input_field = ModernInput(placeholder, is_password=is_password)
            if default_value:
                input_field.setText(default_value)

            self.field_inputs[field] = input_field
            
            # Label de ligne stylisé
            lbl = QLabel(f"{label} :")
            lbl.setStyleSheet("font-size: 13px; font-weight: 500; color: #4B5563;")
            self.manuel_layout.addRow(lbl, input_field)

        # Champs optionnels (titre de section propre)
        if config['champs_optionnels']:
            optional_label = QLabel("Champs optionnels")
            optional_label.setStyleSheet(
                "font-size: 11px; font-weight: 600; color: #059669; "
                "text-transform: uppercase; letter-spacing: 0.5px; margin-top: 16px; margin-bottom: 4px;"
            )
            self.manuel_layout.addRow(optional_label)

            for field in config['champs_optionnels']:
                field_config = FIELD_DESCRIPTIONS.get(field, {})
                label = field_config.get('label', field)
                placeholder = field_config.get('placeholder', '')
                is_password = field_config.get('type') == 'password'

                input_field = ModernInput(placeholder, is_password=is_password)
                self.field_inputs[field] = input_field
                
                # Label de ligne optionnel stylisé
                lbl = QLabel(f"{label} (opt) :")
                lbl.setStyleSheet("font-size: 13px; font-weight: 500; color: #4B5563;")
                self.manuel_layout.addRow(lbl, input_field)

    def _change_mode_combo(self, index):
        """Change entre mode manuel et mode URL."""
        if index == 1:  # URL mode
            self.stacked.setCurrentIndex(1)
            mode = 'url'
        else:  # Manuel mode
            self.stacked.setCurrentIndex(0)
            mode = 'manuel'

        # Réinitialiser le bouton test
        self.test_btn.setText("Tester la connexion")
        self.test_btn.setStyleSheet("")
        self.save_btn.setEnabled(False)

    def get_data(self):
        """Récupère les données du formulaire."""
        # Récupérer le mode (0 = manuel, 1 = url)
        mode = 'url' if self.mode_combo.currentIndex() == 1 else 'manuel'
        data = {
            'nom': self.nom_input.text().strip(),
            'type': self.selected_db_type,
            'mode': mode
        }

        if mode == 'url':
            data['url'] = self.url_input.text().strip()
        else:
            # Récupérer les champs dynamiques
            for field_name, input_widget in self.field_inputs.items():
                value = input_widget.text().strip()
                if field_name == 'port' and value:
                    data[field_name] = int(value)
                else:
                    data[field_name] = value

        return data

    def _test_connection(self):
        """Teste la connexion à la base de données."""
        data = self.get_data()

        if not data['nom']:
            QMessageBox.warning(self, "Erreur", "Le nom affiché est obligatoire.")
            return

        mode = data['mode']

        if mode == 'url':
            if not data.get('url'):
                QMessageBox.warning(self, "Erreur", "L'URL de connexion est obligatoire.")
                return
            res = self.controller.test_connection(data['type'], 'url', {'url': data['url']})
        else:
            # Valider les champs obligatoires
            config = DB_FIELD_CONFIG[data['type']]
            for field in config['champs_obligatoires']:
                if not data.get(field):
                    QMessageBox.warning(self, "Erreur", f"Le champ '{field}' est obligatoire.")
                    return

            res = self.controller.test_connection(data['type'], 'manuel', data)

        if res['ok']:
            self.is_connected = True
            self.save_btn.setEnabled(True)
            self.test_btn.setText("Connexion réussie")
            self.test_btn.setStyleSheet(
                "background-color: #D1FAE5; color: #065F46; "
                "border: 1px solid #6EE7B7; font-weight: 500;"
            )
            QMessageBox.information(self, "Succès", "Connexion à la base de données réussie !")
        else:
            self.is_connected = False
            self.save_btn.setEnabled(False)
            self.test_btn.setText("Test échoué")
            self.test_btn.setStyleSheet(
                "background-color: #FEE2E2; color: #991B1B; "
                "border: 1px solid #FCA5A5; font-weight: 500;"
            )
            QMessageBox.warning(self, "Erreur de connexion", res['erreur'])


class DatabasesPanel(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(16)

        self.header_layout = QHBoxLayout()
        self.title = QLabel("Bases de données")
        self.title.setObjectName("title")

        self.add_btn = ModernButton("+ Ajouter une base", "primary")
        self.add_btn.clicked.connect(self._add_database)

        self.header_layout.addWidget(self.title)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.add_btn)

        self.table = ModernTable()
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        self.empty_state = EmptyState(
            "Aucune base de données",
            "Cliquez sur 'Ajouter une base' pour connecter votre première base de données."
        )
        self.empty_state.hide()

        self.layout.addLayout(self.header_layout)
        self.layout.addWidget(self.table)
        self.layout.addWidget(self.empty_state)

    def refresh(self):
        dbs = self.controller.get_databases()
        if not dbs:
            self.table.hide()
            self.empty_state.show()
        else:
            self.empty_state.hide()
            self.table.show()
            headers = ["ID", "Nom", "Type", "Mode", "Actif", "Créé le"]
            data = [
                [db['id'], db['nom'], db['type'], db['mode_connexion'], db['actif'], db['created_at']]
                for db in dbs
            ]
            self.table.set_data(headers, data)

    def _show_context_menu(self, position):
        """Affiche un menu contextuel au clic droit."""
        item = self.table.itemAt(position)
        if not item:
            return

        row = item.row()
        base_id = int(self.table.item(row, 0).text())
        base_name = self.table.item(row, 1).text()

        from PyQt6.QtWidgets import QMenu
        context_menu = QMenu(self)
        delete_action = context_menu.addAction("Supprimer cette base")
        action = context_menu.exec(self.table.mapToGlobal(position))

        if action == delete_action:
            self._delete_database(base_id, base_name)

    def _delete_database(self, base_id: int, base_name: str):
        """Supprime une base de données après confirmation."""
        reply = QMessageBox.question(
            self,
            "Confirmation de suppression",
            f"Êtes-vous sûr de vouloir supprimer la base '{base_name}' ?\n\n"
            f"Cette action supprimera également toutes les permissions des utilisateurs sur cette base.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            res = self.controller.delete_database(base_id)
            if res['ok']:
                QMessageBox.information(self, "Succès", f"Base de données '{base_name}' supprimée avec succès.")
                self.refresh()
            else:
                QMessageBox.warning(self, "Erreur de suppression", res.get('erreur', 'Erreur inconnue'))

    def _add_database(self):
        dialog = DatabaseDialog(self.controller, self)
        if dialog.exec() and dialog.is_connected:
            data = dialog.get_data()
            res = self.controller.save_database(data['nom'], data['type'], data['mode'], data)
            if res['ok']:
                self.refresh()
            else:
                QMessageBox.warning(self, "Erreur d'enregistrement", res['erreur'])
