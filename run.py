from src.model import create_model

app, canvas, view, generator, timer , sensor= create_model(
    gen_surface_type='circle',
    gen_pos_dist_type='uniform',
    gen_vel_norm_dist_type='constant',
    gen_vel_norm_dist_params={'value': 2.0},
    gen_alpha=20,
    gen_emit_dist_type='expon',
    gen_emit_dist_params={'scale': 0.7},
)

app.run()
