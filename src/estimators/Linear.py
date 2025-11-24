##################################################################################################################################################################################

from . import *
import numpy as np

####################################################################################################################################################################################

class LinearEstimator:
    """
    Estimate the scale m in the model y = m * x
    where x_i are strictly increasing positive integers
    with minimum step 1 (x_{i+1} >= x_i + 1).

    Estimation is done by:
    1) scanning a grid of candidate m values
    2) for each m, computing the best integer sequence x via dynamic programming
    """

    @staticmethod
    def best_x_for_m_dp(y, m, xmin, xmax):
        """
        Given m, compute the optimal strictly increasing integer sequence x_i ∈ [xmin, xmax]
        minimizing sum (y_i - m*x_i)^2 using dynamic programming.
        Returns (x, cost).
        Complexity: O(n * (xmax-xmin)).
        """
        y = np.asarray(y, float)
        n = len(y)
        xs = np.arange(xmin, xmax + 1)
        V = len(xs)

        # DP initialization
        dp_prev = (y[0] - m * xs) ** 2
        parents = [np.full(V, -1, dtype=int)]

        # DP forward pass
        for i in range(1, n):
            cost_here = (y[i] - m * xs) ** 2

            # prefix min of previous DP layer
            prefix_min = np.minimum.accumulate(dp_prev)

            dp = np.empty(V)
            dp[0] = np.inf                       # cannot choose smallest x (no parent < 0)
            dp[1:] = cost_here[1:] + prefix_min[:-1]

            # argmin parents
            argmins = np.zeros(V, dtype=int)
            best_idx = 0
            for j in range(1, V):
                if dp_prev[j] < dp_prev[best_idx]:
                    best_idx = j
                argmins[j] = best_idx

            parent = np.empty(V, dtype=int)
            parent[0] = -1
            parent[1:] = argmins[:-1]
            parents.append(parent)

            dp_prev = dp

        # Backtracking
        j = int(np.argmin(dp_prev))
        x_idx = np.empty(n, dtype=int)
        x_idx[-1] = j
        for i in range(n - 1, 0, -1):
            x_idx[i - 1] = parents[i][x_idx[i]]

        return xs[x_idx], float(dp_prev[j])

    @staticmethod
    def estimate_m_and_x_dp(y, xmin=1, xmax=None, m_grid=None):
        """
        Estimate m and the optimal integer sequence x using grid-search on m
        + dynamic programming for x for each tested m.
        Returns (best_m, best_x, best_cost).
        """
        y = np.asarray(y, float)
        n = len(y)

        if xmax is None:
            xmax = xmin + n + 50  # heuristic range

        if xmax <= xmin + n - 1:
            raise ValueError("xmax too small: must allow strictly increasing x values.")

        # Default m grid
        ymax = max(1.0, np.max(np.abs(y)))
        if m_grid is None:
            m_min = 1e-6
            m_max = max(1.0, ymax / max(1, xmin))
            m_grid = np.concatenate([
                np.linspace(m_min, m_max, 50),
                np.linspace(m_max, 3 * m_max, 30)
            ])

        best_m, best_x, best_cost = None, None, np.inf

        for m in m_grid:
            x, cost = LinearEstimator.best_x_for_m_dp(y, m, xmin, xmax)
            if cost < best_cost:
                best_m, best_x, best_cost = m, x, cost

        return best_m, best_x, best_cost

    def __call__(self, y, xmin=1, xmax=None, m_grid=None):
        """
        Estimate m and the optimal integer sequence x using grid-search on m
        + dynamic programming for x for each tested m.
        Returns (best_m, best_x, best_cost).
        """
        return self.estimate_m_and_x_dp(y, xmin, xmax, m_grid)  
    
####################################################################################################################################################################################
