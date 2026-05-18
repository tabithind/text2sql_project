from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, 
                               QComboBox, QMessageBox, QLabel, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from widgets.topbar import Topbar
from controllers.user_controller import UserController
from ui.user.query_panel import QueryPanel
from ui.user.visualization_panel import VisualizationPanel
from ui.user.export_panel import ExportPanel
from ui.admin.settings_panel import SettingsPanel
from ui.user.api_key_dialog import APIKeyDialog

class ClickableLabel(QLabel):
    """Label cliquable pour afficher le menu IA."""
    clicked = pyqtSignal()
    
    def mousePressEvent(self, event):
        self.clicked.emit()

class UserDashboard(QWidget):
    logout_requested = pyqtSignal()
    
    def __init__(self, user_data: dict, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.controller = UserController(user_data)
        self._setup_ui()
        
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Topbar
        self.topbar = Topbar(title=f"QueryAI | Espace Utilisateur")
        self.topbar.logout_clicked.connect(self.logout_requested.emit)

        # Add database selection to topbar
        self.db_combo = QComboBox()
        self.db_combo.setMinimumWidth(200)
        self.db_combo.currentIndexChanged.connect(self._change_database)

        # Create menu for AI models
        self.ia_menu = QMenu()
        self.ia_menu.addAction("Claude", lambda: self._select_ia_model("claude"))
        self.ia_menu.addAction("GPT", lambda: self._select_ia_model("gpt"))
        self.ia_menu.addAction("Gemini", lambda: self._select_ia_model("gemini"))
        self.ia_menu.addSeparator()
        self.ia_menu.addAction("Changer la clé", self._change_api_key)
        self.ia_menu.addAction("Supprimer la clé", self._delete_api_key)

        # Create button for AI selection
        self.ia_button = ClickableLabel("API")
        self.ia_button.setStyleSheet("font-weight: bold; color: #0066CC; cursor: pointer;")
        self.ia_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.ia_button.clicked.connect(lambda: self.ia_menu.exec(self.ia_button.mapToGlobal(
            self.ia_button.rect().center())))
        
        # Create button for Open Source Model selection
        self.os_button = ClickableLabel("Open source model")
        self.os_button.setStyleSheet("font-weight: bold; color: #6B7280; cursor: pointer;")
        self.os_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.os_button.clicked.connect(self._select_open_source)
        
        db_layout = QHBoxLayout()
        db_layout.addWidget(QLabel("Base :"))
        db_layout.addWidget(self.db_combo)
        db_layout.addSpacing(10)
        db_layout.addWidget(QLabel("IA :"))
        db_layout.addWidget(self.ia_button)
        db_layout.addSpacing(10)
        db_layout.addWidget(self.os_button)
        
        # Inject custom widgets into topbar
        index = self.topbar.layout.indexOf(self.topbar.info_label)
        self.topbar.layout.insertLayout(index + 1, db_layout)
        
        self.layout.addWidget(self.topbar)
        
        # Main content area
        self.content_widget = QWidget()
        self.content_layout = QHBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Navigation (Horizontal tabs or sidebar)
        # Using a simple horizontal tab-like navigation for Query Analysis, Visualization, Export
        self.nav_widget = QWidget()
        self.nav_widget.setObjectName("surface")
        self.nav_widget.setFixedHeight(40)
        self.nav_layout = QHBoxLayout(self.nav_widget)
        self.nav_layout.setContentsMargins(20, 0, 20, 0)
        
        from widgets.modern_button import ModernButton
        self.btn_query = ModernButton("Query Analysis", "secondary")
        self.btn_viz = ModernButton("Visualization", "secondary")
        self.btn_export = ModernButton("Export", "secondary")
        self.btn_settings = ModernButton("Settings", "secondary")
        
        self.btn_query.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.btn_viz.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.btn_export.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        self.btn_settings.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        
        self.nav_layout.addWidget(self.btn_query)
        self.nav_layout.addWidget(self.btn_viz)
        self.nav_layout.addWidget(self.btn_export)
        self.nav_layout.addStretch()
        self.nav_layout.addWidget(self.btn_settings)
        
        # Stacked Widget for panels
        self.stacked_widget = QStackedWidget()
        
        # We need a shared state object for panels
        self.shared_state = {
            'last_query_result': None,
            'last_columns': None,
            'last_rows': None
        }
        
        self.query_panel = QueryPanel(self.controller, self.shared_state)
        self.viz_panel = VisualizationPanel(self.controller, self.shared_state)
        self.export_panel = ExportPanel(self.controller, self.shared_state)
        self.settings_panel = SettingsPanel(self.user_data.get('id'), is_admin=False)
        
        self.stacked_widget.addWidget(self.query_panel)
        self.stacked_widget.addWidget(self.viz_panel)
        self.stacked_widget.addWidget(self.export_panel)
        self.stacked_widget.addWidget(self.settings_panel)
        
        content_vlayout = QVBoxLayout()
        content_vlayout.addWidget(self.nav_widget)
        content_vlayout.addWidget(self.stacked_widget)
        
        self.content_layout.addLayout(content_vlayout)
        self.layout.addWidget(self.content_widget, 1)
        
        self._load_databases()

    def _load_databases(self):
        dbs = self.controller.get_accessible_databases()
        self.db_combo.blockSignals(True)
        self.db_combo.clear()
        for db in dbs:
            self.db_combo.addItem(f"[{db['type']}] {db['nom']} (Accès: {db['type_acces']})", db['id'])
        self.db_combo.blockSignals(False)
        
        if self.db_combo.count() > 0:
            self._change_database()
        else:
            QMessageBox.information(self, "Info", "Vous n'avez accès à aucune base de données. Contactez votre administrateur.")
            
    def _change_database(self):
        db_id = self.db_combo.currentData()
        if db_id:
            res = self.controller.connect_to_database(db_id)
            if not res['ok']:
                QMessageBox.warning(self, "Erreur de connexion", res['erreur'])

    def _select_ia_model(self, nom_service: str):
        """Appelé quand l'utilisateur sélectionne un modèle IA."""
        try:
            # Vérifier si une clé API existe
            if not self.controller.api_key_exists(nom_service):
                # Afficher le dialogue pour saisir la clé
                dialog = APIKeyDialog(nom_service, self)
                result = dialog.exec()

                if result == APIKeyDialog.DialogCode.Accepted:
                    api_key = dialog.api_key
                    if api_key:  # Vérifier que la clé n'est pas vide
                        # Sauvegarder la clé
                        res = self.controller.save_api_key(nom_service, api_key)
                        if res['ok']:
                            # Mettre à jour le bouton avec le nom du modèle et styles
                            self.ia_button.setText(nom_service.upper())
                            self.ia_button.setStyleSheet("font-weight: bold; color: #0066CC; cursor: pointer;")
                            self.os_button.setStyleSheet("font-weight: bold; color: #6B7280; cursor: pointer;")
                            self.controller.set_ia_service(nom_service)
                            QMessageBox.information(self, "Succès",
                                f"Clé API {nom_service.upper()} enregistrée avec succès!")
                        else:
                            QMessageBox.warning(self, "Erreur",
                                f"Erreur lors de l'enregistrement: {res.get('erreur', 'Erreur inconnue')}")
                # Si annulation (DialogCode.Rejected), on ne fait rien
            else:
                # La clé existe déjà, juste changer le service et styles
                self.ia_button.setText(nom_service.upper())
                self.ia_button.setStyleSheet("font-weight: bold; color: #0066CC; cursor: pointer;")
                self.os_button.setStyleSheet("font-weight: bold; color: #6B7280; cursor: pointer;")
                self.controller.set_ia_service(nom_service)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue: {str(e)}")

    def _select_open_source(self):
        """Appelé quand l'utilisateur sélectionne le modèle open-source."""
        try:
            self.ia_button.setStyleSheet("font-weight: bold; color: #6B7280; cursor: pointer;")
            self.os_button.setStyleSheet("font-weight: bold; color: #0066CC; cursor: pointer;")
            self.controller.set_ia_service("open_source")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue: {str(e)}")

    def _change_api_key(self):
        """Permet à l'utilisateur de changer la clé API."""
        # Afficher un menu pour choisir quel service changer
        submenu = QMenu()
        submenu.addAction("Claude", lambda: self._do_change_key("claude"))
        submenu.addAction("GPT", lambda: self._do_change_key("gpt"))
        submenu.addAction("Gemini", lambda: self._do_change_key("gemini"))
        submenu.addAction("Open source model", lambda: self._do_change_key("open_source"))
        submenu.exec(QCursor.pos())

    def _do_change_key(self, nom_service: str):
        """Change la clé API pour un service spécifique."""
        dialog = APIKeyDialog(nom_service, self)
        result = dialog.exec()

        if result == APIKeyDialog.DialogCode.Accepted:
            api_key = dialog.api_key
            if api_key:
                res = self.controller.save_api_key(nom_service, api_key)
                if res['ok']:
                    service_display = "OpenRouter" if nom_service == "open_source" else nom_service.upper()
                    QMessageBox.information(self, "Succès",
                        f"Clé API {service_display} mise à jour avec succès!")
                else:
                    QMessageBox.warning(self, "Erreur",
                        f"Erreur lors de la mise à jour: {res.get('erreur', 'Erreur inconnue')}")

    def _delete_api_key(self):
        """Permet à l'utilisateur de supprimer une clé API."""
        submenu = QMenu()
        submenu.addAction("Claude", lambda: self._do_delete_key("claude"))
        submenu.addAction("GPT", lambda: self._do_delete_key("gpt"))
        submenu.addAction("Gemini", lambda: self._do_delete_key("gemini"))
        submenu.addAction("Open source model", lambda: self._do_delete_key("open_source"))
        submenu.exec(QCursor.pos())

    def _do_delete_key(self, nom_service: str):
        """Supprime la clé API pour un service spécifique."""
        service_display = "OpenRouter" if nom_service == "open_source" else nom_service.upper()
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Êtes-vous sûr de vouloir supprimer la clé API {service_display} ?\nVous devrez en fournir une nouvelle pour utiliser ce service.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            res = self.controller.delete_api_key(nom_service)
            if res['ok']:
                QMessageBox.information(self, "Succès",
                    f"Clé API {service_display} supprimée avec succès!")
            else:
                QMessageBox.warning(self, "Erreur",
                    f"Erreur lors de la suppression: {res.get('erreur', 'Erreur inconnue')}")
