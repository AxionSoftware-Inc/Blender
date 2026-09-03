# Spectra Science — UI Information Architecture

This document defines how a future Spectra product should organize scientific workflows without letting UI structure become the scientific model.

The same conceptual information architecture should inform:

- Blender panels;
- standalone desktop application;
- WebGPU/web client;
- tablet/mobile clients where practical;
- advanced project inspectors.

## Principle

The UI should mirror the project/state layers rather than renderer-native object structure.

Do not organize the product primarily around:

```text
Blender collections
native mesh objects
shader nodes
Python modules
```

Organize it around:

```text
Project
Model
Parameters
Solve
Results
Views
Presentation
Experiments
Resources
Diagnostics
Export
```

## Primary workspace structure

Recommended top-level product areas:

### Project

- project identity;
- model list;
- external resources;
- plugin requirements;
- saved studies;
- result history;
- presentation variants.

### Model

Scientific definition of the active study.

Examples:

- Maxwell sources/boundaries;
- thermal material/source;
- particle initial state;
- reaction network;
- metric/geodesic problem;
- CFD domain/reference problem.

### Solve

Numerical execution choices:

- solver policy;
- compatible implementations;
- precision;
- fixed/adaptive settings;
- timestep/tolerance;
- local/remote execution;
- stability/preflight diagnostics.

### Results

- latest result;
- historical/stale results;
- fields/trajectories;
- diagnostics;
- provenance;
- comparison.

### View

Select scientific representation:

- vectors;
- field lines;
- scalar slice;
- trajectory;
- probability density;
- phase;
- experiment plot.

View is scientific visualization selection, not premium styling.

### Presentation

- preset;
- camera;
- color scale;
- legend;
- axes;
- annotations;
- lighting intent;
- reveal/animation;
- quality/display sampling.

Changing this should not trigger a solve.

### Experiments

- parameter sweep;
- metrics;
- solver comparison;
- convergence;
- sensitivity;
- uncertainty;
- calibration;
- Pareto analysis.

### Resources

- imported datasets;
- mesh/grid files;
- external references;
- cache status;
- missing resources;
- unit/frame mapping.

### Diagnostics

- validation errors;
- numerical warnings;
- stability/conservation;
- missing capabilities/plugins;
- backend/presentation warnings;
- execution trace/provenance.

### Export

- image;
- animation;
- Scene JSON;
- experiment artifact;
- project package;
- `.blend`;
- report figure/metadata.

## Central viewport

The viewport should show the current scientific View + Presentation variant.

Renderer-native selection may be mapped back to semantic IDs.

When the user clicks a Blender/WebGPU object, UI should resolve:

```text
native object
    -> Spectra semantic/presentation resource ID
    -> scientific object/view element
```

Do not make native object identity the only selection model.

## Inspector panel

The inspector should adapt to semantic selection.

Examples:

### Selected particle

```text
position
velocity
mass
charge
trajectory/result reference
```

### Selected field view

```text
quantity
unit
sampling
color scale
source result
```

### Selected legend

```text
presentation resource
range
unit
palette
```

### Selected solver result

```text
method
implementation
precision
accepted/requested steps
diagnostics
```

## Status bar

Useful product state indicators:

```text
Model valid / invalid
Result current / stale
Solving / idle
View current / stale
Presentation current / stale
Renderer connected / rebuilding
Warnings count
Execution backend
```

Do not use one global "dirty" indicator.

## Model editor pattern

A domain should expose semantic parameter metadata to UI rather than custom UI code for every simple parameter.

Conceptual parameter metadata:

```text
name
label
type
unit
default
range/constraints
description
group
```

Complex domain-specific editors are allowed where generic forms are insufficient, but they should still construct semantic objects through public APIs.

## Units UI

Users may choose display/input units independently from internal SI execution.

UI should show:

```text
value + unit
```

and convert explicitly.

Do not hide assumed units in placeholder text only.

## Solver UI

Default user view should be simple:

```text
Recommended
Fast local
High accuracy
GPU if available
```

Advanced mode may expose:

- exact implementation;
- method order;
- adaptive flag;
- tolerance;
- execution backend;
- policy rules;
- provenance.

