import dataclasses
import numpy as np
import pytest
from coilgun.config import Config
from coilgun.force import (inductance, d_inductance_dx,
                           flux_linkage, d_flux_linkage_dx)

cfg = Config()


# A wrong sign or a dropped factor of 2 in either derivative would not crash, it would just make
# the slug fly at the wrong speed. Comparing against a central difference catches that.
# Central difference, not one-sided: its error goes as h^2 instead of h, so a real bug cannot
# hide inside the approximation's own error.
@pytest.mark.parametrize("x", [-cfg.a, -cfg.a/2, cfg.a/2, cfg.a, 2*cfg.a])
def test_d_inductance_dx_matches_numerical_derivative(x):
    h = cfg.a * 1e-6
    numeric = (inductance(x + h, cfg.L0, cfg.dL, cfg.a)
               - inductance(x - h, cfg.L0, cfg.dL, cfg.a)) / (2 * h)
    analytic = d_inductance_dx(x, cfg.L0, cfg.dL, cfg.a)
    assert abs(analytic - numeric) / abs(numeric) < 1e-6


@pytest.mark.parametrize("x", [-cfg.a_pm, -cfg.a_pm/2, cfg.a_pm/2, cfg.a_pm])
def test_d_flux_linkage_dx_matches_numerical_derivative(x):
    lam_pm, h = 0.015, cfg.a_pm * 1e-6
    numeric = (flux_linkage(x + h, lam_pm, cfg.a_pm)
               - flux_linkage(x - h, lam_pm, cfg.a_pm)) / (2 * h)
    analytic = d_flux_linkage_dx(x, lam_pm, cfg.a_pm)
    assert abs(analytic - numeric) / abs(numeric) < 1e-6


# The relative check above divides by zero at the centre, so that point gets its own test.
# This zero is the whole project: it is where the force vanishes and then reverses.
def test_force_vanishes_at_coil_centre():
    assert d_inductance_dx(0.0, cfg.L0, cfg.dL, cfg.a) == 0.0
    assert d_flux_linkage_dx(0.0, 0.015, cfg.a_pm) == 0.0


def test_inductance_peaks_at_centre_and_decays_far_away():
    assert inductance(0.0, cfg.L0, cfg.dL, cfg.a) == pytest.approx(cfg.L0 + cfg.dL)
    assert inductance(10*cfg.a, cfg.L0, cfg.dL, cfg.a) == pytest.approx(cfg.L0)


# Suckback in one assertion: the coil pulls the slug forward before the centre and drags it
# back after, because dL/dx changes sign there.
def test_force_reverses_across_the_coil_centre():
    before = d_inductance_dx(-cfg.a, cfg.L0, cfg.dL, cfg.a)
    after = d_inductance_dx(cfg.a, cfg.L0, cfg.dL, cfg.a)
    assert before > 0 and after < 0
    assert before == pytest.approx(-after)
