###########################################################################################################################################
#                                                   Imports
###########################################################################################################################################

from . import *
from .generator import GeneratorCube

###########################################################################################################################################

# Create canvas i.e Main window
canvas = scene.SceneCanvas(keys='interactive', #  enable keyboard and mouse interaction
                           size=(800, 600), # resolution
                           show=True, # showing windows
                           title="Generator Modelisation")

# Add 3D view
view = canvas.central_widget.add_view() # add a 3D views inside the central Widget

# Background color
view.bgcolor = (0.85, 0.82, 0.78, 1.0) #(0.95, 0.95, 0.92, 1.0)  # off-white

# Camera properties
view.camera = scene.cameras.TurntableCamera(
    fov=45, # field of view in degre
    elevation=30, # vertical angle
    azimuth=30, # horizontal angle
    distance=5, # camera distance from the scene
    up='z' # Z axis considered as 'up'
)

view.camera.center = (2.5, 0, 0)   # moves the entire scene towards +X

# Axes : creates XYZ axes and attach to the view
axis = scene.visuals.XYZAxis(parent=view.scene)

# Create generator cube ----------------------------------------------

generator = GeneratorCube(
    parent=view.scene
)

# Timer -----------------------------------------------------------

last_time = 0

def update(ev):
    global last_time
    dt = ev.elapsed - last_time
    last_time = ev.elapsed

    generator.update(dt, view.scene)

timer = app.Timer(interval=1/60, # ren frq (Hz)
                  connect=update, # call the update function each tick
                  start=True) 

# Main ----------------------------------------------------------------

if __name__ == '__main__':
    app.run()


