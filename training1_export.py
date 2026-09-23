import os
import numpy as np
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
    QListWidgetItem, QPushButton, QLabel, QGroupBox, 
    QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt

class ExportLinesDialog(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("Lines Plan Export")
        self.resize(1350, 750)
        
        self.setup_ui()
        self.populate_lists()
        self.update_live_preview()

    def setup_ui(self):
        main_hbox = QHBoxLayout(self)
        left_ctrl_panel = QVBoxLayout()
        
        lists_vbox = QVBoxLayout()
        
        # List Station
        st_group = QGroupBox("Stations (X Selection)")
        st_layout = QVBoxLayout(st_group)
        st_btns = QHBoxLayout()
        self.btn_st_all = QPushButton("All")
        self.btn_st_none = QPushButton("Clear")
        st_btns.addWidget(self.btn_st_all)
        st_btns.addWidget(self.btn_st_none)
        st_layout.addLayout(st_btns)
        self.st_list = QListWidget()
        st_layout.addWidget(self.st_list)
        lists_vbox.addWidget(st_group)
        
        # List Waterline
        wl_group = QGroupBox("Waterlines (Z Selection)")
        wl_layout = QVBoxLayout(wl_group)
        wl_btns = QHBoxLayout()
        self.btn_wl_all = QPushButton("All")
        self.btn_wl_none = QPushButton("Clear")
        wl_btns.addWidget(self.btn_wl_all)
        wl_btns.addWidget(self.btn_wl_none)
        wl_layout.addLayout(wl_btns)
        self.wl_list = QListWidget()
        wl_layout.addWidget(self.wl_list)
        lists_vbox.addWidget(wl_group)
        
        left_ctrl_panel.addLayout(lists_vbox)
        
        # Close button
        self.btn_close_wizard = QPushButton("Close Wizard")
        self.btn_close_wizard.setStyleSheet("height: 35px; font-weight: bold; background-color: #e74c3c; color: white;")
        left_ctrl_panel.addWidget(self.btn_close_wizard)
        
        main_hbox.addLayout(left_ctrl_panel, stretch=1)
        
        import pyqtgraph as pg

        # PANEL BODY PLAN
        body_plan_group = QGroupBox("Body Plan Layout Preview")
        body_layout = QVBoxLayout(body_plan_group)
        
        self.plot_body = pg.PlotWidget()
        self.plot_body.setBackground('w')
        self.plot_body.showGrid(x=True, y=True, alpha=0.3)
        self.plot_body.setAspectLocked(True)
        self.plot_body.setLabel('left', "Z - Height (m)", color='k')
        self.plot_body.setLabel('bottom', "Y - Breadth (m)", color='k')
        self.plot_body.getAxis('left').setPen('k')
        self.plot_body.getAxis('left').setTextPen('k')
        self.plot_body.getAxis('bottom').setPen('k')
        self.plot_body.getAxis('bottom').setTextPen('k')
        body_layout.addWidget(self.plot_body)
        
        self.btn_export_body = QPushButton("⚙️ Export Body Plan (DXF)")
        self.btn_export_body.setStyleSheet("font-weight: bold; background-color: #2ecc71; color: white; height: 35px;")
        body_layout.addWidget(self.btn_export_body)
        
        main_hbox.addWidget(body_plan_group, stretch=2)
        
        #PANEL WATERLINE PLAN
        wl_plan_group = QGroupBox("Half-Breadth Plan Layout Preview")
        wl_layout = QVBoxLayout(wl_plan_group)
        
        self.plot_wl = pg.PlotWidget()
        self.plot_wl.setBackground('w')
        self.plot_wl.showGrid(x=True, y=True, alpha=0.3)
        self.plot_wl.setAspectLocked(True)
        self.plot_wl.setLabel('left', "Y - Breadth (m)", color='k')
        self.plot_wl.setLabel('bottom', "X - Length (m)", color='k')
        self.plot_wl.getAxis('left').setPen('k')
        self.plot_wl.getAxis('left').setTextPen('k')
        self.plot_wl.getAxis('bottom').setPen('k')
        self.plot_wl.getAxis('bottom').setTextPen('k')
        wl_layout.addWidget(self.plot_wl)
        
        self.btn_export_wl = QPushButton("⚙️ Export Waterline Plan (DXF)")
        self.btn_export_wl.setStyleSheet("font-weight: bold; background-color: #3498db; color: white; height: 35px;")
        wl_layout.addWidget(self.btn_export_wl)
        
        main_hbox.addWidget(wl_plan_group, stretch=3) 
        
        # SIGNALS CONNECTIONS
        self.btn_st_all.clicked.connect(lambda: self.set_all_checked(self.st_list, True))
        self.btn_st_none.clicked.connect(lambda: self.set_all_checked(self.st_list, False))
        self.btn_wl_all.clicked.connect(lambda: self.set_all_checked(self.wl_list, True))
        self.btn_wl_none.clicked.connect(lambda: self.set_all_checked(self.wl_list, False))
        
        self.st_list.itemChanged.connect(self.update_live_preview)
        self.wl_list.itemChanged.connect(self.update_live_preview)
        
        self.btn_export_body.clicked.connect(self.export_only_body_plan)
        self.btn_export_wl.clicked.connect(self.export_only_waterline_plan)
        self.btn_close_wizard.clicked.connect(self.reject)

    def set_all_checked(self, list_widget, check_state):
        list_widget.blockSignals(True)
        for row in range(list_widget.count()):
            item = list_widget.item(row)
            item.setCheckState(Qt.Checked if check_state else Qt.Unchecked)
        list_widget.blockSignals(False)
        self.update_live_preview()

    def populate_lists(self):
        self.st_list.blockSignals(True)
        if hasattr(self.main_window, 'station_order'):
            for x in sorted(self.main_window.station_order):
                name = self.main_window.station_names.get(x, f"Station {x:.3f}")
                item = QListWidgetItem(name)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                item.setData(Qt.UserRole, x)
                self.st_list.addItem(item)
        self.st_list.blockSignals(False)
                
        self.wl_list.blockSignals(True)
        if hasattr(self.main_window, 'waterlines'):
            for z in sorted(self.main_window.waterlines.keys()):
                wl_names_dict = getattr(self.main_window, 'wl_names', {})
                name = wl_names_dict.get(z, f"Waterline Z: {z:.3f} m")
                item = QListWidgetItem(name)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                item.setData(Qt.UserRole, z)
                self.wl_list.addItem(item)
        self.wl_list.blockSignals(False)

    def update_live_preview(self):
        self.plot_body.clear()
        self.plot_wl.clear()
        import pyqtgraph as pg

        all_pts = [pt for st in self.main_window.stations.values() for pt in st]
        max_x = max(self.main_window.station_order) if self.main_window.station_order else 100.0
        max_y = max([pt[1] for pt in all_pts]) if all_pts else 15.0
        max_z = max([pt[2] for pt in all_pts]) if all_pts else 8.0

        # --- BODY PLAN PLOT ---
        self.plot_body.plot([-max_y * 1.3, max_y * 1.3], [0, 0], pen=pg.mkPen('k', width=1))
        self.plot_body.plot([0, 0], [-0.5, max_z * 1.3], pen=pg.mkPen('k', width=1, style=Qt.DashLine))

        for row in range(self.st_list.count()):
            item = self.st_list.item(row)
            if item.checkState() == Qt.Checked:
                x_coord = item.data(Qt.UserRole)
                pts = self.main_window.stations.get(x_coord, [])
                if len(pts) < 2: continue
                
                y_vals = np.array([pt[1] for pt in pts])
                z_vals = np.array([pt[2] for pt in pts])
                
                # Sisi Kanan & Kiri Simetri
                self.plot_body.plot(y_vals, z_vals, pen=pg.mkPen((46, 204, 113), width=2))
                self.plot_body.plot(-y_vals, z_vals, pen=pg.mkPen((46, 204, 113), width=2))

        # --- WATERLINE PLAN PLOT ---
        self.plot_wl.plot([-10, max_x * 1.1], [0, 0], pen=pg.mkPen('k', width=1, style=Qt.DashLine))
        self.plot_wl.plot([0, 0], [-max_y * 1.3, max_y * 1.3], pen=pg.mkPen('k', width=1))

        for row in range(self.wl_list.count()):
            item = self.wl_list.item(row)
            if item.checkState() == Qt.Checked:
                z_coord = item.data(Qt.UserRole)
                wl_pts = self.main_window.waterlines.get(z_coord, [])
                if len(wl_pts) < 2: continue

                x_vals = np.array([pt[0] for pt in wl_pts])
                y_vals = np.array([pt[1] for pt in wl_pts])
                
                # Sisi Atas & Sisi Bawah Plan
                self.plot_wl.plot(x_vals, y_vals, pen=pg.mkPen((41, 128, 185), width=2))
                self.plot_wl.plot(x_vals, -y_vals, pen=pg.mkPen((41, 128, 185), width=2))

    def export_only_body_plan(self):
        selected_stations = [self.st_list.item(r).data(Qt.UserRole) for r in range(self.st_list.count()) if self.st_list.item(r).checkState() == Qt.Checked]
        
        if not selected_stations:
            QMessageBox.warning(self, "Empty", "Check Minimum One Type To Proceed.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Export Body Plan to DXF", "", "AutoCAD DXF (*.dxf)")
        if not file_path: return

        import ezdxf
        try:
            doc = ezdxf.new('R2000')
            msp = doc.modelspace()
            if 'JALAYN_GRID' not in doc.layers:
                doc.layers.new(name='JALAYN_GRID', dxfattribs={'color': 7})
            if 'JALAYN_STATIONS' not in doc.layers:
                doc.layers.new(name='JALAYN_STATIONS', dxfattribs={'color': 3})

            all_pts = [pt for st in self.main_window.stations.values() for pt in st]
            max_y = max([pt[1] for pt in all_pts]) if all_pts else 15.0
            max_z = max([pt[2] for pt in all_pts]) if all_pts else 8.0

            msp.add_line((-max_y * 1.3, 0.0), (max_y * 1.3, 0.0), dxfattribs={'layer': 'JALAYN_GRID'})
            msp.add_line((0.0, -0.5), (0.0, max_z * 1.3), dxfattribs={'layer': 'JALAYN_GRID', 'linetype': 'DASHED'})

            for x_coord in selected_stations:
                pts = self.main_window.stations.get(x_coord, [])
                if len(pts) < 2: continue
                msp.add_lwpolyline([(pt[1], pt[2]) for pt in pts], dxfattribs={'layer': 'JALAYN_STATIONS'})
                msp.add_lwpolyline([(-pt[1], pt[2]) for pt in pts], dxfattribs={'layer': 'JALAYN_STATIONS'})

            doc.saveas(file_path)
            QMessageBox.information(self, "Export Success", f"File saved to:\n{os.path.basename(file_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def export_only_waterline_plan(self):
        selected_waterlines = [self.wl_list.item(r).data(Qt.UserRole) for r in range(self.wl_list.count()) if self.wl_list.item(r).checkState() == Qt.Checked]
        
        if not selected_waterlines:
            QMessageBox.warning(self, "Empty", "Check Minimum One Type To Proceed.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Export Half-Breadth Plan to DXF", "", "AutoCAD DXF (*.dxf)")
        if not file_path: return

        import ezdxf
        try:
            doc = ezdxf.new('R2000')
            msp = doc.modelspace()
            if 'JALAYN_GRID' not in doc.layers:
                doc.layers.new(name='JALAYN_GRID', dxfattribs={'color': 7})
            if 'JALAYN_WATERLINES' not in doc.layers:
                doc.layers.new(name='JALAYN_WATERLINES', dxfattribs={'color': 5})

            max_x = max(self.main_window.station_order) if self.main_window.station_order else 100.0
            all_pts = [pt for st in self.main_window.stations.values() for pt in st]
            max_y = max([pt[1] for pt in all_pts]) if all_pts else 15.0

            msp.add_line((-10.0, 0.0), (max_x * 1.1, 0.0), dxfattribs={'layer': 'JALAYN_GRID', 'linetype': 'DASHED'})
            msp.add_line((0.0, -max_y * 1.3), (0.0, max_y * 1.3), dxfattribs={'layer': 'JALAYN_GRID'})

            for z_coord in selected_waterlines:
                wl_pts = self.main_window.waterlines.get(z_coord, [])
                if len(wl_pts) < 2: continue
                msp.add_lwpolyline([(pt[0], pt[1]) for pt in wl_pts], dxfattribs={'layer': 'JALAYN_WATERLINES'})
                msp.add_lwpolyline([(pt[0], -pt[1]) for pt in wl_pts], dxfattribs={'layer': 'JALAYN_WATERLINES'})

            doc.saveas(file_path)
            QMessageBox.information(self, "Export Success", f"File saved to:\n{os.path.basename(file_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))