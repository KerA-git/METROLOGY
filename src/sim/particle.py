# import :

from . import *

####################################################################################################

class Particle:
    
    id_counter = 0 # facilate unique ID assignment. maybe not a good idea in this context but suficient for small scale simulation.

    def __init__(self, position, velocity):    
        # unique ID : 
        self.id = Particle.id_counter
        Particle.id_counter += 1
        # geometrical properties :
        self.position = np.array(position, float)[np.newaxis, :]  # (x, y, z)
        self.velocity = np.array(velocity, float)[np.newaxis, :]  # (x, y, z)
        # Dectection properties :
        self.detection_is_detected = False  # Flag to indicate if the particle has been detected.
        self.detection_time = None  # Time of detection.
        self.detection_position = None  # Position at detection.
        self.detection_velocity = None  # Velocity at detection.
        self.detection_duration  = 0.0  # Duration of detection.

    def update(self, dt):
        # --- update position ---
        self.position += self.velocity * dt
