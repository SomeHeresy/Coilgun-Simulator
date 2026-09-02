import math

V0, R, C, dt, steps = 5.0, 100, 1e-4, 1e-6, 20
t, V = [0], [V0]


def rk4_step(v_current, dt, R, C):
    k1_dvdt = -v_current / (R * C)
    vmid_a = v_current + k1_dvdt * (dt / 2)
    k2_dvdt = -vmid_a / (R * C)
    vmid_b = v_current + k2_dvdt * (dt / 2)
    k3_dvdt = -vmid_b / (R * C)
    vend = v_current + k3_dvdt * dt
    k4_dvdt = -vend / (R * C)
    k_avg_dvdt = (k1_dvdt + 2 * k2_dvdt + 2 * k3_dvdt + k4_dvdt) / 6
    final_voltage = v_current + k_avg_dvdt * dt
    return final_voltage


for i in range(steps):
    v_current = V[-1]
    V.append(rk4_step(v_current, dt, R, C))
    t.append(t[-1] + dt)

print(f"Final voltage: {V[-1]:.6f} V")
expected_voltage = V0 * math.exp(-t[-1] / (R * C))
print(f"Expected voltage: {expected_voltage:.6f} V")
print(abs(V[-1] - expected_voltage))
