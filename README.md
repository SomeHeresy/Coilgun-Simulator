# Coilgun Simulator

A physics simulator for a multi-stage coilgun. The goal is a CLI tool that takes coil
geometry, capacitor bank specs, and slug mass, and predicts muzzle velocity plus the
optimal switch on/off time for each stage.

I built a coilgun (V3) that chronographs at **16 m/s**. The point of this project is to
predict that number from first principles, and then to be honest about the gap between
the prediction and the measurement.

## Status

Work in progress. The circuit solver is finished and validated. The magnetic force model
and slug motion are not written yet, so the simulator does not yet simulate a coilgun —
it simulates the capacitor discharge that drives one.

| Part | State |
| --- | --- |
| RK4 integrator | done |
| RLC circuit model | done, validated |
| Magnetic force + slug motion | not started |
| CLI, config file, CSV output | not started |
| pytest suite, CI | not started |
| Validation against V3 hardware | not started |

## Running it

Requires Python 3.10+ and numpy.

```bash
pip install -r requirements.txt
```

Simulate the capacitor discharge and check energy behaviour:

```bash
python -m coilgun.run_rlc
```

Check the integrator against the analytic solution:

```bash
python -m coilgun.validate_rlc
```

Both read their parameters from `coilgun/config.py`.

## The physics so far

A charged capacitor discharging through the coil is a series RLC circuit. With state
`[V, I]`:

```
dV/dt = -I / C
dI/dt = (V - I*R) / L
```

Default parameters are 500 V, 660 µF, 150 µH, 0.15 Ω. That gives α = 500 and
ω₀ ≈ 3178 rad/s, so α < ω₀ and the circuit is underdamped — the current rings rather
than decaying smoothly, which is what a real coilgun bank does.

## How I know the solver is right

Three independent checks, all in `validate_rlc.py` and `run_rlc.py`:

1. **Against the closed-form solution.** The underdamped RLC has an exact analytic
   answer. Max error over a 6 ms run is about **1e-9 V**.

2. **Convergence order.** A true 4th-order method should cut its error by 16x when you
   halve the step size. Measured: **15.94x** for voltage, **15.95x** for current. This
   is the check I trust most, because it fails loudly if the integrator is subtly wrong
   even when the numbers still look plausible.

3. **Energy.** The resistor can only remove energy from the circuit, so stored energy
   `½CV² + ½LI²` must never rise from one step to the next. Over 6000 steps it rises
   **0 times**.

## Layout

```
coilgun/
├── config.py           # all simulation parameters, one dataclass
├── integrator_rk4.py   # generic RK4 stepper, physics-agnostic
├── rlc.py              # RLC derivative function
├── run_rlc.py          # discharge driver, prints results + energy check
└── validate_rlc.py     # analytic comparison + convergence check
scratch/
└── integrator_euler.py # first attempt, plain Euler on an RC circuit. kept for reference
```

The integrator does not know any physics. It takes a state vector, a step size, and a
derivative function, so adding slug position and velocity later means writing a new
derivative function, not touching the solver.

## What's next

The state vector grows to `[V, I, x, v]` and the coil inductance becomes a function of
slug position:

```
L(x) = L0 + ΔL * exp(-(x/a)²)
F    = ½ I² dL/dx
```

The important detail is that the force has to come from `dL/dx` rather than being bolted
on separately. If the force does not trace back to the same `L(x)` that the circuit sees
through its back-EMF, the slug gains energy the capacitor never paid for, and the whole
simulation quietly becomes a free-energy machine.

This model also produces **suckback** for free: `dL/dx` flips sign at the coil centre, so
the coil pulls the slug in on the way there and drags it back on the way out unless the
current is switched off in time. Finding that switch-off time is the actual problem this
project exists to solve.

After that: a JSON config and CLI, CSV output, plots, a real pytest suite, and finally
running my measured V3 parameters through it to see how far off the prediction is.

## Known limitations

The model is a lumped-element approximation. It ignores eddy currents in the slug,
magnetic saturation of the iron, and the temperature dependence of coil resistance. I
expect these to be the main reasons the prediction misses the measured 16 m/s, and I
plan to write up the size of that gap rather than tune parameters until it disappears.
