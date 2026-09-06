# Validation Execution Order — Spectra current development stack

Run this only when local validation resources are available. This document is a concise execution companion to the historical chat handoff and the dedicated flagship validation handoffs.

## 1. Establish exact state

```bash
git status
git log -1 --oneline
git pull
```

Record HEAD.

## 2. Python import/compile gate

```bash
python -m compileall spectra
```

Must pass before deeper promotion work.

## 3. Full Python suite

```bash
pytest -q
```

On failure, preserve the initial failure count and fix root causes. Do not hide architectural regressions by weakening tests.

Priority areas:

- domain auto-discovery/catalog;
- solver registry transactions/defaults/policies;
- RK4, Heun, adaptive RK45 selection;
- fixed/adaptive numerical provenance;
- PDE role dispatch;
- experiment sweeps, batching, convergence, sensitivity, uncertainty, calibration, Pareto, artifacts, tracing, views;
- Scene v5 / visual attributes / quantitative presentation;
- Maxwell showcase;
- Electrostatic showcase;
- Quantum wavepacket showcase;
- Thermoelastic heated-bar showcase.

## 4. Catalog audit

Recompute and report:

- unique deterministic domain count;
- provider count;
- important capability ownership;
- no duplicate/ambiguous semantic provider regressions.

Do not reuse old historical domain/provider numbers as current results.

## 5. Blender 5.2 targeted smokes

At minimum run the repository's current commands/scripts for:

- generic static/incremental backend path as applicable;
- `examples/blender_quantitative_smoke.py`;
- `examples/blender_maxwell_showcase_smoke.py`;
- `examples/blender_electrostatic_lab_smoke.py`;
- `examples/blender_quantum_wavepacket_smoke.py`;
- `examples/blender_thermoelastic_bar_smoke.py`.

Validate native invariants rather than screenshots only:

- object/datablock identity;
- batched PointCloud/VectorGlyphSet representation where applicable;
- native color attribute presence;
- bounded material/object count;
- correct scientific vs playback time for Maxwell;
- probability/phase quantitative attributes and phase-alpha confidence cue for Quantum;
- thermoelastic quantitative temperature attribute and deformed-geometry fidelity;
- cleanup/orphan behavior.

## 6. Relativity/geodesic numerical gate before flagship #5

Before implementing or promoting Schwarzschild / black-hole geodesics, audit the generic finite-difference connection path:

```text
Schwarzschild metric (ct, r, theta, phi)
    -> geometry.christoffel_symbols
    -> geometry.solve_geodesic
```

The current reference implementation uses a single absolute derivative step unless hardened. Because the chart mixes length-like and angular coordinates, do not accept a visually plausible trajectory as validation by itself.

Required outcome before flagship #5 promotion:

- derivative-step behavior is made scale-aware or quantitatively shown to be stable for the canonical configuration;
- flat/Euclidean and existing curvature tests remain unchanged in meaning;
- Schwarzschild-specific connection/geodesic checks use known analytic or conserved-quantity references where practical;
- renderer projection remains explicit and never changes the solved trajectory.

## 7. Promotion report

If everything passes, record a new trusted baseline with:

- exact SHA;
- compileall result;
- pytest pass count;
- initial failure count;
- fixes made;
- catalog domain/provider counts;
- solver inventory/default/policy checks;
- provenance checks;
- experiments checks;
- quantitative presentation checks;
- Maxwell smoke;
- Electrostatic smoke;
- Quantum smoke;
- Thermoelastic smoke;
- blockers (must explicitly say none if none).

Only then relabel the current development stack as `VERIFIED GREEN`.

## 8. No CI substitution

GitHub Actions are intentionally absent in this repository. Do not recreate them as a substitute for the requested local/native validation unless the user explicitly requests CI.
