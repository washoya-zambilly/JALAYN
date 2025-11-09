class CanvasDrawer:
    def draw_viewport(self, origin_x, origin_y, proj_func, title, target_canvas=None, scale=None, pan=None):
        canvas = target_canvas if target_canvas else self.canvas

        # Set scale dan pan
        if scale is None:
            if title == "Front View (Y-Z)":
                scale = self.front_scale 
            elif title == "Side View (X-Z)":
                scale = self.side_scale 
            elif title == "Top View (X-Y)":
                scale = self.top_scale 
            else :
                scale = self.scale

        if pan is None:
            if title == "Front View (Y-Z)":
                pan_x, pan_y = self.view_pan_front
            elif title == "Side View (X-Z)":
                pan_x, pan_y = self.view_pan_side
            elif title == "Top View (X-Y)":
                pan_x, pan_y = self.view_pan_top
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
        

        # === Centerline & Baseline (clipping) ===
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

        # === centerline buttock (Y=0) ===
        if title == "Side View (X-Z)" and hasattr(self, "centerline_points") and len(self.centerline_points) > 1:
            coords = []
            # limit side view
            left_s = cx - w // 2
            right_s = cx + w // 2
            top_s = cy - h // 2
            bottom_s = cy + h // 2

            last_valid = None
            for x, z in self.centerline_points:
                sx = cx + x * scale + pan_x
                sy = cy - z * scale + pan_y

                # skip if in the outside
                if sx < left_s or sx > right_s or sy < top_s or sy > bottom_s:
                    last_valid = None
                    continue

                if last_valid:
                    canvas.create_line(last_valid[0], last_valid[1], sx, sy, fill="blue", width=2, smooth=True)
                last_valid = (sx, sy)

            # draw point
            for (x, z) in self.centerline_points:
                sx = cx + x * scale + pan_x
                sy = cy - z * scale + pan_y
                if left_s <= sx <= right_s and top_s <= sy <= bottom_s:
                    r = 5
                    canvas.create_oval(sx - r, sy - r, sx + r, sy + r, fill="blue")


        # draw station and point (with clipping)
        for x in self.station_order:
            pts = self.stations.get(x, [])
            if not pts:
                continue
            proj_pts = []
            for px, py, pz in pts:
                sx, sy = proj_func(px, py, pz)
                #if title == "Front View (Y-Z)":
                sx = cx + sx * scale + pan_x
                sy = cy - sy * scale + pan_y

                # Clipping
                sx = max(left, min(right, sx))
                sy = max(top, min(bottom, sy))
                proj_pts.append((sx, sy))

            # Draw lines
            if len(proj_pts) > 1:
                coords = []
                for sx, sy in proj_pts:
                    coords.extend([sx, sy])
                is_selected = (self.selected_station==x)
                use_spline = self.station_spline.get(x, True)  # mode spline
                canvas.create_line(*coords, fill="red" if is_selected else "black",
                                smooth=use_spline,
                                    width=3 if (title=="Front View (Y-Z)" and self.selected_station==x) else 2)

            # Draw points
            for i, (sx, sy) in enumerate(proj_pts):
                r = 6
                canvas.create_oval(max(left, sx - r), max(top, sy - r),
                                min(right, sx + r), min(bottom, sy + r),
                                fill="blue", tags=("point", f"point_{x}_{i}"))
                
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
            

        # === draw waterlines ===
        for z in self.waterlines:
            wl_points = self.waterline_points.get(z, [])
            if len(wl_points) < 2:
                continue

            proj_pts = []
            for x, y in wl_points:
                if "Top View" in title:
                    sx, sy = proj_func(x, y, z)
                elif "Front View" in title:
                    sx, sy = proj_func(x, y, z)
                elif "Side View" in title:
                    sx, sy = proj_func(x, y, z)
                elif "Isometric" in title:
                    sx, sy = proj_func(x, y, z)
                else:
                    continue

                #if title == "Front View (Y-Z)":
                sx = cx + sx * scale + pan_x
                sy = cy - sy * scale + pan_y
                # Clipping
                sx = max(left, min(right, sx))
                sy = max(top, min(bottom, sy))
                proj_pts.append((sx, sy))

            coords = []
            for sx, sy in proj_pts:
                coords.extend([sx, sy])
            is_selected = (self.selected_station==x)
            use_spline = self.station_spline.get(x, True)  # mode spline
            canvas.create_line(*coords, fill="green" if is_selected else "black",
                                smooth=use_spline,
                                    width=2, dash=(3,3))

            # name for waterline
            mid_idx = len(proj_pts)//2
            if proj_pts:
                mx, my = proj_pts[mid_idx]
                canvas.create_text(mx, my - 10, text=f"WL z={z:.2f}", fill="green", font=("Arial", 8, "bold"))



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
            

        # draw buttock line in side view
        if self.centerline_points:
            cx, cy = self.offsets['side']
            scale = self.side_scale
            pan_x, pan_y = self.view_pan_side
            w = self.width // 2
            h = self.height // 2
            left = cx - w//2
            right = left + w
            top = cy - h//2
            bottom = top + h

            segments = []
            current_segment = []

            for x, z in self.centerline_points:
                sx = cx + x * scale + pan_x
                sy = cy - z * scale + pan_y

                # if point inside canvas
                if left <= sx <= right and top <= sy <= bottom:
                    current_segment.extend([sx, sy])
                else:
                    # if outside, save
                    if len(current_segment) >= 4:
                        segments.append(current_segment)
                    current_segment = []

            # new segment
            if len(current_segment) >= 4:
                segments.append(current_segment)

            # draw new segment
            for seg in segments:
                self.canvas.create_line(
                    *seg,
                    fill="red",
                    width=2,
                    smooth=self.centerline_spline
                )

            # draw point
            for (x, z) in self.centerline_points:
                sx = cx + x * scale + pan_x
                sy = cy - z * scale + pan_y
                if left <= sx <= right and top <= sy <= bottom:
                    r = 5
                    self.canvas.create_oval(sx - r, sy - r, sx + r, sy + r, fill="red")


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
                    self.canvas.create_line(*coords, fill="cyan", width=1, dash=(3, 2))

        self.update_waterlines()


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

    def draw_spline_side(self, pts2d, color="red"):
        """
        Same as polyline but draw with smooth=True for spline-like curve.
        """
        if not pts2d:
            return

        cx, cy = self.offsets['side']
        scale = self.side_scale
        pan_x, pan_y = self.view_pan_side

        coords = []
        for x_model, z_model in pts2d:
            sx = cx + x_model * scale + pan_x
            sy = cy - z_model * scale + pan_y
            coords.extend([sx, sy])

        if len(coords) >= 6:
            try:
                self.canvas.create_line(*coords, fill=color, width=2, smooth=True, splinesteps=12)
            except TypeError:
                self.canvas.create_line(*coords, fill=color, width=2, smooth=True)
        elif len(coords) >= 4:
            self.canvas.create_line(*coords, fill=color, width=2, smooth=True)

        # draw points
        r = 4
        for i in range(0, len(coords), 2):
            sx = coords[i]
            sy = coords[i+1]
            self.canvas.create_oval(sx - r, sy - r, sx + r, sy + r, fill=color, outline="")

    def draw_polyline_side(self, pts2d, color="red"):
        """
        pts2d : list of (x_model, z_model) OR list of projected (x,z) pairs.
        This function maps model coords -> canvas coords for the Side viewport,
        then draws a polyline and markers.
        """
        if not pts2d:
            return

        # Side viewport center & transforms
        cx, cy = self.offsets['side']
        scale = self.side_scale
        pan_x, pan_y = self.view_pan_side

        # Build flattened coords
        coords = []
        for x_model, z_model in pts2d:
            sx = cx + x_model * scale + pan_x
            sy = cy - z_model * scale + pan_y
            coords.extend([sx, sy])

        # Draw polyline and points
        if len(coords) >= 4:
            try:
                self.canvas.create_line(*coords, fill=color, width=2, smooth=False)
            except Exception:
                # fallback safe draw
                self.canvas.create_line(*coords, fill=color, width=2)

        # draw points
        r = 4
        for i in range(0, len(coords), 2):
            sx = coords[i]
            sy = coords[i+1]
            self.canvas.create_oval(sx - r, sy - r, sx + r, sy + r, fill=color, outline="")