Do not force ordinary users to understand internal implementation IDs to run a standard study.

## Maturity UI

Capabilities/solvers/backends may display maturity badges from `CAPABILITY_MATURITY_MODEL.md`.

Examples:

```text
Reference
Experimental
Beta
Production
```

Advanced details can show verification commit/environment.

Avoid alarming users with every internal pre-alpha detail in normal workflows, but do not misrepresent reference solvers as industrial-grade.

## Result history

A project should retain multiple result records where practical.

Example list:

```text
Result 18 — current — GPU — 08:42
Result 17 — stale — RK45 — parameter k=...
Result 16 — failed attempt — convergence error
```

A failed new run should not automatically erase the last successful result.

## Experiments UI

Parameter-space editor:

```text
parameter
values/range
unit
sampling mode
```

Metrics panel:

```text
metric
unit
objective
retain raw result? yes/no
```

Result views:

- table;
- response curve;
- Pareto plot;
- sensitivity;
- uncertainty summary;
- convergence plot.

## Presentation UI

Start with high-level presets and progressively reveal advanced overrides.

Example:

```text
Preset: Cinematic
[Camera]
[Color & Legend]
[Annotations]
[Lighting]
[Animation]
[Quality]
```

Presentation controls should operate on semantic policies, not Blender node names.

An advanced Blender-specific panel may expose backend tuning separately, clearly labeled as renderer-specific.

## Scientific-time controls

Timeline transport should represent Spectra engine time.

UI may display:

```text
frame 31
scientific time 0.500 s
```

where Blender frame is transport and scientific time is semantic.

If presentation sequence includes holds/reveals, UI should distinguish presentation time from scientific simulation time.

## Diagnostics UX

Diagnostics should be grouped by category/severity.

Example:

```text
Errors (1)
  charge density unit mismatch

Warnings (2)
  CFL near conservative limit
  cinematic volumetric effect unsupported by current backend
```

Scientific and visual/backend warnings should be visually distinguishable.

## Plugin UI

Plugin manager should show:

```text
plugin
version
publisher
maturity
compatible/incompatible
enabled/disabled
provided domains/capabilities
native components
```

Opening a project requiring a missing plugin should show the requirement without auto-installing executable code.

## Remote execution UI

If remote workers exist:

```text
execution target
queue/staging/running state
resource usage/cost where available
cancel
result revision
```

Remote status belongs to Solve/Jobs, not scientific model parameters.

## Command palette

A product may expose semantic commands:

```text
Add point charge
Run current study
Show electric potential slice
Create parameter sweep
Switch to publication preset
Export current figure
```

Commands should call project/engine APIs, not manipulate native renderer objects as authoritative state.

## AI assistant integration

AI should use the same command/project model.

Example:

```text
User: show magnetic field and reduce arrow density
AI:
  -> changes View display sampling
  -> keeps Maxwell result current
  -> recompiles view/presentation
```

It should not trigger a full solve unless scientific inputs changed.

## Workspace presets

Possible UI workspace layouts:

```text
Modeling
Analysis
Experiments
Presentation
Rendering
Developer
```

These are UI arrangements only. They do not define different scientific engines.

## Blender-specific integration

Inside Blender, Spectra UI should avoid mirroring every native object/material property.

Preferred:

```text
Spectra Project
Model
Solve
View
Presentation
Diagnostics
```

Native Blender properties remain available to advanced users, but editing them directly may be treated as renderer customization outside the semantic project unless explicitly synchronized.

## Standalone client

Standalone UI can use the same information architecture with WebGPU or another viewport backend.

The standalone product should not need to reimplement scientific domains that already exist in the engine.

## Tablet/mobile adaptation

Smaller screens may collapse top-level areas into task modes:

```text
Model
Run
Inspect
Present
```

The underlying project state remains identical.

## Accessibility

UI should support:

- keyboard navigation where relevant;
- readable diagnostic severity;
- color-independent status indicators;
- scalable text;
- reduced motion;
- units/values not communicated by color alone.

## Success criterion

A user should understand whether they are editing the scientific model, numerical execution, scientific view, or visual presentation—and the product should recompute only the layers actually invalidated by that action.
