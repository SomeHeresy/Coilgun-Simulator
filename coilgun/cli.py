import argparse
import csv
import dataclasses
import json
from .config import Config
from .force import inductance
from .simulate import simulate, peak_and_exit


# Build a Config from a JSON file. Anything the file leaves out keeps the default from config.py,
# so a config only has to list what it changes.
def load_config(path):
    with open(path) as f:
        overrides = json.load(f)

    known = {field.name for field in dataclasses.fields(Config)}
    unknown = set(overrides) - known
    # a typo in a JSON key would otherwise be silently ignored and you would spend an hour
    # wondering why the run did not change.
    if unknown:
        raise SystemExit(f"unknown keys in {path}: {', '.join(sorted(unknown))}")

    return dataclasses.replace(Config(), **overrides)


def write_csv(path, t, history):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["t_s", "V_volts", "I_amps", "x_m", "v_mps", "W_joules"])
        for row in zip(t, *history.T):
            writer.writerow([f"{value:.9e}" for value in row])


def main():
    parser = argparse.ArgumentParser(
        description="Simulate one coilgun stage and report peak and exit velocity.")
    parser.add_argument("--config", help="JSON file of Config overrides")
    parser.add_argument("--csv", help="write the time series to this CSV file")
    args = parser.parse_args()

    cfg = load_config(args.config) if args.config else Config()

    t, history = simulate(cfg)
    V_all, I_all, x_all, v_all, W_all = history.T
    peak, exit_v = peak_and_exit(t, history, cfg.x_exit)

    projectile = "magnet" if cfg.lam_pm != 0 else "ferromagnetic slug"
    print(f"{projectile}, {cfg.mass*1e3:.2f} g, fired at {cfg.V0:.0f} V "
          f"from x0 = {cfg.x0*1e3:+.1f} mm")
    print(f"Peak velocity:  {peak:.4f} m/s")

    if exit_v is None:
        print(f"Exit velocity:  slug never reached x_exit={cfg.x_exit*1e3:.1f} mm "
              f"(got to {x_all.max()*1e3:+.2f} mm) -- raise steps or lower x_exit")
    else:
        bank_energy = 0.5 * cfg.C * cfg.V0**2
        muzzle_energy = 0.5 * cfg.mass * exit_v**2
        print(f"Exit velocity:  {exit_v:.4f} m/s")
        print(f"Suckback loss between peak and exit: "
              f"{peak-exit_v:.4f} m/s ({100*(1-exit_v/peak):.1f}%)")
        print(f"Efficiency: {muzzle_energy:.3f} J of {bank_energy:.1f} J "
              f"= {100*muzzle_energy/bank_energy:.2f}%")

    # same identity as run_coilgun.py -- if this is not tiny the run is not trustworthy
    L_all = inductance(x_all, cfg.L0, cfg.dL, cfg.a)
    e_totals = (0.5 * cfg.C * V_all**2 + 0.5 * L_all * I_all**2
                + 0.5 * cfg.mass * v_all**2 + W_all)
    deviation = max(abs(e_totals - e_totals[0])) / e_totals[0]
    print(f"Energy identity holds to {deviation:.2e} relative")

    if args.csv:
        write_csv(args.csv, t, history)
        print(f"Wrote {len(t)} rows to {args.csv}")


if __name__ == "__main__":
    main()
