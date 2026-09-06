import numpy as np
from .force import inductance, d_inductance_dx, flux_linkage, d_flux_linkage_dx


# Pure function, same style as rlc_derivative: plain numbers in, plain array out.
# No Config here -- the driver script owns Config and passes these values in.
#
# Handles both projectile types through one set of equations. The total flux through the coil is
#     lambda = L(x)*I + lam_pm(x)
# where the first term is the coil's own field (ferromagnetic slug raises L, so this term is what
# accelerates it) and the second is the magnet's own field threading the coil (independent of I).
# lam_pm = 0 gives a plain ferromagnetic slug and every extra term below vanishes.
def coilgun_derivative(t, state, R, C, L0, dL, a, mass, lam_pm=0.0, a_pm=1.0):
    V, I, x, v, W = state

    L = inductance(x, L0, dL, a)
    dL_dx = d_inductance_dx(x, L0, dL, a)
    d_lam_dx = d_flux_linkage_dx(x, lam_pm, a_pm)

    dv_dt_cap = -I / C
    # both motion terms are back-EMF: the slug moving changes the flux through the coil, and the
    # circuit has to pay for that. They pair with the two force terms below -- keeping one without
    # the other is exactly the free-energy bug, so the energy check in run_coilgun.py catches it.
    di_dt = (V - R*I - I*v*dL_dx - v*d_lam_dx) / L
    dx_dt = v
    # reluctance force is quadratic in I and does not care about current direction.
    # magnet force is linear in I, so reversing the current reverses it.
    dvel_dt = (0.5 * I**2 * dL_dx + I * d_lam_dx) / mass
    dW_dt = I**2 * R

    return np.array([dv_dt_cap, di_dt, dx_dt, dvel_dt, dW_dt])
