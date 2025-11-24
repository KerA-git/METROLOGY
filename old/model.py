###########################################################################################################################################
#                                                   Imports
###########################################################################################################################################

from . import *
from .generator import GeneratorCube
from .capteur import Sensor

###########################################################################################################################################

# -------------------------------------------------------------------
# MODEL
# -------------------------------------------------------------------

def create_model(time_scale=1.0,**params):

    # ---------------------------
    # separation of parameters
    # ---------------------------
    generator_params = {}
    sensor_params = {}

    for key, val in params.items():
        if key.startswith("gen_"):
            generator_params[key[4:]] = val
        elif key.startswith("sen_"):
            sensor_params[key[4:]] = val
        else:
            print(f"[WARNING] Unknown param '{key}' ignored")

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
    scene.visuals.XYZAxis(parent=view.scene)
    # Create generator cube and sensor ----------------------------------------------

    generator = GeneratorCube(
        parent=view.scene,
        **generator_params
    )
    sensor = Sensor(
        parent=view.scene,
         **sensor_params
    )

    # Update -----------------------------------------------------------

    last_time = None
    sim_time = None

    def update(ev):
        nonlocal last_time, sim_time
        # First frame init
        if last_time is None:
            last_time = ev.elapsed
            sim_time = ev.elapsed
            return

        # real time elapsed since last frame
        real_dt = ev.elapsed - last_time
        # simulation time scaled by time_scale
        sim_dt = real_dt * time_scale

        # advance times
        last_time = ev.elapsed
        sim_time += sim_dt

        # update generator with scaled simulation delta
        generator.update(sim_dt, view.scene)

        # --- particle detect ---
        for p in generator.particles:
            if sensor.detect(p, sim_time):
                print(f"Particle detected at time {sim_time:.4f} s")
                sensor.record(p, sim_time)
                p.set_color((0, 1, 0, 1))
            elif p.id in sensor.particle_seen:
                p.set_color((0, 1, 0, 1))

    timer = app.Timer(interval=1/60, # ren frq (Hz)
                    connect=update, # call the update function each tick
                    start=True) 
    
    return app, canvas, view, generator, timer, sensor

# Main ----------------------------------------------------------------

#if __name__ == '__main__':
#    app.run()


