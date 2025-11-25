##################################################################################################################################################################################

from . import *
import numpy as np

####################################################################################################################################################################################

class GeometricalEstimator:
    """Hypothesis : 
    - uniform ditribution for position and velocity direction within the generator cone.
    - well-know geometry of the space."""

    def __init__(self):
        """
        Initialize the GeometricalEstimator.
        """

    @staticmethod
    def Vcone(alpha: float , v: float) -> float:
        """Volume of the cone of angle alpha and height v."""
        return (1/3) * np.pi *( (v * np.tan(np.deg2rad(alpha)))**2 )* v

    def __call__(self, estimed_rate:float , emission_angle:float , emission_radius : float , sensor_x_dimension :np.ndarray , sensor_x_position:float ) -> float:
        """
        Estimate the average scale parameter based on geometrical considerations.

        Parameters:
        positions : np.ndarray
            The observed positions of the particles.
        velocities : np.ndarray
            The observed velocities of the particles.

        Returns:
        float
            The estimated scale parameter.
        """
        V_total =  (self.Vcone( emission_angle , sensor_x_position + sensor_x_dimension[0]/2 + emission_radius/np.tan( np.deg2rad(emission_angle) ) ) - 
                    self.Vcone( emission_angle , sensor_x_position - sensor_x_dimension[0]/2 + emission_radius/np.tan( np.deg2rad(emission_angle) ) )
                    ) 
        return estimed_rate * (V_total / ( sensor_x_dimension[0] * sensor_x_dimension[1] * sensor_x_dimension[2] ))
