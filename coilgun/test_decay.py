import math
from integrator_rk4 import rk4_step
from rlc import derivative_func
import numpy as np

# variables, state_history is a list of [V, I] arrays used in rlc.py to calculate di/dt and dV/dt.
# t is a list of time values.
V0, I0, R, C, L, dt, steps = 5.0, 0.0, 100, 1e-4, 1e-3, 1e-6, 200
t, state_history = [0], [np.array([V0, I0])]

for i in range(steps):
    state_history.append(
        rk4_step(state_history[-1], dt, lambda v: derivative_func(v, R, C, L)))
    t.append(t[-1] + dt)

# state_history[][] meaning: state_history[the latest step][0 for voltage, 1 for current]
print(f"Final voltage: {state_history[-1][0]:.6f} V")
print(f"Final current: {state_history[-1][1]:.6f} A")

# --- Energy conservation check ---
energies = []

# calculate stored energy in the capacitor and inductor at each time step, also the total energy in the system.
for state in state_history:
    V, I = state[0], state[1]
    cap_energy = 0.5 * C * V**2
    ind_energy = 0.5 * L * I**2
    energies.append(cap_energy + ind_energy)

print(f"\nInitial stored energy: {energies[0]:.10e} J")
print(f"Final stored energy:   {energies[-1]:.10e} J")

# check difference between initial and final energy for each step, and count how many times the energy increased from one step to the next.
# also track the largest single increase in energy.
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
