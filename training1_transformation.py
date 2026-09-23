#training1_transformation
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QGroupBox, QFormLayout, 
                             QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt

class HullTransformationDialog(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("Hull Scaling")
        self.resize(450, 500)
        
        # Main Dimension Data
        self.old_dimensions = getattr(main_window, 'ship_data', {})
        self.old_lpp = float(self.old_dimensions.get("LPP", 1.0))
        self.old_b = float(self.old_dimensions.get("B", 1.0))
        self.old_d = float(self.old_dimensions.get("D", 1.0))
        self.old_t = float(self.old_dimensions.get("T", 1.0))
        
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # === New Dim, input ===
        input_group = QGroupBox("Enter New Ship Dimensions")
        form_layout = QFormLayout(input_group)
        
        self.input_lpp = QLineEdit()
        self.input_lpp.setPlaceholderText(f"Current: {self.old_lpp} m")
        self.input_lpp.textChanged.connect(self.calculate_live_comparison)
        
        self.input_b = QLineEdit()
        self.input_b.setPlaceholderText(f"Current: {self.old_b} m")
        self.input_b.textChanged.connect(self.calculate_live_comparison)
        
        self.input_d = QLineEdit()
        self.input_d.setPlaceholderText(f"Current: {self.old_d} m")
        self.input_d.textChanged.connect(self.calculate_live_comparison)
        
        self.input_t = QLineEdit()
        self.input_t.setPlaceholderText(f"Current: {self.old_t} m")
        self.input_t.textChanged.connect(self.calculate_live_comparison)
        
        form_layout.addRow("New LPP (m):", self.input_lpp)
        form_layout.addRow("New Breadth (B) (m):", self.input_b)
        form_layout.addRow("New Depth (D) (m):", self.input_d)
        form_layout.addRow("New Draft (T) (m):", self.input_t)
        
        main_layout.addWidget(input_group)

        # === Comparison table ===
        comp_group = QGroupBox("Dimension Comparison & Scaling Factors")
        comp_layout = QVBoxLayout(comp_group)
        
        self.table_comp = QTableWidget(4, 3)
        self.table_comp.setHorizontalHeaderLabels(["Old Dim", "New Dim", "Factor (Ratio)"])
        self.table_comp.setVerticalHeaderLabels(["LPP (X)", "B (Y)", "D/T (Z)"])
        self.table_comp.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_comp.setEditTriggers(QTableWidget.NoEditTriggers) 
        
        self.table_comp.setItem(0, 0, QTableWidgetItem(f"{self.old_lpp:.3f}"))
        self.table_comp.setItem(1, 0, QTableWidgetItem(f"{self.old_b:.3f}"))
        self.table_comp.setItem(2, 0, QTableWidgetItem(f"{self.old_d:.3f}"))
        self.table_comp.setItem(3, 0, QTableWidgetItem(f"{self.old_t:.3f}"))
        self.table_comp.setVerticalHeaderLabels(["LPP (X)", "B (Y)", "Depth (Z)", "Draft (T)"])
        
        for row in range(4):
            self.table_comp.setItem(row, 1, QTableWidgetItem("-"))
            self.table_comp.setItem(row, 2, QTableWidgetItem("1.0000"))
            
        comp_layout.addWidget(self.table_comp)
        main_layout.addWidget(comp_group)

        # === Action Button ===
        btn_layout = QHBoxLayout()
        self.btn_apply = QPushButton("Scale Hull")
        self.btn_apply.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        self.btn_apply.clicked.connect(self.execute_transformation)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(self.btn_apply)
        main_layout.addLayout(btn_layout)

    def get_inputs(self):
        try:
            lpp_new = float(self.input_lpp.text()) if self.input_lpp.text() else self.old_lpp
            b_new = float(self.input_b.text()) if self.input_b.text() else self.old_b
            d_new = float(self.input_d.text()) if self.input_d.text() else self.old_d
            t_new = float(self.input_t.text()) if self.input_t.text() else self.old_t
            return lpp_new, b_new, d_new, t_new
        except ValueError:
            return None

    def calculate_live_comparison(self):
        inputs = self.get_inputs()
        if not inputs:
            return
        
        l_new, b_new, d_new, t_new = inputs
        
        f_x = l_new / self.old_lpp if self.old_lpp > 0 else 1.0
        f_y = b_new / self.old_b if self.old_b > 0 else 1.0
        f_z_d = d_new / self.old_d if self.old_d > 0 else 1.0
        f_z_t = t_new / self.old_t if self.old_t > 0 else 1.0
        
        self.table_comp.setItem(0, 1, QTableWidgetItem(f"{l_new:.3f}"))
        self.table_comp.setItem(1, 1, QTableWidgetItem(f"{b_new:.3f}"))
        self.table_comp.setItem(2, 1, QTableWidgetItem(f"{d_new:.3f}"))
        self.table_comp.setItem(3, 1, QTableWidgetItem(f"{t_new:.3f}"))
        
        self.table_comp.setItem(0, 2, QTableWidgetItem(f"{f_x:.4f}"))
        self.table_comp.setItem(1, 2, QTableWidgetItem(f"{f_y:.4f}"))
        self.table_comp.setItem(2, 2, QTableWidgetItem(f"{f_z_d:.4f}"))
        self.table_comp.setItem(3, 2, QTableWidgetItem(f"{f_z_t:.4f}"))

    def execute_transformation(self):
        inputs = self.get_inputs()
        if not inputs:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numerical values.")
            return
            
        l_new, b_new, d_new, t_new = inputs
        
        f_x = l_new / self.old_lpp if self.old_lpp > 0 else 1.0
        f_y = b_new / self.old_b if self.old_b > 0 else 1.0
        f_z = d_new / self.old_d if self.old_d > 0 else 1.0 

        reply = QMessageBox.question(
            self, "Confirm Transformation",
            f"Are you sure you want to scale the hull?\nFactors -> X: {f_x:.4f}, Y: {f_y:.4f}, Z: {f_z:.4f}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return

        try:
            if hasattr(self.main_window.state, 'save_snapshot'):
                self.main_window.state.save_snapshot()

            new_stations = {}
            for old_x, pts_list in self.main_window.stations.items():
                new_x = float(old_x) * f_x
                
                new_pts = []
                for pt in pts_list:
                    nx = pt[0] * f_x
                    ny = pt[1] * f_y
                    nz = pt[2] * f_z
                    
                    ang_in = pt[4] if len(pt) > 4 else None
                    ang_out = pt[5] if len(pt) > 5 else None
                    
                    new_pt = [nx, ny, nz]
                    if ang_in is not None: new_pt.append(ang_in)
                    if ang_out is not None: new_pt.append(ang_out)
                    new_pts.append(tuple(new_pt))
                
                new_stations[new_x] = new_pts

            self.main_window.stations = new_stations
            self.main_window.station_order = sorted(new_stations.keys())

            if hasattr(self.main_window, 'station_names'):
                new_names = {}
                for old_x, name in self.main_window.station_names.items():
                    new_names[float(old_x) * f_x] = name
                self.main_window.station_names = new_names

            if hasattr(self.main_window, 'profile_points') and self.main_window.profile_points:
                new_prof = []
                for pt in self.main_window.profile_points:
                    nx = pt[0] * f_x
                    ny = pt[1] * f_y
                    nz = pt[2] * f_z
                    new_prof.append((nx, ny, nz))
                self.main_window.profile_points = new_prof

            self.main_window.ship_data["LPP"] = l_new
            self.main_window.ship_data["B"] = b_new
            self.main_window.ship_data["D"] = d_new
            self.main_window.ship_data["T"] = t_new

            self.main_window.sync_station_list()
            if hasattr(self.main_window, 'update_dimension_input_fields'):
                self.main_window.update_dimension_input_fields()
                
            self.main_window.state.refresh_waterlines()
            self.main_window.state.refresh_buttocklines()
            self.main_window.update_all_views()
            
            QMessageBox.information(self, "Success", "Hull linear transformation executed successfully!")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Transformation failed: {str(e)}")

def launch_hull_transformation(main_window):
    if not hasattr(main_window, 'stations') or not main_window.stations:
        QMessageBox.warning(main_window, "Warning", "No active hull data found to transform.")
        return

    dialog = HullTransformationDialog(main_window)
    dialog.exec()