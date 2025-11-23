####################################################################################################################################################################

from . import *

from typing import List

####################################################################################################################################################################

class Sensor:
    """
    Measurement modelisation.
    
    Coordinates:
        u-axis  → width
        v-axis  → depth
        n-axis  → thickness (normal to the detector plane)
    """

    def __init__(self,
                 width=1,
                 depth=3,
                 height=0.5,
                 direction=(0, 0, 1),
                 pos=(3, 0, 0),
                 fs=1000,
                 parent=None,
                 show_visual=True):

        # --- geometric parameters -------------------------------------------------
        self.width = float(width)          
        self.depth = float(depth)          
        self.height = float(height)  

        # Normal direction (thickness axis)
        self.direction = np.array(direction, float)
        self.direction /= np.linalg.norm(self.direction)

        # Center position
        self.pos = np.array(pos, float)

        # --- temporal sampling ----------------------------------------------------
        self.fs = float(fs)
        self.next_sample_time = 0.0

        # --- visualisation --------------------------------------------------------
        self.parent = parent
        self.show_visual = show_visual

        if show_visual and parent is not None:
            self._build_visual()

        # --- detection records ----------------------------------------------------
        self.records = []
        self.particle_seen : List[int] = []  # IDs of particles already detected.

    ####################################################################################################
    #                                           VISUALISATION
    ####################################################################################################

    def _build_visual(self):

        # --- Crée la box dans son repère local ---
        self.visual = scene.visuals.Box(
            width=self.width,        # axe X local
            height=self.height,      # axe Y local
            depth=self.depth,        # axe Z local = normal désirée
            color=(0.2, 0.7, 1.0, 0.2),
            edge_color='white',
            parent=self.parent
        )

        # --- Transformation ---
        transform = MatrixTransform()

        # 1) ROTATION d’abord (aligne Z sur direction)
        z_axis = np.array([0, 0, 1], float)
        n = self.direction

        v = np.cross(z_axis, n)
        s = np.linalg.norm(v)
        c = np.dot(z_axis, n)

        if s != 0:
            # Rodrigues
            vx = np.array([[0, -v[2], v[1]],
                        [v[2], 0, -v[0]],
                        [-v[1], v[0], 0]])
            R = np.eye(3) + vx + (vx @ vx) * ((1 - c) / (s**2))
        else:
            # parallèle ou anti
            R = np.eye(3) if c > 0 else np.diag([1, -1, -1])

        # place la rotation dans transform
        M = np.eye(4)
        M[:3, :3] = R
        transform.matrix = M

        # 2) TRANSLATION ensuite
        transform.translate(self.pos)

        # 3) Assignation finale
        self.visual.transform = transform




    ####################################################################################################
    #                                             DETECTION
    ####################################################################################################

    def detect(self, particle, t):
        """Returns True if particle is inside the measurement volume at time t."""
        if particle.id in self.particle_seen:
            return False  # already detected
        # ---- Temporal sampling ----
        if t < self.next_sample_time:
            return False
        self.next_sample_time += 1.0 / self.fs

        # ---- Use the real transform matrix of the sensor ----
        M = self.visual.transform.matrix  # 4×4 matrix from VisPy
        R = M[:3, :3]     # rotation
        T = M[3, :3]      # translation
        
        # Position in global space
        p = particle.position[0]
        # Convert to local sensor coordinates
        p_local = R.T @ (p - T)

        x, y, z = p_local  # x=width, y=depth, z=height (by construction)

        # ---- Check bounding box in local coordinates ----
        return (
            abs(x) <= self.width / 2 and
            abs(y) <= self.depth / 2 and
            abs(z) <= self.height / 2
        )



    ####################################################################################################
    #                                             RECORD
    ####################################################################################################

    def record(self, particle, t):
        self.particle_seen.append(particle.id)
        self.records.append({
            't': t,
            'pos': particle.position.copy(),
            'vel': particle.velocity.copy()
        })
