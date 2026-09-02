def rk4_step(v_current, dt, derivative_func):
    k1_dvdt = derivative_func(v_current)
    vmid_a = v_current + k1_dvdt * (dt / 2)
    k2_dvdt = derivative_func(vmid_a)
    vmid_b = v_current + k2_dvdt * (dt / 2)
    k3_dvdt = derivative_func(vmid_b)
    vend = v_current + k3_dvdt * dt
    k4_dvdt = derivative_func(vend)
    k_avg_dvdt = (k1_dvdt + 2 * k2_dvdt + 2 * k3_dvdt + k4_dvdt) / 6
    final_voltage = v_current + k_avg_dvdt * dt
    return final_voltage
