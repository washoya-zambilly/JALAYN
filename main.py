import tkinter as tk

# Import
from core.bodyplan_app import BodyPlan3DApp
from core.state_manager import StateManager
from core.viewer3d2 import Viewer3D
from core.nurbs import NurbsSurface

from core.geometry_nurbs import Nurbs_geometry
from ui.draw_canvas import CanvasDrawer
from ui.events import EventHandler
from ui.menu_bar import MenuBar
from splash_screen import show_splash
from ui.bodyplan_ui import BodyPlanUI
from core.nurbs_curve import NurbsCurve


class JalaynApp(tk.Frame, BodyPlan3DApp, BodyPlanUI, StateManager, CanvasDrawer, EventHandler, MenuBar, Viewer3D, NurbsSurface, Nurbs_geometry, NurbsCurve) :
    def __init__(self, master):

        # Initialization
        tk.Frame.__init__(self, master)
        BodyPlan3DApp.__init__(self, master)
        BodyPlanUI.__init__(self)
        StateManager.__init__(self)
        CanvasDrawer.__init__(self)
        EventHandler.__init__(self)
        MenuBar.__init__(self)
        Viewer3D.__init__(self)

        self.setup_ui()
        self.create_menu_bar()

def start_main_app():
    root.deiconify()
    root.title("JALAYN Ver.0.2 (Experimental)")
    root.geometry("1200x800")

    app = JalaynApp(root)
    app.pack(fill="both", expand=True)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  
    show_splash(root, start_main_app)
    root.mainloop()
