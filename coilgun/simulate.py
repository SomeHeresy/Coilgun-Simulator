import numpy as np
from .integrator_rk4 import rk4_step
from .coilgun_derivative import coilgun_derivative


# The same loop run_coilgun.py uses, wrapped in a function so the CLI, the sweep and the tests
# can all call it with a different Config instead of each keeping their own copy.
def simulate(cfg):
    t, state_history = [0.0], [
        np.array([cfg.V0, cfg.I0, cfg.x0, cfg.vel0, cfg.W0])]
    for i in range(cfg.steps):
        state_history.append(
            rk4_step(t[i], state_history[-1], cfg.dt,
                     lambda time, state: coilgun_derivative(
                         time, state, cfg.R, cfg.C, cfg.L0, cfg.dL, cfg.a, cfg.mass,
                         cfg.lam_pm, cfg.a_pm)))
        t.append((i + 1) * cfg.dt)
    return np.array(t), np.array(state_history)


# peak is what perfect switch timing would give, exit is what a chronograph at the barrel end
# reads. Returns None for the exit velocity if the slug never got that far.
def peak_and_exit(t, history, x_exit):
    x_all, v_all = history[:, 2], history[:, 3]
    peak = v_all.max()

    crossed = np.nonzero(x_all >= x_exit)[0]
    if len(crossed) == 0:
        return peak, None

    # RK4 steps over x_exit rather than landing on it, so interpolate across the crossing.
    j = crossed[0]
    frac = (x_exit - x_all[j-1]) / (x_all[j] - x_all[j-1])
    return peak, v_all[j-1] + frac * (v_all[j] - v_all[j-1])
