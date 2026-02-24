import os
import tkinter as tk
from PIL import Image, ImageTk

def show_splash(root, on_finish, duration=2500, fade_steps=20):
    """
    duration: total time 
    fade_steps: fade for the images, larger will be better
    """

    splash = tk.Toplevel()
    splash.overrideredirect(True)  
    splash.configure(bg="#0A1A2F")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(base_dir, "assets", "splash.png")

# === SPLASH SCREEN VIEW ===
    try:
        img = Image.open(img_path)
        img = img.resize((500, 300)) 
        splash_img = ImageTk.PhotoImage(img)

        label = tk.Label(splash, image=splash_img, bg="#0A1A2F")
        label.image = splash_img
        label.pack(fill="both", expand=True)
    except Exception as e:
        print("⚠️ Splash image not found:", e)
        tk.Label(splash, text="JALAYN", fg="white", bg="#0A1A2F",
                 font=("Poppins", 26, "bold")).pack(expand=True)
        
    # Label Loading
    loading_label = tk.Label(
        splash, text="Loading modules",
        fg="white", bg="#1B5CB1", font=("Poppins", 10)
    )
    loading_label.place(relx=0.5, rely=0.9, anchor="center")

    def animate_dots(count=0):
        dots = "." * (count % 4)
        loading_label.config(text=f"Loading modules{dots}")
        splash.after(500, animate_dots, count + 1)

    animate_dots()

    # === center screen ===
    def center_window(win, w, h):
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        x, y = (sw - w) // 2, (sh - h) // 2
        win.geometry(f"{w}x{h}+{x}+{y}")
    center_window(splash, 500, 300)

    # === fade in/out ===
    splash.attributes("-alpha", 0.0)

    def fade_in(step=0):
        alpha = step / fade_steps
        splash.attributes("-alpha", alpha)
        if step < fade_steps:
            splash.after(50, fade_in, step + 1)
        else:
            splash.after(duration, fade_out)

    def fade_out(step=fade_steps):
        alpha = step / fade_steps
        splash.attributes("-alpha", alpha)
        if step > 0:
            splash.after(50, fade_out, step - 1)
        else:
            splash.destroy()
            on_finish()

    fade_in()
    