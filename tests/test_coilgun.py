import dataclasses
import numpy as np
import pytest
from coilgun.config import Config
from coilgun.force import inductance
from coilgun.simulate import simulate, peak_and_exit

STEEL = Config()
MAGNET = dataclasses.replace(Config(), dL=40e-6, lam_pm=0.015,
                             a=0.0191, a_pm=0.0191, mass=0.03923)


# Capacitor + inductor + kinetic + dissipated heat, which must stay constant at every step.
def total_energy(cfg, history):
    V, I, x, v, W = history.T
    L = inductance(x, cfg.L0, cfg.dL, cfg.a)
    return 0.5*cfg.C*V**2 + 0.5*L*I**2 + 0.5*cfg.mass*v**2 + W


# This is the test that matters most. The force term and the back-EMF term are two halves of the
# same bookkeeping -- keep one without the other and the slug gains energy the capacitor never
# paid for. Nothing else in the suite would notice, the numbers would just be wrong.
@pytest.mark.parametrize("cfg", [STEEL, MAGNET], ids=["steel", "magnet"])
def test_energy_is_conserved(cfg):
    t, history = simulate(dataclasses.replace(cfg, steps=4000))
    energies = total_energy(cfg, history)
    assert np.max(np.abs(energies - energies[0])) / energies[0] < 1e-10


@pytest.mark.parametrize("cfg", [STEEL, MAGNET], ids=["steel", "magnet"])
def test_is_fourth_order(cfg):
    # compare final states at three step sizes over the same total simulated time
    coarse = dataclasses.replace(cfg, dt=1e-5, steps=600)
    finals = [simulate(dataclasses.replace(coarse, dt=coarse.dt/n,
                                           steps=coarse.steps*n))[1][-1]
              for n in (1, 2, 4)]
    ratio = (np.linalg.norm(finals[0] - finals[1])
             / np.linalg.norm(finals[1] - finals[2]))
    assert 14 < ratio < 18


# lam_pm = 0 has to reduce exactly to the plain ferromagnetic case, otherwise adding the magnet
# support quietly changed the results that were already validated.
def test_zero_flux_linkage_reduces_to_the_ferromagnetic_case():
    cfg = dataclasses.replace(Config(), steps=2000)
    _, without = simulate(cfg)
    _, with_zero = simulate(dataclasses.replace(cfg, lam_pm=0.0, a_pm=0.03))
    assert np.array_equal(without, with_zero)


# The slug must be pulled toward the coil on approach and braked after it passes centre.
# If this fails, a sign is wrong somewhere in dL/dx or the force term.
def test_peak_velocity_occurs_at_the_coil_centre():
    t, history = simulate(STEEL)
    x, v = history[:, 2], history[:, 3]
    assert abs(x[int(np.argmax(v))]) < 1e-3
    assert v[-1] < v.max()


def test_exit_velocity_is_interpolated_onto_the_barrel_end():
    t, history = simulate(STEEL)
    peak, exit_v = peak_and_exit(t, history, STEEL.x_exit)
    assert exit_v is not None
    # exit must sit between the two steps that bracket the crossing, not on either of them
    j = np.nonzero(history[:, 2] >= STEEL.x_exit)[0][0]
    low, high = sorted((history[j-1, 3], history[j, 3]))
    assert low <= exit_v <= high
    assert exit_v < peak


def test_reports_no_exit_when_the_slug_never_reaches_the_barrel_end():
    cfg = dataclasses.replace(Config(), steps=500)
    t, history = simulate(cfg)
    peak, exit_v = peak_and_exit(t, history, cfg.x_exit)
    assert exit_v is None
