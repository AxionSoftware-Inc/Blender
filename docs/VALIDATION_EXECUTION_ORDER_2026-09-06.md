# Validation Execution Order — Spectra current development stack

Run this only when local validation resources are available. This document is a concise execution companion to `docs/CHAT_LIMIT_HANDOFF_2026-09-06.md`.

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
- Electrostatic showcase.

## 4. Catalog audit

Recompute and report:

- unique deterministic domain count;
- provider count;
- important capability ownership;
- no duplicate/ambiguous semantic provider regressions.

Do not reuse old 106/403 numbers as current results; those belong to the older green checkpoint.

## 5. Blender 5.2 targeted smokes

At minimum run the repository's current commands/scripts for:

- generic static/incremental backend path as applicable;
- `examples/blender_quantitative_smoke.py`;
- `examples/blender_maxwell_showcase_smoke.py`;
- `examples/blender_electrostatic_showcase_smoke.py`.

Validate native invariants rather than screenshots only:

- object/datablock identity;
- batched PointCloud/VectorGlyphSet representation;
- native color attribute presence;
- bounded material/object count;
- correct scientific vs playback time for Maxwell;
- cleanup/orphan behavior.

## 6. Promotion report

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
- blockers (must explicitly say none if none).

Only then relabel the current development stack as `VERIFIED GREEN`.

## 7. No CI substitution

GitHub Actions are intentionally absent in this repository. Do not recreate them as a substitute for the requested local/native validation unless the user explicitly requests CI.
