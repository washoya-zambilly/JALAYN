#geometry_nurbs.py
from scipy.interpolate import CubicSpline
import numpy as np
from .nurbs import NurbsSurface


class Nurbs_geometry: 
    def __init__(self):
        self.surface = None
        self.station_frames = []   

    def resample_station(points, n):
        y = [p[1] for p in points]
        z = [p[2] for p in points]

        t = np.linspace(0, 1, len(points))
        cs_y = CubicSpline(t, y)
        cs_z = CubicSpline(t, z)

        t2 = np.linspace(0, 1, n)
        return list(zip(cs_y(t2), cs_z(t2)))


    @staticmethod
    def loft_surface_from_stations(
        stations,
        station_order,
        deg_u=3,
        deg_v=3,
        n_v=25
    ):

        xs = station_order
        nu = len(xs)
        nv = n_v

        # ================================
        # 1. Z max global
        # ================================
        z_max = 0.0
        for x in xs:
            for _, _, z in stations[x]:
                z_max = max(z_max, z)

        # V global (waterline virtual)
        V_global = np.linspace(0.0, 1.0, nv)

        # ================================
        # 2. Control net
        # ================================
        P = np.zeros((nu, nv, 3))
        W = np.ones((nu, nv))

        for i, x in enumerate(xs):
            # sort station by z
            pts = sorted(stations[x], key=lambda p: p[2])

            y_vals = np.array([p[1] for p in pts])
            z_vals = np.array([p[2] for p in pts])

            # interpolation
            from scipy.interpolate import CubicSpline

            # length curve station (arc-length)
            dy = np.diff(y_vals)
            dz = np.diff(z_vals)
            ds = np.sqrt(dy**2 + dz**2)

            s = np.concatenate(([0.0], np.cumsum(ds)))

            if s[-1] < 1e-6:
                s = np.linspace(0, 1, len(y_vals))
            else:
                s /= s[-1]

            # spline Y(s) & Z(s)
            cs_y = CubicSpline(s, y_vals)
            cs_z = CubicSpline(s, z_vals)

            # sample 
            y_new = cs_y(V_global)
            z_new = cs_z(V_global)

            # 🔒 lock sheer (optional)
            z_new[-1] = z_max


            for j in range(nv):
                P[i, j, 0] = x
                P[i, j, 1] = y_new[j]
                P[i, j, 2] = z_new[j]

        # ================================
        # 3. Knot vector (OPEN UNIFORM)
        # ================================
        U = NurbsSurface.open_uniform_knot(nu, deg_u)
        V = NurbsSurface.open_uniform_knot(nv, deg_v)

        return NurbsSurface(P, W, U, V, deg_u, deg_v)



    def sample_surface(surface, nu=50, nv=30):
        return np.array([
            [surface.evaluate(u, v)
            for v in np.linspace(0, 1, nv)]
            for u in np.linspace(0, 1, nu)
        ])


    @staticmethod
    def find_v_for_waterline(surface, z_target, u=0.5, n=200):
        vs = np.linspace(0, 1, n)
        best_v = 0
        best_err = 1e9

        for v in vs:
            pt = surface.evaluate(u, v)
            err = abs(pt[2] - z_target)
            if err < best_err:
                best_err = err
                best_v = v

        return best_v
    

    @staticmethod
    def refine_surface_by_waterlines(surface, waterline_zs):
        for z in waterline_zs:
            v = Nurbs_geometry.find_v_for_waterline(surface, z)
            surface.insert_knot_v(v)

    
    def add_station_frame(self, x_pos, yz_points, n_samples=50, collapse=False):
        frame = StationFrame(
            x_pos,
            yz_points,
            n_samples=n_samples,
            collapse=collapse
        )
        self.station_frames.append(frame)


    @staticmethod
    def build_virtual_station_from_centerline(
        centerline_pts,
        x_target,
        z_span=0.5,
        n=8
    ):
        """
        Build degenerate station from centerline
        centerline_pts: [(x,z)] atau [(x,y,z)]
        """

        xs = []
        zs = []

        for p in centerline_pts:
            if len(p) == 2:
                x, z = p
            elif len(p) == 3:
                x, _, z = p
            else:
                raise ValueError("Centerline point format invalid")

            xs.append(x)
            zs.append(z)

        xs = np.array(xs)
        zs = np.array(zs)

        # spline Z(X)
        cs_z = CubicSpline(xs, zs, extrapolate=True)
        z0 = cs_z(x_target)

        # buat station degenerate (Y=0)
        zs_local = np.linspace(z0 - z_span, z0, n)
        ys_local = np.zeros_like(zs_local)

        return [(x_target, y, z) for y, z in zip(ys_local, zs_local)]
    


    @staticmethod
    def build_gordon_surface(
        station_curves,    # list of NurbsCurve (parameter v)
        waterline_curves,  # list of NurbsCurve (parameter u)
        nu=40,
        nv=30
    ):
        """
        Gordon Surface:
        - station_curves  : interpolatory curves (YZ)
        - waterline_curves: interpolatory curves (XY)
        """

        # ==============================
        # 1. Sample grid
        # ==============================
        u_vals = np.linspace(0, 1, nu)
        v_vals = np.linspace(0, 1, nv)

        Su = np.zeros((nu, nv, 3))
        Sv = np.zeros((nu, nv, 3))
        Suv = np.zeros((nu, nv, 3))

        # ==============================
        # 2. Surface from stations
        # ==============================
        for i, u in enumerate(u_vals):
            idx = int(u * (len(station_curves) - 1))
            curve = station_curves[idx]

            for j, v in enumerate(v_vals):
                Su[i, j] = curve.evaluate(v)

        # ==============================
        # 3. Surface from waterlines
        # ==============================
        for j, v in enumerate(v_vals):
            idx = int(v * (len(waterline_curves) - 1))
            curve = waterline_curves[idx]

            for i, u in enumerate(u_vals):
                Sv[i, j] = curve.evaluate(u)

        # ==============================
        # 4. Correction surface
        # ==============================
        for i, u in enumerate(u_vals):
            idx_u = int(u * (len(station_curves) - 1))
            c_u = station_curves[idx_u]

            for j, v in enumerate(v_vals):
                idx_v = int(v * (len(waterline_curves) - 1))
                c_v = waterline_curves[idx_v]

                Suv[i, j] = 0.5 * (
                    c_u.evaluate(v) +
                    c_v.evaluate(u)
                )

        # ==============================
        # 5. Final Gordon surface grid
        # ==============================
        Q = Su + Sv - Suv

        # ==============================
        # 6. Interpolate surface from Q
        # ==============================
        return Q


    @staticmethod
    def build_gordon_surface_grid(
        station_frames,     # list of StationFrame (sudah resample!)
        waterline_zs        # list of Z (waterline)
        ):
        """
        Gordon Surface GRID-LOCKED
        - station_frames harus punya jumlah sample YZ sama
        - waterline_zs diambil dari domain Z yang sama
        """

        n_station = len(station_frames)
        n_v = len(station_frames[0].yz)
        n_wl = len(waterline_zs)

        # ==============================
        # 1. GRID from STATION
        # S[i,j]
        # ==============================
        S = np.zeros((n_station, n_v, 3))

        for i, frame in enumerate(station_frames):
            for j, (y, z) in enumerate(frame.yz):
                S[i, j] = [frame.x, y, z]

        # ==============================
        # 2. GRID from WATERLINE
        # W[j,i]
        # ==============================
        W = np.zeros((n_wl, n_station, 3))
        I = np.zeros((n_station, n_v, 3))  # intersection

        z_min = min(
            z for frame in station_frames
            for _, z in frame.yz
            )

        for j, z_wl in enumerate(waterline_zs):

            is_bottom = abs(z_wl - z_min) < 1e-6

            for i, frame in enumerate(station_frames):
                ys = [p[0] for p in frame.yz]
                zs = [p[1] for p in frame.yz]

                # ensure z valid
                if z_wl < zs[0] or z_wl > zs[-1]:
                    W[j, i] = [frame.x, 0.0, z_wl]
                    continue

                y = np.interp(z_wl, zs, ys)
                W[j, i] = [frame.x, y, z_wl]

                if is_bottom:
                    continue 

        # ==============================
        # 3. INTERSECTION GRID
        # I[i,j]
        # ==============================
        for i in range(n_station):
            for j in range(n_v):
                I[i, j] = S[i, j]  # identic by construction

        # ==============================
        # 4. GORDON FORMULA (GRID)
        # ==============================
        Q = np.zeros_like(S)

        z_min = min(
            z for frame in station_frames
            for _, z in frame.yz
        )

        for i in range(n_station):
            for j in range(n_v):
                z = S[i, j, 2]

                # bottom = station only
                if abs(z - z_min) < 1e-6:
                    Q[i, j] = S[i, j]
                    continue

                k = np.argmin(np.abs(np.array(waterline_zs) - z))
                Q[i, j] = S[i, j] + W[k, i] - I[i, j]

        return Q


    @staticmethod
    def build_surface_from_buttock(
        station_frames,
        buttockline_points
    ):
        """
        SIMPLE bottom surface from buttock lines
        - station_frames : list StationFrame (punya x)
        - buttockline_points[y] = [(x,z), ...]
        """

        # 1️⃣ grid Y from buttock
        Y = sorted(buttockline_points.keys())
        X = [frame.x for frame in station_frames]

        n_station = len(X)
        n_buttock = len(Y)

        Q = np.zeros((n_station, n_buttock, 3))

        # 2️⃣ loop buttock
        for j, y in enumerate(Y):
            pts = buttockline_points[y]
            pts = sorted(pts, key=lambda p: p[0])  # sort by x

            xs = [p[0] for p in pts]
            zs = [p[1] for p in pts]

            # spline z(x)
            cs = CubicSpline(xs, zs, extrapolate=True)

            # 3️⃣ isi surface
            for i, x in enumerate(X):
                z = cs(x)
                Q[i, j] = [x, y, z]

        return Q


class StationFrame:
    def __init__(self, x_pos, yz_points, n_samples=50, collapse=False):
        """
        x_pos     : position station (meter)
        yz_points : [(y, z), ...] from station 
        """
        self.x = x_pos

        # resample 
        yz = Nurbs_geometry.resample_station(
            [(None, y, z) for y, z in yz_points],
            n_samples
        )

        # ============================
        # degenerate station
        # ============================
        if collapse:
            self.yz = [(0.0, z) for (_, z) in yz]
        else:
            self.yz = yz


    def evaluate(self):
        """
        Return [(x, y, z), ...]
        """
        return [(self.x, y, z) for y, z in self.yz]



