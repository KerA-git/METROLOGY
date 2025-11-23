####################################################################################################################################################################################
from src.model import create_model
from src.StaticAnalysis import StaticAnalysisExtraction
import time
####################################################################################################################################################################################

# run simulation : - - - - - - - - - - - - - - - - - - - - - - - - - - 

time_scale = 2.0  # speed up simulation time

app, canvas, view, generator, timer , sensor= create_model(
    time_scale=time_scale ,
    gen_surface_type='circle',
    gen_pos_dist_type='uniform',
    gen_vel_norm_dist_type='constant',
    gen_vel_norm_dist_params={'value': 2.0},
    gen_alpha=20,
    gen_emit_dist_type='expon',
    gen_emit_dist_params={'scale': 0.7},
)

_start_time = time.perf_counter()
app.run()
_end_time = time.perf_counter()

sim_time = (_end_time - _start_time ) * time_scale
print(f"\nSimulation finished in {sim_time :.4f} seconds\n")

analysis = StaticAnalysisExtraction(sim_time , sensor , generator)
# Static analysis : - - - - - - - - - - - - - - - - - - - - - - - - - 

print(analysis)