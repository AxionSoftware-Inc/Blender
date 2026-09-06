# Spectra Science — Quantitative Presentation + Native CPU Validation Handoff

Status: **post-`b9ca6b0...` runtime batch; validation pending**.

Last fully verified baseline:

```text
b9ca6b017cac83f45cc3864a88e219c848c12fc8
compileall: PASS
pytest: 276 passed
catalog: 119 domains / 467 providers
Blender 5.2 targeted smoke: PASS
```

Do not promote current `main` until every applicable gate below passes.

## What this batch changes

This is a bounded product-depth/performance batch. It must not become a new foundational rewrite.

### 1. Renderer-neutral quantitative presentation

New/expanded runtime:

```text
spectra/color_scales.py
spectra/presentation_models.py
spectra/presentation.py
spectra/sdk/presentation.py
```

Required semantics:

- deterministic `VIRIDIS`, `MAGMA`, `COOLWARM`, `PHASE` palettes;
- `DATA`, `FIXED`, `SYMMETRIC` range modes;
- one shared range across all matching scalar attributes in one Scene;
- no per-primitive auto-range when multiple primitives represent the same quantity;
- mixed units on one shared scale fail explicitly until an explicit conversion policy exists;
- scalar scientific values remain unchanged;
- scalar -> `display_color` happens renderer-neutrally;
- `display_color` VisualAttribute is the source of truth;
- PointCloud/VectorGlyphSet legacy `colors` fields are only compatibility bridges;
- quantitative legend uses the same resolved min/max/palette as the mapped data;
- analysis preset materializes deterministic XYZ axes;
- camera is fitted to scientific content before legend/axes/annotation resources are added.

### 2. Presentation recomposition and ownership

Modified:

```text
spectra/core/animation.py
spectra/core/serialization.py
spectra/presentation.py
```

Required semantics:

- `Track.owner` defaults to `scientific`;
- presentation-generated tracks use owner `presentation`;
- scientific `(target_id, property_path)` wins over conflicting presentation reveal;
- old presentation primitives/tracks are removed before recomposition;
- `presentation -> analysis` does not leave presentation reveal tracks;
- a purely presentation-created Timeline tail is removed on recomposition;
- a longer intentional scientific Timeline duration is preserved;
- repeated composition is resource/track/duration idempotent;
- FIT_PRIMARY temporary framing Scene contains no unrelated timeline references;
- non-default track owner persists through Scene-v5 round-trip;
- old scientific tracks keep the previous JSON shape with owner omitted;
- no Scene schema bump is required solely for the optional owner field.

### 3. Camera-facing world-space presentation annotations

Title/subtitle/time annotations must no longer be placed at the camera eye.

Required behavior:

- annotation resources are outside scientific framing calculation;
- title/subtitle/time use a deterministic camera-facing transform near the scientific bounds;
- annotation rotation matches camera orientation;
- annotation anchor is not camera translation;
- these resources remain renderer-neutral Scene primitives, not Blender-only overlays.

Full screen-space UI remains later work.

### 4. Blender quantitative mesh realization

New:

```text
spectra/backends/blender/quantitative.py
QuantitativeBlenderBackend
```

Target mappings:

```text
Surface vertex display_color
    -> one Blender mesh FLOAT_COLOR / POINT attribute

PointCloud instance display_color
    -> expand one value across the current 6-vertex octahedron instance
    -> one Blender mesh FLOAT_COLOR / POINT attribute
```

Native attribute name:

```text
spectra_display_color
```

Required behavior:

- no high-cardinality material-slot explosion for quantitative Surface/PointCloud;
- one quantitative primitive uses one quantitative shader material;
- >256 distinct PointCloud values work;
- generic scalar-to-color mapping is not recomputed in Blender;
- color-only updates preserve Blender object identity;
- color-only updates preserve mesh/datablock identity;
- per-value `Color.a` survives into the native mesh color attribute;
- effective rendered alpha is `attribute_alpha * primitive.opacity`;
- primitive opacity is applied in the quantitative material, not baked into geometry;
- opacity-only updates preserve object and mesh/datablock identity;
- quantitative material identity is preserved across opacity changes;
- repeated updates do not leak objects, materials, meshes, or color attributes;
- cleanup removes owned resources.

