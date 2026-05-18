from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QTextEdit, QMessageBox, QTabWidget)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from widgets.modern_button import ModernButton
from widgets.modern_table import ModernTable
from widgets.modern_card import ModernCard
from widgets.loading_spinner import LoadingSpinner
from services.language_manager import LanguageManager

class QueryWorker(QThread):
    finished = pyqtSignal(dict)
    
    def __init__(self, controller, query_text):
        super().__init__()
        self.controller = controller
        self.query_text = query_text
        
    def run(self):
        res = self.controller.process_query(self.query_text)
        self.finished.emit(res)

class QueryPanel(QWidget):
    def __init__(self, controller, shared_state, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.shared_state = shared_state
        self._setup_ui()
        
    def _setup_ui(self):
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(16)
        
        lm = LanguageManager()
        
        # Panel 1: Natural Language Query
        self.nlq_card = ModernCard()
        self.nlq_layout = self.nlq_card.layout
        self.nlq_layout.addWidget(QLabel(lm.get('query.nlq_title', 'Natural Language Query')))
        
        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText(lm.get('query.placeholder', 'Ask a question about your data...'))
        self.query_input.setStyleSheet("background-color: transparent; border: 1px solid #E5E7EB; border-radius: 4px; padding: 8px;")
        
        btn_layout = QHBoxLayout()
        self.run_btn = ModernButton(f"▶ {lm.get('query.run', 'Run Query')}", "primary")
        self.clear_btn = ModernButton(f"✕ {lm.get('query.clear', 'Clear')}", "secondary")
        self.spinner = LoadingSpinner()
        
        self.run_btn.clicked.connect(self._run_query)
        self.clear_btn.clicked.connect(lambda: self.query_input.clear())
        
        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.spinner)
        btn_layout.addStretch()
        
        self.nlq_layout.addWidget(self.query_input)
        self.nlq_layout.addLayout(btn_layout)
        
        # Panel 2: Generated Query
        self.gen_card = ModernCard()
        self.gen_layout = self.gen_card.layout
        self.gen_layout.addWidget(QLabel(lm.get('query.generated', 'Generated Query / Operation')))
        
        self.generated_text = QTextEdit()
        self.generated_text.setReadOnly(True)
        self.generated_text.setStyleSheet("background-color: #F3F4F6; color: #1F2937; border: 1px solid #E5E7EB; border-radius: 4px; font-family: monospace;")
        
        self.copy_btn = ModernButton(lm.get('query.copy', 'Copy'), "secondary")
        self.copy_btn.clicked.connect(self._copy_query)
        
        self.gen_layout.addWidget(self.generated_text)
        self.gen_layout.addWidget(self.copy_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        
        # Panel 3: Results & Insights
        self.res_card = ModernCard()
        self.res_layout = self.res_card.layout
        self.res_layout.addWidget(QLabel(lm.get('query.results', 'Results & Insights')))
        
        self.tab_widget = QTabWidget()
        
        # Tab 1: Results Table
        self.result_table = ModernTable()
        self.tab_widget.addTab(self.result_table, lm.get('query.tab_results', 'Résultats'))
        
        # Tab 2: Insights Text
        self.insights_text = QTextEdit()
        self.insights_text.setReadOnly(True)
        self.insights_text.setPlaceholderText("Aucun insight généré. Exécutez d'abord une requête.")
        self.insights_text.setStyleSheet("background-color: transparent; border: none; padding: 8px;")
        self.tab_widget.addTab(self.insights_text, lm.get('query.tab_insights', 'Insights'))
        
        self.res_layout.addWidget(self.tab_widget)
        
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #6B7280; font-size: 11px; font-style: italic; margin-top: 4px;")
        self.res_layout.addWidget(self.info_label)
        
        # Setup proportions (1:1:1)
        self.layout.addWidget(self.nlq_card, 1)
        self.layout.addWidget(self.gen_card, 1)
        self.layout.addWidget(self.res_card, 1)

    def _run_query(self):
        text = self.query_input.toPlainText().strip()
        if not text:
            return
            
        self.run_btn.setEnabled(False)
        self.spinner.start()
        self.generated_text.clear()
        self.result_table.clear()
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
        self.insights_text.clear()
        self.insights_text.setPlaceholderText("Génération des insights en cours...")
        self.info_label.setText("")
        
        self.worker = QueryWorker(self.controller, text)
        self.worker.finished.connect(self._on_query_finished)
        self.worker.start()
        
    def _on_query_finished(self, res):
        self.spinner.stop()
        self.run_btn.setEnabled(True)
        
        if not res['ok']:
            # Affichage erreur permission ou autre
            self.generated_text.setText(f"❌ Erreur\n{res.get('erreur')}")
            return
            
        # Display generated query
        query_str = res.get('query', '')
        if isinstance(query_str, dict):
            import json
            query_str = json.dumps(query_str, indent=2)
        self.generated_text.setText(str(query_str))
        
        if res.get('requires_confirmation'):
            reply = QMessageBox.question(
                self, "Confirmation requise", 
                f"Cette opération ({res['intention']}) modifiera des données.\nImpact estimé : {res.get('preview', {}).get('affected_rows', 'inconnu')} ligne(s).\nVoulez-vous exécuter ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.spinner.start()
                write_res = self.controller.execute_write_confirmation(res['query'])
                self.spinner.stop()
                if write_res['ok']:
                    QMessageBox.information(self, "Succès", f"Opération réussie. {write_res.get('affected_rows', 0)} ligne(s) affectée(s).")
                else:
                    QMessageBox.warning(self, "Erreur d'exécution", write_res.get('erreur', 'Erreur inconnue'))
            else:
                self.generated_text.append("\n\n-- Opération annulée par l'utilisateur.")
        elif res.get('intention') == 'schema':
            schema = res.get('schema', {})
            import json
            self.generated_text.setText("SHOW SCHEMA\n\n" + json.dumps(schema, indent=2))
        else:
            # Result table display
            result_data = res.get('result', {})
            if result_data.get('ok'):
                columns = result_data.get('columns', [])
                rows = result_data.get('rows', [])
                
                # Update shared state with ALL rows (so export & charts have the complete dataset)
                self.shared_state['last_columns'] = columns
                self.shared_state['last_rows'] = rows
                
                # Display only the first 10 rows in the UI table
                self.result_table.set_data(columns, rows[:10])
                
                # Update the info label
                if len(rows) > 10:
                    self.info_label.setText(f"💡 Affichage des 10 premières lignes sur {len(rows)} disponibles (exportez pour tout voir).")
                else:
                    self.info_label.setText("")
                
                # Affichage des insights
                insights = res.get('insights', '')
                if insights:
                    self.insights_text.setMarkdown(insights)
                else:
                    self.insights_text.setPlaceholderText("Aucun insight généré pour ces données.")
            else:
                self.generated_text.append(f"\n\n❌ Erreur d'exécution:\n{result_data.get('erreur')}")
                self.insights_text.setPlaceholderText("Erreur lors de l'exécution de la requête. Aucun insight disponible.")
                self.info_label.setText("")
                
    def _copy_query(self):
        from PyQt6.QtWidgets import QApplication
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Mode.Clipboard)
        cb.setText(self.generated_text.toPlainText(), mode=cb.Mode.Clipboard)
