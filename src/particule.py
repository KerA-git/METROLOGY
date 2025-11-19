####################################################################################################################################
#                                                   Importation
####################################################################################################################################

from . import *

####################################################################################################################################

class Particle:
    def __init__(self, position, velocity, parent=None):
        self.position = np.array(position, float)[np.newaxis, :]
        self.velocity = np.array(velocity, float)[np.newaxis, :]

        self.visual = scene.visuals.Markers(parent=parent)

        # visual parameters
        self.marker_kwargs = dict(
            face_color=(0, 0, 0, 1),
            edge_color=(0, 0, 0, 1),
            symbol='disc',
            size=5,
        )

        self.visual.set_data(
            pos=self.position,
            **self.marker_kwargs
        )

    def update(self, dt):
        self.position += self.velocity * dt
        self.visual.set_data(
            pos=self.position,
            **self.marker_kwargs
        )


    