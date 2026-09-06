import numpy as np
from .integrator_rk4 import rk4_step
from .coilgun_derivative import coilgun_derivative
from .config import Config

# not a pytest file yet -- run it with python -m coilgun.validate_coilgun and read the printed ratios.
cfg = Config()


def run_simulation(dt, steps, cfg):
    t, state_history = [0.0], [
        np.array([cfg.V0, cfg.I0, cfg.x0, cfg.vel0, cfg.W0])]
    for i in range(steps):
        state_history.append(
            rk4_step(t[i], state_history[-1], dt,
                     lambda time, state: coilgun_derivative(
                         time, state, cfg.R, cfg.C, cfg.L0, cfg.dL, cfg.a, cfg.mass,
                     cfg.lam_pm, cfg.a_pm)))
        t.append((i + 1) * dt)
    return state_history[-1]


test_dt = 1e-5
# same total simulated time as production
test_steps = round(cfg.dt * cfg.steps / test_dt)

final_dt = run_simulation(test_dt, test_steps, cfg)
final_dt_half = run_simulation(test_dt / 2, test_steps * 2, cfg)
final_dt_quarter = run_simulation(test_dt / 4, test_steps * 4, cfg)

print(f"Final state at dt:      {final_dt}")
print(f"Final state at dt/2:    {final_dt_half}")
print(f"Final state at dt/4:    {final_dt_quarter}")

diff_1 = np.linalg.norm(final_dt - final_dt_half)
diff_2 = np.linalg.norm(final_dt_half - final_dt_quarter)

print(f"\nChange from dt to dt/2:   {diff_1:.6e}")
print(f"Change from dt/2 to dt/4: {diff_2:.6e}")
print(f"Ratio (should be ~16 for true 4th-order RK4): {diff_1/diff_2:.2f}")
