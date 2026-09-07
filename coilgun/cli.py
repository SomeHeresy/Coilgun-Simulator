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


# The two projectiles I have. Mirrors configs/v3_steel.json and configs/v3_magnet.json.
PROJECTILES = {
    "steel": {"mass": 0.05464, "dL": 750e-6, "a": 0.0205,
              "lam_pm": 0.0, "a_pm": 0.0191, "steps": 12000},
    "magnet": {"mass": 0.03923, "dL": 40e-6, "a": 0.0191,
               "lam_pm": 0.015, "a_pm": 0.0191, "steps": 45000},
}


# Ask for one value, showing the current one in brackets. Empty input keeps it, bad input asks
# again rather than crashing halfway through a list of questions.
def ask(label, current, cast=float):
    while True:
        raw = input(f"  {label} [{current}]: ").strip()
        if raw == "":
            return current
        try:
            return cast(raw)
        except ValueError:
            print(f"    '{raw}' is not a number, try again")


def ask_choice(label, options, current):
    while True:
        raw = input(f"{label} ({'/'.join(options)}) [{current}]: ").strip().lower()
        if raw == "":
            return current
        if raw in options:
            return raw
        print(f"    pick one of: {', '.join(options)}")


# Walk the user through the parameters instead of making them write a config file.
# Starts from whatever cfg was already built, so --config and --interactive combine.
def ask_for_config(cfg):
    print("Coilgun simulator -- press Enter to keep the value in brackets.")
    print()

    projectile = ask_choice("Projectile type", ("steel", "magnet"),
                            "magnet" if cfg.lam_pm != 0 else "steel")
    cfg = dataclasses.replace(cfg, **PROJECTILES[projectile])

    print()
    print("Capacitor bank")
    cfg = dataclasses.replace(
        cfg,
        V0=ask("Charge voltage, V", cfg.V0),
        C=ask("Capacitance, F", cfg.C),
        R=ask("Circuit resistance, ohm", cfg.R))

    print()
    print("Coil and projectile")
    cfg = dataclasses.replace(
        cfg,
        L0=ask("Coil inductance with slug far away L0, H", cfg.L0),
        dL=ask("Inductance rise with slug centred dL, H", cfg.dL),
        a=ask("Width of the inductance bump a, m", cfg.a),
        mass=ask("Projectile mass, kg", cfg.mass),
        x0=ask("Starting position, m (negative = before coil centre)", cfg.x0),
        x_exit=ask("Barrel end, m from coil centre", cfg.x_exit))

    if projectile == "magnet":
        cfg = dataclasses.replace(
            cfg,
            lam_pm=ask("Peak flux linkage of the magnet, Wb", cfg.lam_pm),
            a_pm=ask("Width of the flux linkage bump, m", cfg.a_pm))

    print()
    print("Solver")
    cfg = dataclasses.replace(
        cfg,
        dt=ask("Time step, s", cfg.dt),
        steps=ask("Number of steps", cfg.steps, int))

    print()
    return cfg


# Give every field in Config its own command line flag, generated from the dataclass itself so
# adding a parameter to Config makes it settable here without touching this file.
def add_config_arguments(parser):
    group = parser.add_argument_group(
        "simulation parameters",
        "any of these override the config file and the defaults in config.py")
    for field in dataclasses.fields(Config):
        group.add_argument(f"--{field.name}", type=type(field.default),
                           help=f"default {field.default}")


def main():
    parser = argparse.ArgumentParser(
        description="Simulate one coilgun stage and report peak and exit velocity.")
    parser.add_argument("--config", help="JSON file of Config overrides")
    parser.add_argument("--csv", help="write the time series to this CSV file")
    parser.add_argument("-i", "--interactive", action="store_true",
                        help="ask for each parameter instead of reading flags")
    add_config_arguments(parser)
    args = parser.parse_args()

    # three layers, each beating the one before it: config.py defaults, then the JSON file,
    # then anything typed on the command line.
    cfg = load_config(args.config) if args.config else Config()
    typed = {field.name: getattr(args, field.name)
             for field in dataclasses.fields(Config)
             if getattr(args, field.name) is not None}
    if typed:
        cfg = dataclasses.replace(cfg, **typed)

    # interactive runs last so the questions are pre-filled with whatever the file and flags set.
    # Ctrl-C or a closed stdin should quit cleanly, not dump a traceback.
    if args.interactive:
        try:
            cfg = ask_for_config(cfg)
        except (KeyboardInterrupt, EOFError):
            raise SystemExit("\ncancelled")

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
