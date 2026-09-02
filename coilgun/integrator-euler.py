import math

V0, R, C, dt, steps = 5.0, 100, 1e-4, 1e-6, 2000
t, V = [0], [V0]

for i in range(steps):
    dVdt = -V[-1] / (R * C)
    V.append(V[-1] + dVdt * dt)
    t.append(t[-1] + dt)

print(f"Final voltage: {V[-1]:.6f} V")
expected_voltage = V0 * math.exp(-t[-1] / (R * C))
print(f"Expected voltage: {expected_voltage:.6f} V")
print(abs(V[-1] - expected_voltage))
