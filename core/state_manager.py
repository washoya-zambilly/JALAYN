from tkinter import simpledialog, messagebox
from tkinter import messagebox 
import math

class StateManager:
    def hermite(self, p0, p1, m0, m1, t):
        h00 = 2*t**3 - 3*t**2 + 1
        h10 = t**3 - 2*t**2 + t
        h01 = -2*t**3 + 3*t**2
        h11 = t**3 - t**2
        return (
            h00*p0[0] + h10*m0[0] + h01*p1[0] + h11*m1[0],
            h00*p0[1] + h10*m0[1] + h01*p1[1] + h11*m1[1]
        )
    
    def generate_hermite_waterline(self, points, steps=20):
        if len(points) < 2:
            return points

        result = []
        n = len(points)

        tangents = []
        for i in range(n):
            if i == 0:
                # forward difference
                m = (points[1][0] - points[0][0],
                    points[1][1] - points[0][1])
            elif i == n - 1:
                # backward difference
                m = (points[-1][0] - points[-2][0],
                    points[-1][1] - points[-2][1])
            else:
                # central difference
                m = ((points[i+1][0] - points[i-1][0]) * 0.5,
                    (points[i+1][1] - points[i-1][1]) * 0.5)
            tangents.append(m)

        # === Build egments ===
        for i in range(n - 1):
            p0 = points[i]
            p1 = points[i+1]
            m0 = tangents[i]
            m1 = tangents[i+1]

            for s in range(steps):
                t = s / steps
                result.append(self.hermite(p0, p1, m0, m1, t))

        result.append(points[-1])
        return result

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

    #---------------------------------------------
    #Draw Waterlines
    #---------------------------------------------
    def add_waterline(self):
        z = simpledialog.askfloat(
            "Add Waterline",
            "Enter Z level (vertical position):"
        )
        if z is None:
            return
        
        if not isinstance(self.waterlines, dict):
            self.waterlines = {}


        if z in self.waterlines:
            messagebox.showinfo(
                "Info",
                f"Waterline at Z={z} already exists."
            )
            return

        self.save_state()

        self.waterlines[z] = []          # create empty point list
        self.waterline_order.append(z)
        self.waterline_order.sort(reverse=True)

        self.calculate_waterline_points(z)
        self.draw_all()

    def update_waterlines(self):
        """Update the waterline"""
        if not self.stations or not self.waterlines:
            return

        if not hasattr(self, "waterline_points"):
            self.waterline_points = {}

        for z_level in self.waterlines:
            self.waterline_points[z_level] = self.calculate_waterline_points(z_level)

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
        """Calculate raw (unsmoothed) waterline intersection points."""
        wl_points = []

        # === Intersection with station (YZ section) ===
        for x in self.station_order:
            pts = self.stations[x]
            if len(pts) < 2:
                continue

            for (x1, y1, z1), (x2, y2, z2) in zip(pts[:-1], pts[1:]):
                if (z1 - z) * (z2 - z) <= 0 and z1 != z2:
                    t = (z - z1) / (z2 - z1)

                    # NOTE: X station fixed, do NOT interpolate X!
                    y_interp = y1 + t * (y2 - y1)

                    wl_points.append((x, y_interp))

        # === Intersection with centerline (XZ plane, Y=0) ===
        if hasattr(self, "centerline_points") and len(self.centerline_points) >= 2:
            for (cx1, cz1), (cx2, cz2) in zip(
                    self.centerline_points[:-1],
                    self.centerline_points[1:]):

                if cz1 == cz2:
                    continue

                if (cz1 < z and cz2 > z) or (cz1 > z and cz2 < z):
                    t = (z - cz1) / (cz2 - cz1)
                    x_int = cx1 + t * (cx2 - cx1)

                    wl_points.append((x_int, 0.0))

        # Sort by X
        wl_points.sort(key=lambda p: p[0])

        # Save raw points
        if not hasattr(self, "waterline_points"):
            self.waterline_points = {}
        self.waterline_points[z] = wl_points

        return wl_points

    def build_smooth_waterline(self, z, steps=20):
        raw = self.calculate_waterline_points(z)

        if len(raw) < 2:
            return raw

        smooth = self.generate_hermite_waterline(raw, steps)
        return smooth
    

    #---------------------------------------------
    #Draw Centerline
    #---------------------------------------------
    def hermite_segment(self, p0, p1, t0, t1, samples=32):
        curve = []
        for i in range(samples+1):
            t = i / samples
            h00 = 2*t*t*t - 3*t*t + 1
            h10 = t*t*t - 2*t*t + t
            h01 = -2*t*t*t + 3*t*t
            h11 = t*t*t - t*t

            x = h00*p0[0] + h10*t0[0] + h01*p1[0] + h11*t1[0]
            z = h00*p0[1] + h10*t0[1] + h01*p1[1] + h11*t1[1]
            curve.append((x, z))
        return curve

    # ===========================
    # Spline For Centerline
    # ===========================
    def hermite_segment(self, p0, p1, t0, t1, samples=32):
        curve = []
        for i in range(samples+1):
            t = i / samples
            h00 = 2*t**3 - 3*t**2 + 1
            h10 = t**3 - 2*t**2 + t
            h01 = -2*t**3 + 3*t**2
            h11 = t**3 - t**2

            x = h00*p0[0] + h10*t0[0] + h01*p1[0] + h11*t1[0]
            z = h00*p0[1] + h10*t0[1] + h01*p1[1] + h11*t1[1]

            curve.append((x,z))
        return curve

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
    

    #---------------------------------------------
    # === Draw Buttock Lines ===
    #---------------------------------------------
    def add_buttockline(self):
        """Add a new buttock line (Y constant plane)"""
        y = simpledialog.askfloat("Add Buttock Line", "Enter Y level (transverse position):")
        if y is None:
            return

        if y in getattr(self, "buttocklines", []):
            messagebox.showinfo("Info", f"Buttock line at Y={y} already exists.")
            return

        self.save_state()

        if not hasattr(self, "buttocklines"):
            self.buttocklines = []
        self.buttocklines.append(y)
        self.buttocklines.sort()

        self.calculate_buttockline_points(y)
        self.draw_all()

    def calculate_buttockline_points(self, y):
        bl_points = []

        # === Intersection with each station  ===
        for x in self.station_order:
            pts = self.stations[x]
            for i in range(len(pts) - 1):
                p1 = pts[i]
                p2 = pts[i + 1]
                y1, y2 = p1[1], p2[1]

                if (y1 - y) * (y2 - y) <= 0 and y1 != y2:
                    t = (y - y1) / (y2 - y1)
                    x_interp = p1[0] + t * (p2[0] - p1[0])
                    z_interp = p1[2] + t * (p2[2] - p1[2])
                    bl_points.append((x_interp, z_interp))
                    
        if hasattr(self, "waterline_points"):
            for z, wl_pts in self.waterline_points.items():
                if len(wl_pts) < 2:
                    continue

                for (x1, y1), (x2, y2) in zip(wl_pts[:-1], wl_pts[1:]):
                    if (y1 <= y < y2) or (y2 <= y < y1):
                        t = (y - y1) / (y2 - y1)
                        x_i = x1 + t * (x2 - x1)
                        bl_points.append((x_i, z))


        bl_points = list(set(bl_points))   
        bl_points.sort(key=lambda p: (p[0], p[1]))


        # Save to dict
        if not hasattr(self, "buttockline_points"):
            self.buttockline_points = {}
        self.buttockline_points[y] = bl_points

    def update_buttocklines(self):
        """Update semua buttock line berdasarkan data terbaru"""
        if not hasattr(self, "buttocklines") or not self.buttocklines:
            return

        if not hasattr(self, "buttockline_points"):
            self.buttockline_points = {}

        for y_level in self.buttocklines:
            self.calculate_buttockline_points(y_level)

    def refresh_buttocklines(self):
        """Refresh buttock lines"""
        if not hasattr(self, "buttocklines") or not self.buttocklines:
            messagebox.showinfo("Info", "No buttock lines to refresh.")
            return

        self.save_state()
        self.update_buttocklines()
        self.draw_all()
        messagebox.showinfo("Refreshed", "All buttock lines have been updated.")