# a generic implementation of the Runge-Kutta 4th order method for solving capacitor discharge problems.
# This is used in run_rlc.py to solve the RLC circuit equations.

def rk4_step(t, state, dt, derivative_func):
    # state must be a numpy array so the + and * below act on the whole state at once.
    # derivative_func is called as derivative_func(t, state) and returns an array of the same shape.
    # t is passed in because RK4 samples the derivative at the start of the step, twice at the
    # midpoint, and at the end. Reusing one t for all four stages is invisible now, but it would
    # drop the method below 4th order as soon as the physics depends on t, which switch timing does.
    k1 = derivative_func(t, state)
    k2 = derivative_func(t + dt / 2, state + k1 * (dt / 2))
    k3 = derivative_func(t + dt / 2, state + k2 * (dt / 2))
    k4 = derivative_func(t + dt, state + k3 * dt)
    k_avg = (k1 + 2 * k2 + 2 * k3 + k4) / 6
    final_state = state + k_avg * dt
    return final_state
