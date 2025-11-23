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

####################################################################################################
#                                             Estimators
####################################################################################################

