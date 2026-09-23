#Training1_menubar
from PySide6.QtWidgets import (
    QApplication, QMainWindow,  QWidget, QToolBar,
    QVBoxLayout, QMenuBar, QStatusBar, QFileDialog, QMessageBox)
from PySide6.QtCore import QObject, Signal
import json 
from PySide6.QtWidgets import QFileDialog

from PySide6.QtGui import QPen, QAction, QIcon

from training1_visualizer import HullVisualizer
from training1_main_dim import ShipDimensionDialog
from training1_offset_table import FullOffsetTableDialog
from training1_hydrostatic import HydrostaticsDialog
from training1_transformation import launch_hull_transformation
from training1_export import ExportLinesDialog
from training1_export_3d import IGES3DExporter
#from training1_ai_window import AIEngineWindow
from training1_holtrop import ResistanceHoltropDialog
from training1_help_window import JalaynHelpWindow


class MenuBar(QObject):
    addStationRequested = Signal()
    addWaterlineRequested = Signal()
    addButtocklineRequested = Signal()
    refreshWaterlinesRequested = Signal()
    refreshButtocklinesRequested = Signal()

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.undo_snapshots = []
        self.redo_snapshots = []

        self.help_window = None

        self.save_snapshot()

    def create_menu_bar(self):
        # Menu bar
        menubar = QMenuBar(self.main_window)
        self.main_window.setMenuBar(menubar)

        # File menu
        file_menu = menubar.addMenu("File")
        new_action = file_menu.addAction("New")
        load_action = file_menu.addAction("Load")
        save_action = file_menu.addAction("Save")
        save_as_action = file_menu.addAction("Save As...")
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")

        new_action.triggered.connect(self.new_project)
        load_action.triggered.connect(self.load_project_json)
        save_action.triggered.connect(self.save_project_json)
        save_as_action.triggered.connect(self.save_project_as_json)
        exit_action.triggered.connect(self.main_window.close)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        undo_action = edit_menu.addAction("Undo")
        redo_action = edit_menu.addAction("Redo")
        edit_menu.addSeparator()
        add_station_action = edit_menu.addAction("Add Station")
        edit_menu.addSeparator()
        add_waterline_action = edit_menu.addAction("Add Waterline")
        refresh_waterlines_action = edit_menu.addAction("Refresh Waterlines")
        edit_menu.addSeparator()
        add_buttockline_action = edit_menu.addAction("Add Buttockline")
        refresh_buttocklines_action = edit_menu.addAction("Refresh Buttocklines")

        undo_action.triggered.connect(self.trigger_undo)
        redo_action.triggered.connect(self.trigger_redo)
        add_station_action.triggered.connect(self.addStationRequested.emit)
        add_waterline_action.triggered.connect(self.addWaterlineRequested.emit)
        refresh_waterlines_action.triggered.connect(self.refreshWaterlinesRequested.emit)
        add_buttockline_action.triggered.connect(self.addButtocklineRequested.emit)
        refresh_buttocklines_action.triggered.connect(self.refreshButtocklinesRequested.emit)

        # Window menu
        window_menu = menubar.addMenu("Window")
        open_ship_dimension_window_action = window_menu.addAction("Ship Dimension")
        offset_table_action = window_menu.addAction("Offset Table")
        calc_hydro_action = window_menu.addAction("Hydrostatics Table")
        window_menu.addSeparator()
        hull_transform_action = window_menu.addAction("Hull Scaling")
        window_menu.addSeparator()
        open_export_wizard_action = window_menu.addAction("Export Lines")
        export_3d_iges_action = window_menu.addAction("Export 3D Hull")

        open_ship_dimension_window_action.triggered.connect(self.open_ship_dimension_dialog)
        offset_table_action.triggered.connect(self.open_full_offset_table)
        calc_hydro_action.triggered.connect(self.open_hydrostatic)
        hull_transform_action.triggered.connect(lambda: launch_hull_transformation(self.main_window))
        open_export_wizard_action.triggered.connect(self.open_export_wizard)
        export_3d_iges_action.triggered.connect(self.execute_3d_iges_export)

        # View menu
        view_menu = menubar.addMenu("View")
        preview_hull_3d_action = view_menu.addAction("Preview Hull")
        view_menu.addSeparator()
        pop_front_action = view_menu.addAction("Detach Front View")
        pop_side_action = view_menu.addAction("Detach Side View")

        preview_hull_3d_action.triggered.connect(self.preview_hull_3d)
        pop_front_action.triggered.connect(self.main_window.pop_up_front_view)
        pop_side_action.triggered.connect(self.main_window.pop_up_side_view)

        #AI Menu
        #ai_menu = menubar.addMenu("AI Tools")
        #generate_hull = ai_menu.addAction("Generate Hull Automatically")

        #generate_hull.triggered.connect(self.open_ai_window)

        #Resistance Menu
        resistance_menu = menubar.addMenu("Resistance")
        holtrop_action = resistance_menu.addAction("Holtrop Mennen Method")

        holtrop_action.triggered.connect(self.open_resistance_dialog)

        #Help Menu
        help_menu = menubar.addMenu("Help")
        open_dictionary_action = help_menu.addAction("Help")

        open_dictionary_action.triggered.connect(self.open_help_window)


    # === TOOLBAR ===
    def create_tool_bar(self):
        """Membuat bilah alat shortcut ikon murni secara resmi."""
        from PySide6.QtCore import QSize
        import os 

        toolbar = QToolBar("Main Toolbar", self.main_window)
        self.main_window.addToolBar(toolbar)
        toolbar.setIconSize(QSize(32, 33)) 

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        # ==================== ICON 1: NEW ====================
        path_new = os.path.join(BASE_DIR, "icon", "new.png")
        if not os.path.exists(path_new):
            path_new = os.path.join(BASE_DIR, "icon", "new.png")

        action_new = toolbar.addAction(QIcon(path_new), "")
        action_new.setToolTip("New") 
        action_new.triggered.connect(self.new_project)

        toolbar.addSeparator()

        # ==================== ICON 2: LOAD ====================
        path_load = os.path.join(BASE_DIR, "icon", "load.png")
        if not os.path.exists(path_load):
            path_load = os.path.join(BASE_DIR, "icon", "load.png")

        action_load = toolbar.addAction(QIcon(path_load), "")
        action_load.setToolTip("Load") 
        action_load.triggered.connect(self.load_project_json)

        toolbar.addSeparator()

        # ==================== ICON 3: SAVE ====================
        path_save = os.path.join(BASE_DIR, "icon", "save.png")
        if not os.path.exists(path_save):
            path_save = os.path.join(BASE_DIR, "icon", "save.png")

        action_save = toolbar.addAction(QIcon(path_save), "")
        action_save.setToolTip("Save") 
        action_save.triggered.connect(self.save_project_json)

        toolbar.addSeparator()

        # ==================== ICON 4: SAVE AS ====================
        path_save_as = os.path.join(BASE_DIR, "icon", "save_as.png")
        if not os.path.exists(path_save_as):
            path_save_as = os.path.join(BASE_DIR, "icon", "save_as.png")

        action_save_as = toolbar.addAction(QIcon(path_save_as), "")
        action_save_as.setToolTip("Save as") 
        action_save_as.triggered.connect(self.save_project_as_json)

        toolbar.addSeparator()
    
        # ==================== ICON 5: ADD STATION ====================
        path_station = os.path.join(BASE_DIR, "icon", "add_station.png")
        if not os.path.exists(path_station):
            path_station = os.path.join(BASE_DIR, "icon", "add_station.png.png")

        action_station = toolbar.addAction(QIcon(path_station), "")
        action_station.setToolTip("Add Station") 
        action_station.triggered.connect(self.addStationRequested.emit)

        toolbar.addSeparator()

        # ==================== ICON 6: ADD WATERLINE ====================
        path_wl = os.path.join(BASE_DIR, "icon", "add_waterline.png")
        if not os.path.exists(path_wl):
            path_wl = os.path.join(BASE_DIR, "icon", "add_waterline.png.png")

        action_wl = toolbar.addAction(QIcon(path_wl), "")
        action_wl.setToolTip("Add Waterline") 
        action_wl.triggered.connect(self.addWaterlineRequested.emit)

        toolbar.addSeparator()


        # ==================== ICON 7: ADD BUTTOCKLINE ====================
        path_bl = os.path.join(BASE_DIR, "icon", "add_buttockline.png")
        if not os.path.exists(path_bl):
            path_bl = os.path.join(BASE_DIR, "icon", "add_buttockline.png.png")

        action_bl = toolbar.addAction(QIcon(path_bl), "")
        action_bl.setToolTip("Add Buttockline") 
        action_bl.triggered.connect(self.addButtocklineRequested.emit)

        toolbar.addSeparator()

        # ==================== ICON 8: REFRESH WATERLINE ====================
        path_rw = os.path.join(BASE_DIR, "icon", "refresh_waterline.png")
        if not os.path.exists(path_rw):
            path_rw = os.path.join(BASE_DIR, "icon", "refresh_waterline.png")

        action_rw = toolbar.addAction(QIcon(path_rw), "")
        action_rw.setToolTip("Refresh Waterline") 
        action_rw.triggered.connect(self.refreshWaterlinesRequested.emit)

        toolbar.addSeparator()

        # ==================== ICON 9: REFRESH BUTTOCKLINE ====================
        path_rb = os.path.join(BASE_DIR, "icon", "refresh_buttockline.png")
        if not os.path.exists(path_rb):
            path_rb = os.path.join(BASE_DIR, "icon", "refresh_buttockline.png")

        action_rb = toolbar.addAction(QIcon(path_rb), "")
        action_rb.setToolTip("Refresh Buttockline") 
        action_rb.triggered.connect(self.refreshButtocklinesRequested.emit)

        toolbar.addSeparator()

        # ==================== ICON 10: UNDO ====================
        path_undo = os.path.join(BASE_DIR, "icon", "undo.png")
        if not os.path.exists(path_undo):
            path_undo = os.path.join(BASE_DIR, "icon", "undo.png")

        action_undo = toolbar.addAction(QIcon(path_undo), "")
        action_undo.setToolTip("Undo") 
        action_undo.triggered.connect(self.trigger_undo)

        toolbar.addSeparator()

        # ==================== ICON 11: REDO ====================
        path_redo = os.path.join(BASE_DIR, "icon", "redo.png")
        if not os.path.exists(path_redo):
            path_redo = os.path.join(BASE_DIR, "icon", "redo.png")

        action_redo = toolbar.addAction(QIcon(path_redo), "")
        action_redo.setToolTip("Redo") 
        action_redo.triggered.connect(self.trigger_redo)

        toolbar.addSeparator()

        # ==================== ICON 12: SHIP DIMENSION ====================
        path_ship_dimension = os.path.join(BASE_DIR, "icon", "ship_dimension.png")
        if not os.path.exists(path_ship_dimension):
            path_ship_dimension = os.path.join(BASE_DIR, "icon", "ship_dimension.png")

        action_ship_dimension = toolbar.addAction(QIcon(path_ship_dimension), "")
        action_ship_dimension.setToolTip("Ship Dimension") 
        action_ship_dimension.triggered.connect(self.open_ship_dimension_dialog)

        toolbar.addSeparator()

        # ==================== ICON 13: OFFSET TABLE ====================
        path_offset_table = os.path.join(BASE_DIR, "icon", "offset_table.png")
        if not os.path.exists(path_offset_table):
            path_offset_table = os.path.join(BASE_DIR, "icon", "offset_table.png")

        action_offset_table = toolbar.addAction(QIcon(path_offset_table), "")
        action_offset_table.setToolTip("Offset Table") 
        action_offset_table.triggered.connect(self.open_full_offset_table)

        toolbar.addSeparator()

        # ==================== ICON 14: HYDROSTATIC TABLE ====================
        path_hydrostatic = os.path.join(BASE_DIR, "icon", "hydrostatic.png")
        if not os.path.exists(path_hydrostatic):
            path_hydrostatic = os.path.join(BASE_DIR, "icon", "hydrostatic.png")

        action_hydrostatic = toolbar.addAction(QIcon(path_hydrostatic), "")
        action_hydrostatic.setToolTip("Hydrostatic Table") 
        action_hydrostatic.triggered.connect(self.open_hydrostatic)

        toolbar.addSeparator()

        # ==================== ICON 15: SCALE HULL ====================
        path_scale = os.path.join(BASE_DIR, "icon", "scale.png")
        if not os.path.exists(path_scale):
            path_scale = os.path.join(BASE_DIR, "icon", "scale.png")

        action_scale = toolbar.addAction(QIcon(path_scale), "")
        action_scale.setToolTip("Scale Hull") 
        action_scale.triggered.connect(lambda: launch_hull_transformation(self.main_window))

        toolbar.addSeparator()

        # ==================== ICON 16: EXPORT LINES ====================
        path_export_lines = os.path.join(BASE_DIR, "icon", "export_lines.png")
        if not os.path.exists(path_export_lines):
            path_export_lines = os.path.join(BASE_DIR, "icon", "export_lines.png")

        action_export_lines = toolbar.addAction(QIcon(path_export_lines), "")
        action_export_lines.setToolTip("Export Lines") 
        action_export_lines.triggered.connect(self.open_export_wizard)

        toolbar.addSeparator()

        # ==================== ICON 17: EXPORT 3D ====================
        path_export_3d = os.path.join(BASE_DIR, "icon", "export_3d.png")
        if not os.path.exists(path_export_3d):
            path_export_3d = os.path.join(BASE_DIR, "icon", "export_3d.png")

        action_export_3d = toolbar.addAction(QIcon(path_export_3d), "")
        action_export_3d.setToolTip("Export 3D") 
        action_export_3d.triggered.connect(self.execute_3d_iges_export)

        toolbar.addSeparator()

        # ==================== ICON 18: PREVIEW HULL ====================
        path_preview = os.path.join(BASE_DIR, "icon", "preview.png")
        if not os.path.exists(path_preview):
            path_preview = os.path.join(BASE_DIR, "icon", "preview.png")

        action_preview = toolbar.addAction(QIcon(path_preview), "")
        action_preview.setToolTip("Preview Hull") 
        action_preview.triggered.connect(self.preview_hull_3d)

        toolbar.addSeparator()


    # ================= NEW PROJECT =================
    def new_project(self):
        reply = QMessageBox.question(
            self.main_window, 'New Project',
            "Are you sure to make a new project? your unsaved data will be lost.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.main_window.stations = {}
            self.main_window.station_order = []
            self.main_window.station_names = {}
            self.main_window.current_station_x = None
            
            if hasattr(self.main_window, 'profile_points'):
                self.main_window.profile_points = []
            
            if hasattr(self.main_window, 'waterlines'):
                self.main_window.waterlines = {}
            if hasattr(self.main_window, 'buttocklines'):
                self.main_window.buttocklines = {}
            if hasattr(self.main_window, 'wl_names'):
                self.main_window.wl_names = {}
            if hasattr(self.main_window, 'bl_names'):
                self.main_window.bl_names = {}
            if hasattr(self.main_window, 'station_visibility'):
                self.main_window.station_visibility = {}

            self.main_window.sync_station_list()
            self.main_window.sync_wl_list()  
            self.main_window.sync_bl_list()  
            
            if hasattr(self.main_window, 'sync_profile_list'):
                self.main_window.sync_profile_list()
            elif hasattr(self.main_window, 'sync_profile_points'):
                self.main_window.sync_profile_points()
            
            self.main_window.update_offset_table(None)
            self.main_window.update_all_views()
            
            self.undo_snapshots.clear()
            self.redo_snapshots.clear()

            self.save_snapshot()
            
            self.main_window.update_window_title()
            self.main_window.statusBar().showMessage("New Project Started", 3000)

    # ================= SAVE (OVERWRITE) =================
    def save_project_json(self):
        """Only overwrite active file."""
        current_path = getattr(self.main_window, 'current_file_path', None)
        
        if current_path:
            self._write_json_to_disk(current_path)
            self.main_window.statusBar().showMessage(f"Project successfully updated at: {current_path}", 3000)
        else:
            QMessageBox.warning(
                self.main_window, 
                "Save Failed", 
                "This is a new project. Please use 'Save As' first to select a file location."
            )


    # ================= SAVE AS (NEW FILE) =================
    def save_project_as_json(self):
        """Alaways open a new dialog to locate the file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window, "Save Project As", "", "Jalayn Project (*.json)"
        )
        if not file_path:
            return

        self.main_window.current_file_path = file_path
        
        self._write_json_to_disk(file_path)
        self.main_window.update_window_title()
        QMessageBox.information(self.main_window, "Success", "Project saved as a new file successfully!")
        self.main_window.statusBar().showMessage(f"Active file: {file_path}", 4000)


    # --- SAVE AS JSON TO DISK ---
    def _write_json_to_disk(self, file_path):
        wl_data = getattr(self.main_window, 'waterlines', {})
        bl_data = getattr(self.main_window, 'buttocklines', {})
        st_names = getattr(self.main_window, 'station_names', {})
        wl_names = getattr(self.main_window, 'wl_names', {})
        bl_names = getattr(self.main_window, 'bl_names', {})
        prof_pts = getattr(self.main_window, 'profile_points', [])
        ship_dimensions = getattr(self.main_window, 'ship_data', {})

        project_data = {
            "ship_data": ship_dimensions,
            "current_station_x": self.main_window.current_station_x,
            "station_order": self.main_window.station_order,
            "stations": self.main_window.stations,
            "station_names": st_names,
            "wl_names": wl_names,
            "bl_names": bl_names,
            "waterlines": wl_data,
            "buttocklines": bl_data,
            "profile_points": prof_pts
        }

        try:
            with open(file_path, 'w') as f:
                json.dump(project_data, f, indent=4)
        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", f"Failed to write file: {str(e)}")


    def load_project_json(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window, "Open Project", "", "Jalayn Project (*.json)"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            self.main_window.current_file_path = file_path

            # 1. Load Stations & Names 
            self.main_window.stations = {float(k): [tuple(pt) for pt in v] for k, v in data["stations"].items()}
            self.main_window.station_order = [float(x) for x in data["station_order"]]
            self.main_window.station_names = {float(k): v for k, v in data.get("station_names", {}).items()}

            # 2. Load Profile Points 
            if "profile_points" in data:
                self.main_window.profile_points = [tuple(pt) for pt in data["profile_points"]]
            else:
                self.main_window.profile_points = []

            # 3. Load Waterlines & Buttocklines
            self.main_window.waterlines = {float(k): v for k, v in data.get("waterlines", {}).items()}
            self.main_window.buttocklines = {float(k): v for k, v in data.get("buttocklines", {}).items()}
            self.main_window.wl_names = {float(k): v for k, v in data.get("wl_names", {}).items()}
            self.main_window.bl_names = {float(k): v for k, v in data.get("bl_names", {}).items()}

            # === 3b. MAIN DIM (LPP, B, D, T) ===
            if "ship_data" in data:
                self.main_window.ship_data = data["ship_data"]
        
                if hasattr(self.main_window, 'update_dimension_input_fields'):
                    self.main_window.update_dimension_input_fields()
                elif hasattr(self.main_window, 'load_dimensions_to_ui'):
                    self.main_window.load_dimensions_to_ui()
            else:

                if not hasattr(self.main_window, 'ship_data') or not self.main_window.ship_data:
                    self.main_window.ship_data = {"LPP": 1.0, "B": 1.0, "D": 1.0, "T": 1.0}

            # 4. UI
            self.main_window.current_station_x = data.get("current_station_x")
            self.main_window.sync_station_list()
            self.main_window.sync_wl_list()
            self.main_window.sync_bl_list()
            
            self.main_window.state.refresh_waterlines()
            self.main_window.state.refresh_buttocklines()
            
            self.main_window.update_all_views()
            self.main_window.update_window_title()
            QMessageBox.information(self.main_window, "Success", "Project loaded successfully!")
            
            self.undo_snapshots.clear()
            self.redo_snapshots.clear()
            self.save_snapshot() 
            
        except Exception as e:
            QMessageBox.critical(self.main_window, "Error", f"Failed to load: {str(e)}")


    #CODE TO CALL MENU BAR 
    # ------- PREVIEW HULL -------------
    def preview_hull_3d(self):
        self.visualizer = HullVisualizer(self.main_window) # Kirim main_window utuh
        self.visualizer.run()


    # ================= ENGINE UNDO / REDO SYSTEM =================
    def save_snapshot(self):
        wl_data = getattr(self.main_window, 'waterlines', {})
        bl_data = getattr(self.main_window, 'buttocklines', {})
        st_names = getattr(self.main_window, 'station_names', {})
        prof_pts = getattr(self.main_window, 'profile_points', [])

        snapshot = {
            "current_station_x": self.main_window.current_station_x,
            "station_order": list(self.main_window.station_order),
            "stations": json.loads(json.dumps(self.main_window.stations)), 
            "station_names": json.loads(json.dumps(st_names)),
            "waterlines": json.loads(json.dumps(wl_data)),
            "buttocklines": json.loads(json.dumps(bl_data)),
            "profile_points": json.loads(json.dumps(prof_pts))
        }
        
        self.undo_snapshots.append(snapshot)
        self.redo_snapshots.clear() 

    def trigger_undo(self):
        if len(self.undo_snapshots) < 2: 
            self.main_window.statusBar().showMessage("Nothing to undo", 2000)
            return

        current_state = self.undo_snapshots.pop()
        self.redo_snapshots.append(current_state)

        past_state = self.undo_snapshots[-1]
        self._apply_snapshot_to_hull(past_state)
        self.main_window.statusBar().showMessage("Undo executed", 2000)

    def trigger_redo(self):
        if not self.redo_snapshots:
            self.main_window.statusBar().showMessage("Nothing to redo", 2000)
            return

        next_state = self.redo_snapshots.pop()
        self.undo_snapshots.append(next_state)
        
        self._apply_snapshot_to_hull(next_state)
        self.main_window.statusBar().showMessage("Redo executed", 2000)

    def _apply_snapshot_to_hull(self, state_data):
        # 1. Inject Stations & Profile 
        self.main_window.stations = {float(k): [tuple(pt) for pt in v] for k, v in state_data["stations"].items()}
        self.main_window.station_order = [float(x) for x in state_data["station_order"]]
        self.main_window.station_names = {float(k): v for k, v in state_data["station_names"].items()}
        self.main_window.profile_points = [tuple(pt) for pt in state_data["profile_points"]]

        # 2. Inject Waterlines & Buttocklines
        self.main_window.waterlines = {float(k): v for k, v in state_data["waterlines"].items()}
        self.main_window.buttocklines = {float(k): v for k, v in state_data["buttocklines"].items()}
        self.main_window.current_station_x = state_data["current_station_x"]

        # 3. UI 
        self.main_window.sync_station_list()
        self.main_window.sync_wl_list()
        self.main_window.sync_bl_list()
        self.main_window.state.refresh_waterlines()
        self.main_window.state.refresh_buttocklines()
        self.main_window.update_all_views()

    #------SHIP DIMENSION------
    def open_ship_dimension_dialog(self):
        dialog = ShipDimensionDialog(self.main_window)
        dialog.exec()

    #------OFFSET TABLE WINDOW------
    def open_full_offset_table(self):
        dialog = FullOffsetTableDialog(self.main_window)
        dialog.exec()

    #------HYDROSTATIC WINDOW------
    def open_hydrostatic(self):
        hydro = HydrostaticsDialog(self.main_window) 
        hydro.open_hydrostatics_dialog()

    #------EXPORT WINDOW------
    def open_export_wizard(self):
        dialog = ExportLinesDialog(self.main_window)
        dialog.exec()
    
    def execute_3d_iges_export(self):
        exporter = IGES3DExporter(self.main_window)
        exporter.export_hull_to_iges()

    #AI Window
    #def open_ai_window(self):
        #dialog = AIEngineWindow(self.main_window)
        #dialog.exec()

    #Help Window
    def open_help_window(self):
        if not hasattr(self, 'help_window') or self.help_window is None:
            self.help_window = JalaynHelpWindow(self.main_window)
        
        self.help_window.show()
        self.help_window.raise_()
        self.help_window.activateWindow()

    #Resistance Window
    def open_resistance_dialog(self):
        dialog = ResistanceHoltropDialog(self.main_window)
        dialog.exec()