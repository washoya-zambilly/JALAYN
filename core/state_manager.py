from tkinter import simpledialog, messagebox
from tkinter import messagebox 

class StateManager:
    def rename_curve(self):
        if self.selected_station is None:
            messagebox.showinfo("Info", "Select a Curve first.")
            return
        
        cur_name = self.station_names.get(self.selected_station, "")
        name = simpledialog.askstring("Curve Name", "Input Curve Name:", initialvalue=cur_name)
        if name is None:
            return  
        self.station_names[self.selected_station] = name
        self.draw_all()

    #Draw Waterlines
    def add_waterline(self):
        z = simpledialog.askfloat("Add Waterline", "Enter Z level (vertical position):")
        if z is None:
            return

        if z in self.waterlines:
            messagebox.showinfo("Info", f"Waterline at Z={z} already exists.")
            return

        self.save_state() 
        self.waterlines.append(z)
        self.waterlines.sort(reverse=True) 
        self.calculate_waterline_points(z)
        self.draw_all()

    def update_waterlines(self):
        """Update the waterline"""
        if not self.stations or not self.waterlines:
            return

       
        if not hasattr(self, "waterline_points"):
            self.waterline_points = {}

        for z_level in self.waterlines:
            wl_points = []

            # === Intersection with station ===
            for x in self.station_order:
                pts = self.stations[x]
                if len(pts) < 2:
                    continue

                for (x1, y1, z1), (x2, y2, z2) in zip(pts[:-1], pts[1:]):
                    if (z1 - z_level) * (z2 - z_level) <= 0 and z1 != z2:
                        t = (z_level - z1) / (z2 - z1)
                        y_int = y1 + t * (y2 - y1)
                        wl_points.append((x, y_int))
                        break  

            # === Intersection with CL (XZ in Y=0) ===
            if hasattr(self, "centerline_points") and len(self.centerline_points) >= 2:
                center_pt = None
                for (x1, z1), (x2, z2) in zip(self.centerline_points[:-1], self.centerline_points[1:]):
                    if (z1 - z_level) * (z2 - z_level) <= 0 and z1 != z2:
                        t = (z_level - z1) / (z2 - z1)
                        x_interp = x1 + t * (x2 - x1)
                        center_pt = (x_interp, 0.0)
                        break

                if center_pt is not None:
                    mid_index = len(wl_points) // 2
                    wl_points.insert(mid_index, center_pt)

            wl_points.sort(key=lambda p: p[0])  
            self.waterline_points[z_level] = wl_points


    def refresh_waterlines(self):
        """Refresh waterline"""
        if not self.waterlines:
            messagebox.showinfo("Info", "No waterlines to refresh.")
            return

        self.save_state()  
        self.update_waterlines()
        self.draw_all()
        messagebox.showinfo("Refreshed", "All waterlines have been updated.")

    def calculate_waterline_points(self, z):
        """Hitung titik-titik waterline di semua station berdasarkan z"""
        wl_points = []

        # === Intersection with station (YZ in X) ===
        for x in self.station_order:
            pts = self.stations[x]
            for i in range(len(pts)-1):
                p1 = pts[i]
                p2 = pts[i+1]
                z1, z2 = p1[2], p2[2]

                if (z1 - z)*(z2 - z) <= 0 and z1 != z2:
                    t = (z - z1) / (z2 - z1)
                    x_interp = p1[0] + t * (p2[0] - p1[0])
                    y_interp = p1[1] + t * (p2[1] - p1[1])
                    wl_points.append((x_interp, y_interp))
            
        # === Intersection with centerline (XZ in Y=0) ===
            if hasattr(self, "centerline_points") and len(self.centerline_points) >= 2:
                center_pt = None
                for (x1, z1), (x2, z2) in zip(self.centerline_points[:-1], self.centerline_points[1:]):
                    if (z1 - z) * (z2 - z) <= 0 and z1 != z2:
                        t = (z - z1) / (z2 - z1)
                        x_interp = x1 + t * (x2 - x1)
                        center_pt = (x_interp, 0.0)
                        break

                if center_pt is not None:
                    mid_index = len(wl_points) // 2
                    wl_points.insert(mid_index, center_pt)

        if not hasattr(self, "waterline_points"):
            self.waterline_points = {}
        self.waterline_points[z] = wl_points
    

    #Draw Centerline
    def add_centerline_point(self):
        """Add centerline point in the side view (only for centerline)"""
        try:
            if not hasattr(self, "centerline_points"):
                self.centerline_points = []

            if not hasattr(self, "right_click_pos") or self.right_click_pos is None:
                messagebox.showwarning("Warning", "No click position detected.")
                return

            canvas_x, canvas_y = self.right_click_pos
            cx, cy = self.offsets['side']
            scale = self.side_scale
            pan_x, pan_y = self.view_pan_side

            x = (canvas_x - cx - pan_x) / scale
            z = (cy - canvas_y + pan_y) / scale

            self.centerline_points.append((x, z))

            self.draw_all()

        except Exception as e:
            messagebox.showerror("Error", str(e))


    def delete_centerline_point(self):
        if not self.centerline_points:
            messagebox.showinfo("Info", "No points in centerline.")
            return

        # find nearest
        x, y = self.right_click_pos
        cx_s, cy_s = self.offsets['side']
        scale = self.side_scale
        pan_x, pan_y = self.view_pan_side
        min_dist = 9999
        idx = None
        for i, (px, pz) in enumerate(self.centerline_points):
            sx = cx_s + px * scale + pan_x
            sy = cy_s - pz * scale + pan_y
            dist = abs(sx - x) + abs(sy - y)
            if dist < min_dist:
                min_dist = dist
                idx = i
        if idx is not None:
            del self.centerline_points[idx]
            self.draw_all()


    def add_point_between_centerline(self):
        if not hasattr(self, "centerline_points") or len(self.centerline_points) < 2:
            messagebox.showinfo("Info", "Need at least two points to add between.")
            return

        canvas_x, canvas_y = self.right_click_pos
        cx, cy = self.offsets['side']
        scale = self.side_scale
        pan_x, pan_y = self.view_pan_side

        x_new = (canvas_x - cx - pan_x) / scale
        z_new = (cy - canvas_y + pan_y) / scale

        min_dist = float('inf')
        insert_index = len(self.centerline_points)
        for i in range(len(self.centerline_points) - 1):
            x1, z1 = self.centerline_points[i]
            x2, z2 = self.centerline_points[i + 1]

            if (x1 <= x_new <= x2) or (x2 <= x_new <= x1):
                dist = abs(x_new - ((x1 + x2) / 2))
                if dist < min_dist:
                    min_dist = dist
                    insert_index = i + 1

        if insert_index == len(self.centerline_points):
            self.centerline_points.append((x_new, z_new))
        else:
            self.centerline_points.insert(insert_index, (x_new, z_new))

        self.draw_all()


    def toggle_centerline_spline(self):
        self.centerline_spline = not self.centerline_spline
        self.draw_all()
    