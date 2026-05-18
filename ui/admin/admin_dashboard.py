from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget
from PyQt6.QtCore import pyqtSignal
from widgets.sidebar import Sidebar
from widgets.topbar import Topbar
from controllers.admin_controller import AdminController
from ui.admin.users_panel import UsersPanel
from ui.admin.databases_panel import DatabasesPanel
from ui.admin.permissions_panel import PermissionsPanel
from ui.admin.settings_panel import SettingsPanel

class AdminDashboard(QWidget):
    logout_requested = pyqtSignal()
    
    def __init__(self, admin_data: dict, parent=None):
        super().__init__(parent)
        self.admin_data = admin_data
        self.controller = AdminController(admin_data)
        self._setup_ui()
        
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Topbar
        self.topbar = Topbar(title="QueryAI | Espace Admin")
        self.topbar.logout_clicked.connect(self.logout_requested.emit)
        self.layout.addWidget(self.topbar)
        
        # Main content area
        self.content_widget = QWidget()
        self.content_layout = QHBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Sidebar
        sidebar_items = [
            ("users_icon", "Utilisateurs"),
            ("db_icon", "Bases de données"),
            ("perm_icon", "Permissions"),
            ("settings_icon", "Paramètres")
        ]
        self.sidebar = Sidebar(sidebar_items)
        self.sidebar.item_selected.connect(self._change_panel)
        self.content_layout.addWidget(self.sidebar)
        
        # Stacked Widget for panels
        self.stacked_widget = QStackedWidget()
        self.content_layout.addWidget(self.stacked_widget, 1)
        
        self.layout.addWidget(self.content_widget, 1)
        
        # Initialize panels
        self._init_panels()
        
    def _init_panels(self):
        self.users_panel = UsersPanel(self.controller)
        self.databases_panel = DatabasesPanel(self.controller)
        self.permissions_panel = PermissionsPanel(self.controller)
        self.settings_panel = SettingsPanel(self.admin_data.get('id'), is_admin=True)
        
        self.stacked_widget.addWidget(self.users_panel)
        self.stacked_widget.addWidget(self.databases_panel)
        self.stacked_widget.addWidget(self.permissions_panel)
        self.stacked_widget.addWidget(self.settings_panel)
        
    def _change_panel(self, index: int):
        self.stacked_widget.setCurrentIndex(index)
        # Call refresh method if panel has one
        current_panel = self.stacked_widget.currentWidget()
        if hasattr(current_panel, 'refresh'):
            current_panel.refresh()
