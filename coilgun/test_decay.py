import math
from integrator_rk4 import rk4_step
from rlc import derivative_func

V0, R, C, dt, steps = 5.0, 100, 1e-4, 1e-6, 20
t, V = [0], [V0]

for i in range(steps):
    v_current = V[-1]
    V.append(rk4_step(v_current, dt, lambda v: derivative_func(v, R, C)))
    t.append(t[-1] + dt)

print(f"Final voltage: {V[-1]:.6f} V")
expected_voltage = V0 * math.exp(-t[-1] / (R * C))
print(f"Expected voltage: {expected_voltage:.6f} V")
print(abs(V[-1] - expected_voltage))
