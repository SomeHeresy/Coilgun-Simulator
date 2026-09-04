import numpy as np


def derivative_func(state, R, C, L):
    dvdt = -state[1] / C
    didt = (state[0] - R * state[1]) / L
    return np.array([dvdt, didt])
