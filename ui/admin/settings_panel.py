from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QMessageBox)
from PyQt6.QtCore import Qt
from widgets.modern_button import ModernButton
from services.settings_manager import SettingsManager
from services.theme_manager import ThemeManager
from services.language_manager import LanguageManager

class SettingsPanel(QWidget):
    def __init__(self, user_id: int, is_admin: bool = False, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.is_admin = is_admin
        self._setup_ui()
        self._load_settings()
        
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(16)
        
        self.title = QLabel("Paramètres")
        self.title.setObjectName("title")
        
        self.theme_label = QLabel("Thème :")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setFixedHeight(36)
        
        self.lang_label = QLabel("Langue :")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["fr", "en"])
        self.lang_combo.setFixedHeight(36)
        
        self.save_btn = ModernButton("Enregistrer les préférences", "primary")
        self.save_btn.setFixedWidth(200)
        self.save_btn.clicked.connect(self._save_settings)
        
        self.layout.addWidget(self.title)
        self.layout.addSpacing(20)
        
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(self.theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        self.layout.addLayout(theme_layout)
        
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(self.lang_label)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        self.layout.addLayout(lang_layout)
        
        self.layout.addSpacing(20)
        self.layout.addWidget(self.save_btn)
        self.layout.addStretch()
        
    def _load_settings(self):
        u_id = None if self.is_admin else self.user_id
        a_id = self.user_id if self.is_admin else None
        
        theme = SettingsManager.get_setting("theme", u_id, a_id, "light")
        lang = SettingsManager.get_setting("langue", u_id, a_id, "fr")
        
        self.theme_combo.setCurrentText(theme)
        self.lang_combo.setCurrentText(lang)

    def _save_settings(self):
        u_id = None if self.is_admin else self.user_id
        a_id = self.user_id if self.is_admin else None
        
        theme = self.theme_combo.currentText()
        lang = self.lang_combo.currentText()
        
        SettingsManager.set_setting("theme", theme, u_id, a_id)
        SettingsManager.set_setting("langue", lang, u_id, a_id)
        
        # Apply immediately
        ThemeManager().set_theme(theme)
        LanguageManager().set_language(lang)
        
        QMessageBox.information(self, "Succès", "Préférences enregistrées avec succès.")
