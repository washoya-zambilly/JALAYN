import tkinter as tk
from tkinter import messagebox
from tkinter import messagebox, filedialog
from tkinter import ttk
import csv
import copy

class MenuBar:


    def create_menu_bar(self):
        """Dipanggil setelah tk.Frame sudah aktif"""
                # Menu bar
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        # File menu
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="New", command=self.new_file)
        filemenu.add_command(label="Load", command=self.load_project)
        filemenu.add_command(label="Save", command=self.save_project)
        filemenu.add_command(label="Load CSV", command=self.load_csv)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.master.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.undo)
        edit_menu.add_command(label="Redo", command=self.redo)
        edit_menu.add_command(label="Add Waterline", command=self.add_waterline)
        edit_menu.add_command(label="Refresh Waterlines", command=self.refresh_waterlines)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        # Window menu
        window_menu = tk.Menu(menubar, tearoff=0)
        window_menu.add_command(label="Ship Dimension", command=self.open_ship_dimension_window)
        window_menu.add_command(label="Station List", command=self.station_list)
        menubar.add_cascade(label="Window", menu=window_menu)


    #Definition For Menu Bar
    def new_file(self):
        if messagebox.askyesno("New Project", "Any unsaved changes will be lost. Continue?"):
            # Reset semua data
            self.stations = {}
            self.station_names = {}
            self.station_order = []
            self.front_scale = 50
            self.view_pan_front = [0, 0]
            self.waterlines = []
            self.waterline_points = {}    
            self.waterline_names = {}
            self.centerline_points = []


            # Bersihkan canvas
            self.draw_all()

            messagebox.showinfo("New Project", "New project created.")

    def save_project(self):
        if not self.station_order and not self.waterlines and not getattr(self, "centerline_points", []):
            messagebox.showwarning("Warning", "No station, waterline, or centerline exists.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save as CSV"
        )

        if not filename:
            return  # user batal

        try:
            with open(filename, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # header
                writer.writerow(["type", "name", "axis_value", "y", "z"])

                # === tulis stations ===
                for x in self.station_order:
                    name = self.station_names.get(x, f"Station X={x:.3f}")
                    pts = self.stations[x]
                    if not pts:
                        writer.writerow(["station", name, f"{x:.3f}", "-", "-"])
                        continue
                    for _, y, z in pts:
                        writer.writerow(["station", name, f"{x:.3f}", f"{y:.3f}", f"{z:.3f}"])

                # === tulis waterlines ===
                for z in self.waterlines:
                    name = self.waterline_names.get(z, f"WL z={z:.3f}")
                    points = self.waterline_points.get(z, [])
                    if not points:
                        continue
                    for x, y in points:
                        writer.writerow(["waterline", name, f"{z:.3f}", f"{x:.3f}", f"{y:.3f}"])

                # === tulis centerline ===
                if hasattr(self, "centerline_points") and self.centerline_points:
                    for x, z in self.centerline_points:
                        writer.writerow(["centerline", "Buttock Y=0", f"{x:.3f}", "0.000", f"{z:.3f}"])

            messagebox.showinfo("Success", f"Data successfully saved to:\n{filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Fail to save CSV:\n{e}")


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

                        # pastikan semua struktur ada
                        if not hasattr(self, "waterlines"):
                            self.waterlines = []
                        if not hasattr(self, "waterline_points"):
                            self.waterline_points = {}
                        if not hasattr(self, "waterline_names"):
                            self.waterline_names = {}

                        if z_val not in self.waterlines:
                            self.waterlines.append(z_val)
                            self.waterline_points[z_val] = []
                            self.waterline_names[z_val] = name
                        self.waterline_points[z_val].append((x, y))

                    elif row_type == "centerline":
                        try:
                            x = float(row["axis_value"])
                            z = float(row["z"])
                        except ValueError:
                            continue
                        self.centerline_points.append((x, z))

            # Sort ulang
            self.station_order.sort()
            self.waterlines.sort(reverse=True)
            self.centerline_points.sort(key=lambda p: p[0])

            self.draw_all()
            messagebox.showinfo("Success", f"Loaded project from {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")


    def station_list(self):
        # Buat jendela baru
        win = tk.Toplevel(self)
        win.title("Station List (Y, Z)")
        win.geometry("500x400")

        # Buat Treeview
        tree = ttk.Treeview(win)
        tree["columns"] = ("Y", "Z")
        tree.heading("#0", text="Station")
        tree.heading("Y", text="Y")
        tree.heading("Z", text="Z")
        tree.column("#0", width=180, anchor="w")
        tree.column("Y", width=100, anchor="center")
        tree.column("Z", width=100, anchor="center")
        tree.pack(fill=tk.BOTH, expand=True)

        # Tambahkan scrollbar vertikal
        scrollbar = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # === Fungsi untuk memuat ulang data ke tabel ===
        def refresh_table():
            # Hapus isi lama
            for item in tree.get_children():
                tree.delete(item)

            # Masukkan data ke tabel
            if not self.station_order:
                tree.insert("", "end", text="No station exist")
            else:
                for x in self.station_order:
                    # Ambil nama station (jika ada)
                    name = self.station_names.get(x, f"Station X={x}")
                    parent_id = tree.insert("", "end", text=f"{name} (X={x:.3f})")

                    pts = self.stations[x]
                    if not pts:
                        tree.insert(parent_id, "end", text="(No point exist)", values=("", ""))
                        continue

                    for _, y, z in pts:
                        tree.insert(parent_id, "end", text="", values=(f"{y:.3f}", f"{z:.3f}"))
            
        # === Fungsi untuk ekspor CSV ===
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
                return  # user batal

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
        
        # === Tombol di bawah tabel ===
        btn_frame = ttk.Frame(win)
        btn_frame.pack(pady=5)

        btn_refresh = ttk.Button(btn_frame, text="Refresh", command=refresh_table)
        btn_refresh.pack(side=tk.LEFT, padx=5)

        btn_export = ttk.Button(btn_frame, text="Export CSV", command=export_csv)
        btn_export.pack(side=tk.LEFT, padx=5)

        btn_close = ttk.Button(btn_frame, text="Close", command=win.destroy)
        btn_close.pack(side=tk.LEFT, padx=5)

        # Muat tabel pertama kali
        refresh_table()
    

    def load_csv(self):
        filename = filedialog.askopenfilename(title="Load CSV", filetypes=[("CSV files","*.csv")])
        if not filename:
            return
        # Simpan state sebelum load, agar bisa undo
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

                    # Tambahkan ke stations
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
        # deepcopy supaya tidak terpengaruh perubahan selanjutnya
        state = {
            'stations': copy.deepcopy(self.stations),
            'station_names': copy.deepcopy(self.station_names),
            'station_order': copy.deepcopy(self.station_order)
        }
        self.undo_stack.append(state)
        # setiap perubahan baru, redo stack dikosongkan
        self.redo_stack.clear()
    
    def undo(self):
        if not self.undo_stack:
            return
        # Simpan current state ke redo
        self.redo_stack.append({
            'stations': copy.deepcopy(self.stations),
            'station_names': copy.deepcopy(self.station_names),
            'station_order': copy.deepcopy(self.station_order)
        })
        # ambil state terakhir dari undo
        state = self.undo_stack.pop()
        self.stations = state['stations']
        self.station_names = state['station_names']
        self.station_order = state['station_order']
        self.draw_all()

    def redo(self):
        if not self.redo_stack:
            return
        # Simpan current state ke undo
        self.undo_stack.append({
            'stations': copy.deepcopy(self.stations),
            'station_names': copy.deepcopy(self.station_names),
            'station_order': copy.deepcopy(self.station_order)
        })
        # ambil state terakhir dari redo
        state = self.redo_stack.pop()
        self.stations = state['stations']
        self.station_names = state['station_names']
        self.station_order = state['station_order']
        self.draw_all()

    # ===============================
    # Ship Dimension Window
    # ===============================
    def open_ship_dimension_window(self):
        # Pastikan hanya satu jendela aktif
        win = tk.Toplevel(self.master)
        win.title("Ship Dimension")
        win.geometry("300x250")
        win.resizable(False, False)

        # Jika belum ada data, inisialisasi
        if not hasattr(self, "ship_dimensions"):
            self.ship_dimensions = {"Lpp": 50.0, "Bmax": 20.0, "Draft": 5.0}

        dims = self.ship_dimensions

        # Judul
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

        # Tombol simpan & tutup
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


