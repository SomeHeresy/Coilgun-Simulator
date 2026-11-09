# Coilgun Simulator

![tests](https://github.com/SomeHeresy/Coilgun-Simulator/actions/workflows/tests.yml/badge.svg)

A Python physics simulator for one coil gun stage.

- Models the capacitor discharge and the projectile's motion together.
- Uses a custom RK4 solver.
- Reports muzzle speed and the best starting position for the projectile.
- Works for a steel slug or a permanent magnet.

**Why:** my real coil gun (V3) fires a 54.64 g steel slug at 350 V and measures **6–7 m/s**. I wanted to predict that from physics, and be honest about where the model is wrong.

---

## Quick start

You need **Python 3.10+**. (On some systems, use `python3` instead of `python`.)

```bash
git clone https://github.com/SomeHeresy/Coilgun-Simulator.git
cd Coilgun-Simulator
pip install -r requirements.txt
python -m coilgun.cli
```

<details>
<summary>Optional: use a virtual environment</summary>

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

</details>

This simulates my V3 hardware and prints:

```
ferromagnetic slug, 54.64 g, fired at 350 V from x0 = -22.0 mm
Peak velocity:  18.1358 m/s
Exit velocity:  9.6437 m/s
Suckback loss between peak and exit: 8.4921 m/s (46.8%)
Efficiency: 2.541 J of 40.4 J = 6.29%
Energy identity holds to 5.75e-14 relative
```

> Keep the `-m`. Running `python coilgun/cli.py` directly fails with an ImportError.

---

## What the output means

| Line | Meaning |
|---|---|
| `x0` | Starting position from the coil center. Negative = behind it. |
| **Peak velocity** | Fastest speed, reached at the coil center. What you'd get with perfect timing. |
| **Exit velocity** | Speed at the barrel end. **This is what a chronograph measures.** |
| **Suckback loss** | Speed the coil pulls back after the projectile passes the center. |
| **Efficiency** | Muzzle energy ÷ energy stored in the capacitors. Real coil guns are usually 1–3%. |
| **Energy identity** | Self-check. Above ~1e-10 means don't trust the result (usually the time step is too big). |

---

## Use your own numbers

You don't need to edit any code. Pick one:

| Way | Command | Best for |
|---|---|---|
| **Interactive** | `python -m coilgun.cli -i` | First-time users. It asks for each value; press Enter to keep the default. |
| **Flags** | `python -m coilgun.cli --V0 400 --x0 -0.034` | Quick tests. See all flags with `--help`. |
| **JSON file** | `python -m coilgun.cli --config configs/v3_steel.json` | Setups you reuse. A file only needs the keys it changes. |
| **Defaults** | Edit `coilgun/config.py` | Making your hardware the default. |

They stack, in this order (later wins):

```
config.py  ->  --config file  ->  flags  ->  --interactive
```

Example: load a setup and change one value.

```bash
python -m coilgun.cli --config configs/v3_steel.json --V0 500
```

Two configs are included: `configs/v3_steel.json` and `configs/v3_magnet.json`. A misspelled key gives an error instead of being ignored.

---

## Save and plot results

```bash
python -m coilgun.cli --config configs/v3_steel.json --csv results.csv   # full time series to CSV
python -m coilgun.sweep                                                  # plots + sweep CSV (60 runs, a few seconds)
```

`sweep` writes `results_sweep.png`, `results_timeseries.png`, and `results_sweep.csv`.

---

## Tests

```bash
python -m pytest tests/ -v
```

22 tests, about 1 second. They run on every push (Python 3.10, 3.12, 3.13).

<details>
<summary>Other diagnostic scripts</summary>

These print checks instead of asserting. They read `coilgun/config.py` and take no arguments.

```bash
python -m coilgun.force              # dL/dx vs a numerical derivative
python -m coilgun.run_rlc            # circuit only, with an energy check
python -m coilgun.validate_rlc       # circuit vs the exact solution, convergence order
python -m coilgun.run_coilgun        # full model, energy check, writes a CSV
python -m coilgun.validate_coilgun   # convergence order for the full model
```

</details>

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `No module named coilgun` | Run from the project folder, and use `python -m coilgun.cli`. |
| `No module named numpy` (or matplotlib, pytest) | Run `pip install -r requirements.txt`, or activate your virtual environment. |
| `slug never reached x_exit` | The run ended too early. Raise `--steps` or lower `--x_exit`. Magnets need many more steps. |
| `unknown keys in ...` | Typo in your JSON. The message names the bad key. |
| Peak velocity is almost zero | The projectile starts too far from the coil. Try `--x0` about the same size as `--a`. |
| Energy identity above 1e-10 | Time step too big. Lower `--dt` and raise `--steps` by the same factor. |

---

## Results

Steel slug, 54.64 g, 350 V, starting 22 mm behind the coil center (where it sits on my hardware):

| | |
|---|---|
| Peak velocity | 18.14 m/s |
| Exit velocity | 9.64 m/s |
| Lost to suckback | **46.8%** |
| Predicted efficiency | 6.29% |
| Measured velocity | 6–7 m/s |
| Measured efficiency | 2.86% |

**Almost half the speed is lost after the slug passes the coil center.**

![velocity vs starting position](results_sweep.png)

Sweeping the starting position gives a prediction I can test:

```
Best peak velocity: 18.14 m/s at x0 = -22.3 mm   <- about where I put it
Best exit velocity: 13.22 m/s at x0 = -33.8 mm
```

Starting the slug **~12 mm further back** should raise exit speed from 9.64 to 13.22 m/s (**+37%**) with no other changes. That's the next hardware test.

![time series](results_timeseries.png)

---

## The physics

### Circuit

The capacitor discharging through the coil is a series RLC circuit:

```
dV/dt = -I / C
dI/dt = (V - I*R) / L
```

With my values (350 V, 660 µF, 750 µH, 0.15 Ω) the circuit is underdamped: the current rings instead of fading smoothly.

### Adding the projectile

The coil's inductance changes with the slug's position, and that change is what creates the force. I model it as a Gaussian bump:

```
L(x)  = L0 + dL * exp(-(x/a)^2)
dL/dx = -(2x/a^2) * dL * exp(-(x/a)^2)
```

Full equations, with state `[V, I, x, v, W]`:

```
dV/dt = -I / C
dI/dt = (V - I*R - I*v*dL/dx - v*dlambda_pm/dx) / L(x)
dx/dt = v
dv/dt = (0.5 * I^2 * dL/dx + I * dlambda_pm/dx) / m
dW/dt = I^2 * R
```

Two key points:

- **The force must come from the same `dL/dx` as the back-EMF.** Otherwise the slug gains energy the capacitor never supplied. That bug wouldn't crash or look obviously wrong.
- **Heat `W` is tracked inside the solver**, so the energy check is exact.

### Permanent magnets

A magnet adds its own flux through the coil, so total flux is:

```
lambda = L(x) * I + lambda_pm(x)
```

Setting `lambda_pm = 0` gives the steel case exactly. The magnet preset uses a much smaller `dL`, because a neodymium magnet barely raises the coil's inductance.

### Suckback

`dL/dx` flips sign at the coil center: the coil pulls the slug in, then pulls it back. This comes out of the model on its own, and peak speed lands at x = -0.01 mm (the coil center). **When to cut the current, or where to start the slug, is the whole problem.**

---

## How I know it's right

All four checks are automated in `tests/`.

1. **Matches the exact solution.** The circuit-only case has a known formula. Error stays below 1e-5.
2. **Correct convergence order.** RK4 error should drop 16× when the step halves. Measured **16.01** (circuit) and **16.04** (full model). Tests use a coarser step on purpose, so rounding noise doesn't hide the result.
3. **Energy is conserved.** Capacitor + coil + motion + heat stays constant to **6e-14**, for both projectiles:
   ```
   0.5*C*V^2 + 0.5*L(x)*I^2 + 0.5*m*v^2 + W = constant
   ```
4. **Derivatives are checked numerically.** Both match a finite-difference estimate to ~1e-11.

**The tests can fail.** I broke the code on purpose to check:

| Bug I added | Caught by |
|---|---|
| Removed the back-EMF term | Energy check, both projectiles |
| Flipped the force sign | Energy check + peak-at-center check |
| Dropped the factor of 2 in `dL/dx` | Numerical derivative check |

Another test confirms the magnet code gives the same steel results bit for bit when `lambda_pm = 0`.

---

## Where the model is wrong

The model predicts **9.64 m/s**; I measure **6–7 m/s**. It over-predicts by about 45%. I have not tuned anything to close that gap.

**Left out of the model**

- **Eddy currents** in the solid slug. Probably the biggest missing loss.
- **Magnetic saturation.** Real inductance rise is smaller at high current.
- **Friction** between slug and barrel.
- **Heating.** Coil resistance rises during the shot; here it's constant.

**Estimated, not measured**

- `L0 = 750 µH`. A standard formula gives ~590 µH, so it needs an LCR meter.
- `dL`. Not measured, and results are very sensitive to it.
- `a = 20.5 mm`. Derived from the coil and slug geometry. It's the most sensitive parameter.
- `lambda_pm` for the magnet is made up, so magnet results show shape, not exact values.
- `R = 0.15 Ω`.

**Simplifications**

- The slug is treated as a point, but it's as long as the coil (44 mm). This is the biggest simplification.
- `L(x)` is a Gaussian because it has the right shape, not because the real geometry gives one.
- One stage only.
- No flyback diode. Adding one would break RK4's accuracy at the switching moment.

**Open question:** the slug (13 mm × 44 mm, 54.64 g) is too dense for plain steel. Only the measured mass is used, so this doesn't affect results, but I don't know the material yet.

---

## Code layout

```
coilgun/
├── config.py               # all simulation parameters
├── integrator_rk4.py       # generic RK4 solver (no physics inside)
├── rlc.py                  # circuit-only equations
├── force.py                # L(x), dL/dx, and magnet flux
├── coilgun_derivative.py   # full 5-variable equations
├── simulate.py             # shared run loop
├── cli.py                  # command line + JSON config
├── sweep.py                # starting-position sweep and plots
├── run_rlc.py              # circuit-only run + energy check
├── run_coilgun.py          # full run + energy check
├── validate_rlc.py         # circuit accuracy and convergence
└── validate_coilgun.py     # full-model convergence
configs/                    # JSON setups for steel and magnet
tests/                      # pytest suite, run in CI
scratch/
└── integrator_euler.py     # first attempt (plain Euler), kept for reference
```

The solver knows no physics. It takes a state, a step size, and an equation function, so it never changed as the model grew from 1 variable to 5.

---

## What I wrote vs. where I used AI

I used AI assistants (OpenAI Codex and Anthropic Claude).

**I wrote:**

- The RK4 solver
- The circuit equations and the exact-solution test
- `L(x)`, `dL/dx`, and their numerical check
- The full 5-variable model, including pairing the force and back-EMF terms and tracking heat
- The energy checks
- All the hardware and measurements

**AI helped with:**

- **Code review that changed the design.** For example, adding a time argument to the solver, and spotting that a convergence test was measuring rounding noise.
- **Physics I didn't know**, like how to model a permanent magnet.
- **Parameter estimates** for `L0`, `a`, and the slug density.
- **Tooling:** the CLI, JSON config, CSV output, plots, test suite, and CI.
- **This README.**

The physics, solver, and validation plan are mine. The tooling is mostly AI-assisted.
