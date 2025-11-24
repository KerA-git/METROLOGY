# imports :

from . import *  # imports globaux
from .particle import Particle

###########################################################################################################

class GeneratorCircle:
    """
    Particle generator that emits particles from a circular area.
    ####################################################################################################
    """ 

    def __init__(self,
                 
                 radius=0.5, # circle radius
                 alpha=20, # cone angle in degrees for velocity direction 

                 emission_rate=10,  # particles per second

                 pos_dist_type='uniform', # position distribution type
                 pos_dist_params=None, # position distribution parameters   

                 vel_norm_dist_type='constant',      # velocity norm distribution type
                 vel_norm_dist_params={'value': 1},  # velocity norm distribution parameters
                 vel_dir_dist_type='uniform_cone',  # velocity direction distribution type
                 vel_dir_dist_params=None, # velocity direction distribution parameters

                 emit_dist_type='constant', # emission time distribution type
                 emit_dist_params={'value': 0.5} # emission time distribution parameters
            ):     
        # --- geometric parameters -------------------------------------------------
        self.radius = float(radius)
        self.alpha = float(alpha)  # degrees
        self.emission_rate = float(emission_rate)
        # --- position distribution -----------------------------------------------
        self._build_pos_distribution(pos_dist_type, pos_dist_params)
        # --- velocity distributions -----------------------------------------------
        self._build_velocity_norm_distribution(vel_norm_dist_type, vel_norm_dist_params)
        self.vel_dir_distribution_params = self._build_velocity_direction_distribution(vel_dir_dist_type , vel_dir_dist_params)
        # --- emission time distribution -------------------------------------------
        self._build_emit_distribution(emit_dist_type, emit_dist_params)

        self.time_since_last_emit = 0.0

    ### building distributions # # # # # # # # # # # # # # # # # # # # # # # # # # 

    def _build_pos_distribution(self, pos_dist_type, pos_dist_params):

        if not hasattr(stats, pos_dist_type):
            raise ValueError(f"Distribution SciPy inconnue : {pos_dist_type}")

        pos_dist_class = getattr(stats, pos_dist_type)
        self.pos_distribution = pos_dist_class(**pos_dist_params)

    def _build_velocity_norm_distribution(self , vel_norm_dist_type, vel_norm_dist_params):

    # Special case : constant
        if vel_norm_dist_type == 'constant':
            if 'value' not in vel_norm_dist_params:
                raise ValueError("missing value inside vel_norm_dist_params. Exemple: vel_norm_dist_params={'value': 1} .")
            self.constant_speed = float(vel_norm_dist_params['value'])
            self.vel_norm_distribution = None
            return
        
        if not hasattr(stats, vel_norm_dist_type):
            raise ValueError(f"Distribution SciPy inconnue pour la norme de vitesse : {vel_norm_dist_type}")
        
        dist_class = getattr(stats, vel_norm_dist_type)
        self.vel_norm_distribution = dist_class(**vel_norm_dist_params)

    def _dist_vel_direction_uniform_cone(self):
        # cos(theta) uniforme dans [cos(alpha), 1]
        alpha_rad = np.deg2rad(self.alpha)
        u = np.random.uniform(np.cos(alpha_rad), 1.0)
        theta = np.arccos(u)
        # phi uniforme dans [0, 2pi]
        phi = 2 * np.pi * np.random.rand()

        # direction dans repère x-y-z
        dx = u
        dy = np.sin(theta) * np.cos(phi)
        dz = np.sin(theta) * np.sin(phi)

        return np.array([dx, dy, dz])
    
    def _dist_vel_driection_truncnorm_cone(self,loc=None,scale=None):
        # truncated normal distribution for theta within [0, alpha]
        alpha_rad = np.deg2rad(self.alpha)
        mu = alpha_rad / 2  if loc is None else loc  # mean at half the cone angle
        sigma = alpha_rad / 6  if scale is None else scale  # standard deviation

        a, b = (0 - mu) / sigma, (alpha_rad - mu) / sigma
        theta = stats.truncnorm.rvs(a, b, loc=mu, scale=sigma)

        # phi uniforme dans [0, 2pi]
        phi = 2 * np.pi * np.random.rand()

        # direction dans repère x-y-z
        dx = np.cos(theta)
        dy = np.sin(theta) * np.cos(phi)
        dz = np.sin(theta) * np.sin(phi)

        return np.array([dx, dy, dz])


    def _build_velocity_direction_distribution(self , vel_dir_dist_type, vel_dir_dist_params=None):
        if vel_dir_dist_type == 'uniform_cone':
            # return a sampler (callable) that draws one direction when called
            return self._dist_vel_direction_uniform_cone
        elif vel_dir_dist_type == 'truncnorm_cone':
            if vel_dir_dist_params is None:
                return self._dist_vel_driection_truncnorm_cone
            else:
                return lambda: self._dist_vel_driection_truncnorm_cone(loc=vel_dir_dist_params.get('loc'), scale=vel_dir_dist_params.get('scale'))
        else:
            raise ValueError(f"Distribution angulaire inconnue : {vel_dir_dist_type}")
    
    def _build_emit_distribution(self , emit_dist_type , emit_dist_params):
        if emit_dist_type == 'constant':
            if 'value' not in emit_dist_params:
                raise ValueError("Missing 'value' in emit_dist_params.")
            self.constant_emit_delay = float(emit_dist_params['value'])
            self.emit_distribution = None
            return
        
        if not hasattr(stats, emit_dist_type):
            raise ValueError(f"Distribution SciPy inconnue pour l'émission : {emit_dist_type}")

        dist_class = getattr(stats, emit_dist_type)
        self.emit_distribution = dist_class(**emit_dist_params)

    # emission - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

    def __call__(self, dt=0.0):
        """Advance internal clock by dt and generate a new Particle when it's time.
        Returns a Particle or None."""
        # advance internal timer
        self.time_since_last_emit += float(dt)

        # ensure there is a scheduled next emit delay
        if not hasattr(self, '_next_emit_delay'):
            if self.emit_distribution is None:
                self._next_emit_delay = float(self.constant_emit_delay)
            else:
                self._next_emit_delay = float(self.emit_distribution.rvs())

        # not yet time to emit
        if self.time_since_last_emit < self._next_emit_delay:
            return None

        # it's time (or past time) to emit one particle — attempt generation
        try:
            # --- sample position on the circular emission surface ---
            # radial sample: draw raw value from distribution, map to area-uniform via sqrt(CDF)
            raw_r = self.pos_distribution.rvs()
            u = self.pos_distribution.cdf(raw_r)
            u = np.clip(u, 0.0, 1.0)
            r = self.radius * np.sqrt(u)
            theta = 2 * np.pi * np.random.rand()
            # emission surface lies in local y-z plane, x=0 (same convention as other generators)
            position = np.array([0.0, r * np.cos(theta), r * np.sin(theta)])

            # --- velocity norm ---
            if self.vel_norm_distribution is None:
                speed = self.constant_speed
            else:
                speed = float(self.vel_norm_distribution.rvs())

            # --- velocity direction ---
            if callable(self.vel_dir_distribution_params):
                direction = np.array(self.vel_dir_distribution_params())
            else:
                # fallback: if a fixed vector was stored
                direction = np.array(self.vel_dir_distribution_params)

            # normalize direction to be safe
            norm = np.linalg.norm(direction)
            if norm == 0:
                return None
            direction = direction / norm

            velocity = speed * direction

            particle = Particle(position=position, velocity=velocity)
        except Exception:
            # If any sampling fails, do not change timers and return None
            return None

        # successful emission: reset timer and schedule next emit
        self.time_since_last_emit = 0.0
        if self.emit_distribution is None:
            self._next_emit_delay = float(self.constant_emit_delay)
        else:
            self._next_emit_delay = float(self.emit_distribution.rvs())

        return particle

        