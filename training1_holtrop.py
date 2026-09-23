import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, 
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, 
    QPushButton, QMessageBox, QDoubleSpinBox, QComboBox
)

class ResistanceHoltropDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.main_win = parent  
        
        self.ship_data = getattr(parent, 'ship_data', {})
        self.state = getattr(parent, 'state', None)
        
        self.setWindowTitle("Resistance Analysis - Holtrop & Mennen Method - Jalayn")
        self.resize(1100, 750)
        
        if not self.ship_data or not self.state:
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, self.show_warning_and_close)
            return

        self.setup_ui()
    
    def show_warning_and_close(self):
        """Warning dialog"""
        QMessageBox.warning(
            self.main_win, 
            "Data Insufficient", 
            "Please ensure ship main dimensions and hydrostatic state are available!"
        )
        self.reject()
        
    def setup_ui(self):
        if not self.ship_data or not self.state:
            QMessageBox.warning(
                self.main_win, 
                "Data Insufficient", 
                "Please ensure ship main dimensions and hydrostatic state are available!"
            )
            return

        if not self.layout():
            self.setup_ui()
            
        self.exec()

    def setup_ui(self):
        main_layout = QHBoxLayout(self) 

        # ================= LEFT PANEL: INPUT & CALCULATION =================
        left_layout = QVBoxLayout()
        
        # Group 1: Hydrostatic Link 
        hydro_group = QGroupBox("Hydrostatic Input Reference")
        hydro_grid = QGridLayout(hydro_group)
        
        hydro_grid.addWidget(QLabel("Target Draft for Analysis (m):"), 0, 0)
        self.draft_input = QDoubleSpinBox()
        self.draft_input.setRange(0.1, self.ship_data.get("H", 10.0))
        self.draft_input.setValue(self.ship_data.get("T", 5.0))
        self.draft_input.setDecimals(3)
        hydro_grid.addWidget(self.draft_input, 0, 1)
        
        left_layout.addWidget(hydro_group)

        # Group 2: Specific Holtrop Parameters 
        holtrop_group = QGroupBox("Holtrop Specific Parameters")
        holtrop_grid = QGridLayout(holtrop_group)
        
        # input Holtrop: Bow and Stern Type 
        holtrop_grid.addWidget(QLabel("Stern Type:"), 0, 0)
        self.stern_type = QComboBox()
        self.stern_type.addItems(["Pram with bulbous bow", "Normal section stern", "V-shaped sections"])
        holtrop_grid.addWidget(self.stern_type, 0, 1)
        
        # Vs input, for graph (Knot)
        holtrop_grid.addWidget(QLabel("Min Speed (Knots):"), 1, 0)
        self.min_speed = QDoubleSpinBox()
        self.min_speed.setValue(10.0)
        holtrop_grid.addWidget(self.min_speed, 1, 1)
        
        holtrop_grid.addWidget(QLabel("Max Speed (Knots):"), 2, 0)
        self.max_speed = QDoubleSpinBox()
        self.max_speed.setValue(22.0)
        holtrop_grid.addWidget(self.max_speed, 2, 1)
        
        left_layout.addWidget(holtrop_group)

        # Action Button
        btn_calculate = QPushButton("Calculate Resistance")
        btn_calculate.setStyleSheet("font-weight: bold; background-color: #3498db; color: white; height: 35px;")
        btn_calculate.clicked.connect(self.run_holtrop_analysis)
        left_layout.addWidget(btn_calculate)

        # Group 3: Output Table Summary
        res_group = QGroupBox("Resistance Output Summary")
        res_vbox = QVBoxLayout(res_group)
        
        self.res_table = QTableWidget()
        headers = ["Speed (Knots)", "Fn", "R_Total (kN)", "EHP (kW)"]
        self.res_table.setColumnCount(len(headers))
        self.res_table.setHorizontalHeaderLabels(headers)
        self.res_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        res_vbox.addWidget(self.res_table)
        
        left_layout.addWidget(res_group)
        main_layout.addLayout(left_layout, stretch=2)

        # ================= RIGHT PANEL: GRAPH VISUALIZATION =================
        graph_group = QGroupBox("Resistance vs Speed Curve")
        graph_layout = QVBoxLayout(graph_group)
        
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', "Total Resistance / R_T (kN)", color='k', **{'font-size': '10pt'})
        self.plot_widget.setLabel('bottom', "Ship Speed (Knots)", color='k', **{'font-size': '10pt'})
        self.plot_widget.getAxis('left').setPen('k')
        self.plot_widget.getAxis('left').setTextPen('k')
        self.plot_widget.getAxis('bottom').setPen('k')
        self.plot_widget.getAxis('bottom').setTextPen('k')
        
        graph_layout.addWidget(self.plot_widget)
        main_layout.addWidget(graph_group, stretch=3)

    def run_holtrop_analysis(self):
        """Mengambil data hidrostatik secara real-time dan menghitung Holtrop"""
        target_draft = self.draft_input.value()
        
        # 1. Hydrostatic Data Input, from hydrostatic calculation module
        hydro_data = self.state.compute_hydrostatics(target_draft)
        
        if not hydro_data:
            QMessageBox.critical(self, "Calculation Error", "Failed to retrieve hydrostatic data for this draft.")
            return
            
        # Hydrostatic Parameter Needed For Holtrop
        disp = hydro_data['DISP']      # Displacement (ton)
        wsa = hydro_data['WLA']        # Wetted Surface Area (m²) 
        cb = hydro_data['CB']          # Block Coefficient
        cp = hydro_data['CP']          # Prismatic Coefficient
        lcb = hydro_data['LCB']        # Longitudinal Center of Buoyancy
        
        # Ship Main Dimension
        L = self.ship_data.get("LBP", 100.0)
        B = self.ship_data.get("B", 16.0)
        
        # 2. Vs Calculation
        v_min = self.min_speed.value()
        v_max = self.max_speed.value()
        speeds_knot = np.linspace(v_min, v_max, 10)
        
        self.res_table.setRowCount(0)
        self.plot_widget.clear()
        
        speeds_ms = speeds_knot * 0.514444 # convert to m/s
        r_total_list = []
        ehp_list = []
        
        for i, (v_knot, v_ms) in enumerate(zip(speeds_knot, speeds_ms)):
            # Froude Number (Fn) Calculation
            g = 9.81
            fn = v_ms / np.sqrt(g * L)
            
            # --- FORMULA HOLTROP & MENNEN (Simple) ---
            rho = 1025  
            cf = 0.075 / (np.log10(v_ms * L / 1.188e-6) - 2)**2 # ITTC-57 Friction
            k = 0.12 + 0.11 * (B / L) # Form factor approach
            
            # 1. Friction Resistance 
            r_friction_N = 0.5 * rho * wsa * (v_ms**2) * cf * (1 + k)
            r_friction_kN = r_friction_N / 1000.0
            
            # 2. Wave Resistance 
            r_wave_kN = disp * g * (fn**4) * 0.05 
            
            # 3. Total Resistance 
            r_total = r_friction_kN + r_wave_kN 
            
            # 4. Effective Horse Power 
            ehp = r_total * v_ms 
            
            r_total_list.append(r_total)
            ehp_list.append(ehp)

            # Input to table
            self.res_table.insertRow(i)
            self.res_table.setItem(i, 0, QTableWidgetItem(f"{v_knot:.2f}"))
            self.res_table.setItem(i, 1, QTableWidgetItem(f"{fn:.3f}"))
            self.res_table.setItem(i, 2, QTableWidgetItem(f"{r_total:.2f}"))
            self.res_table.setItem(i, 3, QTableWidgetItem(f"{ehp:.2f}"))
            
        # 3. PLOT TO PYQTGRAPH
        self.plot_widget.plot(
            speeds_knot, r_total_list, 
            pen=pg.mkPen(color=(46, 204, 113), width=3.0),
            symbol='o', symbolSize=6, symbolBrush='d'
        )