import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, 
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, 
    QFrame, QLabel, QPushButton, QMessageBox, QDoubleSpinBox
)

#HYDROSTATIC DIALOG
class HydrostaticsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.main_win = parent  
        
        self.ship_data = getattr(parent, 'ship_data', {})
        self.stations = getattr(parent, 'stations', [])
        self.state = getattr(parent, 'state', None)
        
        self.setWindowTitle("Hydrostatic Calculation - Jalayn")
        self.resize(1250, 800)
        self.checkboxes = []
        
    def open_hydrostatics_dialog(self):
        if not hasattr(self, 'ship_data') or not self.stations:
            QMessageBox.warning(self, "Data not sufficient", "Please input the ship main dimension!.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Hydrostatic Calculation")
        dialog.resize(1250, 800) 
        main_layout = QVBoxLayout(dialog)

        # 1. TABLE & PANEL
        table_group = QGroupBox("Hydrostatic Table Summary")
        table_hbox = QHBoxLayout(table_group) 
        
        # MAIN TABLE
        table = QTableWidget()
        headers = [
            "T (m)", "Volume (m³)", "DISP (t)", "WLA (m²)", "TPC (t/cm)", 
            "LCB (m)", "LCF (m)", "KB (m)", 
            "BM_T (m)", "BM_L (m)", "KM_T (m)", "KM_L (m)", 
            "CB", "CWP", "CM", "CP", "MCTC (t.m/cm)"
        ]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.setEditTriggers(QTableWidget.NoEditTriggers)

        max_t = self.ship_data.get("H", 10.0) 
        drafts = np.linspace(0.5, max_t, 15)
        for row, d in enumerate(drafts):
            data = self.state.compute_hydrostatics(d) 
            if data:
                table.insertRow(row)
                table.setItem(row, 0, QTableWidgetItem(f"{data['T']:.3f}"))
                table.setItem(row, 1, QTableWidgetItem(f"{data['VOLUME']:.1f}"))
                table.setItem(row, 2, QTableWidgetItem(f"{data['DISP']:.1f}"))
                table.setItem(row, 3, QTableWidgetItem(f"{data['WLA']:.1f}"))
                table.setItem(row, 4, QTableWidgetItem(f"{data['TPC']:.2f}"))
                table.setItem(row, 5, QTableWidgetItem(f"{data['LCB']:.3f}"))
                table.setItem(row, 6, QTableWidgetItem(f"{data['LCF']:.3f}"))
                table.setItem(row, 7, QTableWidgetItem(f"{data['KB']:.3f}"))
                table.setItem(row, 8, QTableWidgetItem(f"{data['BM_T']:.3f}"))
                table.setItem(row, 9, QTableWidgetItem(f"{data['BM_L']:.3f}"))
                table.setItem(row, 10, QTableWidgetItem(f"{data['KM_T']:.3f}"))
                table.setItem(row, 11, QTableWidgetItem(f"{data['KM_L']:.3f}"))
                table.setItem(row, 12, QTableWidgetItem(f"{data['CB']:.4f}"))
                table.setItem(row, 13, QTableWidgetItem(f"{data['CWP']:.4f}"))
                table.setItem(row, 14, QTableWidgetItem(f"{data['CM']:.4f}"))
                table.setItem(row, 15, QTableWidgetItem(f"{data['CP']:.4f}"))
                table.setItem(row, 16, QTableWidgetItem(f"{data['MCTC']:.3f}"))

        table_hbox.addWidget(table, stretch=4) 

        # CHECK BOX
        filter_panel = QGroupBox("Show/Hide Columns")
        filter_layout = QVBoxLayout(filter_panel)
        
        master_btn_layout = QHBoxLayout()
        btn_all = QPushButton("All")
        btn_none = QPushButton("Clear")
        master_btn_layout.addWidget(btn_all)
        master_btn_layout.addWidget(btn_none)
        filter_layout.addLayout(master_btn_layout)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        filter_layout.addWidget(line)

        self.checkboxes = []

        for col_idx, header_name in enumerate(headers):
            cb = QCheckBox(header_name)
            cb.setChecked(True) 
            
            if col_idx == 0:
                cb.setDisabled(True)
                
            cb.stateChanged.connect(lambda state, idx=col_idx: table.setColumnHidden(idx, state == 0))
            
            filter_layout.addWidget(cb)
            self.checkboxes.append(cb)

        filter_layout.addStretch() 
        table_hbox.addWidget(filter_panel, stretch=1) 

        main_layout.addWidget(table_group)

        # CALCULATOR
        calc_group = QGroupBox("Specific Draft Calculator")
        calc_layout = QGridLayout(calc_group)

        calc_layout.addWidget(QLabel("<b>Input Target Draft (m):</b>"), 0, 0)
        self.draft_input = QDoubleSpinBox()
        self.draft_input.setRange(0.0, max_t)
        self.draft_input.setDecimals(3)
        self.draft_input.setSingleStep(0.1)
        self.draft_input.setValue(self.ship_data.get("T", 5.0))
        self.draft_input.setStyleSheet("font-weight: bold; color: blue;")
        calc_layout.addWidget(self.draft_input, 0, 1)

        # Label Output 
        self.res_disp = QLabel("-"); self.res_volume = QLabel("-"); self.res_lcb = QLabel("-")
        self.res_lcf = QLabel("-"); self.res_kb = QLabel("-"); self.res_kmt = QLabel("-")
        self.res_kml = QLabel("-"); self.res_mctc = QLabel("-"); self.res_cb = QLabel("-"); self.res_tpc = QLabel("-")

        calc_layout.addWidget(QLabel("Displacement:"), 1, 0); calc_layout.addWidget(self.res_disp, 1, 1)
        calc_layout.addWidget(QLabel("Molded Volume:"), 1, 2); calc_layout.addWidget(self.res_volume, 1, 3)
        calc_layout.addWidget(QLabel("TPC:"), 1, 4); calc_layout.addWidget(self.res_tpc, 1, 5)
        calc_layout.addWidget(QLabel("LCB (from AP/FP):"), 2, 0); calc_layout.addWidget(self.res_lcb, 2, 1)
        calc_layout.addWidget(QLabel("LCF (Sumbu Trim):"), 2, 2); calc_layout.addWidget(self.res_lcf, 2, 3)
        calc_layout.addWidget(QLabel("KB (VCB):"), 2, 4); calc_layout.addWidget(self.res_kb, 2, 5)
        calc_layout.addWidget(QLabel("KM Transversal (KM_T):"), 3, 0); calc_layout.addWidget(self.res_kmt, 3, 1)
        calc_layout.addWidget(QLabel("KM Longitudinal (KM_L):"), 3, 2); calc_layout.addWidget(self.res_kml, 3, 3)
        calc_layout.addWidget(QLabel("MCTC:"), 3, 4); calc_layout.addWidget(self.res_mctc, 3, 5)
        calc_layout.addWidget(QLabel("Block Coeff (CB):"), 4, 0); calc_layout.addWidget(self.res_cb, 4, 1)

        self.draft_input.valueChanged.connect(self._update_quick_hydro)
        main_layout.addWidget(calc_group)

        # --- BUTTON (ALL / CLEAR) ---
        def select_all_columns():
            for cb in self.checkboxes:
                cb.setChecked(True)

        def clear_all_columns():
            for idx, cb in enumerate(self.checkboxes):
                if idx != 0: 
                    cb.setChecked(False)
        
        filter_layout.addWidget(line)

        # CREATE CURVE
        btn_curve = QPushButton("Show Curve")
        btn_curve.setStyleSheet("font-weight: bold; background-color: #2ecc71; color: white; height: 30px;")
        filter_layout.addWidget(btn_curve)

        filter_layout.addStretch() 
        table_hbox.addWidget(filter_panel, stretch=1)

        btn_all.clicked.connect(select_all_columns)
        btn_none.clicked.connect(clear_all_columns)

        btn_curve.clicked.connect(lambda: self.show_hydrostatic_curves(drafts, headers, table))

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dialog.accept)
        main_layout.addWidget(btn_close)

        self._update_quick_hydro()
        dialog.exec()

    def _update_quick_hydro(self):
        """Update Result"""
        d = self.draft_input.value()
        data = self.state.compute_hydrostatics(d)
        
        if data:
            self.res_disp.setText(f"<b>{data['DISP']:.2f} Ton</b>")
            self.res_volume.setText(f"<b>{data['VOLUME']:.2f} m³</b>")
            self.res_lcb.setText(f"<b>{data['LCB']:.3f} m</b>")
            self.res_lcf.setText(f"<b>{data['LCF']:.3f} m</b>")
            self.res_kb.setText(f"<b>{data['KB']:.3f} m</b>")
            self.res_kmt.setText(f"<b>{data['KM_T']:.3f} m</b>")
            self.res_kml.setText(f"<b>{data['KM_L']:.3f} m</b>")
            self.res_mctc.setText(f"<b>{data['MCTC']:.3f} t.m/cm</b>")
            self.res_cb.setText(f"<b>{data['CB']:.4f}</b>")
            self.res_tpc.setText(f"<b>{data['TPC']:.3f} t/cm</b>")
        else:
            labels = [
                self.res_disp, self.res_volume, self.res_lcb, self.res_lcf, 
                self.res_kb, self.res_kmt, self.res_kml, self.res_mctc, 
                self.res_cb, self.res_tpc
            ]
            for lbl in labels:
                lbl.setText("N/A")
    
    def show_hydrostatic_curves(self, drafts, headers, table):
        selected_indices = []
        selected_names = []
        for idx, cb in enumerate(self.checkboxes):
            if idx != 0 and cb.isChecked():
                selected_indices.append(idx)
                selected_names.append(headers[idx])

        if not selected_names:
            QMessageBox.information(self, "Choose Parameter", "Please check at least one parameter.")
            return

        curve_dialog = QDialog(self)
        curve_dialog.setWindowTitle("Hydrostatic Curves Diagram")
        curve_dialog.resize(950, 750)
        curve_layout = QVBoxLayout(curve_dialog)

        # Import  pyqtgraph 
        import pyqtgraph as pg

        plot_widget = pg.PlotWidget()
        plot_widget.setBackground('w')
        plot_widget.showGrid(x=True, y=True, alpha=0.3)
        plot_widget.addLegend(offset=(10, 10))

        # Title
        plot_widget.setTitle("Hydrostatic Curves Diagram", color="k", size="14pt", bold=True)
        plot_widget.setLabel('left', "Draft / T (m)", color='k', **{'font-size': '11pt', 'font-weight': 'bold'})
        plot_widget.setLabel('bottom', "Parameter Value", color='k', **{'font-size': '11pt', 'font-weight': 'bold'})
        
        plot_widget.getAxis('left').setPen('k')
        plot_widget.getAxis('left').setTextPen('k')
        plot_widget.getAxis('bottom').setPen('k')
        plot_widget.getAxis('bottom').setTextPen('k')

        # Color
        curve_colors = [
            (214, 40, 40),   # red
            (0, 48, 73),     # blue
            (247, 127, 0),   # Orange
            (56, 176, 0),    # green
            (114, 9, 183),   # violet
            (72, 202, 228),  # Cyan
            (241, 91, 181),  # Pink
            (0, 0, 0)        # black
        ]

        for color_idx, (idx, name) in enumerate(zip(selected_indices, selected_names)):
            actual_drafts = []
            param_values = []

            for row in range(table.rowCount()):
                draft_item = table.item(row, 0)
                param_item = table.item(row, idx)
                
                if draft_item and param_item:
                    actual_drafts.append(float(draft_item.text()))
                    param_values.append(float(param_item.text()))

            if param_values:
                color = curve_colors[color_idx % len(curve_colors)]
                
                plot_widget.plot(
                    param_values, 
                    actual_drafts, 
                    name=name, 
                    pen=pg.mkPen(color=color, width=3.0) 
                )

        curve_layout.addWidget(plot_widget)

        #Close
        btn_close_curve = QPushButton("Close")
        btn_close_curve.setStyleSheet("height: 30px; font-weight: bold;")
        btn_close_curve.clicked.connect(curve_dialog.accept)
        curve_layout.addWidget(btn_close_curve)

        curve_dialog.exec()