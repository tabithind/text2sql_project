from PyQt6.QtWidgets import QTableWidget, QHeaderView, QAbstractItemView
from PyQt6.QtCore import Qt

class ModernTable(QTableWidget):
    def __init__(self, rows=0, columns=0, parent=None):
        super().__init__(rows, columns, parent)
        
        # Modern table configuration
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        
        self.setMinimumHeight(200)

    def set_data(self, headers, data):
        self.clear()
        self.setRowCount(len(data))
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        for row_idx, row_data in enumerate(data):
            # Si row_data est un dictionnaire ou assimilé, on mappe selon l'ordre des headers
            if hasattr(row_data, 'get') and not isinstance(row_data, (str, bytes)):
                row_values = [row_data.get(h) for h in headers]
            elif isinstance(row_data, dict):
                row_values = [row_data.get(h) for h in headers]
            else:
                row_values = row_data
                
            for col_idx, col_data in enumerate(row_values):
                from PyQt6.QtWidgets import QTableWidgetItem
                item = QTableWidgetItem(str(col_data) if col_data is not None else "")
                # item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(row_idx, col_idx, item)
        self.resizeColumnsToContents()
