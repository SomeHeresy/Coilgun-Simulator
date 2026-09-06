import math
import numpy as np
import pytest
from coilgun.config import Config
from coilgun.integrator_rk4 import rk4_step
from coilgun.rlc import rlc_derivative

cfg = Config()

# Coarser than the production dt on purpose. At cfg.dt the error is already down near 1e-14
# relative, which is the double precision floor, and the convergence ratio then measures
# rounding noise instead of the method.
TEST_DT = 1e-5
TEST_STEPS = round(cfg.dt * cfg.steps / TEST_DT)


def analytic_state(t, V0, R, L, C):
    alpha = R / (2 * L)
    omega_d = (1/(L*C) - alpha**2) ** 0.5
    vt = V0 * math.exp(-alpha*t) * (math.cos(omega_d*t)
                                    + (alpha/omega_d)*math.sin(omega_d*t))
    it = (V0 / (L*omega_d)) * math.exp(-alpha*t) * math.sin(omega_d*t)
    return np.array([vt, it])


# Fresh state every call, so two runs with different dt are actually comparable.
def max_error(dt, steps):
    t, state = 0.0, np.array([cfg.V0, cfg.I0])
    worst_v, worst_i = 0.0, 0.0
    for i in range(steps):
        state = rk4_step(t, state, dt,
                         lambda time, s: rlc_derivative(time, s, cfg.R, cfg.C, cfg.L))
        t = (i + 1) * dt
        exact = analytic_state(t, cfg.V0, cfg.R, cfg.L, cfg.C)
        worst_v = max(worst_v, abs(state[0] - exact[0]))
        worst_i = max(worst_i, abs(state[1] - exact[1]))
    return worst_v, worst_i


def test_matches_the_analytic_underdamped_solution():
    # the closed form below assumes an underdamped circuit, so check that first
    assert cfg.R / (2*cfg.L) < 1 / (cfg.L*cfg.C) ** 0.5
    worst_v, worst_i = max_error(TEST_DT, TEST_STEPS)
    assert worst_v / cfg.V0 < 1e-5
    assert worst_i < 1e-4


# Halving dt should cut the error by 2^4. This is the check that fails loudly if the integrator
# is subtly wrong while the numbers still look plausible.
def test_is_fourth_order():
    v1, i1 = max_error(TEST_DT, TEST_STEPS)
    v2, i2 = max_error(TEST_DT / 2, TEST_STEPS * 2)
    assert 14 < v1 / v2 < 18
    assert 14 < i1 / i2 < 18
