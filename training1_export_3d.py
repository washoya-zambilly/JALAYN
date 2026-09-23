from pathlib import Path
from PySide6.QtWidgets import QFileDialog, QMessageBox
import numpy as np

#IGES Exporter is still under development, currently file can be exported as vtk
class IGES3DExporter:
    def __init__(self, main_window):
        self.main_window = main_window

    def evaluate_hermite_spline_3d(self, points_6d, n_samples=60, is_profile=False):
        if len(points_6d) < 2: 
            return [p[:3] for p in points_6d]

        tangents_in_3d = []
        tangents_out_3d = []

        for i in range(len(points_6d)):
            p = points_6d[i]
            angle_in = p[4] if len(p) > 4 else None
            angle_out = p[5] if len(p) > 5 else None

            if angle_in is not None:
                rad_in = np.radians(angle_in)
                t_in = np.array([np.cos(rad_in), 0.0, np.sin(rad_in)]) if is_profile else np.array([0.0, np.cos(rad_in), np.sin(rad_in)])
            else:
                if i == 0: t_in = np.array(points_6d[i+1][:3]) - np.array(points_6d[i][:3])
                elif i == len(points_6d) - 1: t_in = np.array(points_6d[i][:3]) - np.array(points_6d[i-1][:3])
                else: t_in = (np.array(points_6d[i+1][:3]) - np.array(points_6d[i-1][:3])) * 0.5
            tangents_in_3d.append(t_in)

            if angle_out is not None:
                rad_out = np.radians(angle_out)
                t_out = np.array([np.cos(rad_out), 0.0, np.sin(rad_out)]) if is_profile else np.array([0.0, np.cos(rad_out), np.sin(rad_out)])
            else:
                if i == 0: t_out = np.array(points_6d[i+1][:3]) - np.array(points_6d[i][:3])
                elif i == len(points_6d) - 1: t_out = np.array(points_6d[i][:3]) - np.array(points_6d[i-1][:3])
                else: t_out = (np.array(points_6d[i+1][:3]) - np.array(points_6d[i-1][:3])) * 0.5
            tangents_out_3d.append(t_out)

        evaluated_points = []
        n_segments = len(points_6d) - 1
        steps_per_seg = max(2, n_samples // n_segments)
        
        for i in range(n_segments):
            p0 = np.array(points_6d[i][:3])
            p1 = np.array(points_6d[i+1][:3])
            dist = np.linalg.norm(p1 - p0)
            
            t0 = (tangents_out_3d[i] / (np.linalg.norm(tangents_out_3d[i]) + 1e-6)) * dist * 0.4
            t1 = (tangents_in_3d[i+1] / (np.linalg.norm(tangents_in_3d[i+1]) + 1e-6)) * dist * 0.4
            
            current_steps = steps_per_seg if i < n_segments - 1 else (n_samples - len(evaluated_points))
            for s in range(current_steps):
                t = s / current_steps
                h1 = 2*t**3 - 3*t**2 + 1
                h2 = t**3 - 2*t**2 + t
                h3 = -2*t**3 + 3*t**2
                h4 = t**3 - t**2
                res_pt = h1*p0 + h2*t0 + h3*p1 + h4*t1
                evaluated_points.append(res_pt.tolist())
                
        if len(evaluated_points) < n_samples:
            evaluated_points.append(points_6d[-1][:3])
            
        return evaluated_points[:n_samples]

    #Still as vtk
    def export_hull_to_iges(self):
        if not hasattr(self.main_window, 'stations') or not self.main_window.stations:
            QMessageBox.warning(None, "Data Not Found", "Object Not Found.")
            return

        self.station_order = sorted(self.main_window.stations.keys())
        self.waterlines = getattr(self.main_window, 'waterlines', {})
        profile_pts = getattr(self.main_window, 'profile_points', [])

        if len(self.station_order) < 2:
            QMessageBox.warning(None, "Insufficient Data", "Need minimum 2 stations to create a surface")
            return

        file_path_raw, _ = QFileDialog.getSaveFileName(None, "Export Integrated Hull Data to VTK", "", "VTK PolyData (*.vtk)")
        if not file_path_raw: 
            return

        from pathlib import Path
        import pyvista as pv
        import numpy as np

        save_path = Path(file_path_raw).resolve()

        try:
            size_v = 60 
            
            x_aft_limit = self.station_order[0]
            x_fore_limit = self.station_order[-1]

            smooth_profile = []
            if len(profile_pts) >= 2:
                smooth_profile = self.evaluate_hermite_spline_3d(profile_pts, n_samples=150, is_profile=True)

            profile_stern = [p for p in smooth_profile if p[0] <= x_aft_limit]
            profile_stem = [p for p in smooth_profile if p[0] >= x_fore_limit]

            all_cross_sections = []

            raw_pts_st0 = self.main_window.stations[x_aft_limit]
            smooth_st0 = self.evaluate_hermite_spline_3d(raw_pts_st0, n_samples=size_v, is_profile=False)
            if len(smooth_st0) >= 2 and smooth_st0[0][2] > smooth_st0[-1][2]:
                smooth_st0 = smooth_st0[::-1]

            # A. Stern
            if len(profile_stern) >= 2:
                xp = np.array([p[0] for p in profile_stern])
                zp = np.array([p[2] for p in profile_stern])
                sort_idx = np.argsort(zp)
                xp_sorted = xp[sort_idx]
                zp_sorted = zp[sort_idx]

                section_stern = []
                for i in range(size_v):
                    target_z = smooth_st0[i][2]
                    target_z_clipped = np.clip(target_z, zp_sorted.min(), zp_sorted.max())
                    fitted_x = np.interp(target_z_clipped, zp_sorted, xp_sorted)
                    section_stern.append([fitted_x, 0.0, target_z])
                all_cross_sections.append(section_stern)

            # B. Station
            for sx in self.station_order:
                raw_pts_6d = self.main_window.stations[sx]
                smooth_pts = self.evaluate_hermite_spline_3d(raw_pts_6d, n_samples=size_v, is_profile=False)
                if len(smooth_pts) >= 2 and smooth_pts[0][2] > smooth_pts[-1][2]:
                    smooth_pts = smooth_pts[::-1]
                if len(smooth_pts) > 0:
                    smooth_pts[0][1] = 0.0
                all_cross_sections.append(smooth_pts)

            # C. Stem
            if len(profile_stem) >= 2:
                raw_pts_st9 = self.main_window.stations[x_fore_limit]
                smooth_st9 = self.evaluate_hermite_spline_3d(raw_pts_st9, n_samples=size_v, is_profile=False)
                if len(smooth_st9) >= 2 and smooth_st9[0][2] > smooth_st9[-1][2]:
                    smooth_st9 = smooth_st9[::-1]

                xp = np.array([p[0] for p in profile_stem])
                zp = np.array([p[2] for p in profile_stem])
                sort_idx = np.argsort(zp)
                xp_sorted = xp[sort_idx]
                zp_sorted = zp[sort_idx]

                section_stem = []
                for i in range(size_v):
                    target_z = smooth_st9[i][2]
                    target_z_clipped = np.clip(target_z, zp_sorted.min(), zp_sorted.max())
                    fitted_x = np.interp(target_z_clipped, zp_sorted, xp_sorted)
                    section_stem.append([fitted_x, 0.0, target_z])
                all_cross_sections.append(section_stem)

            size_u = len(all_cross_sections)
            
            grid_pts_r = []
            grid_pts_l = []
            for section in all_cross_sections:
                for pt in section:
                    grid_pts_r.append([pt[0], pt[1], pt[2]])
                    grid_pts_l.append([pt[0], -pt[1], pt[2]]) 

            # --- RIGHT Body ---
            grid_long_r = pv.StructuredGrid()
            grid_long_r.points = np.array(grid_pts_r, dtype=np.float32)
            grid_long_r.dimensions = [size_v, size_u, 1]  
            surf_master_r = grid_long_r.extract_surface(algorithm='dataset_surface')

            # --- LEFT Body ---
            grid_long_l = pv.StructuredGrid()
            grid_long_l.points = np.array(grid_pts_l, dtype=np.float32)
            grid_long_l.dimensions = [size_v, size_u, 1]
            surf_master_l = grid_long_l.extract_surface(algorithm='dataset_surface')

            # Combine Right & Left Body
            combined_hull = surf_master_r.merge(surf_master_l)

            is_metric_meters = (np.max(grid_long_r.points[:, 0]) < 500.0)
            tube_radius = 0.015 if is_metric_meters else 15.0

            elements_to_merge = [combined_hull]

            #Add waterlines
            if self.waterlines:
                for z, wpts in self.waterlines.items():
                    pts_wl = np.array([p[:3] for p in wpts], dtype=np.float32)
                    if len(pts_wl) >= 2:
                        pts_wl[:, 1] = np.maximum(0.0, pts_wl[:, 1])
                        # Right
                        poly_wl_r = pv.lines_from_points(pts_wl)
                        elements_to_merge.append(poly_wl_r.tube(radius=tube_radius, n_sides=6))
                        # Left
                        pts_wl_l = pts_wl.copy()
                        pts_wl_l[:, 1] = -pts_wl_l[:, 1]
                        poly_wl_l = pv.lines_from_points(pts_wl_l)
                        elements_to_merge.append(poly_wl_l.tube(radius=tube_radius, n_sides=6))

            if len(profile_pts) >= 2:
                poly_prof = pv.lines_from_points(np.array(smooth_profile, dtype=np.float32))
                elements_to_merge.append(poly_prof.tube(radius=tube_radius * 1.5, n_sides=6))

            # ---------------- Merge ---------------------
            final_mesh = combined_hull.merge(elements_to_merge[1:])
            final_mesh.save(str(save_path))

            print(f"[SUCCESS] Export Success: {save_path}")
            QMessageBox.information(None, "Export Success", 
                                    f"Export to VTK!\n\nFile: {save_path.name}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(None, "Error Engine Export", f"Failed to export geometry combination:\n{str(e)}")