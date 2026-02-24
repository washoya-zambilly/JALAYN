# nurbs_curve.py
import numpy as np
from scipy.interpolate import CubicSpline

class NurbsCurve:
    def __init__(self, P, W=None, U=None, degree=3):
        """
        P : array control point (n,3)
        W : weight (optional), default 1
        U : knot vector (optional), default open uniform
        degree : degree B-spline
        """
        self.P = np.array(P)
        self.n = len(P)
        self.degree = degree
        self.W = np.ones(self.n) if W is None else np.array(W)
        self.U = self.open_uniform_knot(self.n, degree) if U is None else np.array(U)

    def evaluate(self, t):
        u = t
        xs = np.linspace(0, 1, self.n)
        cs_x = CubicSpline(xs, self.P[:,0])
        cs_y = CubicSpline(xs, self.P[:,1])
        cs_z = CubicSpline(xs, self.P[:,2])
        return np.array([cs_x(u), cs_y(u), cs_z(u)])

    @staticmethod
    def from_points(points, degree=3):
        """
        Make NurbsCurve from list [(x,y,z), ...]
        """
        P = np.array(points)
        return NurbsCurve(P, degree=degree)

    @staticmethod
    def open_uniform_knot(n_ctrl, degree):
        n = n_ctrl - 1
        m = n + degree + 1
        U = np.zeros(m + 1)
        for j in range(m + 1):
            if j <= degree:
                U[j] = 0.0
            elif j >= m - degree:
                U[j] = 1.0
            else:
                U[j] = (j - degree) / (m - 2*degree)
        return U
