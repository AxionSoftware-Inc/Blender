# Spectra Science — Current Status

This file separates the last fully verified runtime milestone from the current validation-pending development batch.

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

At `b9ca6b0...`:

```text
ode.first_order / rk4.native_cpu
```

was a validated solver-registry/provider/provenance boundary, but still delegated to Python reference RK4. Therefore the verified baseline does **not** prove compiled native CPU acceleration.

## Current development batch — validation pending

Current `main` contains a bounded quantitative-presentation/native-execution batch built on `b9ca6b0...`.

**Do not call current `main` green until `docs/QUANTITATIVE_NATIVE_VALIDATION_HANDOFF.md` completes.**

### Quantitative presentation

Implemented, validation pending:

- renderer-neutral `VIRIDIS`, `MAGMA`, `COOLWARM`, `PHASE` palettes;
- `DATA`, `FIXED`, `SYMMETRIC` range policies;
- one Scene-wide shared range for one quantitative role;
- explicit mixed-unit rejection until a conversion policy exists;
- scalar VisualAttribute -> deterministic `display_color` VisualAttribute;
- PointCloud/VectorGlyphSet legacy color compatibility bridge;
- deterministic quantitative legend resources using the same resolved range;
- deterministic analysis XYZ axes;
- camera-facing world-space title/subtitle/time annotations;
- SDK exposure of quantitative presentation helpers.

Scientific scalar values remain renderer-independent. Blender does not own scalar-to-color mapping.

### Presentation timeline/recomposition fixes

Implemented, validation pending:

- fixed stale `duration=` call to `staggered_reveal`; runtime uses `item_duration=`;
- `Track.owner` defaults to `scientific`;
- presentation reveal tracks use owner `presentation`;
- scientific `(target_id, property_path)` ownership wins over presentation effects;
- presentation recomposition strips old presentation-owned resources/tracks;
- presentation-only Timeline tail is removed when switching back to a non-reveal preset;
- longer intentional scientific Timeline duration is preserved;
- repeated composition is resource/track/duration idempotent;
- FIT_PRIMARY temporary framing Scene has no unrelated timeline references;
- Scene-v5 serialization persists non-default track owner while preserving old scientific-track JSON shape.

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

Implemented intent:

- avoid high-cardinality material-slot explosion for quantitative Surface/PointCloud;
- one quantitative mesh primitive -> one quantitative material;
- >256 distinct PointCloud values through native mesh color attributes;
- per-value `Color.a` preserved in the native color buffer;
- effective alpha = `attribute_alpha * primitive.opacity` in the shader;
- color-only updates preserve object/datablock identity;
- opacity-only updates keep geometry sanitized at opacity 1 and update the quantitative material instead;
- opacity-only updates are intended to preserve object/datablock/material identity;
- cleanup owns/removes quantitative materials with the normal backend lifecycle.

Current deliberate limitation:

```text
VectorGlyphSet remains on the existing Curve/color fallback path
```

The Blender 5.2 quantitative material/attribute path is not yet promoted until native smoke passes.

### Real optional native CPU RK4 kernel

New implementation, validation pending:

```text
native/spectra_native_cpu.c
spectra._native_cpu
```

Compiled state:

```text
NATIVE_CPU_AVAILABLE = True
implementation_id = rk4.native_cpu
method_id = rk4.fixed
execution.kind = cpu
backend = spectra.native_cpu
device = host-cpu
```

Fallback state:

```text
NATIVE_CPU_AVAILABLE = False
implementation_id = rk4.native_cpu
method_id = rk4.fixed
execution.kind = python
backend = spectra.native_cpu.python_fallback
device = None
```

The fallback must not satisfy CPU-only requirements. Targeted tests now exercise direct parity, registry selection, CPU-only requirements, fallback-tag selection, and tracked provenance.

The extension is optional for ordinary installation, but the next validation must explicitly build it and prove the compiled path. Python RHS callbacks are still invoked four times per RK4 step, so performance claims require measurement.

### Targeted tests/examples in this batch

```text
tests/test_quantitative_presentation.py
tests/test_quantitative_shared_scale_and_legend.py
tests/test_presentation_recomposition.py
tests/test_blender_quantitative_backend.py
tests/test_native_cpu_extension_boundary.py
examples/blender_quantitative_smoke.py
```

The Blender smoke now checks 300 quantitative values, native color attributes, per-value alpha, primitive opacity update, color-only/opacity-only identity, one-material behavior, and cleanup.

These tests are written but are not a substitute for the pending full local/native validation.

## Active validation source of truth

Use:

```text
docs/QUANTITATIVE_NATIVE_VALIDATION_HANDOFF.md
```

Required high-level gates:

```text
explicit native extension build
compileall/import boundary
new targeted tests
full pytest
catalog/provider probe
native/reference RK4 parity + convergence
CPU-only policy selection
Python fallback truthfulness
Blender 300-value quantitative smoke
alpha × opacity shader sanity
color-only / opacity-only identity
presentation legend/axes/annotation visual sanity
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
- deterministic legends, analysis axes, camera-facing annotations;
- presentation track ownership/recomposition/duration fixes;
- Blender mesh color-attribute realization for Surface/PointCloud;
- per-value alpha and material-owned primitive opacity;
- color/opacity-only quantitative identity path;
- optional compiled CPython C RK4 loop with truthful fallback metadata;
- explicit native/fallback registry-policy-provenance tests.

### Still future or materially incomplete

- VectorGlyphSet high-cardinality native attribute/Geometry Nodes representation;
- fully screen-space legend/layout system;
- volume rendering primitive semantics;
- typed/batched native numerical buffers that reduce repeated Python RHS overhead;
- GPU numerical provider;
- device-resident grid/PDE pipeline;
- production CFD/FEA/RF/quantum-chemistry solver stacks;
- five canonical polished premium showcase scenes;
- standalone/WebGPU polished product;
- production remote/HPC/collaboration services.

## Rule for the next verified baseline

Only the local-agent validation report may promote this batch.

When it passes, record:

```text
final SHA
actual pytest count
actual domain/provider count
native extension build/availability status
native/fallback selection + provenance status
Blender quantitative/alpha/opacity status
existing Blender regression status
root fixes
benchmarks if meaningful
remaining limitations
repo clean/synced state
```

Until then, the verified runtime baseline remains:

```text
b9ca6b017cac83f45cc3864a88e219c848c12fc8
```
