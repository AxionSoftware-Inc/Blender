# Spectra Science — Quantitative Presentation + Native CPU Validation Handoff

Status: **current post-`b9ca6b0...` runtime batch; validation pending**.

This is the local-agent handoff for the development batch built on the last fully verified baseline:

```text
b9ca6b017cac83f45cc3864a88e219c848c12fc8
```

Do not update the verified baseline until every required gate below is complete.

## Batch goals

This batch deepens two previously verified foundations:

1. renderer-neutral quantitative presentation and Blender realization;
2. the `rk4.native_cpu` provider from a registry/provenance proof into an optional real CPython C-extension RK4 loop.

It also fixes presentation recomposition/timeline ownership bugs found during source audit.

## Major runtime changes

### Quantitative color engine

New:

```text
spectra/color_scales.py
```

Validate:

- VIRIDIS / MAGMA / COOLWARM / PHASE deterministic palette sampling;
- DATA / FIXED / SYMMETRIC range modes;
- Scene-wide shared ranges for the same quantitative role;
- PointCloud/VectorGlyphSet legacy color compatibility bridge;
- generic `display_color` VisualAttribute remains the source of truth;
- mismatched units across one shared scale fail explicitly rather than silently misrepresenting values.

### Presentation runtime depth

Modified:

```text
spectra/presentation_models.py
spectra/presentation.py
spectra/sdk/presentation.py
```

Validate:

- `ColorScalePolicy` resolver defaults and validation;
- staggered reveal bug is fixed (`item_duration`, not stale `duration` keyword);
- scientific animation property ownership wins over presentation reveal;
- `Track.owner="presentation"` permits deterministic preset recomposition;
- switching `presentation -> analysis` removes presentation-owned reveal tracks;
- repeated composition does not duplicate presentation IDs/tracks;
- FIT_PRIMARY camera does not fail because unrelated scientific timeline targets are absent from its temporary bounds Scene;
- analysis preset materializes deterministic XYZ axes;
- quantitative presets materialize deterministic world-space legend resources;
- camera is fitted before axes/legend resources are added, so scientific framing remains authoritative.

### Timeline ownership persistence

Modified:

```text
spectra/core/animation.py
spectra/core/serialization.py
```

Validate:

- `Track.owner` defaults to `scientific`;
- old Scene documents with no owner field still deserialize as scientific;
- scientific tracks preserve the previous JSON shape (owner omitted);
- presentation tracks persist owner through Scene v5 JSON/data round-trip;
- no Scene schema version bump was introduced solely for this additive optional field.

### Blender quantitative mesh realization

New:

```text
spectra/backends/blender/quantitative.py
QuantitativeBlenderBackend
```

Target native paths:

```text
Surface vertex color VisualAttribute
    -> Blender mesh FLOAT_COLOR / POINT attribute

PointCloud instance color VisualAttribute
    -> expand one color across current 6-vertex octahedron instance
    -> Blender mesh FLOAT_COLOR / POINT attribute
```

Native attribute name:

```text
spectra_display_color
```

Validate in Blender 5.2:

- correct API for `mesh.color_attributes`;
- `FLOAT_COLOR` + `POINT` works;
- shader attribute node reads the native attribute;
- one quantitative primitive uses one shader material rather than hundreds of materials;
- >256 unique PointCloud colors work through the quantitative backend;
- color-only updates preserve Blender object identity;
- color-only updates preserve Blender mesh/datablock identity;
- no object/material/datablock leak after repeated updates;
- cleanup removes owned resources;
- non-quantitative existing Blender paths remain unchanged.

Current deliberate limitation:

```text
VectorGlyphSet -> current Curve representation / existing color fallback
```

Do not rewrite VectorGlyphSet representation in this validation patch unless a root regression requires it.

### Native CPU RK4 kernel

New:

```text
native/spectra_native_cpu.c
setup.py
```

Modified:

```text
spectra/domains/differential_equations/native_cpu.py
```

Expected behavior:

When `spectra._native_cpu` successfully builds/imports:

```text
NATIVE_CPU_AVAILABLE = True
execution.kind = cpu
backend = spectra.native_cpu
device = host-cpu
rk4.native_cpu -> C RK4 integration loop
```

When no compiled extension is available:

```text
NATIVE_CPU_AVAILABLE = False
rk4.native_cpu -> deterministic Python RK4 fallback
execution.kind = python
backend = spectra.native_cpu.python_fallback
```

The fallback must never claim native CPU execution.

The extension build is optional for normal package installation, but **this validation should explicitly attempt a real native build** on the validation machine.

## Required validation sequence

### G0 — Repository state

```text
git status
git pull
```

Record starting SHA.

Do not create GitHub Actions.

### G1 — Native extension build

Use the active Python environment and explicitly build the extension so compilation errors are visible.

Typical command:

```text
python setup.py build_ext --inplace
```

Then verify:

```text
python -c "from spectra.domains.differential_equations.native_cpu import NATIVE_CPU_AVAILABLE, NATIVE_RK4_EXECUTION; print(NATIVE_CPU_AVAILABLE, NATIVE_RK4_EXECUTION)"
```

Target for the native validation machine:

```text
NATIVE_CPU_AVAILABLE == True
NATIVE_RK4_EXECUTION.kind == "cpu"
```

