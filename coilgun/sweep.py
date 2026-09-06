import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")   # no display needed, just write PNG files
import matplotlib.pyplot as plt
from dataclasses import replace
from .config import Config
from .simulate import simulate, peak_and_exit


base = Config()

# --- Sweep the starting position ---
# x0 is where the slug sits when the bank fires. It is the one number that is genuinely free
# on the hardware, and sweeping it is the smooth stand-in for switch timing: too far back and
# the current has decayed before the slug arrives, too close and the slug reaches centre while
# current is still high, so the coil brakes it on the way out.
start_positions = np.linspace(-0.09, -0.005, 60)
peaks, exits = [], []

for x0 in start_positions:
    t, history = simulate(replace(base, x0=float(x0)))
    peak, exit_v = peak_and_exit(t, history, base.x_exit)
    peaks.append(peak)
    exits.append(np.nan if exit_v is None else exit_v)

peaks, exits = np.array(peaks), np.array(exits)

best_peak_i = int(np.nanargmax(peaks))
best_exit_i = int(np.nanargmax(exits))
print(f"Best peak velocity: {peaks[best_peak_i]:.3f} m/s "
      f"at x0 = {start_positions[best_peak_i]*1e3:.1f} mm")
print(f"Best exit velocity: {exits[best_exit_i]:.3f} m/s "
      f"at x0 = {start_positions[best_exit_i]*1e3:.1f} mm")

with open("results_sweep.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["x0_m", "peak_velocity_mps", "exit_velocity_mps"])
    for row in zip(start_positions, peaks, exits):
        writer.writerow([f"{value:.9e}" for value in row])
print("Wrote results_sweep.csv")


# --- Plot 1: the sweep ---
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.plot(start_positions * 1e3, peaks, label="peak velocity (perfect timing)")
ax.plot(start_positions * 1e3, exits, label="exit velocity at barrel end")
ax.axvline(start_positions[best_exit_i] * 1e3, color="grey",
           linestyle="--", linewidth=1,
           label=f"best x0 = {start_positions[best_exit_i]*1e3:.1f} mm")
ax.set_xlabel("starting position of slug relative to coil centre (mm)")
ax.set_ylabel("velocity (m/s)")
ax.set_title(f"Velocity vs starting position ({base.V0:.0f} V, {base.C*1e6:.0f} uF)")
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("results_sweep.png", dpi=150)
print("Wrote results_sweep.png")


# --- Plot 2: the time series at the best starting position ---
best_cfg = replace(base, x0=float(start_positions[best_exit_i]))
t, history = simulate(best_cfg)
V_all, I_all, x_all, v_all, W_all = history.T

fig, axes = plt.subplots(2, 2, figsize=(10, 7))
for ax, series, label in zip(
        axes.flat,
        [V_all, I_all, x_all * 1e3, v_all],
        ["capacitor voltage (V)", "coil current (A)",
         "slug position (mm)", "slug velocity (m/s)"]):
    ax.plot(t * 1e3, series)
    ax.set_xlabel("time (ms)")
    ax.set_ylabel(label)
    ax.grid(alpha=0.3)

# the slug crosses the coil centre where dL/dx flips sign, which is exactly where the coil
# stops pulling and starts braking. marking it makes the suckback visible on the velocity plot.
axes.flat[2].axhline(0, color="red", linestyle="--", linewidth=1)
axes.flat[3].axvline(t[int(np.argmax(v_all))] * 1e3, color="red",
                     linestyle="--", linewidth=1, label="slug at coil centre")
axes.flat[3].legend()

fig.suptitle(f"Single stage at {base.V0:.0f} V, slug starting at "
             f"{best_cfg.x0*1e3:.1f} mm")
fig.tight_layout()
fig.savefig("results_timeseries.png", dpi=150)
print("Wrote results_timeseries.png")
