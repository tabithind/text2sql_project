from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QMessageBox)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from widgets.modern_button import ModernButton
from widgets.modern_card import ModernCard
from services.chart_service import ChartService
import os

class VisualizationPanel(QWidget):
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
        
        # Header controls
        controls_layout = QHBoxLayout()
        
        self.chart_type = QComboBox()
        self.chart_type.addItems(['bar', 'line', 'pie', 'donut', 'scatter', 'histogram', 'box', 'area'])
        
        self.x_axis = QComboBox()
        self.y_axis = QComboBox()
        
        self.refresh_btn = ModernButton("Générer Graphique", "primary")
        self.refresh_btn.clicked.connect(self._generate_chart)
        
        controls_layout.addWidget(QLabel("Type :"))
        controls_layout.addWidget(self.chart_type)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(QLabel("X :"))
        controls_layout.addWidget(self.x_axis)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(QLabel("Y :"))
        controls_layout.addWidget(self.y_axis)
        controls_layout.addStretch()
        controls_layout.addWidget(self.refresh_btn)
        
        # Image display
        self.image_label = QLabel("Générez une requête puis un graphique pour le voir ici.")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background-color: #F3F4F6; border: 1px dashed #D1D5DB; border-radius: 8px;")
        self.image_label.setMinimumHeight(400)
        
        self.card_layout.addLayout(controls_layout)
        self.card_layout.addSpacing(20)
        self.card_layout.addWidget(self.image_label, 1)
        
        self.layout.addWidget(self.card)

    def showEvent(self, event):
        super().showEvent(event)
        self._update_columns()

    def _update_columns(self):
        cols = self.shared_state.get('last_columns', [])
        if cols:
            self.x_axis.blockSignals(True)
            self.y_axis.blockSignals(True)
            self.x_axis.clear()
            self.y_axis.clear()
            self.x_axis.addItems(cols)
            self.y_axis.addItem("-- Aucun --")
            self.y_axis.addItems(cols)
            self.x_axis.blockSignals(False)
            self.y_axis.blockSignals(False)

    def _generate_chart(self):
        cols = self.shared_state.get('last_columns')
        rows = self.shared_state.get('last_rows')
        
        if not cols or not rows:
            QMessageBox.warning(self, "Erreur", "Aucune donnée disponible. Veuillez d'abord exécuter une requête dans l'onglet Query Analysis.")
            return
            
        x = self.x_axis.currentText()
        y = self.y_axis.currentText()
        if y == "-- Aucun --": y = None
        
        ctype = self.chart_type.currentText()
        
        # Note: ChartService requires 'kaleido' for write_image to work natively.
        res = ChartService.render_chart(ctype, cols, rows, x, y, title=f"Graphique {ctype}")
        if res['ok']:
            pixmap = QPixmap(res['filepath'])
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            QMessageBox.warning(self, "Erreur de génération", res.get('erreur', 'Erreur inconnue.\nAssurez-vous que les dépendances (kaleido) sont installées.'))