If the local compiler/toolchain is missing, do not fake success. Report the toolchain blocker. Normal package installation should still work because the extension is optional.

### G2 — Compile/import

```text
python -m compileall spectra
```

Must PASS.

Also import at least:

```text
spectra.presentation
spectra.color_scales
spectra.backends.blender
spectra.backends.blender.quantitative
spectra.domains.differential_equations.native_cpu
spectra.sdk.presentation
```

outside Blender to preserve lazy Blender import behavior.

### G3 — Targeted plain-Python tests

Run at minimum:

```text
tests/test_quantitative_presentation.py
tests/test_quantitative_shared_scale_and_legend.py
tests/test_presentation_recomposition.py
tests/test_blender_quantitative_backend.py
tests/test_native_cpu_extension_boundary.py
```

Also rerun existing:

```text
animation
Scene serialization v1-v5 compatibility
presentation
bounds/framing
backend import/contract
solver registry/policy/provenance
DomainCatalog/auto-discovery
SDK/plugin/project tests
```

Fix root causes, not expectations, unless an old expectation is genuinely stale because of the documented additive contract.

### G4 — Full pytest

```text
pytest -q
```

Must PASS with zero failures.

Record the actual new test count; do not reuse 276.

### G5 — Catalog/provider probe

Run the normal catalog/auto-discovery probe.

Record actual:

```text
domain count
provider count
```

Check that native CPU domain registration remains deterministic in both build states.

### G6 — Native CPU semantic parity

With `NATIVE_CPU_AVAILABLE=True`:

- compare native vs reference RK4 on deterministic analytical/reference ODEs;
- confirm times/state shapes;
- confirm order/convergence behavior remains RK4 order 4;
- confirm invalid derivative dimensions propagate useful errors;
- confirm provider selection requiring `execution_kinds=("cpu",)` selects `rk4.native_cpu`;
- confirm tracked provenance reports actual CPU execution metadata;
- confirm no scientific/PDE/mechanics consumer required source changes.

Do not claim meaningful speedup yet unless benchmark evidence actually shows it. Python RHS callbacks remain in the loop and may dominate.

### G7 — Python fallback truthfulness

Also validate an environment/path where `_native_cpu` is unavailable (or temporarily make it unavailable without committing generated binaries).

Confirm:

```text
NATIVE_CPU_AVAILABLE=False
solve_native_rk4 still returns correct results
execution.kind=python
CPU-only requirements do not select the fallback as a CPU implementation
```

This is a provenance correctness gate.

### G8 — Blender 5.2 quantitative smoke

Run:

```text
examples/blender_quantitative_smoke.py
```

This specifically validates:

- 300 distinct quantitative values;
- one PointCloud native object;
- one native shader material for the cloud;
- mesh color attribute length `300 * 6` for the current octahedron representation;
- color-only update;
- object identity preserved;
- mesh/datablock identity preserved;
- cleanup PASS.

If Blender 5.2 API differs from the assumptions in `quantitative.py`, fix the adapter root cause while keeping renderer-neutral Scene semantics unchanged.

### G9 — Existing Blender regression smoke

Rerun the previously green Blender paths:

```text
examples/blender_smoke.py
examples/blender_wave_animation.py
examples/blender_em_wave_animation.py
10k PointCloud / VectorGlyphSet batching check
identity preservation
100-frame leak check
cleanup/orphan check
```

Do not expand dense data into thousands of Blender objects.

### G10 — Performance sanity

Re-measure the existing dense Blender reference workload if practical and record it separately from quantitative color-update timing.

Also measure:

```text
300-value quantitative create
color-only update
```

Do not compare native C RK4 timing to Blender render timing; they are unrelated performance layers.

For native RK4, benchmark only after parity and report:

```text
state size
step count
RHS callback type
Python reference time
native-provider time
speedup or slowdown
```

A slowdown with Python callbacks is not an architectural failure; report it honestly.

## Root-cause rules

Do not:

- weaken scientific range/unit semantics merely to make a render pass;
- silently convert mismatched units without an explicit conversion contract;
- move scalar-to-color mapping into Blender;
- use hundreds of Blender material slots for the new quantitative PointCloud path;
- label Python fallback execution as CPU/native;
- disable old tests to get green;
- recreate GitHub Actions;
- commit `.pyd`, `.so`, `.dll`, `.dylib`, `build/`, or generated wheel artifacts.

## Expected final report

Return one compact but complete report containing:

```text
Final SHA
repo clean/synced?
compileall result
full pytest result + actual test count
initial failure count
root fixes made
domain count
provider count
Scene v5 serialization/Track.owner result
shared color scale/legend/axes result
Blender quantitative smoke result
300-color material/object counts
color-only object identity result
color-only datablock identity result
existing Blender regression smoke result
native extension build result
NATIVE_CPU_AVAILABLE
native vs reference parity result
CPU-only policy selection result
fallback metadata truthfulness result
native RK4 benchmark (if meaningful)
Blender quantitative timing (if measured)
remaining blockers/limitations
GitHub Actions absent confirmation
```

## Promotion rule

Only after all applicable gates pass should the post-`b9ca6b0...` batch become the new verified baseline.
