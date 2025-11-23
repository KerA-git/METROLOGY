####################################################################################################
#                                             IMPORTS
####################################################################################################

from . import *
from .capteur import Sensor
from .generator import GeneratorCube

####################################################################################################
#                                             Extraction
####################################################################################################

class StaticAnalysisExtraction:
    """
    Data analysis from the sensor :
    - extract velocity and position
    - emission rate estimation

    Analysis done after run.
    """

    def __init__(self,time_duration : float , sensor : Sensor , generator : GeneratorCube):
        """
        sensor : instance de Sensor dont on lit les records
        """
        self.sensor = sensor
        self.generator = generator
        # data properties
        self.times = np.array([r["t"] for r in self.sensor.records]) # Array of detection times.
        self.pos =  np.array([r["pos"][0] for r in self.sensor.records]) # Nx3 array of detected positions.
        self.vel = np.array([r["vel"][0] for r in self.sensor.records]) # Nx3 array of detected velocities.
        #self.speed = np.linalg.norm(self.vel, axis=1) # Array of speed.
        # Time:
        self.stop = time_duration # end time of the simulation.

    # for printing - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - :
    def __str__(self):
        """Human-readable summary of the extracted static analysis."""
        return (
            "======    Static Analysis Extraction    ======:\n\n"
            f" Global Summary:\n\n"
            f"  Sensor records: {len(self.times)} detections\n"
            f"  Duration Simulation: {self.stop:.4f} s\n"
            f"  Generator type: {type(self.generator).__name__}\n"
            f"==============================================\n"
        )


    def __repr__(self):
        """ technical representation."""
        x_range = (self.pos[:,0].min(), self.pos[:,0].max()) if len(self.times) > 0 else (0,0)
        y_range = (self.pos[:,1].min(), self.pos[:,1].max()) if len(self.times) > 0 else (0,0)
        z_range = (self.pos[:,2].min(), self.pos[:,2].max()) if len(self.times) > 0 else (0,0)
        return (
            f"  Position range:\n"
            f"    X in [{x_range[0]:.3f}, {x_range[1]:.3f}]\n"
            f"    Y in [{y_range[0]:.3f}, {y_range[1]:.3f}]\n"
            f"    Z in [{z_range[0]:.3f}, {z_range[1]:.3f}]\n\n"
            f" Local precision : \n\n"
            f"  times Array: {self.times}\n"
            f"  pos Array: {self.pos}\n"
            f"  vel Array: {self.vel}\n"
        )

    def estimate_residence_times(self, min_speed_tol: float = 1e-8) -> np.ndarray:
        """
        Estimate the residence time for each detected particle using the sensor geometry.

        Principle:
        - Convert each detected particle velocity to the sensor local frame using the
          sensor visual transform.
        - The thickness / height of the sensor along its local Z axis defines the
          crossing distance. Residence time is height / |v_z_local|.
        - If v_z_local is (near) zero, the residence time is capped to the remaining
          simulation time (self.stop - detection_time).

        Returns:
            numpy array of residence times (same length as `self.times`).
        """
        if len(self.times) == 0:
            return np.array([])

        # Get sensor transform (VisPy 4x4 matrix)
        M = self.sensor.visual.transform.matrix
        R = M[:3, :3]
        T = M[3, :3]

        # local box bounds (following Sensor.detect convention)
        half_x = float(self.sensor.width) / 2.0
        half_y = float(self.sensor.depth) / 2.0
        half_z = float(self.sensor.height) / 2.0

        residence = np.empty(len(self.times), dtype=float)

        for i in range(len(self.times)):
            t0 = float(self.times[i])
            p_global = self.pos[i]
            v_global = self.vel[i]

            # transform to sensor local frame (same convention as detect)
            p_local = (R.T @ (p_global - T))
            v_local = (R.T @ v_global)

            # Slab method for ray-box intersection; here param is time (because v is m/s)
            bounds_min = np.array([-half_x, -half_y, -half_z], dtype=float)
            bounds_max = np.array([half_x, half_y, half_z], dtype=float)

            t_enter = -np.inf
            t_exit = np.inf
            valid = True

            for axis in range(3):
                pv = p_local[axis]
                vv = v_local[axis]
                if abs(vv) < min_speed_tol:
                    # Ray is parallel to slab. If outside slab -> no intersection
                    if pv < bounds_min[axis] or pv > bounds_max[axis]:
                        valid = False
                        break
                    else:
                        # No constraint from this axis
                        continue
                t1 = (bounds_min[axis] - pv) / vv
                t2 = (bounds_max[axis] - pv) / vv
                t_axis_enter = min(t1, t2)
                t_axis_exit = max(t1, t2)
                if t_axis_enter > t_enter:
                    t_enter = t_axis_enter
                if t_axis_exit < t_exit:
                    t_exit = t_axis_exit

            if (not valid) or (t_exit < t_enter):
                # no intersection -> zero residence (shouldn't happen for detected points)
                residence_i = 0.0
            else:
                # We assume detection time corresponds to being inside the box. The
                # remaining time until exit is t_exit if t_exit > 0, otherwise 0.
                residence_i = max(0.0, float(t_exit))

            # Cap to remaining simulation time
            residence_i = min(residence_i, max(0.0, self.stop - t0))
            residence[i] = residence_i

        # store for later use
        self.residence_times = residence
        return residence


    def occupation_array(self, fs: float = None) -> tuple:
        """
        Build an occupation time-series (number of particles inside the sensor) sampled
        at frequency `fs` (defaults to the sensor sampling rate `sensor.fs`).

        Uses detected times (`self.times`) and residence times (computed with
        `estimate_residence_times`) to create intervals [t_detect, t_detect + residence]
        and counts how many intervals cover each sampling instant.

        Returns:
            times: 1D numpy array of sampling times
            counts: 1D numpy array with occupation counts at each sampling time
        """
        """
        Build an occupation array (single array of counts n_k) sampled at frequency
        `fs` (defaults to the sensor sampling rate `sensor.fs`).

        Returns:
            counts: 1D numpy array of length K with occupation counts n_k at each
                    sampling instant (used by `mean_occupation`).
        """
        if fs is None:
            fs = float(self.sensor.fs)

        if not hasattr(self, 'residence_times'):
            self.estimate_residence_times()

        T = float(self.stop)
        if T <= 0 or fs <= 0:
            return np.array([])

        # sampling grid
        n_samples = int(np.ceil(T * fs)) + 1
        times = np.arange(n_samples) / fs

        starts = self.times
        ends = np.minimum(self.times + self.residence_times, T)

        # convert intervals to sample indices
        idx_start = np.floor(starts * fs).astype(int)
        idx_end = np.ceil(ends * fs).astype(int)

        # event counting (prefix sum trick)
        events = np.zeros(n_samples + 1, dtype=int)
        for s, e in zip(idx_start, idx_end):
            if s < 0:
                s = 0
            if e < 0:
                e = 0
            if s >= len(events):
                continue
            events[s] += 1
            if e < len(events):
                events[e] -= 1

        counts = np.cumsum(events)[:n_samples]

        # store times for reference but return only the counts array as requested
        self.occupation_times = times
        self.occupation = counts
        return counts

####################################################################################################
#                                             Estimators
####################################################################################################

