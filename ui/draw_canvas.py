#drawcanvas.py
class CanvasDrawer:
    def __init__(self):
        self.station_visibility = {}  # ← default
        self.iso_scale = 50
        self.view_pan_iso = [0, 0]
        self.point_angles = {}       # key = (station, index) → angle in degrees
        self.point_strength = {}     # key = (station, index) → tangent strength
        self.station_spline = {}     # key = station → True/False for spline on/off

    def angle_to_tangent(self, angle_deg, strength=1.0):
        import math
        rad = math.radians(angle_deg)
        return (math.cos(rad) * strength, math.sin(rad) * strength)


    def hermite(self, p0, p1, m0, m1, t):
        """Cubic Hermite interpolation."""
        h00 = 2*t**3 - 3*t**2 + 1
        h10 = t**3 - 2*t**2 + t
        h01 = -2*t**3 + 3*t**2
        h11 = t**3 - t**2
        return (
            h00*p0[0] + h10*m0[0] + h01*p1[0] + h11*m1[0],
            h00*p0[1] + h10*m0[1] + h01*p1[1] + h11*m1[1]
        )
    
    def generate_hermite_points(self, station, points, steps=20):
        """Generate a polyline using Hermite cubic spline."""
        if len(points) < 2:
            return points

        result = []
        n = len(points)

        # compute tangents 
        tangents = []
        for i in range(n):
            key = (station, i) 
            self.station_spline[key] = True

            if key in self.point_angles:
                angle = self.point_angles[key]
                strength = self.point_strength.get(key, 30)  
                m = self.angle_to_tangent(angle, strength)

            else:
                # fallback normal Catmull-Rom
                if i == 0:
                    m = (points[1][0] - points[0][0], points[1][1] - points[0][1])
                elif i == n - 1:
                    m = (points[-1][0] - points[-2][0], points[-1][1] - points[-2][1])
                else:
                    m = (
                        (points[i+1][0] - points[i-1][0]) * 0.5,
                        (points[i+1][1] - points[i-1][1]) * 0.5
                    )
            tangents.append(m)

        # build Hermite segments
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

    def generate_hermite_points_generic(self, pts, steps=20):
        if len(pts) < 2:
            return pts

        smooth = []
        n = len(pts)

        for i in range(n - 1):
            p0 = pts[i - 1] if i > 0 else pts[i]
            p1 = pts[i]
            p2 = pts[i + 1]
            p3 = pts[i + 2] if i + 2 < n else pts[i + 1]

            for t in range(steps):
                t /= steps
                t2 = t * t
                t3 = t2 * t

                x = 0.5 * (
                    (2 * p1[0]) +
                    (-p0[0] + p2[0]) * t +
                    (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t2 +
                    (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t3
                )

                y = 0.5 * (
                    (2 * p1[1]) +
                    (-p0[1] + p2[1]) * t +
                    (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t2 +
                    (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t3
                )

                smooth.append((x, y))

        smooth.append(pts[-1])
        return smooth


    def draw_viewport(self, origin_x, origin_y, proj_func, title, target_canvas=None, scale=None, pan=None):
        canvas = target_canvas if target_canvas else self.canvas

        # Set scale and pan
        if scale is None:
            if title == "Front View (Y-Z)":
                scale = self.front_scale 
            elif title == "Side View (X-Z)":
                scale = self.side_scale 
            elif title == "Top View (X-Y)":
                scale = self.top_scale 
            elif title == "Isometric View":
                scale = self.iso_scale
            else :
                scale = self.scale

        if pan is None:
            if title == "Front View (Y-Z)":
                pan_x, pan_y = self.view_pan_front
            elif title == "Side View (X-Z)":
                pan_x, pan_y = self.view_pan_side
            elif title == "Top View (X-Y)":
                pan_x, pan_y = self.view_pan_top
            elif title == "Isometric View":
                pan_x, pan_y = self.view_pan_iso
            else:
                pan_x, pan_y = 0, 0
        else:
            pan_x, pan_y = pan
    
        # Calculate divider
        w = self.divider_x if origin_x < self.width // 2 else self.width - self.divider_x
        h = self.divider_y if origin_y < self.height // 2 else self.height - self.divider_y
        left = origin_x - w//2
        top = origin_y - h//2
        right = left + w
        bottom = top + h

        # Viewport background
        canvas.create_rectangle(left, top, right, bottom, fill="#f0f0f0", tags="background")
        canvas.tag_lower("background")

        canvas.create_text(left+10, top+10, text=title, anchor="nw", font=("Arial", 14, "bold"))

        # Center viewport coordinate
        cx, cy = origin_x, origin_y

        # Axis 
        canvas.create_line(max(left, cx - w//2 + pan_x), cy + pan_y,
                        min(right, cx + w//2 + pan_x), cy + pan_y,
                        fill="gray", dash=(4,2))
        canvas.create_line(cx + pan_x, max(top, cy - h//2 + pan_y),
                        cx + pan_x, min(bottom, cy + h//2 + pan_y),
                        fill="gray", dash=(4,2))
        

        # === Guideline For Centerline & Baseline ===
        if title == "Front View (Y-Z)":
            # Vertical centerline
            cx_line = max(left, min(right, cx + pan_x))
            top_line = top        
            bottom_line = bottom 
            canvas.create_line(int(cx_line), int(top_line), int(cx_line), int(bottom_line), fill="green", width=2, dash=(4,2))
            text_cx = min(cx_line + 5, right - 2)
            text_cy = min(top + 15, bottom - 2)
            canvas.create_text(text_cx, text_cy, text="Centerline", fill="green", font=("Arial", 8), anchor="nw")
            # Horizontal baseline
            cy_line = max(top, min(bottom, cy + pan_y))
            right_line = right
            left_line = left
            canvas.create_line(int(left_line), int(cy_line), int(right_line), int(cy_line), fill="brown", width=2, dash=(4,2))
            text_cx = max(left, min(cx + 5 + pan_x, right - 2))
            text_cy = max(top, min(cy_line + 5, bottom - 2))
            canvas.create_text(text_cx, text_cy, text="Baseline", fill="brown", font=("Arial", 8), anchor="nw")

        if title == "Side View (X-Z)":
            # baseline / Z = 0
            scale = self.side_scale  
            pan_x, pan_y = self.view_pan_side  
            
            y0 = cy + pan_y - 0 * scale  # Z=0
            cy_line = max(top, min(bottom, y0))

            # x position
            if self.station_order:
                x_min = min(self.station_order)
                x_max = max(self.station_order)
            else:
                x_min = -10  
                x_max = 10

            left_line = max(left, cx + pan_x + x_min * scale)
            right_line = min(right, cx + pan_x + x_max * scale)

            # baseline
            canvas.create_line(int(left_line), int(cy_line), int(right_line), int(cy_line),
                            fill="brown", width=2, dash=(4,2))

            #  text "Baseline"
            text_cx = max(left, min(cx + 5 + pan_x, right - 2))
            text_cy = max(top, min(cy_line + 5, bottom - 2))
            canvas.create_text(text_cx, text_cy, text="Baseline", fill="brown",
                            font=("Arial", 8), anchor="nw")
            

        #---------------------------------------------------------
        # STATION
        #--------------------------------------------------------
        for x in self.station_order:
            if not self.station_visibility.get(x, True):
                continue

            pts = self.stations.get(x, [])
            if not pts:
                continue

            proj_pts = []
            for px, py, pz in pts:
                sx, sy = proj_func(px, py, pz)

                # Apply scaling and panning
                sx = cx + sx * scale + pan_x
                sy = cy - sy * scale + pan_y

                # Clipping
                sx = max(left, min(right, sx))
                sy = max(top, min(bottom, sy))

                proj_pts.append((sx, sy))


            # ------------------------------------------------------
            #            DRAW CURVE 
            # ------------------------------------------------------
            # Draw lines 
            if len(proj_pts) > 1:
                is_selected = (self.selected_station == x)
                use_spline = self.station_spline.get(x, True)

                # if spline mode 
                if use_spline:
                    smooth_pts = self.generate_hermite_points(x, proj_pts, steps=20)
                else:
                    smooth_pts = proj_pts

                coords = []
                for sx, sy in smooth_pts:
                    coords.extend([sx, sy])

                canvas.create_line(
                    *coords,
                    fill="red" if is_selected else "black",
                    width=3 if (title=="Front View (Y-Z)" and is_selected) else 2
                )



            # ------------------------------------------------------
            #                DRAW POINTS 
            # ------------------------------------------------------
            for i, (sx, sy) in enumerate(proj_pts):
                r = 5

                # Modern point style: blue circle with outline
                canvas.create_oval(
                    max(left, sx - r), max(top, sy - r),
                    min(right, sx + r), min(bottom, sy + r),
                    fill="#274157",               # bright cyan
                    outline="#ffffff",            # white border
                    width=1.3,
                    tags=("point", f"point_{x}_{i}")
                )
                
            # === curve name view ===
            if title == "Front View (Y-Z)":
                name = self.station_names.get(x)
                if name and proj_pts:
                    mid_idx = len(proj_pts) // 2
                    p1 = proj_pts[mid_idx - 1]
                    p2 = proj_pts[mid_idx]
                    mid_sx = (p1[0] + p2[0]) / 2
                    mid_sy = (p1[1] + p2[1]) / 2

                    canvas.create_text(mid_sx, mid_sy - 10, text=name, fill="blue", font=("Arial", 10, "bold"))

            # Draw vertical lines for station in top and side view
            if title == "Top View (X-Y)" or title == "Side View (X-Z)":
                sx = cx + x * scale + pan_x
                sx = max(left, min(right, sx))
                canvas.create_line(sx, top, sx, bottom, fill="red", dash=(2,2))
            

        # === Draw waterlines ===
        for z in self.waterlines:
            wl_points = self.waterline_points.get(z, [])
            if len(wl_points) < 2:
                continue

            # Projected points container
            proj = []

            # === Projection ===
            for (x, y) in wl_points:
                sx, sy = proj_func(x, y, z)

                # Transform to screen
                sx = cx + sx * scale + pan_x
                sy = cy - sy * scale + pan_y

                # Skip if outside viewport (soft clipping)
                if sx < left-20 or sx > right+20 or sy < top-20 or sy > bottom+20:
                    continue

                proj.append((sx, sy))

            if len(proj) < 2:
                continue


            # === APPLY SPLINE ===
            smooth_proj = self.generate_hermite_points_generic(proj, steps=20)


            # Flatten list for canvas.create_line
            coords = [c for pt in smooth_proj for c in pt]

            # === Modern line style ===
            canvas.create_line(
                *coords,
                fill="#1f78b4",        
                width=2,
                dash=(4, 2),          
                capstyle="round",
                joinstyle="round"
            )

            # === Label waterline  ===
            mid = len(smooth_proj) // 2
            mx, my = smooth_proj[mid]

            canvas.create_text(
                mx,
                my - 8,
                text=f"WL {z:.2f}",
                fill="#1f78b4",
                font=("Segoe UI", 8, "bold")
            )


    #DRAW ALL 
    def draw_all(self):
        self.canvas.delete("all")
        w2 = self.width // 2
        h2 = self.height // 2

        self.offsets['top'] = (self.divider_x // 2, self.divider_y // 2)
        self.offsets['front'] = ((self.divider_x + self.width) // 2, self.divider_y // 2)
        self.offsets['side'] = (self.divider_x // 2, (self.divider_y + self.height) // 2)
        self.offsets['iso'] = ((self.divider_x + self.width) // 2, (self.divider_y + self.height) // 2)

        self.draw_viewport(self.divider_x // 2, self.divider_y // 2, self.project_top, "Top View (X-Y)")
        self.draw_viewport((self.divider_x + self.width) // 2, self.divider_y // 2, self.project_front, "Front View (Y-Z)")
        self.draw_viewport(self.divider_x // 2, (self.divider_y + self.height) // 2, self.project_side, "Side View (X-Z)")
        self.draw_viewport((self.divider_x + self.width) // 2, (self.divider_y + self.height) // 2, self.project_iso, "Isometric View")


        self.canvas.create_line(self.divider_x, 0, self.divider_x, self.height, fill="black", width=2, tags="divider_v")
        self.canvas.create_line(0, self.divider_y, self.width, self.divider_y, fill="black", width=2, tags="divider_h")


        
        # === guidelines with Ship Dimensions ===
        if hasattr(self, "ship_dimensions"):
            Lpp = self.ship_dimensions.get("Lpp", 0)
            B = self.ship_dimensions.get("Bmax", 0)
            D = self.ship_dimensions.get("Draft", 0)

            # === SIDE VIEW (X-Z) ===
            cx_s, cy_s = self.offsets['side']
            scale = self.side_scale
            pan_x, pan_y = self.view_pan_side
            w = self.width // 2
            h = self.height // 2
            left_s = cx_s - w // 2
            right_s = left_s + w
            top_s = cy_s - h // 2
            bottom_s = top_s + h

            x0 = cx_s + 0 * scale + pan_x
            x1 = cx_s + Lpp * scale + pan_x
            z0 = cy_s - 0 * scale + pan_y
            zD = cy_s - D * scale + pan_y

            # Clamping helper
            def clamp(val, minv, maxv):
                return max(minv, min(maxv, val))

            # AP and FP guideline (X=0 dan X=Lpp)
            if left_s < x0 < right_s:
                y1 = clamp(top_s, top_s, bottom_s)
                y2 = clamp(bottom_s, top_s, bottom_s)
                self.canvas.create_line(x0, top_s, x0, bottom_s, fill="gray", dash=(4, 2))
                self.canvas.create_text(x0 + 30, top_s + 20, text="X=0 (AP)", fill="gray", font=("Arial", 9, "italic"))
            
            if left_s < x1 < right_s:
                y1 = clamp(top_s, top_s, bottom_s)
                y2 = clamp(bottom_s, top_s, bottom_s)
                self.canvas.create_line(x1, top_s, x1, bottom_s, fill="gray", dash=(4, 2))
                self.canvas.create_text(x1 - 30, top_s + 20, text=f"X=FP={Lpp} m", fill="gray", font=("Arial", 9, "italic"))
            
            
            # baseline and draft guideline
            if top_s < z0 < bottom_s:
                self.canvas.create_line(left_s, z0, right_s, z0, fill="gray", dash=(4, 2))
                self.canvas.create_text(right_s - 50, z0 - 10, text="Baseline (Z=0)", fill="gray", font=("Arial", 9, "italic"))
            if top_s < zD < bottom_s:
                self.canvas.create_line(left_s, zD, right_s, zD, fill="gray", dash=(4, 2))
                self.canvas.create_text(right_s - 50, zD - 10, text=f"Draft (Z={D} m)", fill="gray", font=("Arial", 9, "italic"))

            # === FRONT VIEW (Y-Z) ===
            cx_f, cy_f = self.offsets['front']
            scale = self.front_scale
            pan_x, pan_y = self.view_pan_front
            left_f = cx_f - w // 2
            right_f = left_f + w
            top_f = cy_f - h // 2
            bottom_f = top_f + h

            yL = cx_f - (B / 2) * scale + pan_x
            yR = cx_f + (B / 2) * scale + pan_x
            z0 = cy_f - 0 * scale + pan_y
            zD = cy_f - D * scale + pan_y

            # breadth guideline (Y = ±B/2)
            if left_f < yL < right_f:
                self.canvas.create_line(yL, top_f, yL, bottom_f, fill="gray", dash=(4, 2))
                self.canvas.create_text(yL + 20, top_f + 20, text=f"-B/2={-B/2:.1f} m", fill="gray", font=("Arial", 9, "italic"))

            if left_f < yR < right_f:
                self.canvas.create_line(yR, top_f, yR, bottom_f, fill="gray", dash=(4, 2))
                self.canvas.create_text(yR - 40, top_f + 20, text=f"+B/2={B/2:.1f} m", fill="gray", font=("Arial", 9, "italic"))

            # === Baseline & Draft (Front View) ===
            if top_f < z0 < bottom_f:
                self.canvas.create_line(left_f, z0, right_f, z0, fill="gray", dash=(4, 2))
                self.canvas.create_text(right_f - 60, clamp(z0 - 10, top_f, bottom_f), text="Baseline (Z=0)", fill="gray", font=("Arial", 9, "italic"))

            if top_f < zD < bottom_f:
                self.canvas.create_line(left_f, zD, right_f, zD, fill="gray", dash=(4, 2))
                self.canvas.create_text(right_f - 60, clamp(zD - 10, top_f, bottom_f), text=f"Draft (Z={D} m)", fill="gray", font=("Arial", 9, "italic"))

            # === TOP VIEW (X-Y) ===
            cx_t, cy_t = self.offsets['top']
            scale = self.top_scale
            pan_x, pan_y = self.view_pan_top
            left_t = cx_t - w // 2
            right_t = left_t + w
            top_t = cy_t - h // 2
            bottom_t = top_t + h

            x0 = cx_t + 0 * scale + pan_x
            x1 = cx_t + Lpp * scale + pan_x
            yL = cy_t + (B / 2) * scale + pan_y     
            yR = cy_t - (B / 2) * scale + pan_y

            # breadth guideline in top view (±B/2)
            if left_t < x0 < right_t:
                # left (Y = +B/2)
                if top_t < yL < bottom_t:
                    self.canvas.create_line(left_t, yL, right_t, yL, fill="gray", dash=(4, 2))
                    self.canvas.create_text(right_t - 60, clamp(yL - 10, top_t, bottom_t),
                                            text=f"+B/2={B/2:.1f} m", fill="gray", font=("Arial", 9, "italic"))
                # right (Y = -B/2)
                if top_t < yR < bottom_t:
                    self.canvas.create_line(left_t, yR, right_t, yR, fill="gray", dash=(4, 2))
                    self.canvas.create_text(right_t - 60, clamp(yR - 10, top_t, bottom_t),
                                            text=f"-B/2={-B/2:.1f} m", fill="gray", font=("Arial", 9, "italic"))
        #---------------------------------------------------------------------------------------------


            # ===========================
            # DRAW CENTERLINE 
            # ===========================
            if getattr(self, "centerline_points", None):
                cx, cy = self.offsets['side']
                scale = self.side_scale
                pan_x, pan_y = self.view_pan_side
                w = self.width // 2
                h = self.height // 2
                left, right = cx - w//2, cx + w//2
                top, bottom = cy - h//2, cy + h//2

                if getattr(self, "centerline_points", None) and len(self.centerline_points) >= 2:
                    cx, cy = self.offsets['side']
                    scale = self.side_scale
                    pan_x, pan_y = self.view_pan_side

                    # --- spline ---
                    smooth_pts = self.generate_hermite_points("centerline", self.centerline_points, steps=30)

                    # Convert to canvas coordinates
                    coords = []
                    for x, z in smooth_pts:
                        sx = cx + x*scale + pan_x
                        sy = cy - z*scale + pan_y

                        # Clipping
                        sx = max(left, min(right, sx))
                        sy = max(top, min(bottom, sy))

                        coords.extend([sx, sy])

                    if len(coords) >= 4:
                    # --- Glow effect  ---
                        for w in range(6, 2, -2):
                            self.canvas.create_line(*coords, fill="#ff9999", width=w, smooth=True, splinesteps=100)

                    # --- Line ---
                    self.canvas.create_line(*coords, fill="#ff0000", width=1, smooth=True, splinesteps=100)

                # --- Draw control points  ---
                r = 5
                for x, z in self.centerline_points:
                    sx = cx + x*scale + pan_x
                    sy = cy - z*scale + pan_y
                    if left <= sx <= right and top <= sy <= bottom:
                        # Outer circle (glow)
                        self.canvas.create_oval(sx-r-1, sy-r-1, sx+r+1, sy+r+1, outline="#ff9999", width=1)
                        # Inner circle (main point)
                        self.canvas.create_oval(sx-r, sy-r, sx+r, sy+r, fill="#ff0000", outline="#ff5555", width=1)
            #--------------------------------------------------------


        # === Draw Waterline in Side View (XZ) ===
        if hasattr(self, "waterline_points"):
            cx, cy = self.offsets['side']
            scale = self.side_scale
            pan_x, pan_y = self.view_pan_side
            w = self.width // 2
            h = self.height // 2
            left = cx - w//2
            right = left + w
            top = cy - h//2
            bottom = top + h

            for z_level, pts in self.waterline_points.items():
                if not pts:
                    continue
                coords = []
                for x, y in pts:
                    sx = cx + x * scale + pan_x
                    sy = cy - z_level * scale + pan_y  
                    if left <= sx <= right and top <= sy <= bottom:
                        coords.extend([sx, sy])
                if len(coords) >= 4:
                    for w_glow in range(4, 0, -2):
                        self.canvas.create_line(*coords, fill="#166ad1", width=w_glow, smooth=True)
                    self.canvas.create_line(*coords, fill="#166ad1", width=2, smooth=True)

        self.update_waterlines()
        #-----------------------------------------------------


        # === draw buttock lines ===
        if hasattr(self, "buttocklines"):
            # projection 
            title = "Side View (X-Z)"
            if "Side View (X-Z)" in title: 
                proj_func = self.project_side
            elif "Top View (X-Y)" in title:
                proj_func = self.project_top
            elif "Front View (Y-Z)" in title:
                proj_func = self.project_front
            else:
                proj_func = self.project_iso  # fallback (isometric)

            for y in self.buttocklines:
                bl_points = self.buttockline_points.get(y, [])
                if len(bl_points) < 2:
                    continue

                proj_pts = []
                for x, z in bl_points:
                    sx, sy = proj_func(x, y, z)
                    sx = cx + sx * scale + pan_x
                    sy = cy - sy * scale + pan_y
                    proj_pts.append((sx, sy))

                # Clip & draw
                coords = []
                for sx, sy in proj_pts:
                    sx = max(left, min(right, sx))
                    sy = max(top, min(bottom, sy))
                    coords.extend([sx, sy])

                if len(coords) >= 4:
                    self.canvas.create_line(*coords, fill="red", width=2, dash=(3, 3), smooth=True)

                # label
                mid_idx = len(proj_pts)//2
                if proj_pts:
                    mx, my = proj_pts[mid_idx]
                    self.canvas.create_text(mx, my - 10, text=f"BL y={y:.2f}", fill="red", font=("Arial", 8, "bold"))
            #---------------------------------------------------


    #Sinchronize all canvas
    def draw_all_canvases(self):
        self.draw_all()
        for vp in self.additional_canvases:
            vp.draw()

    def on_canvas_resize(self, event):
        self.width = event.width
        self.height = event.height
        self.divider_x = self.width // 2
        self.divider_y = self.height // 2

        self.offsets['top'] = (self.divider_x // 2, self.divider_y // 2)
        self.offsets['front'] = ((self.divider_x + self.width) // 2, self.divider_y // 2)
        self.offsets['side'] = (self.divider_x // 2, (self.divider_y + self.height) // 2)
        self.offsets['iso'] = ((self.divider_x + self.width) // 2, (self.divider_y + self.height) // 2)

        self.draw_all()

    #------For Hide and Show Station in Station List---------
    def hide_station(self, x_vals):
        for x in x_vals:
            self.station_visibility[x] = False
            tag = f"station_{x:.3f}"
            self.canvas.itemconfigure(tag, state="hidden")

    def show_station(self, x_vals):
        for x in x_vals:
            self.station_visibility[x] = True
            tag = f"station_{x:.3f}"
            self.canvas.itemconfigure(tag, state="normal")
    #---------------------------------------------------
    
    def project_point(self, x, y, z):
        # mouse position
        mx, my = self.last_mouse_pos

        # viewport
        cx, cy = None, None
        proj_func = None
        scale = None
        pan_x, pan_y = None, None

        # TOP VIEW 
        if mx < self.divider_x and my < self.divider_y:
            proj_func = self.project_top
            cx, cy = self.offsets['top']
            scale = self.top_scale
            pan_x, pan_y = self.view_pan_top

        # FRONT VIEW 
        elif mx >= self.divider_x and my < self.divider_y:
            proj_func = self.project_front
            cx, cy = self.offsets['front']
            scale = self.front_scale
            pan_x, pan_y = self.view_pan_front

        # SIDE VIEW 
        elif mx < self.divider_x and my >= self.divider_y:
            proj_func = self.project_side
            cx, cy = self.offsets['side']
            scale = self.side_scale
            pan_x, pan_y = self.view_pan_side

        # ISO VIEW 
        else:
            proj_func = self.project_iso
            cx, cy = self.offsets['iso']
            scale = self.iso_scale
            pan_x, pan_y = self.view_pan_iso

     # projection
        px, py = proj_func(x, y, z)

        # convert
        sx = cx + px * scale + pan_x
        sy = cy - py * scale + pan_y
        return sx, sy

