from dataclasses import dataclass


# One place for every simulation parameter, so the run and validate scripts cannot drift apart.
# Values marked ESTIMATE are not measured from the V3 hardware -- see README before quoting any
# result that depends on them.
#
# Two projectiles fit the same equations, they just use different numbers. Both are 13 mm across
# and roughly as long as the coil, so they differ magnetically, not geometrically.
#
#   steel slug   44.0 mm   dL = 750e-6   lam_pm = 0.0      mass = 0.05464   a = 0.0205   <- default below, and
#                                                                              the only measured case
#   magnet slug  38.1 mm   dL = 40e-6    lam_pm = 0.015    mass = 0.03923   a = 0.0191
#
# The magnet's dL is far smaller on purpose. NdFeB has a recoil permeability near 1.05, so it is
# magnetically almost air and barely raises the coil's inductance, while soft steel raises it a
# lot. Giving the magnet the steel dL would count the same force twice.
@dataclass
class Config:
    V0: float = 350.0    # initial capacitor voltage, V (the single-stage condition I can actually verify)
    I0: float = 0.0      # initial current, A
    R: float = 0.15      # total circuit resistance, ohm  ESTIMATE
    C: float = 660e-6    # capacitance, F
    L: float = 750e-6    # fixed coil inductance, H -- only used by the older run_rlc.py / validate_rlc.py
    L0: float = 750e-6   # base inductance with the slug far away, H  ESTIMATE
                         # Wheeler's multilayer formula gives ~590 uH for 280 turns on this coil,
                         # so 750 uH is the right order but should be measured with an LCR meter
    W0: float = 0.0      # dissipated energy, J
    dL: float = 750e-6   # extra inductance with the slug centred, H  ESTIMATE, and results are very sensitive to it
    a: float = 0.0205    # width of the inductance bump, m, derived from geometry rather than guessed:
                         # coil and slug stop overlapping at |x| = (44 mm + 44 mm)/2 = 44 mm, and a
                         # Gaussian is down to ~1% at 2.15a, so a = 44/2.15 ~ 20.5 mm.
                         # Results are very sensitive to this -- see README.
    mass: float = 0.05464      # steel slug mass, kg (54.64 g, measured; 13 mm dia x 44 mm)
                               # that works out to 9.36 g/cm3, too dense for plain steel, so the
                               # slug is either wider than 13 mm or some other alloy. Only the mass
                               # enters the equations, and the mass is measured, so this is a
                               # labelling question rather than a modelling one.
    x0: float = -0.022   # initial projectile position, m (negative = before the coil centre).
                         # This is where the slug actually sits on the hardware: the 44 mm slug
                         # spans -44 mm to 0 mm while the 44 mm coil spans -22 mm to +22 mm, so
                         # half the slug starts inside the coil.
                         # x0 and a are coupled: a narrower bump means the slug has to start closer
                         # or it sits outside the force region entirely and barely moves.
    vel0: float = 0.0    # initial projectile velocity, m/s
    x_exit: float = 0.05   # barrel end measured from coil centre, m  ESTIMATE
    # Permanent magnet projectile. lam_pm is the peak flux the magnet pushes through the coil.
    # Leave it at 0.0 for a plain ferromagnetic slug, which is what the 6-7 m/s measurement used.
    lam_pm: float = 0.0    # peak flux linkage of a magnet slug, Wb  ESTIMATE when non-zero
    a_pm: float = 0.0191   # width of the flux linkage bump, m, same geometric argument as a but
                           # with the 38.1 mm magnet: (44 + 38.1)/2 / 2.15 ~ 19.1 mm
    dt: float = 1e-6     # fixed RK4 time step, s
    steps: int = 12000   # number of steps to run (long enough for the slug to clear x_exit)
