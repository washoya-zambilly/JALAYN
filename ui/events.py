from tkinter import simpledialog, messagebox
import math


class EventHandler:
    #zoom by scroll
    def on_mouse_wheel(self, event):
        viewport = self.get_viewport_under_mouse(event.x, event.y)
        if viewport is None:
            return
        
        if viewport == "front":
            old_scale = self.front_scale
        elif viewport == "side":
            old_scale = self.side_scale
        elif viewport == "top":
            old_scale = self.top_scale
        else:
            return


        # Zoom in/out
        if event.num == 5 or event.delta < 0:
            new_scale = old_scale / 1.1
        elif event.num == 4 or event.delta > 0:
            new_scale = old_scale * 1.1
        else:
            return

        # limit the zoom
        new_scale = max(10, min(500, new_scale))

        # Update scale
        if viewport == "front":
            self.front_scale = new_scale
        elif viewport == "side":
            self.side_scale = new_scale
        elif viewport == "top":
            self.top_scale = new_scale

        self.draw_all()
    
    #Pan function
    def on_middle_click(self, event):
        viewport = self.get_viewport_under_mouse(event.x, event.y)
        if viewport is not None:
            self.middle_drag_start = (event.x, event.y, viewport)

    def on_middle_drag(self, event):
        if self.middle_drag_start is None:
            return

        prev_x, prev_y, vp = self.middle_drag_start
        dx = event.x - prev_x
        dy = event.y - prev_y

        if vp == "front":
            pan = self.view_pan_front
        elif vp == "side":
            pan = self.view_pan_side
        elif vp == "top":
            pan = self.view_pan_top
        else:
            return

        pan[0] += dx
        pan[1] += dy

        self.middle_drag_start = (event.x, event.y, vp)
        self.draw_all()

    def on_middle_release(self, event):
        self.middle_drag_start = None


    #Add station in X function
    def add_station(self):
        try:
            x_str = simpledialog.askstring("Add Station", "Input coodinate for (X) station:")
            if x_str is None:
                return
            try:
                x = float(x_str)
            except ValueError:
                messagebox.showerror("Error", f"Invalid number: {x_str}")
                return

            if x in self.stations:
                messagebox.showwarning("Warning", f"Station X={x} already exsist!")
                return
            
            self.stations[x] = []
            self.station_order.append(x)
            self.station_order.sort()
            self.station_spline[x] = True  # default spline off

            # Set new station as active station
            self.current_station_x = x
            self.selected_station = x  
            
            self.update_waterlines()
            self.draw_all()
            
            messagebox.showinfo("Station Added", f"New station created at X={x} and set as active.")

        except Exception as e:
            messagebox.showerror("Error", str(e))


    #Add point using dialog (#deleted)
    def add_point(self):
        if not self.station_order:
            messagebox.showwarning("Warning", "Please add the station or x coordinate")
            return
        x = self.current_station_x

        if x is None:
            messagebox.showwarning("Warning", "No active station. Please select or add a station first.")
            return
        
        try:
            x = float(x)
        except ValueError:
            messagebox.showerror("Error", f"Invalid station coordinate: {x}")
            return

        try:
            y_str = simpledialog.askstring("Add Point", "Input coordinate in y:")
            if y_str is None:
                return
            y = float(y_str)

            z_str = simpledialog.askstring("Add point", "Input coordinate in z:")
            if z_str is None:
                return
            z = float(z_str)

            x = self.current_station_x
            if x not in self.stations:
                messagebox.showerror("Error", f"Station X={x} not found.")
                return
            
            self.stations[x].append( (x,y,z) )
            self.update_waterlines()
            self.draw_all()
        except Exception as e:
            messagebox.showerror("Error", str(e))


    # Mouse helpers
    def is_point_near(self, px, py, x, y, tol=10):
        return abs(px - x) <= tol and abs(py - y) <= tol

    def find_nearest_point_front(self, x, y):
        # Find point in front view near x,y canvas pos, return (station_x, point_index)
        cx, cy = self.offsets['front']
        scale = self.front_scale
        w = self.width // 2
        h = self.height // 2
        left = cx - w//2
        top = cy - h//2

        for station_x in self.station_order:
            pts = self.stations[station_x]
            for i, (px, py3d, pz3d) in enumerate(pts):
                sx, sy = self.project_front(px, py3d, pz3d)
                pan_x, pan_y = self.view_pan_front
                sx = cx + sx * scale + pan_x
                sy = cy - sy * scale + pan_y
                if self.is_point_near(sx, sy, x, y):
                    return station_x, i, sx, sy
        return None, None, None, None

    def find_nearest_line_front(self, x, y):
        # Find line segment near x,y canvas pos in Front View, return (station_x, index_of_segment)
        cx, cy = self.offsets['front']
        scale = self.front_scale
        w = self.width // 2
        h = self.height // 2

        def point_line_dist(px, py, x1, y1, x2, y2):
            # Distance from point to line segment
            A = px - x1
            B = py - y1
            C = x2 - x1
            D = y2 - y1

            dot = A * C + B * D
            len_sq = C*C + D*D
            param = dot / len_sq if len_sq != 0 else -1

            if param < 0:
                xx, yy = x1, y1
            elif param > 1:
                xx, yy = x2, y2
            else:
                xx = x1 + param * C
                yy = y1 + param * D

            dx = px - xx
            dy = py - yy
            return math.sqrt(dx*dx + dy*dy), xx, yy

        for station_x in self.station_order:
            pts = self.stations[station_x]
            if len(pts) < 2:
                continue
            for i in range(len(pts)-1):
                p1 = pts[i]
                p2 = pts[i+1]
                sx1, sy1 = self.project_front(*p1)
                sx2, sy2 = self.project_front(*p2)
                pan_x, pan_y = self.view_pan_front
                sx1 = cx + sx1 * scale + pan_x
                sy1 = cy - sy1 * scale + pan_y
                sx2 = cx + sx2 * scale + pan_x
                sy2 = cy - sy2 * scale + pan_y
                dist, xx, yy = point_line_dist(x, y, sx1, sy1, sx2, sy2)
                if dist < 8:
                    return station_x, i, (xx, yy)
        return None, None, None


    # Mouse event handlers
    #left click
    def on_left_click(self, event):
        margin = 5
        if abs(event.x - self.divider_x) < margin:
            self.dragging_divider = 'vertical'
            return
        elif abs(event.y - self.divider_y) < margin:
            self.dragging_divider = 'horizontal'
            return
        # Left click only used in front view area to select curve or start drag point

        # === FRONT VIEW (Y-Z) ===
        cx_f, cy_f = self.offsets['front']
        w = self.width // 2
        h = self.height // 2
        left_f, top_f = cx_f - w//2, cy_f - h//2
        right_f, bottom_f = left_f + w, top_f + h

        # === SIDE VIEW (X-Z) ===
        cx_s, cy_s = self.offsets['side']
        left_s, top_s = cx_s - w//2, cy_s - h//2
        right_s, bottom_s = left_s + w, top_s + h

        if left_s <= event.x <= right_s and top_s <= event.y <= bottom_s:
            if not hasattr(self, "centerline_points") or not self.centerline_points:
                return

            cx, cy = cx_s, cy_s
            scale = self.side_scale
            pan_x, pan_y = self.view_pan_side

            for i, (px, pz) in enumerate(self.centerline_points):
                sx = cx + px * scale + pan_x
                sy = cy - pz * scale + pan_y
                if abs(sx - event.x) <= 8 and abs(sy - event.y) <= 8:
                    
                    self.drag_data['centerline_index'] = i
                    self.drag_data['start_x'] = event.x
                    self.drag_data['start_y'] = event.y
                    return

            return  

        #  FRONT VIEW 
        if not (left_f <= event.x <= right_f and top_f <= event.y <= bottom_f):
            return
        station_x, pidx, sx, sy = self.find_nearest_point_front(event.x, event.y)
        if station_x is not None:
            # Start dragging this point
            self.drag_data['station_x'] = station_x
            self.drag_data['point_index'] = pidx
            self.drag_data['start_x'] = event.x
            self.drag_data['start_y'] = event.y
            self.selected_station = station_x
            self.current_station_x = station_x 
            self.draw_all()
            return

        # Else check if clicked near line segment
        station_x, seg_idx, _ = self.find_nearest_line_front(event.x, event.y)
        if station_x is not None:
            self.selected_station = station_x
            self.current_station_x = station_x 
            self.draw_all()
            return

         # If clicked on empty space in front view, clear selection
        self.selected_station = None
        self.draw_all()


    
    def on_left_drag(self, event):

        if self.dragging_divider == 'vertical':
            self.divider_x = max(100, min(self.width - 100, event.x))
            self.draw_all()
            return
        elif self.dragging_divider == 'horizontal':
            self.divider_y = max(100, min(self.height - 100, event.y))
            self.draw_all()
            return
        
        # === DRAG CENTERLINE IN SIDE VIEW ===
        if 'centerline_index' in self.drag_data and self.drag_data['centerline_index'] is not None:
            idx = self.drag_data['centerline_index']
            cx, cy = self.offsets['side']
            scale = self.side_scale
            pan_x, pan_y = self.view_pan_side

            x = (event.x - cx - pan_x) / scale
            z = (cy - event.y + pan_y) / scale
            self.centerline_points[idx] = (x, z)
            
            self.draw_all()
            return
        
        # === DRAG POINT IN FRONT VIEW ===
        if self.drag_data['station_x'] is None:
            return
        station_x = self.drag_data['station_x']
        pidx = self.drag_data['point_index']
        if station_x not in self.stations:
            return
        pts = self.stations[station_x]
        if pidx < 0 or pidx >= len(pts):
            return

        # Convert canvas pos to y,z coords in front view
        cx, cy = self.offsets['front']
        scale = self.front_scale

        # canvas coords -> projected y,z
        pan_x, pan_y = self.view_pan_front
        proj_y = (event.x - cx - pan_x) / scale
        proj_z = (cy - event.y + pan_y) / scale

        # Update point, keep x fixed (station_x)
        self.stations[station_x][pidx] = (station_x, proj_y, proj_z)
        self.draw_all()


    #left click release
    def on_left_release(self, event):
        self.drag_data['station_x'] = None
        self.drag_data['point_index'] = None
        self.drag_data.pop('centerline_index', None)
        self.dragging_divider = None

    #right click
    def on_right_click(self, event):
        # Hitung ulang batas tiap viewport
        cx_f, cy_f = self.offsets['front']
        cx_s, cy_s = self.offsets['side']
        w = self.divider_x
        h = self.divider_y

        # FRONT VIEW (Y-Z)
        left_f = cx_f - w // 2
        right_f = left_f + w
        top_f = cy_f - h // 2
        bottom_f = top_f + h

        # SIDE VIEW (X-Z)
        left_s = cx_s - w // 2
        right_s = left_s + w
        top_s = cy_s - h // 2
        bottom_s = top_s + h

        
        if left_s <= event.x <= right_s and top_s <= event.y <= bottom_s:
            
            self.right_click_pos = (event.x, event.y)
            self.menu_side.post(event.x_root, event.y_root)
            return

        # --- IF RIGHT CLICK IN FRONT VIEW (Y-Z) ---
        if left_f <= event.x <= right_f and top_f <= event.y <= bottom_f:
            self.right_click_pos = (event.x, event.y)
            self.right_click_station = None
            self.right_click_point_index = None
            self.right_click_line_index = None

            # Try find point near click
            station_x, pidx, sx, sy = self.find_nearest_point_front(event.x, event.y)
            if station_x is not None:
                self.right_click_station = station_x
                self.right_click_point_index = pidx
                self.menu.entryconfig("Delete Point", state="normal")
            else:
                self.right_click_station = getattr(self, "current_station_x", None)
                self.right_click_point_index = None
                self.menu.entryconfig("Delete Point", state="disabled")

            # Try find line near click
            station_x, seg_idx, _ = self.find_nearest_line_front(event.x, event.y)
            if station_x is not None:
                self.right_click_station = station_x
                self.right_click_line_index = seg_idx
                self.menu.entryconfig("Add Point Between", state="normal")
            else:
                self.right_click_line_index = None
                self.menu.entryconfig("Add Point Between", state="disabled")

            # Always enable "Add Point"
            self.menu.entryconfig("Add Point", state="normal")

            self.menu.post(event.x_root, event.y_root)
            return
        

    #zoom function
    def get_viewport_under_mouse(self, x, y):
        w = self.width // 2
        h = self.height // 2

        for vp, (cx, cy) in self.offsets.items():
            left, top = cx - w//2, cy - h//2
            right, bottom = cx + w//2, cy + h//2
            if left <= x <= right and top <= y <= bottom:
                return vp
        return None
    
    
    # Context menu commands
    #menu add point when right click
    def menu_add_point(self):
        self.save_state()  
        canvas_x, canvas_y = self.right_click_pos
        cx, cy = self.offsets['front']
        scale = self.front_scale

        # Convert canvas to y,z
        pan_x, pan_y = self.view_pan_front
        proj_y = (canvas_x - cx - pan_x) / scale
        proj_z = (cy - canvas_y + pan_y) / scale

        # station target:
        if self.right_click_station is not None:
            station_x = self.right_click_station
        elif getattr(self, "current_station_x", None) is not None:
            station_x = self.current_station_x
        elif self.station_order:
            station_x = self.station_order[-1]
        else:
            messagebox.showwarning("Warning", "No station exist.")
            return

        # ensure the station
        if station_x not in self.stations:
            messagebox.showerror("Error", f"Station X={station_x} not found.")
            return

        self.stations[station_x].append((station_x, proj_y, proj_z))
        self.update_waterlines()
        self.draw_all()

    #menu delete point using right click
    def menu_delete_point(self):
        if self.right_click_station is None or self.right_click_point_index is None:
            return
        self.save_state()  
        station_x = self.right_click_station
        pidx = self.right_click_point_index
        pts = self.stations[station_x]
        if 0 <= pidx < len(pts):
            pts.pop(pidx)
            self.draw_all()
    
    #Menu add point between two points in a curve using right click
    def menu_add_point_middle(self):
        if self.right_click_station is None or self.right_click_line_index is None:
            return
        self.save_state()  
        station_x = self.right_click_station
        idx = self.right_click_line_index
        pts = self.stations[station_x]
        if idx < 0 or idx >= len(pts) -1:
            return

        p1 = pts[idx]
        p2 = pts[idx+1]
        mid = (
            station_x,
            (p1[1] + p2[1]) / 2,
            (p1[2] + p2[2]) / 2
        )
        pts.insert(idx+1, mid)
        self.draw_all()


    def on_mouse_move(self, event):
        margin = 5
        if abs(event.x - self.divider_x) < margin:
            self.canvas.config(cursor="sb_h_double_arrow")
        elif abs(event.y - self.divider_y) < margin:
            self.canvas.config(cursor="sb_v_double_arrow")
        else:
            self.canvas.config(cursor="")

    def on_mouse_leave(self, event):
        print("[Leave] Resetting drag state")
        self.dragging_divider = None
        self.drag_data['station_x'] = None
        self.drag_data['point_index'] = None