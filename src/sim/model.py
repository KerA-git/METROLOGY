####################################################################################################

# Imports
from . import *

from typing import List, Tuple
from .generator import GeneratorCircle
from .sensor import RectangularSensor
from .particle import Particle

####################################################################################################

def run( 
    clock = 60,  # simu rate (Hz)
    run_duration = 10.0,  # simu duration (s) [real time]
    visualize = False,  # visualize simulation
    visual_slowdown: float = 0.02,  # seconds pause per frame for visualization
    **params
    ) -> Tuple[List[Particle], int]:
    """
    Create and run the particle simulation model.
    ####################################################################################################
    """
    # ------------------------------------------------------------------------------------------------------------
    # separation of parameters
    # ------------------------------------------------------------------------------------------------------------
    generator_params = {}
    sensor_params = {}

    for key, val in params.items():
        if key.startswith("gen_"):
            generator_params[key[4:]] = val
        elif key.startswith("sen_"):
            sensor_params[key[4:]] = val
        else:
            print(f"[WARNING] Unknown param '{key}' ignored")

    # Create generator and sensor -----------------------------------------------------------------------------------
    generator = GeneratorCircle(**generator_params)
    sensor = RectangularSensor(**sensor_params)

    # Initialization -----------------------------------------------------------------------------------

    # initialize simulation time
    t = 0.0
    dt = 1.0 / clock  # simulation time step
    total_steps = int(run_duration * clock)

    # init particle
    living_particles : List[Particle] = []
    lost_particles : List[int] = [] # store id of lost particles
    detected_particles :List[Particle] = []

    # Main simulation loop -----------------------------------------------------------------------------------
    print(f"Starting simulation with {total_steps} steps...")

    if not visualize:
        for step in range(total_steps):
            percent = (step + 1) / total_steps
            bar_length = 30
            filled = int(percent * bar_length)

            bar = "█" * filled + "-" * (bar_length - filled)
            print(f"\rProgress: |{bar}| {percent*100:5.1f}%. Current living particles: {len(living_particles)} Timing : {t} s", end="")
            # --- Update generator ---
            new_particle = generator(dt) #emit new particle or None
            if new_particle:
                new_particle.emission_time = t
                # generator returns a single Particle or None
                living_particles.append(new_particle)

            # --- Update particles ---
            for particle in living_particles:
                particle.update(dt)
                # --- Check detection ---
                sensor.update(particle, t)
                try:
                    if np.any(particle.position >= sensor.get_range_detect_bounds()) and particle.detection_is_detected:
                        detected_particles.append(particle)
                    elif np.any(particle.position >= sensor.get_range_detect_bounds()) and not particle.detection_is_detected:
                        lost_particles.append(particle.id)
                except Exception:
                    # in case of malformed comparisons, ignore
                    pass

            # --- Remove particles ---
            try:
                living_particles = [p for p in living_particles if np.all(p.position < sensor.get_range_detect_bounds())]
            except Exception:
                # fallback: remove particles far beyond sensor in x
                max_x = float(sensor.position[0,0]) + 10.0 * float(sensor.dimensions[0])
                living_particles = [p for p in living_particles if p.position[0,0] < max_x]

            # Advance simulation time
            t += dt

    else:
        # Visual mode: interactive matplotlib 2D view (x,z). y is out-of-plane -------------------------------------------------
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle

        plt.ion()
        fig, ax = plt.subplots(figsize=(8,6))
        try:
            gen_radius = float(getattr(generator, 'radius', 1.0))
        except Exception:
            gen_radius = 1.0

        sensor_x = float(sensor.position[0,0])
        sensor_z = float(sensor.position[0,2])
        half_height = float(sensor.dimensions[2]) / 2.0

        x_min = -1.0
        x_max = sensor_x + max(1.0, float(sensor.dimensions[0])) * 1.5
        z_min = min(-gen_radius * 1.2, sensor_z - half_height - 0.5)
        z_max = max(gen_radius * 1.2, sensor_z + half_height + 0.5)

        ax.set_xlim(x_min, x_max)
        ax.set_ylim(z_min, z_max)
        ax.set_xlabel('x')
        ax.set_ylabel('z')
        ax.set_title('projection on (x,z) plane')

        # emitter: vertical line at x=0 from z=-R to R
        ax.plot([0,0], [-gen_radius, gen_radius], color='green', linewidth=3, label='emission')

        # sensor face rectangle at front face (x = center - width/2)
        sensor_rect = Rectangle((sensor.position[0,0]-sensor.dimensions[0]/2.0, sensor.position[0,2]-sensor.dimensions[2]/2.0), 
                                sensor.dimensions[0], sensor.dimensions[2],
                                facecolor='cyan', alpha=0.3, edgecolor='black', label='sensor')
        ax.add_patch(sensor_rect)

        scatter = ax.scatter([], [], s=20)
        plt.legend()
        # Main loop -----------------------------------------------------------------------------------
        for step in range(total_steps):
            ## progress bar :
            percent = (step + 1) / total_steps
            bar_length = 30
            filled = int(percent * bar_length)
            bar = "█" * filled + "-" * (bar_length - filled)
            print(f"\rProgress: |{bar}| {percent*100:5.1f}%. Current living particles: {len(living_particles)}. Timing : {t:.2f} s", end="")
            # --- Update generator ---
            new_particle = generator(dt)
            if new_particle:
                new_particle.emission_time = t
                living_particles.append(new_particle)
            # visualization data
            xs = []
            zs = []
            colors = []
            # --- Update particles ---
            for particle in living_particles:
                particle.update(dt)
                sensor.update(particle, t)
                x = float(particle.position[0,0])
                z = float(particle.position[0,2])
                xs.append(x)
                zs.append(z)
                colors.append('red' if particle.detection_is_detected else 'blue')
                particle.update(dt)
                # --- Check detection ---
                sensor.update(particle, t)
                try:
                    if np.any(particle.position >= sensor.get_range_detect_bounds()):
                        if particle.detection_is_detected :
                            if not particle in detected_particles:
                                detected_particles.append(particle)
                        elif particle.id not in lost_particles:
                            lost_particles.append(particle.id)
                        else:
                            pass
                except Exception:
                    # in case of malformed comparisons, ignore
                    pass

            # --- Remove particles ---
            try:
                living_particles = [p for p in living_particles if np.all(p.position < sensor.get_range_detect_bounds())]
            except Exception:
                # fallback: remove particles far beyond sensor in x
                max_x = float(sensor.position[0,0]) + 10.0 * float(sensor.dimensions[0])
                living_particles = [p for p in living_particles if p.position[0,0] < max_x]

            if len(xs) > 0:
                scatter.set_offsets(np.column_stack([xs, zs]))
                scatter.set_color(colors)
            else:
                scatter.set_offsets(np.empty((0,2)))

            plt.draw()
            plt.pause(max(visual_slowdown, 0.001))

            t += dt

        plt.ioff()
        plt.show()
    # Final detection
    for particle in living_particles:
        if particle.detection_is_detected:
            if not particle in detected_particles:
                detected_particles.append(particle)
        else:
            if particle.id not in lost_particles:
                lost_particles.append(particle.id)
    print("")  # new line after progress bar
    print(f"\nSimulation finished.Max particules encountered: {Particle.id_counter},\n Lost particles: {len(lost_particles)},\n Detected particles: {len(detected_particles)}")
    #print(f"detected IDs: {[p.id for p in detected_particles]}")
    #print(f"lost IDs: {lost_particles}")
    return detected_particles, lost_particles


