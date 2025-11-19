####################################################################################################################################
#                                                   Importation
####################################################################################################################################

from . import *

####################################################################################################################################

def depth_color(d):
    # d ∈ [0,1]
    return (d, 0, 1 - d, 1)

####################################################################################################################################

class Particle:
    def __init__(self, position, velocity, parent=None):
        self.position = np.array(position, float)[np.newaxis, :]
        self.velocity = np.array(velocity, float)[np.newaxis, :]

        self.visual = scene.visuals.Markers(parent=parent)
        self.visual.set_gl_state(depth_test=False , blend=True) # particle will be always display

        # visual parameters
        self.marker_kwargs = dict(
            symbol='disc',
            size=5,
            face_color=(0, 0, 0, 1),
            edge_color=(0, 0, 0, 1),
        )

        self.visual.set_data(
            pos=self.position,
            **self.marker_kwargs
        )

    # color change ------------------------------------------------------------------------------------------------------------------

    def set_color(self, color):
        """Change la couleur (face + edge)."""
        self.visual.set_data(
            pos=self.position,
            face_color=color,
            edge_color=color,
            symbol=self.marker_kwargs['symbol'],
            size=self.marker_kwargs['size'],
        )   

    # update ------------------------------------------------------------------------------------------------------------------------

    def update(self, dt):
        # --- update position ---
        self.position += self.velocity * dt

        # --- profondeur (distance 3D depuis l’origine) ---
        dist = np.linalg.norm(self.position)

        # Normalisation : profondeur max = 10 (tu peux changer)
        d = np.clip(dist / 10, 0, 1)

        # --- nouvelle couleur dynamique ---
        new_color = depth_color(d)

        # --- mise à jour du marqueur ---
        self.visual.set_data(
            pos=self.position,
            face_color=new_color,
            edge_color=new_color,
            symbol=self.marker_kwargs['symbol'],
            size=self.marker_kwargs['size'],
        )


    