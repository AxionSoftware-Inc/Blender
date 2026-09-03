# Spectra Science — Export and Reporting Architecture

This document defines how Spectra should export scientific data, Scenes, renderer artifacts, images/video, and report-ready outputs without mixing their responsibilities.

## Export categories

Spectra exports fall into four distinct groups:

```text
scientific data exports
engine/Scene exports
renderer-native exports
communication/report exports
```

These should remain separate in architecture and UI.

## Scientific data export

Purpose: move computed scientific results into analysis/interchange formats.

Potential outputs:

```text
CSV/TSV
JSON summaries
HDF5/NetCDF
VTK-family field/mesh data
NumPy-compatible arrays
trajectory tables
experiment artifacts
```

Scientific export should preserve:

- quantity names;
- units;
- coordinates/frame metadata;
- time values;
- field/component meaning;
- missing-value policy;
- relevant provenance references.

It should not require Blender.

## Scene export

Renderer-neutral Scene export preserves visualization intent:

```text
primitives
materials
camera/light primitives
coordinate frame
Timeline
presentation resources where represented
```

Current `spectra.scene` schema is the existing foundation.

A Scene export is not the same as raw scientific data; it may contain sampled/display-reduced representation.

## Renderer-native export

Examples:

```text
.blend
future WebGPU bundle/cache
future glTF-like presentation derivative
render-engine project artifact
```

Renderer-native files are derived outputs, not primary scientific source of truth.

They may preserve:

- native materials;
- renderer camera/light setup;
- Geometry Nodes;
- compositor resources;
- cached geometry.

They may also contain user edits outside Spectra control.

## Image export

Still figures should support presentation intents such as:

```text
publication
presentation
cinematic
analysis snapshot
```

Export metadata should ideally record:

```text
project/result id
view id
presentation variant
scientific time
image resolution
renderer/backend
color-management context where relevant
```

A publication figure should be reproducible from project/result/presentation configuration where practical.

## Video/animation export

Animation export must distinguish:

```text
scientific time range
presentation sequence duration
frame rate/render cadence
```

If scientific time is slowed/held for explanation, labels/metadata should preserve physical interpretation.

A video frame number must not become the scientific time source of truth.

## Report figure bundles

A useful report export may contain:

```text
figure image
caption metadata
quantity/unit legend metadata
project/result reference
solver/provenance summary
presentation settings
```

This can support paper/report generation without embedding all internal engine state into a PNG.

## Report generation

Future reports may combine:

- project summary;
- model parameters;
- solver/provenance;
- diagnostics;
- result metrics;
- selected figures;
- experiment tables/plots;
- known limitations/maturity notes.

Report generation should consume semantic/project/artifact data, not scrape text from Blender UI.

## Scientific captions

A presentation/report layer may generate structured caption ingredients:

```text
what quantity is shown
unit
view/slice/projection
scientific time
parameter context
solver/method if relevant
important diagnostic
```

Human/AI authoring may turn these into prose, but the underlying values should come from engine metadata.

## Experiment reporting

Experiment reports may include:

```text
parameter-space definition
success/failure counts
metric tables
best case
Pareto front
sensitivity
uncertainty summaries
calibration residuals
solver comparison/convergence
per-case trace references
```

Raw high-dimensional outputs need not be embedded when only metrics are required.

## Provenance verbosity levels

Different exports need different detail.

### Minimal

Suitable for slides/demo:

```text
project/result id
quantity/unit
time
```

### Scientific

Suitable for reports/papers:

```text
model parameters
solver method/implementation
precision
key numerical settings
resource/input identities
```

### Full reproducibility

Includes environment snapshot, capability/provider versions, plugin requirements, resource hashes, and detailed traces.

A cinematic video should not display all this text visually, but metadata/report sidecar can retain it.

## Sidecar metadata

For formats that cannot carry rich metadata safely, export a sidecar:

```text
figure.png
figure.spectra.json
```

or a report bundle.

The sidecar schema should be versioned.

