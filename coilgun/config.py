from dataclasses import dataclass


# One place for every simulation parameter, so run_rlc.py and validate_rlc.py cannot drift apart.
# When the force model lands, its parameters (L0, dL, a, mass, x0, v0) get added here, not to the scripts.
@dataclass
class Config:
    V0: float = 500.0    # initial capacitor voltage, V
    I0: float = 0.0      # initial current, A
    R: float = 0.15      # total circuit resistance, ohm
    C: float = 660e-6    # capacitance, F
    L: float = 1.5e-4    # coil inductance, H
    dt: float = 1e-6     # fixed RK4 time step, s
    steps: int = 6000    # number of steps to run
