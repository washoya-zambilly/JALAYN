import tkinter as tk
from collections import defaultdict
from PIL import Image, ImageTk

class BodyPlan3DApp:

    def setup_ui(self):
        # Canvas
        self.canvas = tk.Canvas(self.master, width=self.width, height=self.height, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind mouse
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<B1-Motion>", self.on_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_release)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-2>", self.on_middle_click)
        self.canvas.bind("<B2-Motion>", self.on_middle_drag)
        self.canvas.bind("<ButtonRelease-2>", self.on_middle_release)

        # Context menus
        self.menu = tk.Menu(self.master, tearoff=0)
        self.menu.add_command(label="Add Point", command=self.menu_add_point)
        self.menu.add_command(label="Delete Point", command=self.menu_delete_point)
        self.menu.add_command(label="Add Point Between", command=self.menu_add_point_middle)
        self.menu.add_separator()
        self.menu.add_command(label="Curve Name", command=self.rename_curve)

        self.menu_side = tk.Menu(self.master, tearoff=0)
        self.menu_side.add_command(label="Add Point", command=self.add_centerline_point)
        self.menu_side.add_command(label="Add Point Between", command=self.add_point_between_centerline)
        self.menu_side.add_command(label="Delete Point", command=self.delete_centerline_point)
        self.menu_side.add_separator()
        self.menu_side.add_command(label="Toggle Spline", command=self.toggle_centerline_spline)

        # Toolbar
        btn_frame = tk.Frame(self.master)
        btn_frame.pack(fill=tk.X)

        self.btn_add_station = tk.Button(btn_frame, text="Add Station (X)", command=self.add_station)
        self.btn_add_station.pack(side=tk.LEFT, padx=5, pady=5)

        # Gambar awal
        self.draw_all_canvases()


    def __init__(self):        
        # --- data initialization ---
        self.width = 1400
        self.height = 700
        self.divider_x = self.width // 2
        self.divider_y = self.height // 2
        self.dragging = None

        self.stations = {}
        self.station_order = []
        self.station_spline = {}

        self.front_scale = 50
        self.side_scale = 50
        self.top_scale = 50
        self.scale = 50
        self.offsets = {}
        self.middle_drag_start = None
        self.view_pan_front = [0, 0]
        self.view_pan_side = [0, 0]
        self.view_pan_top = [0, 0]

        self.dragging_divider = None
        self.drag_data = {'station_x': None, 'point_index': None, 'start_x': 0, 'start_y': 0}
        self.selected_station = None

        self.right_click_pos = (0, 0)
        self.right_click_station = None
        self.right_click_point_index = None
        self.right_click_line_index = None

        self.use_spline = True
        self.station_names = {-1.0: "WL1", -2.5: "WL2"}
        self.waterlines = []
        self.waterline_names = {}
        self.waterline_points = defaultdict(list)
        self.centerline_points = []
        self.centerline_spline = True

        self.undo_stack = []
        self.redo_stack = []
        self.ship_dimensions = {"Lpp": 20.0, "Bmax": 10.0, "Draft": 5.0}
        self.additional_canvases = []

        # UI placeholders
        self.canvas = None
        self.menu = None
        self.menu_side = None



    # ==== projection ====
    def project_top(self, x, y, z): return x, y
    def project_front(self, x, y, z): return y, z
    def project_side(self, x, y, z): return x, z
    def project_iso(self, x, y, z):
        sx = (x - z) * 0.866
        sy = y + (x + z) * 0.5
        return sx, sy
