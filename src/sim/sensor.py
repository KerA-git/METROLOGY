####################################################################################################################################################################

from . import *

from typing import List , Tuple ,Union
from .particle import Particle

####################################################################################################################################################################

class RectangularSensor:
    """
    
    """

    def __init__(self,
                 pos: Tuple[float, float, float],  # (x, y, z) : center position
                 dimensions: Tuple[float, float, float],  # (width, depth, height)
                 fs = 1000.0 # smapling frequency
                 ):
        
        self.position = np.array(pos, float)[np.newaxis, :]  # (x, y, z)
        self.dimensions = np.array(dimensions, float)  # (width, depth, height)
        self.fs = fs  # sampling frequency
    
    def get_range_detect_bounds(self) -> np.ndarray:
        """Returns the max corners of the sensor detection volume according to the basis (x,y,z) and not the local sensor frame."""
        return self.position + self.dimensions[np.newaxis, :] / 2.0

    # update on particle array ------------------------------------------------------------------------------------------------

    def update(self , particles : Union[List[Particle], Particle] , t : float) -> None:
        if isinstance(particles, Particle):
            particles = [particles]
        for particle in particles:
            # check if particle is inside the sensor volume
            relative_pos = particle.position - self.position  # (1, 3)
            half_dims = self.dimensions[np.newaxis, :] / 2.0  # (1, 3)
            if np.all(np.abs(relative_pos) <= half_dims):
                if not particle.detection_is_detected:
                    particle.detection_is_detected = True
                    particle.detection_time = t
                    particle.detection_position = particle.position
                    particle.detection_velocity = particle.velocity
                else:
                    particle.detection_duration += 1.0 / self.fs
        