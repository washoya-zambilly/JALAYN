#nurbs. py
import numpy as np

class NurbsSurface:
    def __init__(self, P, W, U, V, p, q):
        self.P = np.array(P)     # (nu, nv, 3)
        self.W = np.array(W)
        self.U = U
        self.V = V
        self.p = p
        self.q = q
        self.nu, self.nv = self.P.shape[:2]

    @staticmethod
    def bspline_basis(i, k, t, knots, n_ctrl):
        if k == 0:
            if knots[i] <= t < knots[i+1]:
                return 1.0
            if t == knots[-1] and i == n_ctrl - 1:
                return 1.0
            return 0.0

        d1 = knots[i+k] - knots[i]
        d2 = knots[i+k+1] - knots[i+1]


        a = 0.0
        b = 0.0

        if d1 > 0:
            a = (t - knots[i]) / d1 * NurbsSurface.bspline_basis(
                i, k-1, t, knots, n_ctrl
            )
        if d2 > 0:
            b = (knots[i+k+1] - t) / d2 * NurbsSurface.bspline_basis(
                i+1, k-1, t, knots, n_ctrl
            )

        return a + b
    

    def evaluate(self, u, v):
        num = np.zeros(3)
        den = 0.0

        for i in range(self.nu):
            Ni = self.bspline_basis(i, self.p, u, self.U, self.nu)
            if Ni == 0:
                continue
            for j in range(self.nv):
                Nj = self.bspline_basis(j, self.q, v, self.V, self.nv)
                if Nj == 0:
                    continue
                w = self.W[i, j]
                B = Ni * Nj * w
                num += B * self.P[i, j]
                den += B

        return num / den
    

    def insert_knot_v(self, v_new):
        """Insert knot in v-direction (refinement) Shape-preserving"""
        p = self.q
        V = list(self.V)

        # count multiplicity
        s = V.count(v_new)
        if s >= p:
            return  # cannot insert more

        # find span
        k = max(i for i in range(len(V)-1) if V[i] <= v_new < V[i+1])

        # new knot vector
        V_new = V[:k+1] + [v_new] + V[k+1:]

        nu, nv = self.nu, self.nv
        P_new = np.zeros((nu, nv + 1, 3))
        W_new = np.zeros((nu, nv + 1))

        alpha = np.zeros((nv + 1))

        for j in range(k-p+1, k+1):
            denom = V[j+p] - V[j]
            alpha[j] = 0 if denom == 0 else (v_new - V[j]) / denom

        for i in range(nu):
            # unaffected
            for j in range(0, k-p+1):
                P_new[i, j] = self.P[i, j]
                W_new[i, j] = self.W[i, j]

            # affected
            for j in range(k-p+1, k+1):
                P_new[i, j] = (
                    alpha[j] * self.P[i, j] +
                    (1 - alpha[j]) * self.P[i, j-1]
                )
                W_new[i, j] = (
                    alpha[j] * self.W[i, j] +
                    (1 - alpha[j]) * self.W[i, j-1]
                )

            # remaining
            for j in range(k+1, nv+1):
                P_new[i, j] = self.P[i, j-1]
                W_new[i, j] = self.W[i, j-1]

        self.P = P_new
        self.W = W_new
        self.V = np.array(V_new)
        self.nv += 1

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
                U[j] = (j - degree) / (m - 2 * degree)

        return U
