import tkinter as tk

# Import
from core.bodyplan_app import BodyPlan3DApp
from core.state_manager import StateManager
from ui.draw_canvas import CanvasDrawer
from ui.events import EventHandler
from ui.menu_bar import MenuBar
from splash_screen import show_splash


class JalaynApp(tk.Frame, BodyPlan3DApp, StateManager, CanvasDrawer, EventHandler, MenuBar):
    def __init__(self, master):

        # Initialization
        tk.Frame.__init__(self, master)
        BodyPlan3DApp.__init__(self)
        StateManager.__init__(self)
        CanvasDrawer.__init__(self)
        EventHandler.__init__(self)
        MenuBar.__init__(self)

        self.setup_ui()
        self.create_menu_bar()

def start_main_app():
    root.deiconify()
    root.title("JALAYN Ver.0.1 (Experimental)")
    root.geometry("1200x800")

    app = JalaynApp(root)
    app.pack(fill="both", expand=True)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  
    show_splash(root, start_main_app)
    root.mainloop()
