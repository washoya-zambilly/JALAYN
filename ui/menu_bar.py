#menubar.py
import tkinter as tk
from tkinter import messagebox
from tkinter import messagebox, filedialog
from tkinter import ttk
import csv
import copy
import json
from ui.draw_canvas import CanvasDrawer

class MenuBar:
    def create_menu_bar(self):
        # Menu bar
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        # File menu
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="New", command=self.new_file)
        filemenu.add_separator()
        filemenu.add_command(label="Load JSON", command=self.load_project_json)
        filemenu.add_command(label="Save as JSON", command=self.save_project_json)
        #filemenu.add_command(label="Load", command=self.load_project) #not active
        filemenu.add_separator()
        filemenu.add_command(label="Load CSV", command=self.load_csv)
        filemenu.add_command(label="Save as CSV", command=self.save_project)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.master.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.undo)
        edit_menu.add_command(label="Redo", command=self.redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Add Waterline", command=self.add_waterline)
        edit_menu.add_command(label="Refresh Waterlines", command=self.refresh_waterlines)
        edit_menu.add_separator()
        edit_menu.add_command(label="Add Buttockline", command=self.add_buttockline)
        edit_menu.add_command(label="Refresh Buttocklines", command=self.refresh_buttocklines)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        # Window menu
        window_menu = tk.Menu(menubar, tearoff=0)
        window_menu.add_command(label="Ship Dimension", command=self.open_ship_dimension_window)
        window_menu.add_command(label="Station List", command=self.station_list)
        #window_menu.add_command(label="Y-Z Window", command=self.open_yz_window) #Coming Soon
        menubar.add_cascade(label="Window", menu=window_menu)

        # Window View
        window_view = tk.Menu(menubar, tearoff=0)
        window_view.add_command(label="Preview Hull", command=self.preview_hull_3d)
        menubar.add_cascade(label="View", menu=window_view)


    #Definition For Menu Bar
    def new_file(self):
        if messagebox.askyesno("New Project", "Any unsaved changes will be lost. Continue?"):
            # Reset all data
            self.stations = {}
            self.station_names = {}
            self.station_order = []
            self.front_scale = 50
            self.view_pan_front = [0, 0]
            self.waterlines = []
            self.waterline_points = {}    
            self.waterline_names = {}
            self.centerline_points = []
            self.buttocklines = []
            self.buttockline_points = {}
            self.buttockline_names = {}

            # Clear canvas
            self.draw_all()

            messagebox.showinfo("New Project", "New project created.")

    def save_project(self):
        if (not self.station_order
            and not self.waterlines 
            and not getattr(self, "centerline_points", [])
            and not getattr(self, "buttocklines", [])):
            messagebox.showwarning("Warning", "No station, waterline, or centerline exists.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save as CSV"
        )

        if not filename:
            return  # cancel

        try:
            with open(filename, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # header
                writer.writerow(["type", "name", "axis_value", "y", "z"])

                # === save stations ===
                for x in self.station_order:
                    name = self.station_names.get(x, f"Station X={x:.3f}")
                    pts = self.stations[x]
                    if not pts:
                        writer.writerow(["station", name, f"{x:.3f}", "-", "-"])
                        continue
                    for _, y, z in pts:
                        writer.writerow(["station", name, f"{x:.3f}", f"{y:.3f}", f"{z:.3f}"])

                # === save waterlines ===
                for z in self.waterlines:
                    name = self.waterline_names.get(z, f"WL z={z:.3f}")
                    points = self.waterline_points.get(z, [])
                    if not points:
                        continue
                    for x, y in points:
                        writer.writerow(["waterline", name, f"{z:.3f}", f"{x:.3f}", f"{y:.3f}"])

                # === save centerline ===
                if hasattr(self, "centerline_points") and self.centerline_points:
                    for x, z in self.centerline_points:
                        writer.writerow(["centerline", "Buttock Y=0", f"{x:.3f}", "0.000", f"{z:.3f}"])
                
                # === Buttocklines ===
                if hasattr(self, "buttocklines") and self.buttocklines:
                    for y in self.buttocklines:
                        name = self.buttockline_names.get(y, f"BL y={y:.3f}")
                        points = self.buttockline_points.get(y, [])
                        for x, z in points:
                            writer.writerow(["buttockline", name, f"{y:.3f}", f"{x:.3f}", f"{z:.3f}"])

            messagebox.showinfo("Success", f"Data successfully saved to:\n{filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Fail to save CSV:\n{e}")



    def save_project_json(self):
        if (not self.station_order
            and not self.waterlines
            and not getattr(self, "centerline_points", [])
            and not getattr(self, "buttocklines", [])):
            messagebox.showwarning("Warning", "No geometry data to save.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Hull Project (*.json)", "*.json")],
            title="Save Project As JSON"
        )

        if not filename:
            return

        try:
            project = {
                "project": {
                    "name": getattr(self, "project_name", "Unnamed Project"),
                    "unit": "meter",
                    "version": "0.1"
                },

                # === Ship Main Dimensions ===
                "ship_dimensions": getattr(
                    self,
                    "ship_dimensions",
                    {"Lpp": 0.0, "Bmax": 0.0, "Draft": 0.0}
                ),

                "stations": [],
                "waterlines": [],
                "buttocklines": [],
                "centerline": None
            }

            # === Stations ===
            for x in self.station_order:
                project["stations"].append({
                    "x": x,
                    "name": self.station_names.get(x, f"Station X={x:.3f}"),
                    "points": self.stations.get(x, [])
                })

            # === Waterlines ===
            for z in self.waterlines:
                project["waterlines"].append({
                    "z": z,
                    "name": self.waterline_names.get(z, f"WL z={z:.3f}"),
                    "points": self.waterline_points.get(z, [])
                })

            # === Buttocklines ===
            for y in getattr(self, "buttocklines", []):
                project["buttocklines"].append({
                    "y": y,
                    "name": self.buttockline_names.get(y, f"BL y={y:.3f}"),
                    "points": self.buttockline_points.get(y, [])
                })

            # === Centerline ===
            if getattr(self, "centerline_points", []):
                project["centerline"] = {
                    "name": "Buttock Y=0",
                    "points": self.centerline_points
                }

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(project, f, indent=2)

            messagebox.showinfo("Success", f"Project saved as JSON:\n{filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save JSON:\n{e}")



    def load_project_json(self):
        filename = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("Hull Project (*.json)", "*.json")],
            title="Load Project (JSON)"
        )
        if not filename:
            return

        try:
            self.save_state()

            # === Clear existing data ===
            self.stations.clear()
            self.station_names.clear()
            self.station_order.clear()

            self.waterlines.clear()
            self.waterline_names.clear()
            self.waterline_points.clear()
            self.waterline_order = []

            self.centerline_points = []

            self.buttocklines = []
            self.buttockline_names = {}
            self.buttockline_points = {}

            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)

            
            # === Ship Dimensions ===
            self.ship_dimensions = data.get(
                "ship_dimensions",
                {"Lpp": 0.0, "Bmax": 0.0, "Draft": 0.0}
            )


            # === Stations ===
            for st in data.get("stations", []):
                x = float(st["x"])
                self.station_order.append(x)
                self.station_names[x] = st.get("name", f"Station X={x:.3f}")
                self.stations[x] = [
                    tuple(p) for p in st.get("points", [])
                ]

            # === Waterlines ===
            for wl in data.get("waterlines", []):
                z = float(wl["z"])
                self.waterlines[z] = []
                self.waterline_order.append(z)
                self.waterline_names[z] = wl.get("name", f"WL z={z:.3f}")
                self.waterline_points[z] = [
                    tuple(p) for p in wl.get("points", [])
                ]

            # === Buttocklines ===
            for bl in data.get("buttocklines", []):
                y = float(bl["y"])
                self.buttocklines.append(y)
                self.buttockline_names[y] = bl.get("name", f"BL y={y:.3f}")
                self.buttockline_points[y] = [
                    tuple(p) for p in bl.get("points", [])
                ]

            # === Centerline ===
            cl = data.get("centerline")
            if cl:
                self.centerline_points = [
                    tuple(p) for p in cl.get("points", [])
                ]

            # === Sorting ===
            self.station_order.sort()
            self.waterline_order.sort(reverse=True)
            self.centerline_points.sort(key=lambda p: p[0])

            self.draw_all()
            messagebox.showinfo("Success", f"Loaded JSON project:\n{filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load JSON:\n{e}")



    def load_project(self):
        filename = filedialog.askopenfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Load Project"
        )
        if not filename:
            return

        try:
            self.save_state()

            # Clear existing data
            self.stations.clear()
            self.station_names.clear()
            self.station_order.clear()
            self.waterlines.clear()
            self.waterline_names.clear()
            self.waterline_points.clear()
            self.centerline_points = []
            self.buttocklines = []
            self.buttockline_names = {}
            self.buttockline_points = {}

            with open(filename, newline='', encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row_type = row.get("type", "").lower().strip()

                    if row_type == "station":
                        try:
                            x = float(row["axis_value"])
                            y = float(row["y"])
                            z = float(row["z"])
                        except ValueError:
                            continue
                        name = row["name"]

                        if x not in self.stations:
                            self.stations[x] = []
                            self.station_order.append(x)
                            self.station_names[x] = name
                        self.stations[x].append((x, y, z))

                    elif row_type == "waterline":
                        try:
                            z_val = float(row["axis_value"])
                            x = float(row["y"])
                            y = float(row["z"])
                        except ValueError:
                            continue

                        name = row["name"]

                        # pastikan struktur ada
                        if not hasattr(self, "waterlines"):
                            self.waterlines = {}
                        if not hasattr(self, "waterline_order"):
                            self.waterline_order = []
                        if not hasattr(self, "waterline_names"):
                            self.waterline_names = {}

                        if z_val not in self.waterlines:
                            self.waterlines[z_val] = []
                            self.waterline_order.append(z_val)
                            self.waterline_names[z_val] = name

                        self.waterlines[z_val].append((x, y))


                    elif row_type == "centerline":
                        try:
                            x = float(row["axis_value"])
                            z = float(row["z"])
                        except ValueError:
                            continue
                        self.centerline_points.append((x, z))

                    elif row_type == "buttockline":
                        try:
                            y_val = float(row["axis_value"])
                            x = float(row["y"])
                            z = float(row["z"])
                        except ValueError:
                            continue
                        name = row["name"]
                        if y_val not in self.buttocklines:
                            self.buttocklines.append(y_val)
                            self.buttockline_points[y_val] = []
                            self.buttockline_names[y_val] = name
                        self.buttockline_points[y_val].append((x, z))

            # Sorting
            self.station_order.sort()
            self.waterline_order.sort(reverse=True)
            self.centerline_points.sort(key=lambda p: p[0])

            self.draw_all()
            messagebox.showinfo("Success", f"Loaded project from {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")


    def station_list(self):
        # New window
        win = tk.Toplevel(self)
        win.title("Station List (Y, Z)")
        win.geometry("500x400")

        # ensure visibility
        if not hasattr(self, "station_visibility"):
            self.station_visibility = {x: True for x in self.station_order}

        # Treeview
        tree = ttk.Treeview(win)
        tree["columns"] = ("Y", "Z", "Visible")
        tree.heading("#0", text="Station")
        tree.heading("Y", text="Y")
        tree.heading("Z", text="Z")
        tree.heading("Visible", text="Visible")
        tree.column("#0", width=180, anchor="w")
        tree.column("Y", width=100, anchor="center")
        tree.column("Z", width=100, anchor="center")
        tree.column("Visible", width=70, anchor="center")
        tree.pack(fill=tk.BOTH, expand=True)

        # Add scrollbar vertical
        scrollbar = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # === Refresh Table ===
        def refresh_table():
            # Delete old data
            for item in tree.get_children():
                tree.delete(item)

            # Input data to table
            if not self.station_order:
                tree.insert("", "end", text="No station exist")
            else:
                for x in self.station_order:
                    # Take all stations (if exist)
                    name = self.station_names.get(x, f"Station X={x}")
                    visible = "Yes" if self.station_visibility.get(x, True) else "No"
                    parent_id = tree.insert("", "end", text=f"{name} (X={x:.3f})", values=("", "", visible))

                    pts = self.stations[x]
                    if not pts:
                        tree.insert(parent_id, "end", text="(No point exist)", values=("", ""))
                        continue

                    for _, y, z in pts:
                        tree.insert(parent_id, "end", text="", values=(f"{y:.3f}", f"{z:.3f}"))
        
        def on_double_click(event):
            item_id = tree.identify_row(event.y)
            col = tree.identify_column(event.x)

            if not item_id or tree.parent(item_id) == "":  
                return

            x_val = float(tree.item(tree.parent(item_id), "text").split("X=")[1].strip(")"))
            idx = tree.index(item_id)
            old_val = tree.set(item_id, column=col)
            entry = ttk.Entry(tree)
            entry.insert(0, old_val)

            def save_edit(event=None):
                try:
                    new_val = float(entry.get())
                    y, z = self.stations[x_val][idx][1], self.stations[x_val][idx][2]
                    if col == "#1":  # Y column
                        y = new_val
                    elif col == "#2":  # Z column
                        z = new_val
                    self.stations[x_val][idx] = (x_val, y, z)
                    self.draw_all()  # update GUI
                    tree.set(item_id, column=col, value=f"{new_val:.3f}")
                except ValueError:
                    messagebox.showerror("Error", "Invalid number")
                finally:
                    entry.destroy()

            entry.bind("<Return>", save_edit)
            entry.bind("<FocusOut>", save_edit)

            tree.set(item_id, column=col, value="")
            x0, y0, width, height = tree.bbox(item_id, column=col)
            entry.place(x=x0, y=y0, width=width, height=height)
            entry.focus()

        tree.bind("<Double-1>", on_double_click)


        def get_selected_stations():
            x_vals = set()
            for item_id in tree.selection():
                # take the parent
                while tree.parent(item_id):
                    item_id = tree.parent(item_id)
                text = tree.item(item_id, "text")
                if "X=" in text:
                    x_val = float(text.split("X=")[1].strip(")"))
                    x_vals.add(x_val)
            return list(x_vals)

        # === Button Hide / Show ===
        def hide_selected():
            x_vals = get_selected_stations()
            if not x_vals:
                return

            for x in x_vals:
                tag = f"station_{x:.3f}"
                self.canvas.itemconfigure(tag, state="hidden")
                self.station_visibility[x] = False

            refresh_table()

        def show_selected():
            x_vals = get_selected_stations()
            if not x_vals:
                return

            for x in x_vals:
                tag = f"station_{x:.3f}"
                self.canvas.itemconfigure(tag, state="normal")
                self.station_visibility[x] = True

            refresh_table()
            
            
        # === Export CSV ===
        def export_csv():
            if not self.station_order:
                messagebox.showwarning("Warning", "No station exist.")
                return

            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="Save as CSV"
            )

            if not filename:
                return  # cancel 

            try:
                with open(filename, mode="w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["station_name", "station_x", "y", "z"])  # header

                    for x in self.station_order:
                        name = self.station_names.get(x, f"Station X={x:.3f}")
                        pts = self.stations[x]
                        if not pts:
                            writer.writerow([name, f"{x:.3f}", "-", "-"])
                            continue
                        for _, y, z in pts:
                            writer.writerow([name, f"{x:.3f}", f"{y:.3f}", f"{z:.3f}"])

                messagebox.showinfo("Success", f"Data successfuly saved to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Fail to save CSV:\n{e}")
        
        # === Button below the table ===
        btn_frame = ttk.Frame(win)
        btn_frame.pack(pady=5)

        btn_refresh = ttk.Button(btn_frame, text="Refresh", command=refresh_table)
        btn_refresh.pack(side=tk.LEFT, padx=5)

        btn_export = ttk.Button(btn_frame, text="Export CSV", command=export_csv)
        btn_export.pack(side=tk.LEFT, padx=5)

        btn_close = ttk.Button(btn_frame, text="Close", command=win.destroy)
        btn_close.pack(side=tk.LEFT, padx=5)

        btn_hide = ttk.Button(btn_frame, text="Hide Selected", command=hide_selected)
        btn_hide.pack(side=tk.LEFT, padx=5)

        btn_show = ttk.Button(btn_frame, text="Show Selected", command=show_selected)
        btn_show.pack(side=tk.LEFT, padx=5)

        # Refresh
        refresh_table()
    

    def load_csv(self):
        filename = filedialog.askopenfilename(title="Load CSV", filetypes=[("CSV files","*.csv")])
        if not filename:
            return
        # Dave state
        self.save_state()
        try:
            self.stations.clear()
            self.station_names.clear()
            self.station_order.clear()

            with open(filename, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    name = row['station_name']
                    x = float(row['station_x'])
                    y = float(row['y'])
                    z = float(row['z'])

                    # Add to station
                    if x not in self.stations:
                        self.stations[x] = []
                        self.station_order.append(x)
                        self.station_names[x] = name

                    self.stations[x].append((x, y, z))

            self.draw_all()
            messagebox.showinfo("Success", "CSV loaded successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV:\n{e}")


    def save_state(self):
        state = {
            'stations': copy.deepcopy(self.stations),
            'station_names': copy.deepcopy(self.station_names),
            'station_order': copy.deepcopy(self.station_order)
        }
        self.undo_stack.append(state)
        
        self.redo_stack.clear()
    
    def undo(self):
        if not self.undo_stack:
            return
        # save current state to redo
        self.redo_stack.append({
            'stations': copy.deepcopy(self.stations),
            'station_names': copy.deepcopy(self.station_names),
            'station_order': copy.deepcopy(self.station_order)
        })
        # take the latest state 
        state = self.undo_stack.pop()
        self.stations = state['stations']
        self.station_names = state['station_names']
        self.station_order = state['station_order']
        self.draw_all()

    def redo(self):
        if not self.redo_stack:
            return
        # save thr current state to undo
        self.undo_stack.append({
            'stations': copy.deepcopy(self.stations),
            'station_names': copy.deepcopy(self.station_names),
            'station_order': copy.deepcopy(self.station_order)
        })
        # take the latest state 
        state = self.redo_stack.pop()
        self.stations = state['stations']
        self.station_names = state['station_names']
        self.station_order = state['station_order']
        self.draw_all()


    # ===============================
    # Ship Dimension Window
    # ===============================
    def open_ship_dimension_window(self):
        # always active
        win = tk.Toplevel(self.master)
        win.title("Ship Dimension")
        win.geometry("300x250")
        win.resizable(False, False)

        # initialization
        if not hasattr(self, "ship_dimensions"):
            self.ship_dimensions = {"Lpp": 50.0, "Bmax": 20.0, "Draft": 5.0}

        dims = self.ship_dimensions

        # title
        tk.Label(win, text="Enter Main Dimensions", font=("Arial", 12, "bold")).pack(pady=10)

        # Form input
        frm = ttk.Frame(win)
        frm.pack(padx=10, pady=5, fill="x")

        ttk.Label(frm, text="Lpp (m):").grid(row=0, column=0, sticky="w", pady=3)
        ent_lpp = ttk.Entry(frm)
        ent_lpp.grid(row=0, column=1, pady=3)
        ent_lpp.insert(0, str(dims["Lpp"]))

        ttk.Label(frm, text="Bmax (m):").grid(row=1, column=0, sticky="w", pady=3)
        ent_b = ttk.Entry(frm)
        ent_b.grid(row=1, column=1, pady=3)
        ent_b.insert(0, str(dims["Bmax"]))

        ttk.Label(frm, text="Draft (m):").grid(row=2, column=0, sticky="w", pady=3)
        ent_d = ttk.Entry(frm)
        ent_d.grid(row=2, column=1, pady=3)
        ent_d.insert(0, str(dims["Draft"]))

        # save and close button
        btn_frame = ttk.Frame(win)
        btn_frame.pack(pady=10)

        def save_dims():
            try:
                Lpp = float(ent_lpp.get())
                B = float(ent_b.get())
                D = float(ent_d.get())
                self.ship_dimensions = {"Lpp": Lpp, "Bmax": B, "Draft": D}
                messagebox.showinfo("Saved", "Ship dimensions updated.")
                win.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numeric values.")

        ttk.Button(btn_frame, text="Save", command=save_dims).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side=tk.LEFT, padx=5)



