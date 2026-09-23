#training1_canvas.py
from PySide6.QtWidgets import (QGraphicsView)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt
from training1_event import Qt_Events
from training1_utils import project_point

class CanvasView(QGraphicsView):
    def __init__(self, main_window, enable_interaction=False, title=""):
        super().__init__()
        self.setViewport(QOpenGLWidget())
        self.enable_interaction = enable_interaction 

        self.main_window = main_window 
        self.title = title

        self.state = main_window.state
        
        self.events = Qt_Events(self, self.state)

        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        self._panning = False
        self._pan_start = None
        self.title = title

        self.points = []

        self.selected_index = None
        self.dragging = False

    #--------- SCROLL --------------
    def wheelEvent(self, event):
        if not self.enable_interaction:
            return
        zoom_in = 1.25
        zoom_out = 1 / zoom_in
        if event.angleDelta().y() > 0:
            self.scale(zoom_in, zoom_in)
        else:
            self.scale(zoom_out, zoom_out)

    #--------- CLICK --------------------
    def mousePressEvent(self, event):
        if not self.enable_interaction:
            return
        
        scene_pos = self.mapToScene(event.position().toPoint())
        
        # LEFT CLICK
        if event.button() == Qt.LeftButton:
            # 1. Search Point (Profile first, if none go to station)
            if self.title.lower() == "side":
                idx_profile = self.find_profile_point_near(scene_pos)
                if idx_profile is not None:
                    self.state.active_profile_index = idx_profile
                    self.state.active_point_index = None 
                    
                    self.selected_profile_index = idx_profile
                    self.dragging_profile = True
                    self.state.is_dragging = True
                    
                    self.main_window.current_station_x = None 
                    self.main_window.update_properties_panel(idx_profile)
                    
                    self.main_window.update_all_views()
                    event.accept()
                    return

            # 2. Search in station
            index = self.find_point_near(scene_pos)
            if index is not None:
                self.state.active_point_index = index
                self.state.active_profile_index = None 

                self.selected_index = index
                self.dragging = True
                self.state.is_dragging = True

                if hasattr(self.main_window, 'offset_table'):
                    self.main_window.offset_table.selectRow(index)
                
                self.main_window.update_properties_panel(index)
                self.main_window.on_table_cell_clicked(index, 0)
                self.main_window.update_all_views()

                event.accept()
                return
            
            else:
                self.state.active_point_index = None
                self.state.active_profile_index = None
                self.main_window.update_all_views()
    
        # ===== MIDDLE BUTTON (FOR PAN) =====
        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        # ===== RIGHT CLICK =====
        if event.button() == Qt.RightButton:
            self.events.handle_right_click(event)
            event.accept()
            return

        super().mousePressEvent(event)

    #------------ PAN & DRAG ---------------------
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        if not self.enable_interaction:
            return
        
        # PANNING
        if self._panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - int(delta.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - int(delta.y()))
            event.accept()
            return

        # DRAG PROFILE 
        if hasattr(self, 'dragging_profile') and self.dragging_profile:
            if self.selected_profile_index is not None and hasattr(self.main_window, 'profile_points'):
                pts = self.main_window.profile_points
                
                if 0 <= self.selected_profile_index < len(pts):
                    scene_pos = self.mapToScene(event.position().toPoint())
                    scale, ox, oy = 10.0, 200, 200
                
                    new_x = (scene_pos.x() - ox) / scale
                    new_z = -(scene_pos.y() - oy) / scale
                    
                    old_pt = list(pts[self.selected_profile_index])
                    w = old_pt[3] if len(old_pt) > 3 else 1.0
                    a_in = old_pt[4] if len(old_pt) > 4 else None
                    a_out = old_pt[5] if len(old_pt) > 5 else None
                    
                    pts[self.selected_profile_index] = (new_x, 0.0, new_z, w, a_in, a_out)
                
                    self.main_window.update_all_views()
            return 
    
        # DRAG POINT STATION 
        if self.dragging and self.selected_index is not None:
            scene_pos = self.mapToScene(event.position().toPoint())
            current_x = self.main_window.current_station_x
            pts = self.main_window.stations.get(current_x, [])
            if not pts: return

            scale, ox, oy = 10.0, 200, 200
            view_name = self.title.lower()

            val_h, val_v = (scene_pos.x() - ox) / scale, -(scene_pos.y() - oy) / scale 

            old_pt = pts[self.selected_index]
            nx, ny, nz = old_pt[0], old_pt[1], old_pt[2]
            nw = old_pt[3] if len(old_pt) > 3 else 1.0
            na_in = old_pt[4] if len(old_pt) > 4 else None
            na_out = old_pt[5] if len(old_pt) > 5 else None

            if view_name == "front": ny, nz = val_h, val_v
            elif view_name == "side": nz = val_v
            elif view_name == "top": ny = val_v

            pts[self.selected_index] = (nx, ny, nz, nw, na_in, na_out)
            
            # Update
            self.main_window.update_all_views()
            self.main_window.update_properties_panel(self.selected_index)

    #------------ RELEASE -----------------
    def mouseReleaseEvent(self, event):
        if not self.enable_interaction:
            return

        # ===== MIDDLE BUTTON (PANNING) =====
        if event.button() == Qt.MiddleButton:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return

        # ===== LEFT BUTTON (RELEASE DRAG) =====
        if event.button() == Qt.LeftButton:
            is_active_drag = self.dragging or getattr(self, 'dragging_profile', False)

            # Reset semua flag interaksi
            self.dragging = False
            self.dragging_profile = False  
            self.state.is_dragging = False 
            
            saved_station_idx = self.selected_index
            
            self.selected_index = None
            self.selected_profile_index = None

            if is_active_drag:
                current_x = self.main_window.current_station_x
                
                if current_x is not None:
                    self.main_window.update_offset_table(current_x)
                    if saved_station_idx is not None:
                        self.main_window.offset_table.selectRow(saved_station_idx)

                if self.main_window.current_bl_y == "PROFILE_MARKER":
                    self.main_window.on_bl_selected(self.main_window.bl_list_widget.currentItem())
                
                self.main_window.state.refresh_waterlines()
                self.main_window.state.refresh_buttocklines()
                
                if hasattr(self.main_window.menu_bar, 'save_snapshot'):
                    self.main_window.menu_bar.save_snapshot()
                
                self.main_window.update_all_views()
            
            event.accept()

        super().mouseReleaseEvent(event)


    # -------------- SEARCH POINT ---------------------
    def find_point_near(self, scene_pos, threshold=10):
        current_x = self.main_window.current_station_x
        if current_x is None:
            return None

        pts = self.main_window.stations.get(current_x, [])
    
        az = self.main_window.azimuth_slider.value()
        el = self.main_window.elevation_slider.value()

        for i, pt in enumerate(pts):
            x, y, z = pt[0], pt[1], pt[2]

            res = project_point(x, y, z, self.title.lower(), az, el)
        
            if res is None: 
                continue 
            fx, fz = res
            dx = fx - scene_pos.x()
            dy = fz - scene_pos.y()

            if (dx*dx + dy*dy) ** 0.5 < threshold:
                return i
            
        return None

    #------------------ SEARCH LINE -------------------------
    def find_segment_near(self, scene_pos, threshold=10):
        current_x = self.main_window.current_station_x
        if current_x is None:
            return None

        pts = self.main_window.stations.get(current_x, [])
        if len(pts) < 2: return None

        min_dist = threshold
        found_index = None

        az = self.main_window.azimuth_slider.value()
        el = self.main_window.elevation_slider.value()

        for i in range(len(pts) - 1):
            pt1 = pts[i]
            pt2 = pts[i + 1]
            
            x1, y1, z1 = pt1[0], pt1[1], pt1[2]
            x2, y2, z2 = pt2[0], pt2[1], pt2[2]

            p1 = project_point(x1, y1, z1, self.title.lower(), az, el)
            p2 = project_point(x2, y2, z2, self.title.lower(), az, el)

            if p1 is None or p2 is None: continue

            dist = self.distance_point_to_segment(scene_pos, p1, p2)

            if dist < min_dist:
                min_dist = dist
                found_index = i

        return found_index
    
    #---------------- SEARCH POINT & LINE IN PROFILE -------------------------
    def find_profile_segment_near(self, scene_pos, threshold=10):
        if not hasattr(self.main_window, 'profile_points') or len(self.main_window.profile_points) < 2:
            return None

        min_dist = threshold
        found_index = None

        for i in range(len(self.main_window.profile_points) - 1):
            p1_3d = self.main_window.profile_points[i]
            p2_3d = self.main_window.profile_points[i+1]

            p1 = project_point(p1_3d[0], p1_3d[1], p1_3d[2], "side")
            p2 = project_point(p2_3d[0], p2_3d[1], p2_3d[2], "side")

            dist = self.distance_point_to_segment(scene_pos, p1, p2)

            if dist < min_dist:
                min_dist = dist
                found_index = i

        return found_index

    def distance_point_to_segment(self, scene_pos, p1, p2):
        px = scene_pos.x()
        py = scene_pos.y()

        x1, y1 = p1
        x2, y2 = p2

        dx = x2 - x1
        dy = y2 - y1

        if dx == 0 and dy == 0:
            return ((px - x1)**2 + (py - y1)**2) ** 0.5

        t = ((px - x1)*dx + (py - y1)*dy) / (dx*dx + dy*dy)
        t = max(0, min(1, t))

        nearest_x = x1 + t*dx
        nearest_y = y1 + t*dy

        return ((px - nearest_x)**2 + (py - nearest_y)**2) ** 0.5

    def find_profile_point_near(self, scene_pos, threshold=10):
        if not hasattr(self.main_window, 'profile_points'): return None
    
        for i, pt in enumerate(self.main_window.profile_points):
            x, y, z = pt[0], pt[1], pt[2] 
            
            res = project_point(x, y, z, "side") 
            if res is None: continue
            
            fx, fz = res
            dx, dy = fx - scene_pos.x(), fz - scene_pos.y()
            if (dx*dx + dy*dy) ** 0.5 < threshold:
                return i
        return None

