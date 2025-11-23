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
    for step in range(total_steps):
        percent = (step + 1) / total_steps
        bar_length = 30
        filled = int(percent * bar_length)

        bar = "█" * filled + "-" * (bar_length - filled)
        print(f"\rProgress: |{bar}| {percent*100:5.1f}%. Current living particles: {len(living_particles)}", end="")
        # --- Update generator ---
        new_particles = generator(dt) #emit new particles
        if new_particles:
            living_particles.append(new_particles)

        # --- Update particles ---
        for particle in living_particles:
            particle.update(dt)
            # --- Check detection ---
            sensor.update(particle, t)
            if np.any(particle.position>=sensor.get_range_detect_bounds()) and particle.detection_is_detected:
                detected_particles.append(particle)
            elif np.any(particle.position>=sensor.get_range_detect_bounds()) and not particle.detection_is_detected:
                lost_particles.append(particle.id)
        # --- Remove particles ---
        living_particles = [p for p in living_particles if np.all(p.position<sensor.get_range_detect_bounds())]
        # Advance simulation time
        t += dt
    # Final detection
    for particle in living_particles:
        if particle.detection_is_detected:
            detected_particles.append(particle)
        else:
            if particle.id not in lost_particles:
                lost_particles.append(particle.id)

    print(f"\nSimulation finished.Max particules encountered: {Particle.id_counter},\n Lost particles: {len(lost_particles)},\n Detected particles: {len(detected_particles)}")
    return detected_particles, lost_particles