Deliberate limitation:

```text
VectorGlyphSet -> existing Curve/color fallback
```

Do not rewrite VGS/Geometry Nodes in this validation patch unless a root regression proves it necessary.

### 5. Optional real native CPU RK4

New/modified:

```text
native/spectra_native_cpu.c
setup.py
spectra/domains/differential_equations/native_cpu.py
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

The fallback must never satisfy a CPU-only execution requirement.

The native loop still calls the Python RHS four times per RK4 step, so this milestone proves a real compiled integration loop/provider boundary, not guaranteed speedup.

Native build artifacts (`.pyd`, `.so`, `.dll`, `.dylib`, build directories) must not be committed.

## Required validation sequence

### G0 — repo state

```text
git status
git pull
```

Record starting SHA. Do not create GitHub Actions.

### G1 — explicit native build

Use the active Python environment and make compilation errors visible:

```text
python setup.py build_ext --inplace
```

Then:

```text
python -c "from spectra.domains.differential_equations.native_cpu import NATIVE_CPU_AVAILABLE, NATIVE_RK4_EXECUTION; print(NATIVE_CPU_AVAILABLE, NATIVE_RK4_EXECUTION)"
```

Target on the validation machine:

```text
NATIVE_CPU_AVAILABLE == True
NATIVE_RK4_EXECUTION.kind == "cpu"
```

If the compiler/toolchain is missing, report the blocker. Do not fake native success. The extension is optional for ordinary installation, so lack of a compiler must not make normal Python installation impossible.

### G2 — compile/import boundary

```text
python -m compileall spectra
```

Must PASS.

Outside Blender, import at least:

```text
spectra.presentation
spectra.color_scales
spectra.backends.blender
spectra.backends.blender.quantitative
spectra.domains.differential_equations.native_cpu
spectra.sdk.presentation
```

No eager `bpy` import regression.

### G3 — targeted plain-Python tests

Run at minimum:

```text
tests/test_quantitative_presentation.py
tests/test_quantitative_shared_scale_and_legend.py
tests/test_presentation_recomposition.py
tests/test_blender_quantitative_backend.py
tests/test_native_cpu_extension_boundary.py
```

Explicitly confirm:

- shared Scene range;
- fixed/symmetric range behavior;
- legend min/max/quantity labels;
- axes IDs;
- camera-facing annotation placement;
- mixed-unit rejection;
- Track.owner round-trip;
- presentation tail removal and scientific duration preservation;
- preset-switch/recomposition idempotence;
- quantitative sanitization keeps geometry and removes legacy PointCloud material colors;
- quantitative sanitization routes primitive opacity to material path;
- expanded instance colors preserve alpha;
- compiled/fallback native metadata truthfulness;
- CPU-only registry selection behavior;
- tracked provenance reports actual execution kind/backend.

Also rerun existing tests for:

```text
animation
Scene v1-v5 serialization compatibility
bounds/framing
presentation
backend import/contract
solver registry/policy/provenance
DomainCatalog/auto-discovery
SDK/plugin/project
```

Root causes only. Do not weaken tests merely to get green.

### G4 — full suite

```text
pytest -q
```

Must PASS with zero failures. Record the actual new count; do not reuse 276.

### G5 — catalog/provider probe

Run normal DomainCatalog auto-discovery/probe and record actual:

```text
domain count
provider count
```

Check determinism and provider ownership. Native CPU domain version/metadata must be stable for the active build state.

### G6 — native CPU parity and selection

With `NATIVE_CPU_AVAILABLE=True`:

- compare C-extension RK4 to reference RK4 on deterministic ODEs;
- compare times/state shape and values;
- verify expected fourth-order convergence;
- verify derivative dimension mismatch/error propagation;
- CPU-only requirements select `rk4.native_cpu`;
- tracked run reports `execution_kind=cpu`, backend `spectra.native_cpu`, implementation `rk4.native_cpu`;
- high-level science consumers require no source rewrite.

Do not claim a speedup unless measured.

### G7 — fallback truthfulness

Validate a run/import state where `_native_cpu` is unavailable without committing generated binaries.

Confirm:

```text
NATIVE_CPU_AVAILABLE == False
solve_native_rk4 remains semantically correct
execution.kind == python
backend == spectra.native_cpu.python_fallback
CPU-only requirements do not select rk4.native_cpu fallback
fallback-tagged Python selection can still be inspected/tracked explicitly
```

### G8 — Blender 5.2 quantitative smoke

Run:

```text
blender --background --python examples/blender_quantitative_smoke.py
```

The script must prove at minimum:

- 300 quantitative scalar values work (>256 legacy material limit);
- quantitative PointCloud remains one native object;
- one quantitative shader material per quantitative mesh primitive;
- native `spectra_display_color` exists as `FLOAT_COLOR / POINT`;
- current 300-instance cloud has `300 * 6` native color entries;
- color-only update preserves object identity;
- color-only update preserves mesh/datablock identity;
- direct per-value alpha `(0, .25, .75, 1)` survives in the native attribute;
- material graph contains alpha multiplication + transparent mix;
- primitive opacity update changes material opacity from 1 -> .5;
- opacity-only update preserves object identity;
- opacity-only update preserves mesh/datablock identity;
- quantitative material identity is preserved;
- cleanup PASS.

If Blender 5.2 differs from adapter API assumptions, fix the adapter root cause while keeping Scene semantics unchanged.

### G9 — presentation visual sanity in Blender

On at least one quantitative presented Scene verify:

- camera frames scientific content, not legends/annotations;
- legend is on the intended side and camera-facing;
- title/subtitle are visible and not located at the camera eye;
- analysis XYZ axes appear without moving the fitted camera;
- alpha transparency visually behaves monotonically from transparent to opaque.

This is a targeted smoke, not a pixel-perfect golden-image requirement.

### G10 — existing Blender regression smoke

Rerun previously green paths:

```text
examples/blender_smoke.py
examples/blender_wave_animation.py
examples/blender_em_wave_animation.py
10k PointCloud batching
10k VectorGlyphSet batching
object/datablock identity
100-frame leak test
cleanup/orphan check
```

Dense batches must remain one native representation each, not thousands of Blender objects.

### G11 — performance sanity

Record separately:

Blender:

```text
existing dense create/update workload
300-value quantitative create
color-only quantitative update
opacity-only quantitative update
```

Native RK4, only after parity:

```text
state size
step count
RHS callback type
Python reference time
native-provider time
speedup or slowdown
```

Python callback overhead may make the C-loop improvement small or negative. Report honestly.

## Root-cause rules

Do not:

- change scientific scalar values for presentation;
- use per-primitive ranges for one shared quantitative role;
- silently mix/convert units without a declared conversion policy;
- move scalar-to-color computation into Blender;
- restore hundreds of material slots for quantitative PointClouds;
- bake primitive opacity into geometry/color data when material realization owns it;
- label Python fallback as CPU/native;
- make the native provider default merely because it exists;
- disable old tests;
- rewrite VectorGlyphSet representation in this batch without evidence;
- create GitHub Actions;
- commit generated native binaries/build directories.

## Expected final report

Return:

```text
Final SHA
repo clean/synced?
compileall result
full pytest result + actual count
initial failure count
root fixes made
domain count
provider count
Scene v5 / Track.owner result
shared quantitative scale result
legend / axes / annotation result
presentation recomposition/duration result
Blender quantitative smoke result
300-value object/material/attribute counts
per-value alpha result
color-only identity result
opacity-only identity/material result
existing Blender regression result
native extension build result
NATIVE_CPU_AVAILABLE
native/reference parity + convergence
CPU-only selection result
fallback truthfulness result
native RK4 benchmark if meaningful
Blender quantitative timings if measured
remaining blockers/limitations
GitHub Actions absent confirmation
```

## Promotion rule

Only after all applicable gates pass should this batch supersede `b9ca6b017cac83f45cc3864a88e219c848c12fc8` as the verified runtime baseline.
