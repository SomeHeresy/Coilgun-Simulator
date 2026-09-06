import csv
import numpy as np
from .integrator_rk4 import rk4_step
from .coilgun_derivative import coilgun_derivative
from .force import inductance
from .config import Config

cfg = Config()

# state is [V, I, x, v, W] -- W (cumulative resistive heat) starts at cfg.W0
t, state_history = [0.0], [
    np.array([cfg.V0, cfg.I0, cfg.x0, cfg.vel0, cfg.W0])]

for i in range(cfg.steps):
    state_history.append(
        rk4_step(t[i], state_history[-1], cfg.dt,
                 lambda time, state: coilgun_derivative(
                     time, state, cfg.R, cfg.C, cfg.L0, cfg.dL, cfg.a, cfg.mass,
                     cfg.lam_pm, cfg.a_pm)))
    t.append((i + 1) * cfg.dt)

# stack the history once so the checks below can slice whole columns instead of looping
history = np.array(state_history)
t = np.array(t)
V_all, I_all, x_all, v_all, W_all = history.T

final = state_history[-1]
print(
    f"Final: V={final[0]:.4f} I={final[1]:.4f} x={final[2]:.6f} v={final[3]:.4f} W={final[4]:.6e}")


# --- Velocity results ---
# The state at the last step is NOT a muzzle velocity, it is just wherever the slug was when
# the clock ran out. The two numbers below are the ones that mean something.

# peak velocity is what perfect switch timing would give, since the coil starts braking the
# slug the moment it passes centre and dL/dx changes sign.
peak_i = int(np.argmax(v_all))
print(f"\nPeak velocity:  {v_all[peak_i]:.4f} m/s "
      f"at t={t[peak_i]*1e3:.3f} ms, x={x_all[peak_i]*1e3:+.2f} mm")

# exit velocity is what a chronograph at the end of the barrel would read.
# RK4 steps straight over x_exit rather than landing on it, so interpolate between the two
# steps that bracket the crossing instead of taking whichever one happens to be closer.
crossed = np.nonzero(x_all >= cfg.x_exit)[0]
if len(crossed) == 0:
    print(f"Exit velocity:  slug never reached x_exit={cfg.x_exit*1e3:.1f} mm "
          f"(got to {x_all.max()*1e3:+.2f} mm) -- raise steps or lower x_exit")
else:
    j = crossed[0]
    frac = (cfg.x_exit - x_all[j-1]) / (x_all[j] - x_all[j-1])
    v_exit = v_all[j-1] + frac * (v_all[j] - v_all[j-1])
    t_exit = t[j-1] + frac * (t[j] - t[j-1])
    print(f"Exit velocity:  {v_exit:.4f} m/s "
          f"at t={t_exit*1e3:.3f} ms, x={cfg.x_exit*1e3:+.2f} mm")
    print(f"Suckback loss between peak and exit: "
          f"{v_all[peak_i]-v_exit:.4f} m/s ({100*(1-v_exit/v_all[peak_i]):.1f}%)")


# --- Full energy identity check ---
# capacitor + inductor + kinetic + cumulative dissipated heat should equal
# the starting energy at EVERY step, not just avoid increasing.
L_all = inductance(x_all, cfg.L0, cfg.dL, cfg.a)
e_totals = (0.5 * cfg.C * V_all**2 + 0.5 * L_all * I_all**2
            + 0.5 * cfg.mass * v_all**2 + W_all)

max_deviation = np.max(np.abs(e_totals - e_totals[0]))

print(f"\nStarting total energy: {e_totals[0]:.10e} J")
print(f"Final total energy:    {e_totals[-1]:.10e} J")
print(
    f"Max deviation from starting energy across all steps: {max_deviation:.6e} J")
print(f"Relative deviation: {max_deviation/e_totals[0]:.2e}")


# --- CSV output ---
# one row per step so the trajectory can be plotted or checked outside python.
with open("results_timeseries.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["t_s", "V_volts", "I_amps", "x_m", "v_mps", "W_joules"])
    for row in zip(t, V_all, I_all, x_all, v_all, W_all):
        writer.writerow([f"{value:.9e}" for value in row])

print(f"\nWrote {len(t)} rows to results_timeseries.csv")
