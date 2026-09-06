import math
import numpy as np
from .integrator_rk4 import rk4_step
from .rlc import rlc_derivative
from .config import Config

# not a pytest file yet -- run it with python -m coilgun.validate_rlc and read the printed ratios.
cfg = Config()


def alpha(R, L):
    return R / (2 * L)


def omega_0(L, C):
    return 1 / (L * C) ** 0.5


def omega_d(R, L, C):
    alpha_val = alpha(R, L)
    omega_0_val = omega_0(L, C)
    return (omega_0_val**2 - alpha_val**2) ** 0.5


# closed-form underdamped series RLC response, valid only because I0 is 0.
# this is the reference the integrator gets scored against.
def analytic_func(t, V0, R, L, C):
    alpha_val = alpha(R, L)
    omega_d_val = omega_d(R, L, C)
    vt = V0 * math.exp(-alpha_val * t) * (math.cos(omega_d_val * t) +
                                          (alpha_val/omega_d_val)*math.sin(omega_d_val*t))
    it = (V0 / (L * omega_d_val)) * \
        math.exp(-alpha_val * t) * math.sin(omega_d_val * t)
    return np.array([vt, it])


def convergence_test(dt, steps, V0, I0, R, L, C):
    # Fresh state and time list every call -- this is what makes two
    # calls with different dt actually comparable to each other.
    t = [0.0]
    state_history = [np.array([V0, I0])]

    max_voltage_diff = 0.0
    max_current_diff = 0.0

    for i in range(steps):
        state_history.append(
            rk4_step(t[i], state_history[-1], dt,
                     lambda time, state: rlc_derivative(time, state, R, C, L)))
        t.append((i + 1) * dt)

        analytic = analytic_func(t[-1], V0, R, L, C)
        voltage_diff = abs(state_history[-1][0] - analytic[0])
        current_diff = abs(state_history[-1][1] - analytic[1])

        # compare the NEW diff against the running max so far -- not
        # against itself
        max_voltage_diff = max(voltage_diff, max_voltage_diff)
        max_current_diff = max(current_diff, max_current_diff)

    return max_voltage_diff, max_current_diff


# Run at normal dt, then at half dt -- double steps so both runs cover
# the SAME total simulated time, which is required for a fair comparison.
v_err_1, i_err_1 = convergence_test(
    cfg.dt, cfg.steps, cfg.V0, cfg.I0, cfg.R, cfg.L, cfg.C)
v_err_2, i_err_2 = convergence_test(
    cfg.dt / 2, cfg.steps * 2, cfg.V0, cfg.I0, cfg.R, cfg.L, cfg.C)

print(f"dt = {cfg.dt:.2e}   max voltage error = {v_err_1:.6e} V   max current error = {i_err_1:.6e} A")
print(f"dt/2 = {cfg.dt/2:.2e}   max voltage error = {v_err_2:.6e} V   max current error = {i_err_2:.6e} A")
print()
print(
    f"Voltage error ratio (should be ~16 for true 4th-order RK4): {v_err_1/v_err_2:.2f}")
print(
    f"Current error ratio (should be ~16 for true 4th-order RK4): {i_err_1/i_err_2:.2f}")
