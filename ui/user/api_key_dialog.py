from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QMessageBox, QCheckBox)
from PyQt6.QtCore import Qt
from widgets.modern_button import ModernButton

class APIKeyDialog(QDialog):
    """Dialog pour saisir la clé API d'un service IA."""
    
    def __init__(self, nom_service: str, parent=None):
        super().__init__(parent)
        self.nom_service = nom_service
        self.api_key = None
        self._setup_ui()
        
    def _setup_ui(self):
        service_label = "OpenRouter (Open Source)" if self.nom_service == "open_source" else self.nom_service.upper()
        self.setWindowTitle(f"Configurer la clé API - {service_label}")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel(f"Clé API {service_label}")
        title.setObjectName("title")
        layout.addWidget(title)
        
        # Info text
        info_text = QLabel(self._get_info_text())
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(info_text)
        
        # Input field
        input_layout = QHBoxLayout()
        key_label = QLabel("Clé API :")
        self.key_input = QLineEdit()
        placeholder_name = "OpenRouter" if self.nom_service == "open_source" else self.nom_service
        self.key_input.setPlaceholderText(f"Entrez votre clé {placeholder_name}...")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        input_layout.addWidget(key_label)
        input_layout.addWidget(self.key_input)
        layout.addLayout(input_layout)
        
        # Show password checkbox
        self.show_key_checkbox = QCheckBox("Afficher la clé")
        self.show_key_checkbox.toggled.connect(self._toggle_visibility)
        layout.addWidget(self.show_key_checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = ModernButton("Enregistrer", "primary")
        self.cancel_btn = ModernButton("Annuler", "secondary")
        
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
    def _get_info_text(self) -> str:
        """Retourne le texte d'information selon le service."""
        info = {
            'gpt': "Obtenez votre clé API OpenAI sur https://platform.openai.com/api-keys\nAssurez-vous d'avoir un compte actif avec des crédits.",
            'claude': "Obtenez votre clé API Anthropic sur https://console.anthropic.com/\nVérifiez que vous avez accès à Claude 3 Opus.",
            'gemini': "Obtenez votre clé API Google sur https://makersuite.google.com/app/apikey\nAssurez-vous que l'API Generative AI est activée.",
            'open_source': "Obtenez votre clé API OpenRouter sur https://openrouter.ai/keys\nOpenRouter vous permet d'utiliser des modèles open-source performants (Qwen-2.5, DeepSeek-Chat, etc.)."
        }
        return info.get(self.nom_service, "Entrez votre clé API")
    
    def _toggle_visibility(self, checked: bool):
        if checked:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    def get_api_key(self) -> str:
        """Retourne la clé saisie."""
        return self.key_input.text().strip()
    
    def exec(self) -> int:
        """Affiche le dialogue et retourne le résultat."""
        result = super().exec()
        if result == QDialog.DialogCode.Accepted:
            key = self.get_api_key()
            if not key:
                QMessageBox.warning(self, "Erreur", "La clé API ne peut pas être vide.")
                return self.exec()  # Réafficher le dialogue
            self.api_key = key
        return result
