#viewer3d2.py
from core.geometry_nurbs import Nurbs_geometry
from tkinter import messagebox
import numpy as np
from core.nurbs_curve import NurbsCurve
from scipy.interpolate import interp1d
import multiprocessing as mp

class Viewer3D:
    def __init__(self):
        self.stations = {}
        self.station_order = []
        self.geom = Nurbs_geometry()

    def laplacian_smooth(S, iters=5, alpha=0.25):
        S = S.copy()
        for _ in range(iters):
            S_new = S.copy()
            for i in range(1, S.shape[0]-1):
                for j in range(1, S.shape[1]-1):
                    S_new[i, j] = S[i, j] + alpha * (
                        (S[i-1, j] + S[i+1, j] + S[i, j-1] + S[i, j+1]) / 4 - S[i, j]
                    )
            S = S_new
        return S

    def preview_hull_3d(self):
        if len(self.station_order) < 4:
            messagebox.showwarning(
                "Warning",
            "Need at least 4 stations to preview hull"
            )
            return

        # 1 Clear station frames
        self.geom.station_frames.clear()

        # 2 Add stations
        x_bow   = self.station_order[0]
        x_stern = self.station_order[-1]

        for x in self.station_order:
            yz_pts = [(p[1], p[2]) for p in self.stations[x]]

            self.collapse_bow = False
            self.collapse_stern = True

            collapse = (x == x_bow and self.collapse_bow) or (x == x_stern and self.collapse_stern)

            ys = [abs(p[1]) for p in yz_pts]
            curv_hint = max(ys) - min(ys)   
            n_samples = max(40, min(int(40 + curv_hint * 20), 70))
            
            self.geom.add_station_frame(
                x,
                yz_pts,
                #n_samples=500,
                n_samples=n_samples,
                collapse=collapse 
            )

        # 3 Create NURBS
        station_curves = []
        for frame in self.geom.station_frames:
            pts = frame.evaluate()  # [(x,y,z), ...]
            
            station_curves.append(NurbsCurve.from_points(pts))


        # 4 Add waterlines
        waterline_curves = []
        if hasattr(self, "waterline_order") and self.waterline_order:
            for z in self.waterline_order:
                pts = []
                for frame in self.geom.station_frames:
                    
                    zs = [p[1] for p in frame.yz]
                    ys = [p[0] for p in frame.yz]

                    y_interp = np.interp(z, zs, ys)

                    pts.append((frame.x, y_interp, z))
                waterline_curves.append(NurbsCurve.from_points(pts))

                
        # 5 Sample surface grid
        S = Nurbs_geometry.build_gordon_surface_grid(
            station_frames=self.geom.station_frames,
        waterline_zs=self.waterline_order
        )

        # fairness optional
        #S = Viewer3D.laplacian_smooth(S, iters=6, alpha=0.25)

        # 6 Bottom override 
        if hasattr(self, "buttockline_points") and self.buttockline_points:

            B = Nurbs_geometry.build_surface_from_buttock(
                station_frames=self.geom.station_frames,
                buttockline_points=self.buttockline_points
            )

            Y_s = [S[0, j, 1] for j in range(S.shape[1])]

            Y_b = sorted(B[0, :, 1])

            B_interp = np.zeros_like(S)
            for i in range(B.shape[0]):  
                f = interp1d(Y_b, B[i, :, 2], kind='cubic', fill_value='extrapolate')
                for j, y in enumerate(Y_s):
                    B_interp[i, j, 0] = S[i, j, 0]  # x
                    B_interp[i, j, 1] = y           # y
                    B_interp[i, j, 2] = f(y)       

            z_min = np.min(S[:, :, 2])
            z_range = np.max(S[:, :, 2]) - z_min
            z_cut = z_min + 0.08 * z_range   # 5–10% draft

            blend_band = 0.03 * z_range 

            for i in range(S.shape[0]):
                for j in range(S.shape[1]):
                    z = S[i, j, 2]
                    if z <= z_cut:
                        S[i, j] = B_interp[i, j]
                    elif z <= z_cut + blend_band:
                        t = (z - z_cut) / blend_band  # 0..1
                        S[i, j] = (1 - t) * B_interp[i, j] + t * S[i, j]
            
        # 7 Convert 
        vertices, faces = self.surface_to_mesh(S)
        self.show_mesh_vispy(vertices, faces)


    def draw_station_frames(self):
        if not self.geom.station_frames:
            return

        for frame in self.geom.station_frames:
            pts = frame.evaluate(n=50)

            for i in range(len(pts) - 1):
                x1, y1, z1 = pts[i]
                x2, y2, z2 = pts[i + 1]

                sx1, sy1 = self.project(x1, y1, z1)
                sx2, sy2 = self.project(x2, y2, z2)

                self.canvas.create_line(
                    sx1, sy1, sx2, sy2,
                    fill="#666666",    
                    width=1,
                    dash=(3, 3)
                )


    def surface_to_mesh(self, S):
        nu, nv, _ = S.shape
        vertices = S.reshape(-1, 3).astype(np.float32)

        faces = []
        for i in range(nu - 1):
            for j in range(nv - 1):
                p0 = i * nv + j
                p1 = p0 + 1
                p2 = p0 + nv
                p3 = p2 + 1
                faces.append([p0, p1, p2])
                faces.append([p1, p3, p2])

        return vertices, np.array(faces, dtype=np.uint32)
    

    def redraw(self):
        self.canvas.delete("all")

        self.draw_surface()        
        self.draw_station_frames()  


    def create_station_lines_vispy(self, view):
        from vispy import scene
        import numpy as np

        for frame in self.geom.station_frames:
            pts = np.array(frame.evaluate(), dtype=np.float32)

            scene.visuals.Line(
                pos=pts,
                color=(0.2, 0.2, 0.2, 1.0),  
                width=2,
                parent=view.scene
            )

 
    def show_mesh_vispy(self, vertices, faces):
        mp.set_start_method("spawn", force=True)

        p = mp.Process(
            target=run_vispy_viewer,
            args=(vertices, faces)
        )
        p.start()

