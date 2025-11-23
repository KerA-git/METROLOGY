####################################################################################################################################################################################
from src.sim.model import run
from src.StaticAnalysis import StaticAnalysisExtraction
import json
####################################################################################################################################################################################

with open('sim_params.json', 'r') as f:
    params = json.load(f)

# run accepts clock and run_duration as named args; the rest (gen_/sen_) are passed as kwargs
ps , lost_ps = run(clock=params.get('clock', 60),
                    run_duration=params.get('run_duration', 10.0),
                    **{k: v for k, v in params.items() if k not in ('clock', 'run_duration')})

