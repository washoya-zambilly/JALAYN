from PySide6.QtWidgets import QInputDialog
from PySide6.QtGui import QPainterPath
from PySide6.QtCore import QPointF
import numpy as np

from geomdl import fitting
from geomdl import NURBS
from training1_utils import project_point

from OCC.Core.gp import gp_Pnt, gp_Vec, gp_Pln, gp_Ax3, gp_Dir
from OCC.Core.Geom import Geom_Plane, Geom_BSplineCurve
from OCC.Core.TColgp import TColgp_Array1OfPnt, TColgp_HArray1OfPnt
from OCC.Core.TColStd import TColStd_Array1OfReal, TColStd_Array1OfInteger
from OCC.Core.GeomAPI import GeomAPI_Interpolate, GeomAPI_IntCS
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeEdge
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepGProp import brepgprop

class Qt_State:
    def __init__(self, main_window):
        self.main_window = main_window

        self.selected_index = None
        self.active_point_index = None
        self.is_dragging = False

        self.right_click_segment = None
        self.right_click_profile_segment = None
        self.right_click_point = None   

    # ================= CORE NURBS ENGINE =================
    def get_nurbs_curve_with_weights(self, pts_with_weight):
        curve = NURBS.Curve()
        curve.degree = 3
        ctrl_pts = [[p[0], p[1], p[2]] for p in pts_with_weight]
        weights = [p[3] if len(p) > 3 else 1.0 for p in pts_with_weight]
    
        curve.ctrlpts = ctrl_pts
        curve.weights = weights
        return curve
    
    def get_nurbs_interpolation(self, pts_2d, target_val, mode='z_to_y'):
        """Used For Buttocline & Waterline Calc,"""
        if len(pts_2d) < 3: return None
        try:
            curve = fitting.interpolate_curve(pts_2d, 3)
            curve.sample_size = 100
            eval_pts = curve.evalpts
            
            idx_search = 1 if mode == 'z_to_y' else 0
            idx_out = 0 if mode == 'z_to_y' else 1

            for i in range(len(eval_pts) - 1):
                p1, p2 = eval_pts[i], eval_pts[i+1]
                if (p1[idx_search] <= target_val <= p2[idx_search]) or (p2[idx_search] <= target_val <= p1[idx_search]):
                    if abs(p2[idx_search] - p1[idx_search]) < 1e-6: return p1[idx_out]
                    t = (target_val - p1[idx_search]) / (p2[idx_search] - p1[idx_search])
                    return p1[idx_out] + t * (p2[idx_out] - p1[idx_out])
        except Exception as e:
            print(f"NURBS Error: {e}")
        return None
    
    def get_nurbs_all_intersections(self, pts_2d, target_val, mode='z_to_y'):
        if len(pts_2d) < 3: return []
        intersections = []
        try:
            curve = fitting.interpolate_curve(pts_2d, 3)
            curve.sample_size = 150 
            eval_pts = curve.evalpts
            
            idx_search = 1 if mode == 'z_to_y' else 0
            idx_out = 0 if mode == 'z_to_y' else 1

            for i in range(len(eval_pts) - 1):
                p1, p2 = eval_pts[i], eval_pts[i+1]
                if (p1[idx_search] <= target_val <= p2[idx_search]) or (p2[idx_search] <= target_val <= p1[idx_search]):
                    if abs(p2[idx_search] - p1[idx_search]) < 1e-6:
                        intersections.append(p1[idx_out])
                        continue
                    t = (target_val - p1[idx_search]) / (p2[idx_search] - p1[idx_search])
                    intersections.append(p1[idx_out] + t * (p2[idx_out] - p1[idx_out]))
        except:
            pass
        return list(set(intersections)) 



    # ================= STATION MANAGEMENT =================
    def add_point(self, pos, canvas_title):
        canvas_title = canvas_title.lower()
        current_x = self.main_window.current_station_x
        if current_x is None: return

        scale, ox, oy = 10.0, 200, 200
        val_h = (pos.x() - ox) / scale
        val_v = -(pos.y() - oy) / scale

        x, y, z = current_x, 0.0, 0.0
        if canvas_title == "front": y, z = val_h, val_v
        elif canvas_title == "side": z, y = val_v, 0.0
        elif canvas_title == "top": y, z = val_v, 0.0

        new_pt = (x, y, z, 1.0, None, None) 
        self.main_window.stations[current_x].append(new_pt)
        
        self.refresh_waterlines()
        self.refresh_buttocklines()
        self.main_window.update_all_views()
        self.main_window.update_offset_table(current_x)

    def delete_point(self):
        idx = self.right_click_point
        curr_x = self.main_window.current_station_x
        if idx is not None and curr_x in self.main_window.stations:
            self.main_window.stations[curr_x].pop(idx)
            self.refresh_waterlines()
            self.refresh_buttocklines()
            self.main_window.update_all_views()

    def add_point_between(self):
        idx = self.right_click_segment
        curr_x = self.main_window.current_station_x
        if idx is None or curr_x is None: return

        pts = self.main_window.stations[curr_x]
        if 0 <= idx < len(pts) - 1:
            p1, p2 = pts[idx], pts[idx + 1]
            
            mid = (
                (p1[0] + p2[0]) / 2, 
                (p1[1] + p2[1]) / 2, 
                (p1[2] + p2[2]) / 2,
                1.0,   # Weight default
                None,  # Angle In default (Auto)
                None   # Angle Out default (Auto)
            )
            pts.insert(idx + 1, mid)
            
            self.refresh_waterlines()
            self.refresh_buttocklines()
            self.main_window.update_all_views()



    # ================= WATERLINES & BUTTOCKLINES =================
    def add_waterline(self):
        z_val, ok = QInputDialog.getDouble(self.main_window, "Add Waterline", "Z Level (m):", 2.0)
        if ok:
            if not hasattr(self.main_window, 'waterlines'): self.main_window.waterlines = {}
            self.calculate_single_waterline(z_val)
            self.main_window.sync_wl_list()
            self.main_window.update_all_views()

    def calculate_single_waterline(self, z_val):
        station_pts = []
        
        # 1. Station intersection
        for x in self.main_window.station_order:
            pts = self.main_window.stations.get(x, [])
            if len(pts) < 2: continue 
            pts_2d = [[p[1], p[2]] for p in pts]
            y_intersections = self.get_nurbs_all_intersections(pts_2d, z_val, mode='z_to_y')
            
            if y_intersections:
                max_yi = max(y_intersections)
                safe_yi = max(0.0, max_yi)
                
                station_pts.append((x, safe_yi, z_val, 1.0, None, None))
                
        station_pts = sorted(station_pts, key=lambda p: p[0])

        # 2. Prifile Sync.
        profile_start_pts = []
        profile_end_pts = []

        if hasattr(self.main_window, 'profile_points') and len(self.main_window.profile_points) >= 2:
            prof_pts = self.main_window.profile_points
            
            x_intersections = []
            for i in range(len(prof_pts) - 1):
                p1, p2 = prof_pts[i], prof_pts[i+1]
                z1, z2 = p1[2], p2[2]
                if (z1 <= z_val <= z2) or (z2 <= z_val <= z1):
                    if abs(z2 - z1) < 1e-6:
                        x_intersections.append(p1[0])
                    else:
                        t = (z_val - z1) / (z2 - z1)
                        x_intersections.append(p1[0] + t * (p2[0] - p1[0]))

            if station_pts:
                min_station_x = station_pts[0][0]
                max_station_x = station_pts[-1][0]
                
                for xi in x_intersections:
                    pt_profile = (xi, 0.0, z_val, 1.0, None, None)
                    
                    if xi < min_station_x:
                        profile_start_pts.append(pt_profile)
                    elif xi > max_station_x:
                        profile_end_pts.append(pt_profile)
                    else:
                        if not any(abs(sp[0] - xi) < 1e-3 for sp in station_pts):
                            station_pts.append(pt_profile)
                
                station_pts = sorted(station_pts, key=lambda p: p[0])

        # 3. Combine Data
        wl_pts = profile_start_pts + station_pts + profile_end_pts
        self.main_window.waterlines[z_val] = wl_pts

    def refresh_waterlines(self):
        if hasattr(self.main_window, 'waterlines'):
            for z in list(self.main_window.waterlines.keys()): self.calculate_single_waterline(z)

    def add_buttockline(self):
        y_val, ok = QInputDialog.getDouble(self.main_window, "Add Buttockline", "Y Distance:", 1.0)
        if ok:
            if not hasattr(self.main_window, 'buttocklines'): self.main_window.buttocklines = {}
            self.calculate_single_buttockline(y_val)
            self.main_window.sync_bl_list()
            self.main_window.update_all_views()

    def calculate_single_buttockline(self, y_val):
        bl_pts = []
        
        if abs(y_val) < 1e-6 and hasattr(self.main_window, 'profile_points'):
            self.main_window.buttocklines[y_val] = self.main_window.profile_points
            return

        #Station intersection
        for x in self.main_window.station_order:
            pts = self.main_window.stations.get(x, [])
            if len(pts) < 2: 
                continue
            
            min_physical_z = min(p[2] for p in pts)
            
            for i in range(len(pts) - 1):
                p1, p2 = pts[i], pts[i+1]
                y1, y2 = p1[1], p2[1]
                z1, z2 = p1[2], p2[2]
                
                if (y1 <= y_val <= y2) or (y2 <= y_val <= y1):
                    if abs(y2 - y1) < 1e-6:
                        z_potong = min(z1, z2)
                    else:
                        t = (y_val - y1) / (y2 - y1)
                        z_potong = z1 + t * (z2 - z1)
                    
                    if abs(z_potong - min_physical_z) < 0.01:
                        z_potong = min_physical_z
                        
                    bl_pts.append((x, y_val, z_potong, 5.0, None, None))
                    break 

        # WL intersection
        if hasattr(self.main_window, 'waterlines'):
            for z_wl, wl_pts in self.main_window.waterlines.items():
                if len(wl_pts) < 2: 
                    continue
                
                for i in range(len(wl_pts) - 1):
                    p1, p2 = wl_pts[i], wl_pts[i+1]
                    x1, x2 = p1[0], p2[0]
                    y1, y2 = p1[1], p2[1]
                    
                    if (y1 <= y_val <= y2) or (y2 <= y_val <= y1):
                        if abs(y2 - y1) < 1e-6:
                            x_potong = min(x1, x2)
                        else:
                            t = (y_val - y1) / (y2 - y1)
                            x_potong = x1 + t * (x2 - x1)
                        
                        bl_pts.append((x_potong, y_val, z_wl, 5.0, None, None))

        # Filter 
        saring_bl_pts = []
        toleransi = 0.01 
        
        bl_pts.sort(key=lambda p: p[0])
        
        for pt in bl_pts:
            if not saring_bl_pts:
                saring_bl_pts.append(pt)
            else:
                pt_prev = saring_bl_pts[-1]
                jarak_x = abs(pt[0] - pt_prev[0])
                jarak_z = abs(pt[2] - pt_prev[2])
                
                if jarak_x > toleransi or jarak_z > toleransi:
                    saring_bl_pts.append(pt)

        # Save
        self.main_window.buttocklines[y_val] = saring_bl_pts

    def refresh_buttocklines(self):
        if hasattr(self.main_window, 'buttocklines'):
            for y in list(self.main_window.buttocklines.keys()): self.calculate_single_buttockline(y)



    #-------------PROFILE/CENTERLINE--------------
    def add_profile_point(self, pos, canvas_title):
        ox, oy = 200, 200
        scale = 10.0  
    
        x_val = (pos.x() - ox) / scale
        z_val = -(pos.y() - oy) / scale
        y_val = 0.0 

        if not hasattr(self.main_window, 'profile_points'):
            self.main_window.profile_points = []
        
        new_pt = (x_val, y_val, z_val, 1.0, None, None)
        self.main_window.profile_points.append(new_pt)
        
        self.main_window.sync_bl_list() 
        self.main_window.update_all_views()
    
    def add_profile_point_between(self):
        idx = getattr(self, 'right_click_profile_segment', None)
        if idx is None: return

        pts = self.main_window.profile_points
        if 0 <= idx < len(pts) - 1:
            p1, p2 = pts[idx], pts[idx + 1]
            mid = ((p1[0] + p2[0]) / 2, 0.0, (p1[2] + p2[2]) / 2, 1.0, None, None)
            
            pts.insert(idx + 1, mid)
            self.main_window.update_all_views()
    
    def select_profile(self, index):
        self.active_point_index = None
        self.active_profile_index = index
        self.main_window.update_all_views()

    def delete_profile_point(self):
        if not hasattr(self.main_window, 'profile_points') or not self.main_window.profile_points:
            return

        # Delete active point
        active_idx = getattr(self, 'active_profile_index', None)
        if active_idx is not None and 0 <= active_idx < len(self.main_window.profile_points):
            self.main_window.profile_points.pop(active_idx)
            self.active_profile_index = None # Reset indeks setelah dihapus
            self.main_window.update_all_views()
            return

        # Search for the nearest point
        if hasattr(self, 'right_click_point') and self.right_click_point:
            tx, ty, tz = self.right_click_point
            
            closest_idx = None
            min_distance = float('inf')
            
            for idx, pt in enumerate(self.main_window.profile_points):
                dist = ((pt[0] - tx)**2 + (pt[2] - tz)**2)**0.5
                if dist < min_distance:
                    min_distance = dist
                    closest_idx = idx
            
            if closest_idx is not None and min_distance < 1.0:
                self.main_window.profile_points.pop(closest_idx)
                
                if getattr(self, 'active_profile_index', None) == closest_idx:
                    self.active_profile_index = None
                    
                self.main_window.update_all_views()
                self.main_window.sync_bl_list()



    # ================= VISUALIZATION =================
    def get_spline_path(self, points_3d, view_title, az=45, el=30):
        path = QPainterPath()
        if len(points_3d) < 2: return path

        view_title = view_title.lower()
        is_profile = (points_3d is getattr(self.main_window, 'profile_points', None))
        num_pts = len(points_3d)

        # 1. 2 points = linear
        if num_pts == 2:
            p0, p1 = points_3d[0], points_3d[1]
            proj0 = project_point(p0[0], p0[1], p0[2], view_title, az, el)
            proj1 = project_point(p1[0], p1[1], p1[2], view_title, az, el)
            path.moveTo(proj0[0], proj0[1])
            path.lineTo(proj1[0], proj1[1])
            return path

        # 2. vector tangent calc.
        auto_tangents = []
        for i in range(num_pts):
            if i == 0:
                v = gp_Vec(gp_Pnt(points_3d[0][0], points_3d[0][1], points_3d[0][2]), 
                           gp_Pnt(points_3d[1][0], points_3d[1][1], points_3d[1][2]))
            elif i == num_pts - 1:
                v = gp_Vec(gp_Pnt(points_3d[num_pts-2][0], points_3d[num_pts-2][1], points_3d[num_pts-2][2]), 
                           gp_Pnt(points_3d[num_pts-1][0], points_3d[num_pts-1][1], points_3d[num_pts-1][2]))
            else:
                v = gp_Vec(gp_Pnt(points_3d[i-1][0], points_3d[i-1][1], points_3d[i-1][2]), 
                           gp_Pnt(points_3d[i+1][0], points_3d[i+1][1], points_3d[i+1][2]))
            v.Normalize()
            auto_tangents.append(v)

        # 3. Plot
        p_start = points_3d[0]
        proj_start = project_point(p_start[0], p_start[1], p_start[2], view_title, az, el)
        path.moveTo(proj_start[0], proj_start[1])

        # 4. NURBS segment
        for i in range(num_pts - 1):
            p0 = points_3d[i]
            p3 = points_3d[i+1]

            p0_occ = gp_Pnt(p0[0], p0[1], p0[2])
            p3_occ = gp_Pnt(p3[0], p3[1], p3[2])

            dist = np.sqrt((p3[0]-p0[0])**2 + (p3[1]-p0[1])**2 + (p3[2]-p0[2])**2)
            magnitude = dist / 3.0 

            angle_out = p0[5] if len(p0) > 5 else None
            if angle_out is not None:
                rad_out = np.radians(angle_out)
                if is_profile:
                    vec_out = gp_Vec(np.cos(rad_out), 0.0, np.sin(rad_out))
                else:
                    vec_out = gp_Vec(0.0, np.cos(rad_out), np.sin(rad_out))
                vec_out.Normalize()
            else:
                vec_out = auto_tangents[i]

            p1_occ = gp_Pnt(p0_occ.XYZ() + vec_out.XYZ() * magnitude)

            angle_in = p3[4] if len(p3) > 4 else None
            if angle_in is not None:
                rad_in = np.radians(angle_in)
                if is_profile:
                    vec_in = gp_Vec(-np.cos(rad_in), 0.0, -np.sin(rad_in))
                else:
                    vec_in = gp_Vec(0.0, -np.cos(rad_in), -np.sin(rad_in))
                vec_in.Normalize()
            else:
                vec_in = gp_Vec(auto_tangents[i+1].XYZ() * -1.0)

            p2_occ = gp_Pnt(p3_occ.XYZ() + vec_in.XYZ() * magnitude)

            poles = TColgp_Array1OfPnt(1, 4)
            poles.SetValue(1, p0_occ)
            poles.SetValue(2, p1_occ)
            poles.SetValue(3, p2_occ)
            poles.SetValue(4, p3_occ)

            weights = TColStd_Array1OfReal(1, 4)
            weights.SetValue(1, p0[3] if len(p0) > 3 else 1.0)
            weights.SetValue(2, 1.0)
            weights.SetValue(3, 1.0)
            weights.SetValue(4, p3[3] if len(p3) > 3 else 1.0)

            knots = TColStd_Array1OfReal(1, 2)
            knots.SetValue(1, 0.0)
            knots.SetValue(2, 1.0)

            mults = TColStd_Array1OfInteger(1, 2)
            mults.SetValue(1, 4)
            mults.SetValue(2, 4)

            try:
                nurbs_segment = Geom_BSplineCurve(poles, weights, knots, mults, 3)
            except:
                continue

            # 5. Sampling
            steps = 25
            u_min = nurbs_segment.FirstParameter()
            u_max = nurbs_segment.LastParameter()
            
            for s in range(1, steps + 1):
                u = u_min + (s / steps) * (u_max - u_min)
                occ_pt = nurbs_segment.Value(u)
                
                pt_y = occ_pt.Y()
                if view_title == "top" and abs(p0[1]) < 1e-6 and i == 0 and s < 4:
                    pt_y = 0.0

                proj_pt = project_point(occ_pt.X(), pt_y, occ_pt.Z(), view_title, az, el)
                path.lineTo(proj_pt[0], proj_pt[1])

        return path

    def select_station(self, x): self.main_window.current_station_x = x; self.main_window.update_all_views()
    def clear_selection(self): self.active_point_index = None; self.selected_index = None

    

    # ================= HYDROSTATICS ENGINE =================
    def _build_occt_nurbs_curve(self, points_3d):
        num_pts = len(points_3d)
        if num_pts < 2: return None

        poles = TColgp_Array1OfPnt(1, num_pts)
        for i, p in enumerate(points_3d):
            poles.SetValue(i + 1, gp_Pnt(p[0], p[1], p[2]))

        try:
            knots = TColStd_Array1OfReal(1, 2)
            knots.SetValue(1, 0.0); knots.SetValue(2, 1.0)
            mults = TColStd_Array1OfInteger(1, 2)
            mults.SetValue(1, 4); mults.SetValue(2, 4)
            
            h_pts = TColgp_HArray1OfPnt(1, num_pts)
            for i in range(1, num_pts + 1):
                h_pts.SetValue(i, poles.Value(i))
                
            interpolator = GeomAPI_Interpolate(h_pts, False, 1e-6)
            interpolator.Perform()
            if interpolator.IsDone():
                return interpolator.Curve()
        except:
            pass
        return None
    
    def calculate_station_area_at_draft(self, station_pts, draft_z):
        if len(station_pts) < 2: return 0.0, 0.0

        # 1. If draft below station
        min_z_station = min(p[2] for p in station_pts)
        if draft_z <= min_z_station: return 0.0, 0.0

        poly_pts = []
        
        try:
            # 2. Cut & collecty all the coordinates
            for i in range(len(station_pts) - 1):
                p1, p2 = station_pts[i], station_pts[i+1]
                y1, z1 = p1[1], p1[2]
                y2, z2 = p2[1], p2[2]

                if z1 <= draft_z:
                    poly_pts.append((y1, z1))

                if (z1 <= draft_z <= z2) or (z2 <= draft_z <= z1):
                    if abs(z2 - z1) > 1e-6:
                        t = (draft_z - z1) / (z2 - z1)
                        y_intersect = y1 + t * (y2 - y1)
                        poly_pts.append((y_intersect, draft_z))
            
            if station_pts[-1][2] <= draft_z:
                poly_pts.append((station_pts[-1][1], station_pts[-1][2]))

            if len(poly_pts) < 2: return 0.0, 0.0

            # 3. Go to CL
            y_top, z_top = poly_pts[-1][0], draft_z
            y_bot, z_bot = poly_pts[0][0], poly_pts[0][1]

            poly_pts.append((0.0, z_top))     
            poly_pts.append((0.0, z_bot))     

            y_coords = np.array([p[0] for p in poly_pts])
            z_coords = np.array([p[1] for p in poly_pts])
            
            # 4. Shoelace
            y_next = np.roll(y_coords, -1)
            z_next = np.roll(z_coords, -1)
            
            common_factor = (y_coords * z_next - y_next * z_coords)
            
            half_area = 0.5 * np.abs(np.sum(common_factor))
            
            half_v_moment = (1.0 / 6.0) * np.sum((z_coords + z_next) * common_factor)
            half_v_moment = np.abs(half_v_moment) 

            return half_area * 2.0, half_v_moment * 2.0

        except Exception as e:
            print(f"Error Hydrostatic Station: {e}")
            return 0.0, 0.0


    def compute_hydrostatics(self, draft_z):
        if not self.main_window.station_order or draft_z <= 0: return None

        stations_x = sorted(self.main_window.station_order)
        
        areas = []
        v_moments = []       
        lcb_moments = []     
        y_wl_values = []     

        for x in stations_x:
            pts = self.main_window.stations[x]
            area, v_moment = self.calculate_station_area_at_draft(pts, draft_z)
            
            areas.append(area)
            v_moments.append(v_moment)
            lcb_moments.append(area * x)
            
            # Half breadth
            pts_2d = [[p[1], p[2]] for p in pts]
            y_intersections = self.get_nurbs_all_intersections(pts_2d, draft_z, mode='z_to_y')
            y_wl_values.append(max(y_intersections) if y_intersections else 0.0)

        trapz_func = getattr(np, 'trapezoid', getattr(np, 'trapz', None))
        if trapz_func is None: return None

        # 1. Bouyancy center
        volume = trapz_func(areas, stations_x)
        if volume < 1e-6: return None

        lcb = trapz_func(lcb_moments, stations_x) / volume
        kb = trapz_func(v_moments, stations_x) / volume  

        # 2. Waterplane
        wla = trapz_func(y_wl_values, stations_x) * 2.0
        
        y_wl_array = np.array(y_wl_values)
        stations_x_array = np.array(stations_x)
        
        # LCF
        lcf_moment = trapz_func(y_wl_array * stations_x_array, stations_x) * 2.0
        lcf = lcf_moment / wla if wla > 0 else 0.0

        # 3. Inertia Moment Waterplane
        inertia_t_elements = (2.0 / 3.0) * (y_wl_array ** 3)
        it = trapz_func(inertia_t_elements, stations_x)

        inertia_l_elements = 2.0 * y_wl_array * (stations_x_array ** 2)
        il_base = trapz_func(inertia_l_elements, stations_x)
        il = il_base - (wla * (lcf ** 2)) 

        # 4. Metacentric radius
        bm_t = it / volume
        bm_l = il / volume
        km_t = kb + bm_t
        km_l = kb + bm_l

        # 5. Coefficients & Main Dim.
        lpp = self.main_window.ship_data.get("LPP", 1.0)
        b = self.main_window.ship_data.get("B", 1.0)
        density = 1.025 
        
        disp = volume * density
        tpc = (wla * density) / 100.0

        cb = volume / (lpp * b * draft_z) if (lpp * b * draft_z) > 0 else 0.0
        c_wp = wla / (lpp * b) if (lpp * b) > 0 else 0.0
        
        mid_x = sorted(stations_x, key=lambda x: abs(x - (lpp / 2.0)))[0]
        midship_area = areas[stations_x.index(mid_x)]
        c_m = midship_area / (b * draft_z) if (b * draft_z) > 0 else 0.0
        c_p = cb / c_m if c_m > 0 else 0.0

        # 6. Trim
        mctc = (disp * bm_l) / (100.0 * lpp) if lpp > 0 else 0.0

        return {
            "T": draft_z,
            "VOLUME": volume,
            "DISP": disp,
            "WLA": wla,
            "TPC": tpc,
            # --- Centers ---
            "LCB": lcb,
            "LCF": lcf,
            "KB": kb,
            # --- Metacentric ---
            "BM_T": bm_t,
            "BM_L": bm_l,
            "KM_T": km_t,
            "KM_L": km_l,
            # --- Coefficients ---
            "CB": cb,
            "CWP": c_wp,
            "CM": c_m,
            "CP": c_p,
            # --- Inertia & Trim ---
            "MCTC": mctc,
            "IT": it,
            "IL": il
        }