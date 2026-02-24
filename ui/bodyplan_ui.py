#bodyplanui.py
import tkinter as tk
from ui.draw_canvas import CanvasDrawer
from core.bodyplan_app import BodyPlan3DApp

class BodyPlanUI:


    def setup_ui(self):
        # Canvas
        self.canvas = tk.Canvas(self.master, width=self.width, height=self.height, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas_drawer.canvas = self.canvas

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
        self.menu.add_command(label="Change Angle", command=self.change_angle)

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

        self.setup_station_tooltip()
    
    def setup_station_tooltip(self):
        self.tooltip = tk.Label(self.canvas, text="", bg="yellow")
        self.tooltip_window = None

