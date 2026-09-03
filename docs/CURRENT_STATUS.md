# Spectra Science — Current Status

This file separates the last fully verified runtime milestone from the current development batch.

## Last fully verified baseline

Commit:

```text
b9ca6b017cac83f45cc3864a88e219c848c12fc8
```

Reported local validation:

```text
compileall spectra: PASS
pytest: 276 passed
initial failures: 0
DomainCatalog / auto-discovery: PASS
119 domains
467 providers
numerical provenance / solver registry: PASS
presentation / Scene v5 / VisualAttribute: PASS
SDK / plugin / project layers: PASS
native-provider RK4 boundary: PASS
Blender 5.2 targeted smoke: PASS
repo clean / synchronized at the milestone
```

Blender validation at that baseline included static, wave, EM, 10k PointCloud/VectorGlyphSet batching, stable identity, 100-frame leak testing, and cleanup/orphan checks.

Reported Blender reference measurement from that run:

```text
create:          ~170.49 ms
combined update: ~89.95 ms
```

These measurements are commit/machine/workload-specific.

### Native-provider meaning at the verified baseline

At `b9ca6b0...`, the implementation named:

```text
ode.first_order / rk4.native_cpu
```

was a validated solver-registry/provider/provenance boundary, but its implementation still delegated to the Python reference RK4 solver. Therefore `b9ca6b0...` does **not** prove real compiled native CPU acceleration.

That distinction remains important when comparing the verified baseline with the current development batch.

## Current development batch — validation pending

Current `main` has moved beyond `b9ca6b0...` with a new quantitative-presentation/native-execution batch.

At the handoff checkpoint this batch reached:

```text
80256050800205399588ba7c8d83afbb34cd918d
```

and later status/documentation commits may move `main` further without changing the validation rule below.

**Do not call current `main` green until the new local validation completes.**

### Quantitative presentation

Implemented, validation pending:

- renderer-neutral quantitative color scales;
- VIRIDIS / MAGMA / COOLWARM / PHASE palettes;
- DATA / FIXED / SYMMETRIC range policies;
- Scene-wide shared range for one quantitative role;
- explicit rejection of mixed VisualAttribute units on one shared scale until a conversion policy exists;
- scalar VisualAttribute -> deterministic `display_color` VisualAttribute;
- compatibility bridge for current PointCloud/VectorGlyphSet per-instance color fields;
- quantitative legend resources;
- analysis XYZ axes resources;
- SDK exposure of quantitative presentation helpers.

Scientific scalar values remain renderer-independent. Blender must not recompute the scalar-to-color mapping.

### Presentation timeline/recomposition fixes

Implemented, validation pending:

- fixed stale `duration=` call to `staggered_reveal`; runtime uses `item_duration=`;
- `Track.owner` metadata with default `scientific`;
- presentation reveal tracks use owner `presentation`;
- scientific `(target_id, property_path)` ownership wins on conflicts;
- presentation recomposition strips old presentation-owned resources/tracks;
- preset switching should not accumulate reveal tracks;
- FIT_PRIMARY camera temporary Scene no longer includes unrelated timeline targets;
- Scene v5 timeline serialization persists non-default track owner while keeping old scientific-track JSON shape compatible.

### Blender quantitative adapter

New runtime adapter, validation pending:

```text
QuantitativeBlenderBackend
```

Targeted native mapping:

```text
Surface vertex display_color
    -> Blender mesh FLOAT_COLOR / POINT attribute

PointCloud instance display_color
    -> current 6-vertex instance representation
    -> Blender mesh FLOAT_COLOR / POINT attribute
```

Native attribute name:

```text
spectra_display_color
```

The adapter is intended to avoid the old high-cardinality material-slot path for quantitative Surface/PointCloud data.

Current deliberate limitation:

```text
VectorGlyphSet remains on the existing Curve/color fallback path
```

The Blender 5.2 API/material implementation has not yet received the required native validation for this batch.

### Real optional native CPU RK4 kernel

New implementation, validation pending:

```text
native/spectra_native_cpu.c
spectra._native_cpu
```

When the extension successfully builds/imports:

```text
NATIVE_CPU_AVAILABLE = True
execution.kind = cpu
backend = spectra.native_cpu
device = host-cpu
```

and `rk4.native_cpu` executes the RK4 integration loop in the CPython C extension while still invoking the user Python RHS callback at each RK stage.

When the extension is absent:

```text
NATIVE_CPU_AVAILABLE = False
execution.kind = python
backend = spectra.native_cpu.python_fallback
```

and the deterministic Python RK4 fallback is used.

This makes provenance truthful in both environments.

The extension build is optional for ordinary installation, but the next validation must explicitly attempt a real native build and prove the CPU path.

### New targeted tests/examples

The pending batch adds targeted coverage for:

```text
test_quantitative_presentation.py
test_quantitative_shared_scale_and_legend.py
test_presentation_recomposition.py
test_blender_quantitative_backend.py
test_native_cpu_extension_boundary.py
examples/blender_quantitative_smoke.py
```

These tests have been written but are not a substitute for the pending local full-suite/native Blender validation.

## Validation source of truth

Use:

```text
docs/QUANTITATIVE_NATIVE_VALIDATION_HANDOFF.md
```

Required high-level gates:

```text
native extension explicit build
compileall
new targeted tests
full pytest
catalog/provider probe
native/reference RK4 parity
CPU-only policy selection
Python fallback metadata truthfulness
Blender quantitative 300-color smoke
existing Blender static/wave/EM regressions
10k batching / identity / leak / cleanup checks
```

GitHub Actions remains intentionally absent.

## Current capability status

### Fully verified through `b9ca6b0...`

- renderer-independent semantic/capability engine;
- 119-domain / 467-provider reported catalog baseline;
- solver-role/policy/provenance platform;
- RK4/Heun/RK45 reference solvers;
- experiments, sensitivity, uncertainty, calibration, Pareto, reproducibility, artifacts/tracing;
- Scene v5 / VisualAttribute foundation;
- initial renderer-neutral presentation runtime;
- initial SDK/plugin/project runtime layers;
- Blender 5.2 generic/incremental batching and identity behavior.

### Implemented after baseline, awaiting validation

- quantitative shared-range color pipeline;
- deterministic quantitative legends and analysis axes;
- presentation track ownership/recomposition fixes;
- Blender mesh color-attribute realization for Surface/PointCloud;
- optional compiled C RK4 loop with truthful Python fallback metadata.

### Still future or materially incomplete

- VectorGlyphSet high-cardinality native attribute/Geometry Nodes representation;
- fully screen-space legend/layout system;
- volume rendering primitive semantics;
- batched native numerical kernels that avoid repeated Python RHS callbacks;
- GPU numerical provider;
- device-resident grid/PDE pipeline;
- production CFD/FEA/RF/quantum-chemistry solver stacks;
- standalone/WebGPU polished product;
- production remote/HPC/collaboration services.

## Rule for the next verified baseline

Only the local-agent validation report may promote the current batch.

When it passes, record:

```text
final SHA
actual pytest count
actual domain/provider count
native extension availability/build status
Blender quantitative status
root fixes
remaining limitations
repo clean/synced state
```

Until then, the verified runtime baseline remains `b9ca6b017cac83f45cc3864a88e219c848c12fc8`.
