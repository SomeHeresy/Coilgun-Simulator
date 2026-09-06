import numpy as np


# state is [V, I]. t is unused while the circuit is just an RLC loop, but it stays in the
# signature because the switch timing added later does depend on it.
def rlc_derivative(t, state, R, C, L):
    dvdt = -state[1] / C
    didt = (state[0] - R * state[1]) / L
    return np.array([dvdt, didt])
