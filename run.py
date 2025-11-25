####################################################################################################################################################################################
from src.sim.model import run
from src.estimators.LittleLaw import LittleLawEstimator
from src.estimators.Linear import LinearEstimator
from src.estimators.geometrical import GeometricalEstimator
from src.sim.particle import Particle

import json
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats

####################################################################################################################################################################################

with open('sim_params.json', 'r') as f:
    params = json.load(f)

nb_run = 1000
step = 0
given_values = []
# Pre-compute real emission rate from params (independent of per-run randomness)
if params.get('gen_emit_dist_type') == 'constant':
    real_rate = params['gen_emit_dist_params']['value']
elif not hasattr(stats, params.get('gen_emit_dist_type')):
    raise ValueError(f"Distribution SciPy inconnue pour l'émission : {params.get('gen_emit_dist_type')}")
else:
    dist_class = getattr(stats, params.get('gen_emit_dist_type'))
    emit_distribution = dist_class(**params.get('gen_emit_dist_params', {}))
    real_rate = 1 / emit_distribution.mean()
for _ in range(nb_run):
    if nb_run!=1:
        percent = (step + 1) / nb_run
        bar_length = 30
        filled = int(percent * bar_length)
        step+=1
        bar = "█" * filled + "-" * (bar_length - filled)
        print(f"\rProgress: |{bar}| {percent*100:5.1f}%", end="")
    # run accepts clock and run_duration as named args; the rest (gen_/sen_) are passed as kwargs
    ps , lost_ps = run(clock=params.get('clock', 60),
                        run_duration=params.get('run_duration', 100.0),
                        visualize=False,
                        is_progressive=(nb_run==1),
                        **{k: v for k, v in params.items() if k not in ('clock', 'run_duration')})

    # Analysis of results ################################################################################################################################################################
    if nb_run==1:
        print("\n============= Starting estimation ============= \n")

    # (real_rate precomputed before loop)
    if nb_run == 1:
        print(f"\nReal emission rate: {real_rate} particles/second\n")
    # little's Law Estimator - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

    # Prepare data for Little's Law Estimator

    fs = params['sen_fs']  # detection frequency
    detection_interval = 1 / fs
    occupation_array = np.zeros(int(params['run_duration'] * fs))
    residence_times = np.zeros( len(ps) )
    current_time = 0.0
    while current_time < params['run_duration']:
        # Count detected particles at current_time
        detected_count = sum(1 for p in ps if p.detection_time <= current_time < (p.detection_time + p.detection_duration))
        occupation_array[int(current_time * fs)] = detected_count
        current_time += detection_interval
    for i in range(len(ps)):
        p = ps[i]
        if p.detection_is_detected:
            residence_times[i] = p.detection_duration
    residence_times = np.array(residence_times)

    # Instantiate and apply Little's Law Estimator

    LLE = LittleLawEstimator()
    lle_rate = LLE(occupation_array, residence_times)
    if nb_run==1:
        print(f"Estimated rate using Little's Law: {lle_rate} particles/second\n")
        print("\n========================== \n")
    # Linear Estimator - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

    # Prepare data for Linear Estimator
    def estimate_emit_time(p:Particle) -> float:
        """ Estimate the emission time of a detected particle from its detection record. Requires that the particle has been detected.

        WARNING : hypothesis on the mean position emission -> \\mathbb{E}(emission_position) = 0
        """
        if not p.detection_is_detected:
            raise ValueError("Particle was not detected; cannot extract emission time.")
        return p.detection_time - 1/3 * np.sum( p.position / p.velocity)
    est_emit_times = [estimate_emit_time(p) for p in ps if p.detection_is_detected]
    est_emit_times.sort()
    LIN = LinearEstimator()
    best_m, best_x, best_cost = LIN(est_emit_times, xmin=1, xmax=None, m_grid=None)
    if nb_run==1:
        plt.plot(best_x, est_emit_times, 'o', label='Estimated emission times')
        plt.plot([0, max(best_x)], best_m * np.array([0, max(est_emit_times)]), 'r--', label=f'y={best_m:.2f}x reference')
        plt.plot(best_x, [p.emission_time for p in ps if p.detection_is_detected], 'gx', label='True emission times')
        plt.plot([0, max(best_x)], 1 / real_rate * np.array([0, max(best_x)]) , 'k-', label='Desired curve')
        plt.xlabel('Estimated emission index (x)')
        plt.ylabel('Emission Time (y)')
        plt.title('Linear Estimator: Estimated Emission Times vs Detection Times')
        plt.legend()
        plt.grid()
        plt.show()
        print(f"Estimated rate using Linear estimator: {1/best_m} particles/second\n")
        print("\n========================== \n")
    # Geometrical Estimator- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

    GEOM = GeometricalEstimator()

    Sample_rate = len( ps ) / params['run_duration'] # detected particles per second
    geom_rate = GEOM(Sample_rate, emission_angle=params['gen_alpha'], emission_radius=params['gen_radius'], sensor_x_dimension=np.array(params['sen_dimensions']), sensor_x_position=params['sen_pos'][0])
    given_values.append(geom_rate)
    if nb_run==1 :
        print(f"Estimated rate using Geometrical estimator: {geom_rate} particles/second\n")
        print("\n========================== \n")
    # Unknown Estimator - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

    aux = np.zeros( len(est_emit_times)-1 )
    for i in range(0, len(est_emit_times)-1):
        if i==0:
            aux[i] = est_emit_times[i]
        else:
            aux[i] = est_emit_times[i] - est_emit_times[i-1]
    unknown_rate = 1 / np.mean(aux)
    if nb_run==1:
        print(f"Estimated rate using Unknown estimator: {unknown_rate} particles/second\n") 

# Filter non-finite estimates before plotting
vals = np.array(given_values, dtype=float)
finite_vals = vals[np.isfinite(vals)]
if finite_vals.size == 0:
    print("No finite Geom estimates produced — nothing to plot.")
else:
    plt.hist(finite_vals, bins=30, alpha=0.7, color='blue', edgecolor='black')
    plt.axvline(x=np.mean(finite_vals), color='red', linestyle='dashed', linewidth=1, label=f'Mean Estimated Rate: {np.mean(finite_vals):.2f} particles/second')
    # real_rate should be finite (precomputed); guard just in case
    if np.isfinite(real_rate):
        plt.axvline(x=real_rate, color='green', linewidth=1, label=f'Real Emission Rate: {real_rate:.2f} particles/second')
    plt.title(f"Histogram of Geometrical Estimated Rates over {nb_run} runs")
    plt.xlabel('Estimated Rate (particles/second)')
    plt.ylabel('Frequency')
    plt.legend()
    plt.show()