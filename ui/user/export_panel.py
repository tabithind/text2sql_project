from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt
from widgets.modern_button import ModernButton
from widgets.modern_card import ModernCard
from services.export_service import ExportService

class ExportPanel(QWidget):
    def __init__(self, controller, shared_state, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.shared_state = shared_state
        self._setup_ui()
        
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 24, 24, 24)
        self.layout.setSpacing(16)
        
        self.card = ModernCard()
        self.card_layout = self.card.layout
        
        self.title = QLabel("Exporter les Résultats")
        self.title.setObjectName("title")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.info_label = QLabel("Exportez les résultats de votre dernière requête au format CSV ou Excel.")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("color: #6B7280; margin-bottom: 20px;")
        
        self.btn_csv = ModernButton("Exporter en CSV", "primary")
        self.btn_csv.clicked.connect(self._export_csv)
        
        self.btn_excel = ModernButton("Exporter en Excel", "secondary")
        self.btn_excel.clicked.connect(self._export_excel)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_csv)
        btn_layout.addSpacing(20)
        btn_layout.addWidget(self.btn_excel)
        btn_layout.addStretch()
        
        self.card_layout.addWidget(self.title)
        self.card_layout.addWidget(self.info_label)
        self.card_layout.addLayout(btn_layout)
        
        self.layout.addStretch()
        self.layout.addWidget(self.card)
        self.layout.addStretch()

    def _get_data(self):
        cols = self.shared_state.get('last_columns')
        rows = self.shared_state.get('last_rows')
        if not cols or not rows:
            QMessageBox.warning(self, "Erreur", "Aucune donnée disponible à exporter. Exécutez d'abord une requête.")
            return None, None
        return cols, rows

    def _export_csv(self):
        cols, rows = self.get_data()
        if not cols: return
        
        filepath, _ = QFileDialog.getSaveFileName(self, "Sauvegarder CSV", "exports/resultats.csv", "CSV Files (*.csv)")
        if filepath:
            res = ExportService.export_to_csv(cols, rows, filepath)
            if res['ok']:
                QMessageBox.information(self, "Succès", f"Exporté avec succès vers:\n{filepath}")
            else:
                QMessageBox.warning(self, "Erreur", res.get('erreur', 'Erreur inconnue'))

    def _export_excel(self):
        cols, rows = self.get_data()
        if not cols: return
        
        filepath, _ = QFileDialog.getSaveFileName(self, "Sauvegarder Excel", "exports/resultats.xlsx", "Excel Files (*.xlsx)")
        if filepath:
            res = ExportService.export_to_excel(cols, rows, filepath)
            if res['ok']:
                QMessageBox.information(self, "Succès", f"Exporté avec succès vers:\n{filepath}")
            else:
                QMessageBox.warning(self, "Erreur", res.get('erreur', 'Erreur inconnue.\nAssurez-vous que openpyxl est installé.'))

    def get_data(self):
        return self._get_data()
