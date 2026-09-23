#training1.py
import sys
import numpy as np
from scipy.interpolate import CubicSpline
from PySide6.QtWidgets import (
    QApplication, QGraphicsScene, QListWidget, QTableWidget, QTableWidgetItem, QDialog, QGraphicsItem,
    QHeaderView, QVBoxLayout, QListWidgetItem, QMainWindow, QWidget, QMenu, QFrame, QCheckBox,
    QGridLayout, QLabel, QMessageBox, QInputDialog, QHBoxLayout, QSlider
)
from PySide6.QtWidgets import QGroupBox, QDoubleSpinBox, QComboBox, QFormLayout, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QAction, QIcon
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QMessageBox


from training1_state import Qt_State
from training1_menubar import MenuBar
from training1_canvas import CanvasView
from training1_utils import project_point

# ================= Main Window ==================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jalayn Ver 0.3")
        self.resize(1200, 800)

        self.current_file_path = None

        central = QWidget()
        layout = QGridLayout(central)
        layout.setSpacing(4)

        # Save 3D points
        self.points_3d = []
        self.state = Qt_State(self)

        # Stations
        self.stations = {}
        self.station_order = []
        self.current_station_x = None
        
        # Waterlines
        self.waterlines = {}      
        self.current_wl_z = None

        # Buttocklines
        self.buttocklines = {}   
        self.current_bl_y = None

        # Profile
        self.profile_points = []

        # ========== Create menu bar ==========
        self.menu_bar = MenuBar(self)
        self.menu_bar.create_menu_bar()

        self.menu_bar.create_tool_bar()

        self.menu_bar.addStationRequested.connect(self.add_station)
        self.menu_bar.addWaterlineRequested.connect(self.state.add_waterline)
        self.menu_bar.addButtocklineRequested.connect(self.state.add_buttockline)
        self.menu_bar.refreshWaterlinesRequested.connect(
            lambda: (self.state.refresh_waterlines(), self.update_all_views())
        )
        self.menu_bar.refreshButtocklinesRequested.connect(
            lambda: (self.state.refresh_buttocklines(), self.update_all_views())
        )
        
        # ---------------- STATION, WL, BL LIST DOCK ON THE RIGHT SIDE -----------------
        self.right_dock_panel = QWidget()
        right_layout = QVBoxLayout(self.right_dock_panel)

        lists_container = QWidget()
        lists_layout = QHBoxLayout(lists_container)
        lists_layout.setSpacing(5)

        # 1. Station Column
        station_vbox = QVBoxLayout()
        station_vbox.addWidget(QLabel("Stations (X)"))
        self.station_list_widget = QListWidget()
        self.station_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.station_list_widget.customContextMenuRequested.connect(self.show_station_context_menu)
        # -------------------------------
        station_vbox.addWidget(self.station_list_widget)
        lists_layout.addLayout(station_vbox)
        self.station_list_widget.itemClicked.connect(self.on_station_selected)
        self.station_names = {} #Station Name
        self.station_list_widget.itemChanged.connect(self.on_station_item_changed)

        # 2. Waterline Column
        wl_vbox = QVBoxLayout()
        wl_vbox.addWidget(QLabel("Waterlines (Z)"))
        self.wl_list_widget = QListWidget()
        self.wl_names = {}
        self.wl_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.wl_list_widget.customContextMenuRequested.connect(self.show_wl_context_menu)
        # -------------------------------
        self.menu_bar.addWaterlineRequested.connect(self.handle_add_wl)
        wl_vbox.addWidget(self.wl_list_widget)
        lists_layout.addLayout(wl_vbox)
        self.wl_list_widget.itemClicked.connect(self.on_wl_selected)

        # 3. Buttockline Column
        bl_vbox = QVBoxLayout()
        bl_vbox.addWidget(QLabel("Buttocklines (Y)"))
        self.bl_list_widget = QListWidget()
        self.bl_names = {}
        self.bl_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.bl_list_widget.customContextMenuRequested.connect(self.show_bl_context_menu)
        # -------------------------------
        self.menu_bar.addButtocklineRequested.connect(self.handle_add_bl)
        bl_vbox.addWidget(self.bl_list_widget)
        lists_layout.addLayout(bl_vbox)
        self.bl_list_widget.itemClicked.connect(self.on_bl_selected)

        right_layout.addWidget(lists_container)

        # --- Active or Selected Station Table Offset ---
        self.offset_table = QTableWidget(0, 3) 
        self.offset_table.setHorizontalHeaderLabels(["X", "Y", "Z"])
        self.offset_table.cellClicked.connect(self.on_table_cell_clicked)
        self.offset_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.offset_table.itemChanged.connect(self.on_table_edit) 

        right_layout.addWidget(QLabel("Offset Table (Active Station)"))
        right_layout.addWidget(self.offset_table)

        #layout.addWidget(right_panel, 0, 2, 2, 1)
        layout.setColumnStretch(0, 3)
        layout.setColumnStretch(1, 3)
        layout.setColumnStretch(2, 2)
        
        #Point Properties (X, Y, Z)
        self.prop_group = QGroupBox("Point Properties")
        prop_form = QFormLayout()
        
        self.sp_x = QDoubleSpinBox(); self.sp_x.setRange(-500, 500); self.sp_x.setSingleStep(0.1)
        self.sp_y = QDoubleSpinBox(); self.sp_y.setRange(-500, 500); self.sp_y.setSingleStep(0.1)
        self.sp_z = QDoubleSpinBox(); self.sp_z.setRange(-500, 500); self.sp_z.setSingleStep(0.1)
        self.sp_w = QDoubleSpinBox(); self.sp_w.setRange(0.1, 50.0); self.sp_w.setValue(1.0)

        #IN & OUT TANGENT
        self.sp_angle_in = QDoubleSpinBox()
        self.sp_angle_in.setRange(-361, 360)
        self.sp_angle_in.setSuffix(" °")
        self.sp_angle_in.setSpecialValueText("Auto (Free)")
        self.sp_angle_in.setValue(-361)

        self.sp_angle_out = QDoubleSpinBox()
        self.sp_angle_out.setRange(-361, 360)
        self.sp_angle_out.setSuffix(" °")
        self.sp_angle_out.setSpecialValueText("Auto (Free)")
        self.sp_angle_out.setValue(-361)

        #Tangent Type (Under development)
        self.cb_tangent_type = QComboBox()
        self.cb_tangent_type.addItems(["Auto-Smooth", "Symmetric", "Sharp (Knuckle)"])
        self.cb_tangent_type.currentTextChanged.connect(self.on_tangent_type_changed)

        #Coordinate Change
        self.sp_x.valueChanged.connect(self.sync_properties_to_point)
        self.sp_y.valueChanged.connect(self.sync_properties_to_point)
        self.sp_z.valueChanged.connect(self.sync_properties_to_point)

        #Tangent Type (Under development)
        self.cb_tangent = QComboBox()
        self.cb_tangent.addItems(["Free", "Horizontal", "Vertical"])

        #Row For Coordinate
        prop_form.addRow("Pos X:", self.sp_x)
        prop_form.addRow("Pos Y:", self.sp_y)
        prop_form.addRow("Pos Z:", self.sp_z)

        self.sp_x.valueChanged.connect(self.on_property_changed)
        self.sp_y.valueChanged.connect(self.on_property_changed)
        self.sp_z.valueChanged.connect(self.on_property_changed)

        #Weight (Under Development)
        prop_form.addRow("Weight:", self.sp_w)
        self.sp_w.valueChanged.connect(self.on_property_changed)

        #Ange Control Row
        self.prop_group.setLayout(prop_form)
        right_layout.addWidget(self.prop_group)

        prop_form.addRow("Angle IN:", self.sp_angle_in)
        prop_form.addRow("Angle OUT:", self.sp_angle_out)
        
        self.sp_angle_in.valueChanged.connect(self.on_property_changed)
        self.sp_angle_out.valueChanged.connect(self.on_property_changed)
        
        # Visibility controls
        self.station_visibility = {} 
        self.wl_visibility = {}   
        self.bl_visibility = {}   

        self.wl_list_widget.itemChanged.connect(self.on_wl_item_changed)
        self.bl_list_widget.itemChanged.connect(self.on_bl_item_changed)

        # --- Isometric View Control ---
        right_layout.addWidget(QLabel("--- Isometric View Control ---"))
        self.azimuth_slider = QSlider(Qt.Horizontal)
        self.azimuth_slider.setRange(0, 360)
        self.azimuth_slider.setValue(45)
        self.azimuth_slider.valueChanged.connect(self.update_all_views)
        right_layout.addWidget(QLabel("Azimuth (Rotate L-R)"))
        right_layout.addWidget(self.azimuth_slider)

        self.elevation_slider = QSlider(Qt.Horizontal)
        self.elevation_slider.setRange(-90, 90)
        self.elevation_slider.setValue(30)
        self.elevation_slider.valueChanged.connect(self.update_all_views)
        right_layout.addWidget(QLabel("Elevation (Rotate Up-Down)"))
        right_layout.addWidget(self.elevation_slider)

        layout.addWidget(self.right_dock_panel, 0, 2, 2, 1)

        # ========== Create 4 views ==========
        self.front_view = CanvasView(self, enable_interaction=True, title="Front")
        self.top_view = CanvasView(self, enable_interaction=True, title="Top")
        self.side_view = CanvasView(self, enable_interaction=True, title="Side")
        self.iso_view = CanvasView(self, enable_interaction=True, title="Isometric")

        self.front_scene = QGraphicsScene()
        self.top_scene = QGraphicsScene()
        self.side_scene = QGraphicsScene()
        self.iso_scene = QGraphicsScene()

        self.front_view.setScene(self.front_scene)
        self.top_view.setScene(self.top_scene)
        self.side_view.setScene(self.side_scene)
        self.iso_view.setScene(self.iso_scene)

        layout.addWidget(self._wrap_with_label(self.front_view, "FRONT VIEW"), 0, 0)
        layout.addWidget(self._wrap_with_label(self.top_view, "TOP VIEW"), 0, 1)
        layout.addWidget(self._wrap_with_label(self.side_view, "SIDE VIEW"), 1, 0)
        layout.addWidget(self._wrap_with_label(self.iso_view, "ISOMETRIC"), 1, 1)

        self.setCentralWidget(central)

        self.update_window_title()

    def update_window_title(self):
        base_title = "Jalayn Ver 0.3"      
        if self.current_file_path:
            import os
            file_name = os.path.basename(self.current_file_path)
            self.setWindowTitle(f"{base_title} - {file_name}")
        else:
            self.setWindowTitle(f"{base_title} - [Untitled]")

    def _wrap_with_label(self, view, title):
        wrapper = QWidget()
        v = QGridLayout(wrapper)
        label = QLabel(title)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-weight: bold; background:#222; color:white; padding:4px;")
        v.addWidget(label, 0, 0)
        v.addWidget(view, 1, 0)
        v.setRowStretch(1, 1)
        return wrapper
    
    # ================= DETACHED VIEW (POP UP) =================
    def _create_popup_layout(self, dialog, canvas_view, scene):
        popup_layout = QHBoxLayout(dialog)
        popup_layout.setSpacing(8)
        popup_layout.setContentsMargins(6, 6, 6, 6)

        # 1. LEFT
        canvas_view.setScene(scene)
        popup_layout.addWidget(canvas_view, stretch=3)

        # 2. RIGHT
        popup_layout.addWidget(self.right_dock_panel, stretch=1)

        def restore_panel_to_main():
            main_layout = self.centralWidget().layout()
            if main_layout:
                main_layout.addWidget(self.right_dock_panel, 0, 2, 2, 1)
            self.update_all_views()

        dialog.finished.connect(lambda result: restore_panel_to_main())

    #-------------- POP UP FOR FRONT VIEW ---------------
    def pop_up_front_view(self):
        self.popup = QDialog(self)
        self.popup.setWindowTitle("Front View Editor (Body Plan) - Jalayn Detached")
        self.popup.resize(1250, 850)
    
        self.pop_canvas = CanvasView(self, enable_interaction=True, title="Front")
        
        self._create_popup_layout(self.popup, self.pop_canvas, self.front_scene)
        
        self.popup.show()
        self.pop_canvas.centerOn(0, 0)
        self.update_all_views()

    #-------------- POP UP FOR SIDE VIEW ---------------
    def pop_up_side_view(self):
        self.popup_side = QDialog(self)
        self.popup_side.setWindowTitle("Side View Editor (Profile / Sheer Plan) - Jalayn Detached")
        self.popup_side.resize(1350, 750)
    
        self.pop_canvas_side = CanvasView(self, enable_interaction=True, title="Side")
        
        self._create_popup_layout(self.popup_side, self.pop_canvas_side, self.side_scene)
        
        self.popup_side.show()
        self.pop_canvas_side.centerOn(0, 0)
        self.update_all_views()

    #------------------------------------------------------------------------------------------------------

    #POINTS & COORDINATES
    def load_point_to_props(self, pt_dict):
        if not isinstance(pt_dict, dict): return
        self.sp_x.blockSignals(True); self.sp_y.blockSignals(True); self.sp_z.blockSignals(True)
        self.sp_w.blockSignals(True); self.cb_tangent.blockSignals(True)
        x, y, z = pt_dict['pos']
        self.sp_x.setValue(x); self.sp_y.setValue(y); self.sp_z.setValue(z)
        self.sp_w.setValue(pt_dict.get('weight', 1.0)); self.cb_tangent.setCurrentText(pt_dict.get('tangent', 'Free'))
        self.sp_x.blockSignals(False); self.sp_y.blockSignals(False); self.sp_z.blockSignals(False)
        self.sp_w.blockSignals(False); self.cb_tangent.blockSignals(False)

    def update_point_from_props(self):
        curr_x = self.current_station_x
        idx = self.state.selected_index
        if curr_x is None or idx is None: return
        self.stations[curr_x][idx] = {'pos': (self.sp_x.value(), self.sp_y.value(), self.sp_z.value()), 'weight': self.sp_w.value(), 'tangent': self.cb_tangent.currentText()}
        self.update_all_views(); self.update_offset_table(curr_x)

    #ADD STATION
    def add_station(self):
        try:
            x, ok = QInputDialog.getDouble(
                self, "Add Station", "Input coordinate for (X) station:", decimals=3
            )
            if not ok: return

            if x in self.stations:
                QMessageBox.warning(self, "Warning", f"Station X={x} already exists!")
                return

            self.stations[x] = []
            self.station_order.append(x)
            self.station_order.sort()

            self.current_station_x = x
            self.sync_station_list() 
            self.update_all_views()

            QMessageBox.information(self, "Station Added", f"New station created at X={x}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def handle_add_wl(self):
        self.state.add_waterline() 
        self.sync_wl_list()        
        self.update_all_views()    

    def handle_add_bl(self):
        self.state.add_buttockline()
        self.sync_bl_list()        
        self.update_all_views()

    #VIEW FOR STATION, WL, BL
    def update_all_views(self):
        self.front_scene.clear()
        self.top_scene.clear()
        self.side_scene.clear()
        self.iso_scene.clear()

        axis_pen = QPen(Qt.gray, 1)
        axis_pen.setCosmetic(True)
        ext = 500 
        az, el = self.azimuth_slider.value(), self.elevation_slider.value()

        # AXIS
        # Front View CL & BL
        f_cl_start = project_point(0, 0, -ext, "front")
        f_cl_end = project_point(0, 0, ext, "front")
        f_bl_start = project_point(0, -ext, 0, "front")
        f_bl_end = project_point(0, ext, 0, "front")
        self.front_scene.addLine(f_cl_start[0], f_cl_start[1], f_cl_end[0], f_cl_end[1], axis_pen)
        self.front_scene.addLine(f_bl_start[0], f_bl_start[1], f_bl_end[0], f_bl_end[1], axis_pen)

        # Side View BL & Station 0
        s_bl_start = project_point(-ext, 0, 0, "side")
        s_bl_end = project_point(ext, 0, 0, "side")
        s_st0_start = project_point(0, 0, -ext, "side")
        s_st0_end = project_point(0, 0, ext, "side")
        self.side_scene.addLine(s_bl_start[0], s_bl_start[1], s_bl_end[0], s_bl_end[1], axis_pen)
        self.side_scene.addLine(s_st0_start[0], s_st0_start[1], s_st0_end[0], s_st0_end[1], axis_pen)

        # Top View CL & Station 0
        t_cl_start = project_point(-ext, 0, 0, "top")
        t_cl_end = project_point(ext, 0, 0, "top")
        t_st0_start = project_point(0, -ext, 0, "top")
        t_st0_end = project_point(0, ext, 0, "top")
        self.top_scene.addLine(t_cl_start[0], t_cl_start[1], t_cl_end[0], t_cl_end[1], axis_pen)
        self.top_scene.addLine(t_st0_start[0], t_st0_start[1], t_st0_end[0], t_st0_end[1], axis_pen)

        # STATIONS 
        for x_station in self.station_order:
            if not self.station_visibility.get(x_station, True):
                continue

            pts = self.stations[x_station]
            is_active = (x_station == self.current_station_x)
            color = Qt.red if is_active else Qt.white
            pen_line = QPen(color, 1.5 if is_active else 1)
            pen_line.setCosmetic(True)

            if len(pts) >= 2:
                self.front_scene.addPath(self.state.get_spline_path(pts, "front"), pen_line)
                self.top_scene.addPath(self.state.get_spline_path(pts, "top"), pen_line)
                self.side_scene.addPath(self.state.get_spline_path(pts, "side"), pen_line)
                self.iso_scene.addPath(self.state.get_spline_path(pts, "iso", az, el), pen_line)

            # CONTROL POINTS
            for i, pt in enumerate(pts):
                x, y, z = pt[0], pt[1], pt[2]
                
                is_pt_selected = (is_active and i == self.state.active_point_index)
                
                if is_pt_selected:
                    pt_color = Qt.yellow
                    pt_size = 5
                    pt_pen = QPen(Qt.black, 1)
                else:
                    pt_color = color
                    pt_size = 3
                    pt_pen = pen_line

                pt_pen.setCosmetic(True)
                
                # Render Front Scene
                fx, fz = project_point(x, y, z, "front")
                self.front_scene.addEllipse(fx - pt_size/2, fz - pt_size/2, pt_size, pt_size, pt_pen, pt_color)
                
                # Render Side Scene
                sx, sz = project_point(x, y, z, "side")
                self.side_scene.addEllipse(sx - pt_size/2, sz - pt_size/2, pt_size, pt_size, pt_pen, pt_color)
                
                # Render Top Scene
                tx, ty = project_point(x, y, z, "top")
                self.top_scene.addEllipse(tx - pt_size/2, ty - pt_size/2, pt_size, pt_size, pt_pen, pt_color)

        # WATERLINES 
        if hasattr(self, 'waterlines'):
            for z_level, wl_pts in self.waterlines.items():
                if not self.wl_visibility.get(z_level, True): continue
                is_active_wl = (z_level == self.current_wl_z)
                wl_pen = QPen(Qt.red if is_active_wl else Qt.blue, 1.5)
                wl_pen.setCosmetic(True)
                if len(wl_pts) >= 2:
                    self.top_scene.addPath(self.state.get_spline_path(wl_pts, "top"), wl_pen)
                    self.iso_scene.addPath(self.state.get_spline_path(wl_pts, "iso", az, el), wl_pen)

        # BUTTOCKLINES 
        if hasattr(self, 'buttocklines'):
            for y_val, bl_pts in self.buttocklines.items():
                if not self.bl_visibility.get(y_val, True): continue
                is_active_bl = (y_val == self.current_bl_y)
                bl_pen = QPen(Qt.red if is_active_bl else Qt.darkGreen, 1.5)
                bl_pen.setCosmetic(True)
                if len(bl_pts) >= 2:
                    self.side_scene.addPath(self.state.get_spline_path(bl_pts, "side"), bl_pen)
                    self.iso_scene.addPath(self.state.get_spline_path(bl_pts, "iso", az, el), bl_pen)

        # PROFILE 
        if hasattr(self, 'profile_points') and len(self.profile_points) >= 2:
            profile_pen = QPen(Qt.cyan, 2, Qt.SolidLine)
            profile_pen.setCosmetic(True)
            
            pts_pro = self.profile_points
            
            self.side_scene.addPath(self.state.get_spline_path(pts_pro, "side"), profile_pen)
            self.iso_scene.addPath(self.state.get_spline_path(pts_pro, "iso", az, el), profile_pen)

            for i, pt in enumerate(pts_pro):
                px, py, pz = pt[0], pt[1], pt[2]
                
                is_pt_selected = (hasattr(self.state, 'active_profile_index') and i == self.state.active_profile_index)
                
                if is_pt_selected:
                    pt_color = Qt.yellow
                    pt_size = 6
                    pt_pen = QPen(Qt.black, 1)
                else:
                    pt_color = Qt.cyan
                    pt_size = 4
                    pt_pen = QPen(Qt.black, 0.5)
                
                pt_pen.setCosmetic(True)

                # Render Side View
                sx, sz = project_point(px, py, pz, "side")
                self.side_scene.addEllipse(sx - pt_size/2, sz - pt_size/2, pt_size, pt_size, pt_pen, pt_color)

    #--------- SELECTED ITEM -----------------
    def on_station_selected(self, item):
        try:
            x_val = item.data(Qt.UserRole)
            if x_val is not None:
                self.current_station_x = x_val
                self.state.select_station(x_val) 
                self.update_offset_table(x_val)
                self.update_all_views()
        except Exception as e:
            print(f"Error selecting station: {e}")

    def on_wl_selected(self, item):
        self.current_wl_z = item.data(Qt.UserRole)
        self.update_all_views()

    def on_bl_selected(self, item):
        data = item.data(Qt.UserRole)
        self.current_bl_y = data
        
        if data == "PROFILE_MARKER":
            self.current_station_x = None 
            self.offset_table.blockSignals(True)
            self.offset_table.setRowCount(0)
            
            if hasattr(self, 'profile_points'):
                for i, pt in enumerate(self.profile_points):
                    x, y, z = pt[0], pt[1], pt[2]
                    self.offset_table.insertRow(i)
                    self.offset_table.setItem(i, 0, QTableWidgetItem(f"{x:.3f}"))
                    self.offset_table.setItem(i, 1, QTableWidgetItem(f"{y:.3f}"))
                    self.offset_table.setItem(i, 2, QTableWidgetItem(f"{z:.3f}"))
            self.offset_table.blockSignals(False)
        else:
            self.update_all_views()

    #------------- OFFSET TABLE UPDATE & PANEL ----------------
    def update_offset_table(self, x_val):
        self.offset_table.blockSignals(True) 
        self.offset_table.setRowCount(0)
        
        if x_val in self.stations:
            pts = self.stations[x_val] 
            for i, pt in enumerate(pts):
                x, y, z = pt[0], pt[1], pt[2]
                
                self.offset_table.insertRow(i)
                self.offset_table.setItem(i, 0, QTableWidgetItem(f"{x:.3f}"))
                self.offset_table.setItem(i, 1, QTableWidgetItem(f"{y:.3f}"))
                self.offset_table.setItem(i, 2, QTableWidgetItem(f"{z:.3f}"))
                
        self.offset_table.blockSignals(False)

    def update_properties_panel(self, index):
        curr_x = self.current_station_x
        if index is None: return

        if curr_x is not None:
            pts = self.stations.get(curr_x, [])
        elif hasattr(self, 'profile_points'):
            pts = self.profile_points
        else:
            return

        if index < len(pts):
            point = pts[index]
        
            self.sp_x.blockSignals(True); self.sp_y.blockSignals(True); self.sp_z.blockSignals(True)
            self.sp_w.blockSignals(True); self.sp_angle_in.blockSignals(True); self.sp_angle_out.blockSignals(True)
            self.cb_tangent_type.blockSignals(True)
        
            self.sp_x.setValue(point[0])
            self.sp_y.setValue(point[1])
            self.sp_z.setValue(point[2])
            self.sp_w.setValue(point[3] if len(point) > 3 else 1.0)

            a_in = point[4] if len(point) > 4 else None
            a_out = point[5] if len(point) > 5 else None

            self.sp_angle_in.setValue(-361 if a_in is None else a_in)
            self.sp_angle_out.setValue(-361 if a_out is None else a_out)

            if a_in is None and a_out is None:
                self.cb_tangent_type.setCurrentText("Auto-Smooth")
            elif a_in == a_out and a_in is not None:
                self.cb_tangent_type.setCurrentText("Symmetric")
            else:
                self.cb_tangent_type.setCurrentText("Sharp (Knuckle)")
        
            self.sp_x.blockSignals(False); self.sp_y.blockSignals(False); self.sp_z.blockSignals(False)
            self.sp_w.blockSignals(False); self.sp_angle_in.blockSignals(False); self.sp_angle_out.blockSignals(False)
            self.cb_tangent_type.blockSignals(False)
    
    #TANGENT TYPE CHANGE (UNDER DEVELOPMENT)
    def on_tangent_type_changed(self, text):
        self.sp_angle_in.blockSignals(True); self.sp_angle_out.blockSignals(True)
        if text == "Auto-Smooth":
            self.sp_angle_in.setValue(-361)
            self.sp_angle_out.setValue(-361)
        elif text == "Symmetric":
            if self.sp_angle_in.value() == -361:
                self.sp_angle_in.setValue(0.0)
            self.sp_angle_out.setValue(self.sp_angle_in.value())
        self.sp_angle_in.blockSignals(False); self.sp_angle_out.blockSignals(False)
        self.on_property_changed()

    def on_property_changed(self):
        curr_x = self.current_station_x
        idx = self.state.active_point_index if curr_x is not None else getattr(self.state, 'active_profile_index', None)

        if idx is not None:
            x, y, z, w = self.sp_x.value(), self.sp_y.value(), self.sp_z.value(), self.sp_w.value()
            
            ai_ui, ao_ui = self.sp_angle_in.value(), self.sp_angle_out.value()
            actual_ain = ai_ui if ai_ui > -361 else None
            actual_aout = ao_ui if ao_ui > -361 else None

            if self.cb_tangent_type.currentText() == "Symmetric" and actual_ain is not None:
                actual_aout = actual_ain
                self.sp_angle_out.blockSignals(True)
                self.sp_angle_out.setValue(ai_ui)
                self.sp_angle_out.blockSignals(False)

            if curr_x is not None:
                self.stations[curr_x][idx] = (x, y, z, w, actual_ain, actual_aout)
                self.update_offset_table(curr_x)
            elif hasattr(self, 'profile_points'):
                self.profile_points[idx] = (x, 0.0, z, w, actual_ain, actual_aout)
                
            self.update_all_views()
            self.state.refresh_waterlines()
            self.state.refresh_buttocklines()

    #---------------- OFFSET TABLE VALUE EDIT ------------------
    def on_table_edit(self, item):
        row, col = item.row(), item.column()
        curr_x = self.current_station_x
        
        try:
            new_val = float(item.text())
            is_profile = self.bl_list_widget.currentItem() and self.bl_list_widget.currentItem().data(Qt.UserRole) == "PROFILE_MARKER"

            if is_profile and hasattr(self, 'profile_points'):
                pts = self.profile_points
            elif curr_x is not None:
                pts = self.stations[curr_x]
            else:
                return

            old_pt = list(pts[row])
            
            while len(old_pt) <= col:
                old_pt.append(0.0)
                
            old_pt[col] = new_val
            pts[row] = tuple(old_pt)
            
            self.update_all_views()
            if is_profile and col == 0:
                self.profile_points.sort(key=lambda p: p[0])
                
        except (ValueError, IndexError):
            pass

    #-------------- SYNCHRONIZATION FOR LIST -------------------
    def sync_station_list(self):
        self.station_list_widget.blockSignals(True)
        self.station_list_widget.clear()
        for sx in sorted(self.stations.keys()):
            name = self.station_names.get(sx, f"Station {sx}")
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEditable)
            item.setCheckState(Qt.Checked if self.station_visibility.get(sx, True) else Qt.Unchecked)
            item.setData(Qt.UserRole, sx) 
            self.station_list_widget.addItem(item)
        self.station_list_widget.blockSignals(False)

    def sync_wl_list(self):
        self.wl_list_widget.blockSignals(True)
        self.wl_list_widget.clear()
        for z in sorted(self.waterlines.keys()):
            name = self.wl_names.get(z, f"WL Z: {z:.3f} m")
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, z) 
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable | Qt.ItemIsEditable)
            item.setCheckState(Qt.Checked if self.wl_visibility.get(z, True) else Qt.Unchecked)
            self.wl_list_widget.addItem(item)
        self.wl_list_widget.blockSignals(False)

    def sync_bl_list(self):
        self.bl_list_widget.blockSignals(True)
        self.bl_list_widget.clear()
        profile_item = QListWidgetItem("Profile (BL 0)")
        profile_item.setData(Qt.UserRole, "PROFILE_MARKER") 
        profile_item.setFlags(profile_item.flags() | Qt.ItemIsSelectable) 
        self.bl_list_widget.addItem(profile_item)
        
        for y in sorted(self.buttocklines.keys()):
            name = self.bl_names.get(y, f"BL Y: {y:.3f}")
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, y)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable | Qt.ItemIsEditable)  
            item.setCheckState(Qt.Checked if self.bl_visibility.get(y, True) else Qt.Unchecked)
            self.bl_list_widget.addItem(item)
        self.bl_list_widget.blockSignals(False)

    def sync_properties_to_point(self):
        curr_x = self.current_station_x
        idx = self.state.active_point_index
        
        if curr_x is not None and idx is not None:
            new_x = self.sp_x.value()
            new_y = self.sp_y.value()
            new_z = self.sp_z.value()
            
            self.stations[curr_x][idx] = (new_x, new_y, new_z)
            
            self.update_offset_table(curr_x)
            
            self.update_all_views()
            
            self.state.refresh_waterlines()
            self.state.refresh_buttocklines()

    def on_station_item_changed(self, item):
        if self.station_list_widget.signalsBlocked(): return
        sx = item.data(Qt.UserRole)
        if sx is None: return
        self.station_visibility[sx] = (item.checkState() == Qt.Checked)
        self.station_names[sx] = item.text()
        self.update_all_views()

    def on_table_cell_clicked(self, row, column):
        self.state.active_point_index = row
        self.update_properties_panel(row)
        self.update_all_views() 

    def on_wl_item_changed(self, item):
        if self.wl_list_widget.signalsBlocked(): return 
        z_val = item.data(Qt.UserRole)
        if z_val is not None:
            self.wl_visibility[z_val] = (item.checkState() == Qt.Checked)
            self.wl_names[z_val] = item.text()
            self.update_all_views()

    def on_bl_item_changed(self, item):
        if self.bl_list_widget.signalsBlocked(): return
        y_val = item.data(Qt.UserRole)
        if y_val is not None and y_val != "PROFILE_MARKER":
            self.bl_visibility[y_val] = (item.checkState() == Qt.Checked)
            self.bl_names[y_val] = item.text()
            self.update_all_views()


    # ================= CONTEXT MENU & DELETE =================
    def show_station_context_menu(self, pos):
        item = self.station_list_widget.itemAt(pos)
        if not item: return
        
        menu = QMenu(self)
        delete_action = QAction(f"Delete {item.text()}", self)
        delete_action.triggered.connect(lambda: self.delete_station(item))
        menu.addAction(delete_action)
        menu.exec(self.station_list_widget.mapToGlobal(pos))

    def delete_station(self, item):
        sx = item.data(Qt.UserRole)
        if sx is None: return
        
        reply = QMessageBox.question(
            self, "Confirm Delete", f"Are you sure you want to delete Station X={sx}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if sx in self.stations: del self.stations[sx]
            if sx in self.station_order: self.station_order.remove(sx)
            if sx in self.station_visibility: del self.station_visibility[sx]
            if sx in self.station_names: del self.station_names[sx]
            
            if self.current_station_x == sx:
                self.current_station_x = None
                self.offset_table.setRowCount(0)
            
            self.sync_station_list()
            self.update_all_views()

    def show_wl_context_menu(self, pos):
        item = self.wl_list_widget.itemAt(pos)
        if not item: return
        
        menu = QMenu(self)
        delete_action = QAction(f"Delete {item.text()}", self)
        delete_action.triggered.connect(lambda: self.delete_waterline(item))
        menu.addAction(delete_action)
        menu.exec(self.wl_list_widget.mapToGlobal(pos))

    def delete_waterline(self, item):
        z_val = item.data(Qt.UserRole)
        if z_val is None: return
        
        reply = QMessageBox.question(
            self, "Confirm Delete", f"Are you sure you want to delete Waterline Z={z_val:.3f}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if z_val in self.waterlines: del self.waterlines[z_val]
            if z_val in self.wl_visibility: del self.wl_visibility[z_val]
            
            if self.current_wl_z == z_val:
                self.current_wl_z = None
                
            self.sync_wl_list()
            self.update_all_views()

    def show_bl_context_menu(self, pos):
        item = self.bl_list_widget.itemAt(pos)
        if not item: return
        #Profile can not be deleted
        if item.data(Qt.UserRole) == "PROFILE_MARKER":
            return
            
        menu = QMenu(self)
        delete_action = QAction(f"Delete {item.text()}", self)
        delete_action.triggered.connect(lambda: self.delete_buttockline(item))
        menu.addAction(delete_action)
        menu.exec(self.bl_list_widget.mapToGlobal(pos))

    def delete_buttockline(self, item):
        y_val = item.data(Qt.UserRole)
        if y_val is None or y_val == "PROFILE_MARKER": return
        
        reply = QMessageBox.question(
            self, "Confirm Delete", f"Are you sure you want to delete Buttockline Y={y_val:.3f}?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if y_val in self.buttocklines: del self.buttocklines[y_val]
            if y_val in self.bl_visibility: del self.bl_visibility[y_val]
            
            if self.current_bl_y == y_val:
                self.current_bl_y = None
                
            self.sync_bl_list()
            self.update_all_views()

    
if __name__ == "__main__":
    import os
    import ctypes
    
    myappid = 'jalayn.app.ver-0.3' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app = QApplication(sys.argv)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    icon_filename = "jalayn_logo.png" 
    icon_path = os.path.join(base_dir, icon_filename)

    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        print(f"[Jalayn] Icon exist : {icon_path}")
    else:
        print(f"[Jalayn] ERROR: File {icon_filename} not found!")

    w = MainWindow()
    w.show()
    sys.exit(app.exec())