#------------------------------------
#  VISPY VIEWER
#------------------------------------
def add_axes(view, length=1.0):
    from vispy import scene
    import numpy as np

    # X axis
    x = np.array([[0, 0, 0], [length, 0, 0]], dtype=np.float32)
    scene.visuals.Line(pos=x, color=(1, 0, 0, 1), width=3, parent=view.scene)

    # Y axis
    y = np.array([[0, 0, 0], [0, length, 0]], dtype=np.float32)
    scene.visuals.Line(pos=y, color=(0, 1, 0, 1), width=3, parent=view.scene)

    # Z axis
    z = np.array([[0, 0, 0], [0, 0, length]], dtype=np.float32)
    scene.visuals.Line(pos=z, color=(0, 0, 1, 1), width=3, parent=view.scene)


def run_vispy_viewer(vertices, faces):
    from vispy import scene, app
    from vispy.color import Color
    from vispy.geometry import MeshData
    import numpy as np

    mesh_data = MeshData(
        vertices=np.asarray(vertices, dtype=np.float32),
        faces=np.asarray(faces, dtype=np.uint32)
    )

    canvas = scene.SceneCanvas(
        keys='interactive',
        show=True,
        title='Hull Preview'
    )

    view = canvas.central_widget.add_view()
    view.camera = scene.cameras.TurntableCamera(
        fov=35,
        azimuth=30,
        elevation=25,
        distance=3.0
    )

    scene.visuals.Mesh(
        meshdata=mesh_data,
        shading='smooth',
        color=Color("#c4161c"),
        parent=view.scene       
    )
    
    # L For Axis
    Lx = np.max(vertices[:, 0]) - np.min(vertices[:, 0])
    Ly = np.max(vertices[:, 1]) - np.min(vertices[:, 1])
    Lz = np.max(vertices[:, 2]) - np.min(vertices[:, 2])

    L = max(Lx, Ly, Lz)

    # Add Axis
    add_axes(view, length=0.2 * L)

    # Light setting
    view.scene.light_dir = (1, 1, 1)

    app.run()
