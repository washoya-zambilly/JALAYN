from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QHeaderView, QTableWidgetItem, QLabel, QPushButton
from PySide6.QtWidgets import QFormLayout, QDoubleSpinBox, QHBoxLayout

class ShipDimensionDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.main_win = parent 
        self.setWindowTitle("Ship Dimensions - Jalayn")
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout(self)

        if not hasattr(self.main_win, 'ship_data'):
            self.main_win.ship_data = {"LPP": 100.0, "B": 16.0, "H": 8.0, "T": 5.0}

        self.inputs = {}
        for key, val in self.main_win.ship_data.items():
            sp = QDoubleSpinBox()
            sp.setRange(0, 5000)
            sp.setDecimals(3)
            sp.setValue(val)
            layout.addRow(f"{key} (m):", sp)
            self.inputs[key] = sp

        # Button
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save")
        btn_cancel = QPushButton("Cancel")
        
        btn_save.clicked.connect(self._save_dims)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addRow(btn_layout)

    def _save_dims(self):
        """Save ship main dimension."""
        for key, widget in self.inputs.items():
            self.main_win.ship_data[key] = widget.value()
        
        self.main_win.statusBar().showMessage(f"Main Dimensions Updated: LPP {self.main_win.ship_data['LPP']} m", 5000)
        self.accept()