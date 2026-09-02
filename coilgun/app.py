import math

V0, R, C, dt, steps = 5.0, 100, 1e-4, 1e-6, 2000
t, V = [0], [V0]

for i in range(steps):
    dVdt = -V[-1] / (R * C)
    V.append(V[-1] + dVdt * dt)
    t.append(t[-1] + dt)

print(f"Final voltage: {V[-1]:.6f} V")
print(f"Expected voltage: {V0 * math.exp(-t[-1] / (R * C)):.6f} V")
print(abs(V[-1] - V0 * math.exp(-t[-1] / (R * C))))

# new method

V0, R, C, dt, steps = 5.0, 100, 1e-4, 1e-6, 2000
t, V = [0], [V0]

for i in range(steps):
    k1_dvdt = -V[-1] / (R * C)
    vmid_a = V[-1] + k1_dvdt * (dt / 2)
    k2_dvdt = -vmid_a / (R * C)
    vmid_b = V[-1] + k2_dvdt * (dt / 2)
    k3_dvdt = -vmid_b / (R * C)
    vend = V[-1] + k3_dvdt * dt
    k4_dvdt = -vend / (R * C)
    k_avg_dvdt = (k1_dvdt + 2 * k2_dvdt + 2 * k3_dvdt + k4_dvdt) / 6
    V.append(V[-1] + k_avg_dvdt * dt)
    t.append(t[-1] + dt)

print(f"Final voltage: {V[-1]:.6f} V")
print(f"Expected voltage: {V0 * math.exp(-t[-1] / (R * C)):.6f} V")
print(abs(V[-1] - V0 * math.exp(-t[-1] / (R * C))))
