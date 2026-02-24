#bodyplan_app.py
import tkinter as tk
from collections import defaultdict
from PIL import Image, ImageTk
from ui.draw_canvas import CanvasDrawer

class BodyPlan3DApp:

    def __init__(self, master):        
        # --- data initialization ---
        self.width = 1400
        self.height = 700
        self.divider_x = self.width // 2
        self.divider_y = self.height // 2
        self.dragging = None

        self.stations = {}
        self.station_order = []
        self.station_spline = {}

        self.point_angles = {}  # On Progress
        self.point_strength = {}  # On Progress

        self.front_scale = 50
        self.side_scale = 50
        self.top_scale = 50
        self.iso_scale = 50
        self.scale = 50
        self.offsets = {}
        self.middle_drag_start = None
        self.view_pan_front = [0, 0]
        self.view_pan_side = [0, 0]
        self.view_pan_top = [0, 0]
        self.view_pan_iso = [0, 0]

        self.dragging_divider = None
        self.drag_data = {'station_x': None, 'point_index': None, 'start_x': 0, 'start_y': 0}
        self.selected_station = None

        self.right_click_pos = (0, 0)
        self.right_click_station = None
        self.right_click_point_index = None
        self.right_click_line_index = None

        self.use_spline = True
        self.station_names = {-1.0: "WL1", -2.5: "WL2"}

        self.waterlines = {}
        self.waterline_order = []  
        self.waterline_names = {}
        self.waterline_points = defaultdict(list)
        self.centerline_points = []
        self.centerline_spline = True

        self.buttockline_points = defaultdict(list)
        self.buttockline_spline = {}
        self.buttockline_names = {} 

        self.undo_stack = []
        self.redo_stack = []
        self.ship_dimensions = {"Lpp": 20.0, "Bmax": 10.0, "Draft": 5.0}
        self.additional_canvases = []

        self.popup_windows = []

        # UI placeholders
        self.canvas = None
        self.menu = None
        self.menu_side = None

        self.root = master 

        self.frame = self
        self.frame.configure(bg="#0A1A2F")

        self.canvas = tk.Canvas(self.frame, bg="#0A1A2F", highlightthickness=0) #new
        self.canvas.pack(fill="both", expand=True) #new

        
        self.canvas_drawer = CanvasDrawer()
        self.canvas_drawer.width = self.width
        self.canvas_drawer.height = self.height
        self.canvas_drawer.divider_x = self.divider_x
        self.canvas_drawer.divider_y = self.divider_y

        
        self.sync_data_to_drawer()

        

    def sync_data_to_drawer(self):
        d = self.canvas_drawer
        m = self
        d.offsets = m.offsets
        d.stations = m.stations
        d.station_order = m.station_order
        d.station_names = m.station_names
        d.station_spline = m.station_spline
        d.station_visibility = getattr(m, "station_visibility", {x: True for x in m.station_order})
        d.front_scale = m.front_scale
        d.side_scale = m.side_scale
        d.top_scale = m.top_scale
        d.scale = m.scale
        d.view_pan_front = m.view_pan_front
        d.view_pan_side = m.view_pan_side
        d.view_pan_top = m.view_pan_top
        d.selected_station = m.selected_station
        d.centerline_points = m.centerline_points
        d.centerline_spline = m.centerline_spline
        d.waterlines = m.waterlines
        d.waterline_points = m.waterline_points
        d.buttockline_points = m.buttockline_points
        d.buttockline_spline = m.buttockline_spline
        d.buttockline_names = m.buttockline_names
        d.ship_dimensions = m.ship_dimensions
        d.project_top = m.project_top
        d.project_front = m.project_front
        d.project_side = m.project_side
        d.project_iso = m.project_iso
        d.update_waterlines = m.update_waterlines
        

    # ==== projection ====
    def project_top(self, x, y, z): return x, y
    def project_front(self, x, y, z): return y, z
    def project_side(self, x, y, z): return x, z
    def project_iso(self, x, y, z):
        sx = (x - z) * 0.866
        sy = y + (x + z) * 0.5
        return sx, sy