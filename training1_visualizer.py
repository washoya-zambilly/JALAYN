import numpy as np
import pyvista as pv

class HullVisualizer:
    def __init__(self, main_window):
        self.main_window = main_window
        self.stations = main_window.stations
        self.station_order = sorted(self.stations.keys())
        self.waterlines = getattr(main_window, 'waterlines', {})
        self.buttocklines = getattr(main_window, 'buttocklines', {})

    def evaluate_hermite_spline_3d(self, points_6d, n_samples=60, is_profile=False):
        if len(points_6d) < 2:
            return [p[:3] for p in points_6d]

        tangents_in_3d = []
        tangents_out_3d = []

        for i in range(len(points_6d)):
            p = points_6d[i]
            angle_in = p[4] if len(p) > 4 else None
            angle_out = p[5] if len(p) > 5 else None

            # --- (In-Tangent) ---
            if angle_in is not None:
                rad_in = np.radians(angle_in)
                if is_profile:
                    t_in = np.array([np.cos(rad_in), 0.0, np.sin(rad_in)])
                else:
                    t_in = np.array([0.0, np.cos(rad_in), np.sin(rad_in)])
            else:
                if i == 0:
                    t_in = np.array(points_6d[i+1][:3]) - np.array(points_6d[i][:3])
                elif i == len(points_6d) - 1:
                    t_in = np.array(points_6d[i][:3]) - np.array(points_6d[i-1][:3])
                else:
                    t_in = (np.array(points_6d[i+1][:3]) - np.array(points_6d[i-1][:3])) * 0.5
            tangents_in_3d.append(t_in)

            # ---  (Out-Tangent) ---
            if angle_out is not None:
                rad_out = np.radians(angle_out)
                if is_profile:
                    t_out = np.array([np.cos(rad_out), 0.0, np.sin(rad_out)])
                else:
                    t_out = np.array([0.0, np.cos(rad_out), np.sin(rad_out)])
            else:
                if i == 0:
                    t_out = np.array(points_6d[i+1][:3]) - np.array(points_6d[i][:3])
                elif i == len(points_6d) - 1:
                    t_out = np.array(points_6d[i][:3]) - np.array(points_6d[i-1][:3])
                else:
                    t_out = (np.array(points_6d[i+1][:3]) - np.array(points_6d[i-1][:3])) * 0.5
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

    def run(self):
        from geomdl import BSpline as bsplinesurf
        from geomdl import fitting
        import pyvista as pv
        import numpy as np

        self.station_order = sorted(self.main_window.stations.keys())
        self.waterlines = getattr(self.main_window, 'waterlines', {})
        profile_pts = getattr(self.main_window, 'profile_points', [])

        if len(self.station_order) < 2:
            print("Need minimum 2 stations to make a surface")
            return

        plotter = pv.Plotter(title="Jalayn CAD Engine - Controlled Tangent NURBS Surface")
        plotter.set_background("white")

        n_samples_per_curve = 60
        size_v = n_samples_per_curve
        
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

        # A. ADD STERN
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

        # B. ADD STATION
        for sx in self.station_order:
            raw_pts_6d = self.main_window.stations[sx]
            smooth_pts = self.evaluate_hermite_spline_3d(raw_pts_6d, n_samples=size_v, is_profile=False)
            
            if len(smooth_pts) >= 2 and smooth_pts[0][2] > smooth_pts[-1][2]:
                smooth_pts = smooth_pts[::-1]

            if len(smooth_pts) > 0:
                smooth_pts[0][1] = 0.0 

            all_cross_sections.append(smooth_pts)

        # C. ADD STEM
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

        # Convert
        points_list = []
        for section in all_cross_sections:
            for pt in section:
                points_list.append([pt[0], pt[1], pt[2]])

        size_u = len(all_cross_sections)
        surf_actor = None

        try:
            degree_u = 1 
            degree_v = 3 
            
            surf = fitting.interpolate_surface(points_list, size_u, size_v, degree_u, degree_v)
            
            sample_u = 60
            sample_v = 60
            surf.sample_size_u = sample_u
            surf.sample_size_v = sample_v
            surf.evaluate()

            vertices = np.array(surf.evalpts, dtype=np.float32)

            grid_long = pv.StructuredGrid()
            grid_long.points = vertices
            grid_long.dimensions = [sample_v, sample_u, 1]

            surf_master = grid_long.extract_surface(algorithm='dataset_surface')

            surf_actor = plotter.add_mesh(surf_master, color="gray", opacity=0.85, smooth_shading=True, 
                             specular=0.15, specular_power=10, show_edges=False, label="NURBS Surface")

        except Exception as e:
            print(f"Gagal melakukan interpolasi NURBS Surface: {e}")

        # Wireframe
        wf_actors = []

        for sx in self.station_order:
            if sx in self.main_window.stations:
                raw_st = self.evaluate_hermite_spline_3d(self.main_window.stations[sx], n_samples=100, is_profile=False)
                act_st = plotter.add_mesh(pv.lines_from_points(np.array(raw_st)), color="black", line_width=1.5)
                wf_actors.append(act_st)

        if self.waterlines:
            for z, wpts in self.waterlines.items():
                pts_wl = np.array([p[:3] for p in wpts])
                if len(pts_wl) >= 2:
                    pts_wl[:, 1] = np.maximum(0.0, pts_wl[:, 1])
                    act_wl = plotter.add_mesh(pv.lines_from_points(np.array(pts_wl)), color="blue", line_width=1.5)
                    wf_actors.append(act_wl)
        
        if hasattr(self.main_window, 'buttocklines') and self.main_window.buttocklines:
            for y_val, bl_pts in self.main_window.buttocklines.items():
                pts_bl = np.array([p[:3] for p in bl_pts])
                if len(pts_bl) >= 2:
                    act_bl = plotter.add_mesh(pv.lines_from_points(pts_bl), color="green", line_width=1.5, label="Buttockline" if y_val == list(self.main_window.buttocklines.keys())[0] else None)
                    wf_actors.append(act_bl)

        if len(profile_pts) >= 2:
            act_prof = plotter.add_mesh(pv.lines_from_points(np.array(smooth_profile)), color="cyan", line_width=2.5, label="Profile Line")
            wf_actors.append(act_prof)

        # Button
        # --- BUTTON 1: WIREFRAME ---
        def toggle_wf(state):
            for actor in wf_actors:
                actor.visibility = state

        plotter.add_checkbox_button_widget(
            callback=toggle_wf,
            value=True,
            color_on="blue",
            color_off="gray",
            background_color="white",
            size=25,
            position=(10, 10)
        )
        plotter.add_text("Wireframe", position=(45, 13), font_size=10, color="black")

        # --- BUTTON 2: SURFACE HULL  ---
        def toggle_surf(state):
            if surf_actor is not None:
                surf_actor.visibility = state

        plotter.add_checkbox_button_widget(
            callback=toggle_surf,
            value=True,
            color_on="green",
            color_off="gray",
            background_color="white",
            size=25,
            position=(10, 45)
        )
        plotter.add_text("Surface Hull", position=(45, 48), font_size=10, color="black")

        # Cube
        if hasattr(plotter, 'add_camera_orientation_widget'):
            view_cube = plotter.add_camera_orientation_widget()

        plotter.add_axes()
        plotter.enable_lightkit()
        plotter.show()