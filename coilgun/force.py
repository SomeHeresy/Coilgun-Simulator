import numpy as np


def inductance(x, L0, dL, a):
    return L0 + dL * np.exp(-(x/a) ** 2)


def d_inductance_dx(x, L0, dL, a):
    return -(2 * x / a**2) * dL * np.exp(-(x/a) ** 2)


# The two functions above cover a plain ferromagnetic slug, which only ever changes the coil's
# own inductance. A permanent magnet also pushes its own flux through the coil, and that flux
# does not depend on the coil current at all, so it needs its own pair of functions.
# lam_pm is the peak flux linkage in webers, reached when the magnet sits at the coil centre.
# Set lam_pm = 0 for a ferromagnetic slug and everything below drops out cleanly.
def flux_linkage(x, lam_pm, a_pm):
    return lam_pm * np.exp(-(x/a_pm) ** 2)


# Same shape as d_inductance_dx because the bump has the same Gaussian form.
# The sign of lam_pm is the magnet's polarity -- flipping the magnet flips this term, which
# flips whether the coil pulls or pushes for a given current direction.
def d_flux_linkage_dx(x, lam_pm, a_pm):
    return -(2 * x / a_pm**2) * lam_pm * np.exp(-(x/a_pm) ** 2)


if __name__ == "__main__":
    # pulled from Config so this check cannot drift away from the values the sim actually uses
    from .config import Config
    cfg = Config()
    L0, dL, a = cfg.L0, cfg.dL, cfg.a

    h = a * 1e-6

    for x in [-a, a/2, 2*a, a]:
        analytic = d_inductance_dx(x, L0, dL, a)
        numeric = (inductance(x + h, L0, dL, a) -
                   inductance(x - h, L0, dL, a)) / (2 * h)
        rel_error = abs(analytic - numeric) / abs(numeric)
        print(
            f"x={x:.5f}   analytic={analytic:.6e}   numeric={numeric:.6e}   rel_error={rel_error:.2e}")

    # the permanent magnet flux linkage uses the same Gaussian, so check its derivative too
    lam_pm, a_pm = 0.015, cfg.a_pm
    for x in [-a_pm, a_pm/2, a_pm]:
        analytic = d_flux_linkage_dx(x, lam_pm, a_pm)
        numeric = (flux_linkage(x + h, lam_pm, a_pm) -
                   flux_linkage(x - h, lam_pm, a_pm)) / (2 * h)
        rel_error = abs(analytic - numeric) / abs(numeric)
        print(
            f"x={x:.5f}   d_flux/dx analytic={analytic:.6e}   numeric={numeric:.6e}   rel_error={rel_error:.2e}")

    # x=0 special case
    print("d_inductance_dx(0) =", d_inductance_dx(
        0, L0, dL, a), "(should be exactly 0)")

    # sanity check on inductance() itself
    print("inductance(0) =", inductance(0, L0, dL, a), "(should equal L0+dL)")
    print("inductance(10a) =", inductance(
        10*a, L0, dL, a), "(should be close to L0)")
