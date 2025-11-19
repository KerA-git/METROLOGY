####################################################################################################################################################################

from . import *  # imports globaux
from .particule import Particle

####################################################################################################################################################################

class GeneratorCube:

    def __init__(self, 
                area=1,
                parent=None,
                max_range=10.0,
                surface_type='circle',
                pos_dist_type='uniform',
                pos_dist_params=None,
                alpha=20,                          
                vel_norm_dist_type='constant',      # <= par défaut : CONSTANTE
                vel_norm_dist_params={'value': 1},  # <= valeur par défaut : 1 m/s        
                vel_dir_dist_type='uniform_cone',  
                vel_dir_dist_params=None,
                emit_dist_type='constant',
                emit_dist_params={'value': 0.5}):         

        # surface spec - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        self.area = area
        self.max_range = max_range
        self.surface_type = surface_type

        # particle spec - - - - - - - - - - - - - - - - - - - - - - - - - - 
        self.pos_dist_type = pos_dist_type
        self.pos_dist_params = pos_dist_params or {}
        self._build_distribution()

        self.emit_period = 0.5    # secondes entre particules
        self.emit_timer = 0
        self.particles = [] # current particles creates by the generator

        # velocity distributions  - - - - - - - - - - - - - - - - - - - - -  
        self.alpha = np.deg2rad(alpha)

        self.vel_norm_dist_type = vel_norm_dist_type
        self.vel_norm_dist_params = vel_norm_dist_params or {}
        self._build_velocity_norm_distribution()

        self.vel_dir_dist_type = vel_dir_dist_type
        self.vel_dir_dist_params = vel_dir_dist_params or {}

        # Visual - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        self.cube = scene.visuals.Box(
            width=np.sqrt( self.area )*3,
            height=np.sqrt( self.area ),
            depth=np.sqrt( self.area ),
            color=(0.72, 0.58, 0.38, 1.0),   # opaque, brown cream
            edge_color="white",
            parent=parent
        )

        # Transform: origin at center of one face
        self.transform = MatrixTransform()
        self.transform.translate( (-np.sqrt( self.area )/2*3, 0, 0) )
        self.cube.transform = self.transform

        
        #  position distribution - - - - - - - - - - - - - - - - - - -
        
        L = np.sqrt(self.area)

        if self.surface_type == 'square':
            # → Surface carrée
            self.emission_surface = scene.visuals.Plane(
                width=L,
                height=L,
                direction='+x',
                color=(0.40, 0.25, 0.10, 1.0),
                parent=parent
            )

        elif self.surface_type == 'circle':
            # Disque via une Ellipse pleine
            self.emission_surface = scene.visuals.Ellipse(
                center=(0, 0),
                radius=L/2,
                color=(0.40, 0.25, 0.10, 1.0),
                border_width=0,
                parent=parent
            )


        else:
            raise ValueError(f"Surface inconnue pour visualisation : {self.surface_type}")

        # visual emission - - - - - - - - - - - -  - - - - - - -- - - - 
        surface_transform = MatrixTransform()
        surface_transform.rotate(-90, (0, 1, 0))   # rotation
        surface_transform.translate((0.01 , 0 , 0))
        self.emission_surface.transform = surface_transform

        # emit dist - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        self.emit_dist_type = emit_dist_type
        self.emit_dist_params = emit_dist_params or {}
        self._build_emit_distribution()

        # On tire le premier temps d’attente
        self.remaining_emit_time = self._sample_next_emit_time()

    # Particule Generation --------------------------------------------------

    # position :

    def _build_distribution(self):

        if not hasattr(stats, self.pos_dist_type):
            raise ValueError(f"Distribution SciPy inconnue : {self.pos_dist_type}")

        pos_dist_class = getattr(stats, self.pos_dist_type)
        self.pos_distribution = pos_dist_class(**self.pos_dist_params)

    def sample_position(self):

            L = np.sqrt(self.area)

            if self.surface_type == 'circle':
                R = L / 2

                # 1) tirer un rayon avec la distribution choisie
                raw_r = self.pos_distribution.rvs()

                # 2) normaliser dans [0,1]
                u = self.pos_distribution.cdf(raw_r)

                # Clamp si dépassement
                u = np.clip(u, 0, 1)

                # 3) uniforme sur le disque en aire ⇒ sqrt(u)
                r = R * np.sqrt(u)

                theta = np.random.rand() * 2 * np.pi

                return np.array([0,
                                r*np.cos(theta),
                                r*np.sin(theta)])

            elif self.surface_type == 'square':
                # Tirage indépendant pour y et z
                y = self.pos_distribution.rvs() * L - (L/2)
                z = self.pos_distribution.rvs() * L - (L/2)
                return np.array([0, y, z])

            else:
                raise ValueError(f"Surface inconnue : {self.surface_type}")

    # velocity :

    def _build_velocity_norm_distribution(self):

    # Special case : constant
        if self.vel_norm_dist_type == 'constant':
            if 'value' not in self.vel_norm_dist_params:
                raise ValueError("missing value inside self.vel_norm_dist_params. Exemple: vel_norm_dist_params={'value': 1} .")
            self.constant_speed = float(self.vel_norm_dist_params['value'])
            self.vel_norm_distribution = None
            return
        
        if not hasattr(stats, self.vel_norm_dist_type):
            raise ValueError(f"Distribution SciPy inconnue pour la norme de vitesse : {self.vel_norm_dist_type}")
        
        dist_class = getattr(stats, self.vel_norm_dist_type)
        self.vel_norm_distribution = dist_class(**self.vel_norm_dist_params)

    def _sample_velocity_norm(self):

        if self.vel_norm_dist_type == 'constant':
            return self.constant_speed
        
        return float(self.vel_norm_distribution.rvs())

    def _sample_velocity_direction(self):
        if self.vel_dir_dist_type == 'uniform_cone':
            # cos(theta) uniforme dans [cos(alpha), 1]
            u = np.random.rand()
            cos_theta = 1 - u * (1 - np.cos(self.alpha))
            theta = np.arccos(cos_theta)

            phi = 2 * np.pi * np.random.rand()

            # direction dans repère x-y-z
            dx = np.cos(theta)
            dy = np.sin(theta) * np.cos(phi)
            dz = np.sin(theta) * np.sin(phi)

            return np.array([dx, dy, dz])
        
        else:
            raise ValueError(f"Distribution angulaire inconnue : {self.vel_dir_dist_type}")

    def sample_velocity(self):
        norm = self._sample_velocity_norm()
        direction = self._sample_velocity_direction()
        return norm * direction

    # emission - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

    def _build_emit_distribution(self):
        if self.emit_dist_type == 'constant':
            if 'value' not in self.emit_dist_params:
                raise ValueError("Missing 'value' in emit_dist_params.")
            self.constant_emit_delay = float(self.emit_dist_params['value'])
            self.emit_distribution = None
            return
        
        if not hasattr(stats, self.emit_dist_type):
            raise ValueError(f"Distribution SciPy inconnue pour l'émission : {self.emit_dist_type}")

        dist_class = getattr(stats, self.emit_dist_type)
        self.emit_distribution = dist_class(**self.emit_dist_params)

    def _sample_next_emit_time(self):
        if self.emit_dist_type == 'constant':
            return self.constant_emit_delay
        
        return float(self.emit_distribution.rvs())

    def update(self, dt, parent):

        # On décrémente le temps restant avant la prochaine émission
        self.remaining_emit_time -= dt

        # Tant qu’on a dépassé zéro → potentiellement plusieurs émissions d’un coup
        while self.remaining_emit_time <= 0:
            self.emit(parent)
            self.remaining_emit_time += self._sample_next_emit_time()

        # Mise à jour des particules
        alive_particles = []
        p : Particle
        for p in self.particles:
            p.update(dt)
            if np.linalg.norm(p.position[0]) > self.max_range and p.position[0][0]<6:
                print("Trouve")
            if np.linalg.norm(p.position[0]) <= self.max_range:
                alive_particles.append(p)
            else:
                p.visual.parent = None
                p.visual = None
        self.particles = alive_particles


    def emit(self, parent):
        p = Particle(
            position=self.sample_position(),
            velocity=self.sample_velocity(),        
            parent=parent
        )
        self.particles.append(p)  

    # def update(self, dt, parent):
    #         self.emit_timer += dt
    #         if self.emit_timer >= self.emit_period:
    #             self.emit(parent)
    #             self.emit_timer = 0

    #         # Mettre à jour les particules et supprimer celles hors portée
    #         alive_particles = []
    #         for p in self.particles:
    #             p.update(dt)
    #             if np.linalg.norm(p.position[0]) <= self.max_range:
    #                 alive_particles.append(p)
    #             else:
    #                 p.visual.parent = None  
    #                 p.visual = None
    #         self.particles = alive_particles