import numpy as np
from .integrator_rk4 import rk4_step
from .rlc import rlc_derivative
from .config import Config

# variables, state_history is a list of [V, I] arrays used in rlc.py to calculate di/dt and dV/dt.
# t is a list of time values.
cfg = Config()
t, state_history = [0.0], [np.array([cfg.V0, cfg.I0])]

for i in range(cfg.steps):
    # the lambda hands rk4_step whatever time it asks for, instead of pinning every stage to t[i].
    state_history.append(
        rk4_step(t[i], state_history[-1], cfg.dt,
                 lambda time, state: rlc_derivative(time, state, cfg.R, cfg.C, cfg.L)))
    # rebuild t from the step count rather than adding dt each pass, so rounding cannot accumulate.
    t.append((i + 1) * cfg.dt)

# state_history[][] meaning: state_history[the latest step][0 for voltage, 1 for current]
print(f"Final voltage: {state_history[-1][0]:.6f} V")
print(f"Final current: {state_history[-1][1]:.6f} A")


# --- Energy conservation check ---
energies = []

# calculate stored energy in the capacitor and inductor at each time step, also the total energy in the system.
for state in state_history:
    V, I = state[0], state[1]
    cap_energy = 0.5 * cfg.C * V**2
    ind_energy = 0.5 * cfg.L * I**2
    energies.append(cap_energy + ind_energy)

print(f"\nInitial stored energy: {energies[0]:.10e} J")
print(f"Final stored energy:   {energies[-1]:.10e} J")

# check difference between initial and final energy for each step, and count how many times the energy increased from one step to the next.
# also track the largest single increase in energy.
# the resistor only ever removes energy, so stored energy rising at any step means the integrator invented it.
increases = 0
max_jump = 0.0
for i in range(1, len(energies)):
    delta = energies[i] - energies[i - 1]
    if delta > 0:
        increases += 1
        max_jump = max(max_jump, delta)

print(
    f"\nSteps where stored energy increased: {increases} out of {len(energies) - 1}")
if increases > 0:
    print(
        f"Largest single increase: {max_jump:.6e} J  <-- investigate if this is large")
else:
    print("Stored energy never increased step-to-step -- Good, no free energy appearing.")