## Color consistency

Quantitative image/video exports must preserve the presentation color scale and legend definition.

Do not re-auto-range data during final render unless the saved presentation policy explicitly does so.

Color-management transformations should be considered when quantitative color reading matters.

## Transparency

Publication exports may request transparent background.

Transparency is presentation/renderer configuration; it must not remove scientific/context objects required for interpretation unless explicitly selected.

## Resolution and aspect ratio

Output dimensions belong to export/presentation configuration, not scientific Scene semantics.

Useful named targets may eventually include:

```text
paper_single_column
paper_double_column
slide_16_9
social_1_1
video_4k
custom
```

These are layout/output policies and should not change scientific computation.

## Multi-panel figures

Report/export layer may compose multiple view/presentation panels.

Requirements:

- shared scale policies explicit;
- panel labels deterministic;
- camera/time synchronization explicit;
- common legend when appropriate;
- layout independent from renderer-native object hierarchy.

## Vector graphics

Certain 2D/plot-like outputs may benefit from SVG/PDF/vector export in future.

Do not force every 3D renderer Scene through raster-only export if an analytical/plot view can produce cleaner vector graphics through a specialized renderer/exporter.

A future backend can consume generic Scene/experiment view semantics for this purpose.

## 3D interchange

If exporting geometry to formats such as glTF/OBJ/PLY, clarify whether the export represents:

- scientific source geometry;
- sampled visualization geometry;
- presentation-enriched renderer geometry.

These are not equivalent.

Units/coordinate transforms should be explicit.

## Blender export

A `.blend` export should ideally contain:

- Spectra-owned collection/resources;
- semantic ID metadata;
- presentation resources;
- renderer-native realization;
- optional project/result reference metadata.

It should not be required to reconstruct scientific meaning if the renderer-native representation loses semantic detail.

## Export ownership

Generated files should not be written into the source repository automatically.

Project/user-selected export locations and cache locations are separate from source-control paths.

This aligns with the repository policy against generated renders/releases/build artifacts in source control.

## Overwrite behavior

Exports should not silently overwrite important user files.

Future product policy may support:

- fail if exists;
- explicit overwrite;
- versioned/duplicate-safe naming;
- export revision folders.

## Deterministic naming

Useful generated names may derive from:

```text
project
study/result
view
presentation variant
scientific time or revision
```

Avoid renderer-generated random file names when reproducibility/workflow requires stable outputs.

## Export diagnostics

Distinguish:

```text
scientific data export failure
schema serialization failure
renderer unavailable
render failure
codec unavailable
filesystem permission/path failure
unsupported presentation feature
```

Do not report all as generic "export failed".

## Headless export

Scientific data, experiment artifacts, Scene JSON, and report metadata should be exportable headlessly.

Image/video export may route to:

- Blender background mode;
- future headless WebGPU/render service;
- another renderer backend.

## Remote rendering

Numerical execution and rendering may occur on different workers.

Conceptual:

```text
remote numerical solve
   -> semantic result / Scene
   -> render worker
   -> image/video
```

Renderer worker does not need to recalculate the science unless specifically configured.

## Project archives

A future portable project bundle may include:

```text
project document
small embedded resources
presentation configs
experiment artifacts
selected cached results
optional renderer exports
```

Large datasets may remain external references with hashes.

## AI/report authoring

AI may help produce captions, summaries, or report narrative from structured project/result metadata.

It must not invent numerical values or scientific provenance absent from the engine data.

## Maturity labeling

A report may optionally include maturity/model-scope notes for reference solvers.

Example:

> Computed with Spectra reference 3D incompressible-flow solver; not an industrial turbulence-model CFD result.

This protects scientific communication from overclaiming engine foundations.

## Success criterion

The same Spectra result should be exportable as raw scientific data, renderer-neutral Scene, premium Blender figure/video, experiment artifact, or report bundle without confusing sampled visualization data with source numerical data or making a renderer-native file the only scientific record.
