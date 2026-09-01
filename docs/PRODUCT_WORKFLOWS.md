# Spectra Science — Product Workflows

This document defines how product surfaces should orchestrate the Spectra engine without becoming the owner of scientific logic.

Possible product surfaces include:

- Blender panel/add-on UI;
- standalone desktop application;
- WebGPU/browser client;
- CLI/headless service;
- Python API;
- AI authoring assistant.

All should converge on the same semantic/project/numerical/presentation contracts.

## Core product principle

The product UI is not the scientific model.

Desired flow:

```text
user intent/input
    -> validated semantic model/project state
    -> capability/numerical execution
    -> result/artifact
    -> explicit scientific view
    -> presentation intent
    -> generic Scene + Timeline
    -> renderer/export
```

Changing UI technology should not require rewriting scientific domains.

## Workflow 1 — Direct scientific solve

User asks conceptually:

> Solve this electrostatic configuration and show the field.

Product flow:

```text
1. create/validate charge-source semantics
2. resolve required capabilities/domains
3. construct electrostatic problem
4. execute solve through stable numerical contracts
5. produce PotentialField3D
6. choose explicit field view(s)
7. compile generic Scene
8. apply presentation preset
9. send to Blender/WebGPU/backend
```

The renderer never solves Poisson's equation.

## Workflow 2 — Time-dependent simulation

Example:

> Run Maxwell simulation for this source and animate E/B.

Flow:

```text
semantic Maxwell problem
    -> solver role/policy selection
    -> Maxwell history
    -> E/B time fields
    -> explicit vector-field animation view
    -> Scene + scientific Timeline
    -> presentation reveal/camera Timeline
    -> backend playback/render
```

Scientific time remains separate from presentation reveal timing.

## Workflow 3 — Multiphysics composition

Example:

> Simulate heating and resulting deformation.

Flow:

```text
heat source semantics
    -> heat conduction
    -> temperature field
    -> thermoelastic coupling
    -> displacement/stress
    -> composed views
    -> premium presentation
```

The product surface should orchestrate capabilities rather than implement coupling equations itself.

## Workflow 4 — Parameter sweep

Example:

> Sweep thermal conductivity and show peak temperature.

Flow:

```text
ParameterSweep
    -> deterministic cases
    -> per-case scientific evaluator
    -> metrics
    -> optional batch/native execution
    -> ExperimentResult
    -> response/sensitivity/Pareto view
    -> presentation
```

The UI may display progress, but case definition/result semantics belong to the experiment layer.

## Workflow 5 — Calibration

Example:

> Fit diffusivity to measured observations.

Flow:

```text
observations
    -> calibration candidates/study definition
    -> repeated semantic model solves
    -> weighted residual objective
    -> CalibrationResult
    -> best parameter set
    -> optional rerun/presentation of best scientific result
```

A future optimizer may replace candidate-grid search behind an optimization role without changing product workflow semantics.

## Workflow 6 — Solver comparison

Example:

> Compare reference RK4, RK45, and a future native solver.

Flow:

```text
same semantic problem
    -> solver implementations
    -> tracked runs
    -> error/conservation/runtime metrics
    -> convergence/comparison experiment
    -> generic experiment Scene
```

The UI should display actual selected implementation/provenance rather than infer it from a button label.

## Workflow 7 — Premium presentation

Example:

> Make this quantum result presentation-ready.

Flow:

```text
existing scientific result
    -> explicit view: probability density / phase / current
    -> base Scene
    -> PresentationIntent(preset="presentation" or "cinematic")
    -> camera/color/legend/annotation/reveal policies
    -> presentation-enriched Scene
    -> renderer
```

Changing from `analysis` to `cinematic` should normally not recompute the scientific solution.

## Workflow 8 — Publication figure

Example:

> Export a paper-quality plot/field figure.

Flow:

```text
scientific result
    -> publication view
    -> publication presentation preset
    -> deterministic camera/axes/units/color scale
    -> high-quality renderer/vector/raster export backend
```

Publication preset should prioritize quantitative clarity over cinematic effects.

## Workflow 9 — Teaching/explanation sequence

Example:

> Explain how the electric field forms.

Flow:

```text
scientific model/result
    -> presentation sequence
        reveal sources
        reveal potential
        reveal vector field
        reveal field lines
        animate test particle
    -> renderer playback/video
```

AI may help author the sequence, but the field/particle state still comes from deterministic engine semantics.

## Workflow 10 — Blender interactive session

Blender UI should conceptually act as a product shell:

```text
Blender panel controls
    -> edit Spectra project/semantic state
    -> request solve/compile/present
    -> IncrementalBlenderBackend applies Scene
```

Do not let Blender object transforms become hidden scientific state unless an explicit mapping/editor contract says they are semantic edits.

Possible modes:

- inspect result;
- edit presentation;
- edit supported scientific sources/parameters;
- render/export.

## Workflow 11 — Standalone/WebGPU client

The same project can be opened without Blender:

```text
Spectra project
    -> semantic state / result artifacts
    -> generic Scene + presentation
    -> WebGPU renderer
```

If computation is too heavy locally, a remote/headless compute provider may produce semantic result/artifact data while the client remains a presentation/editor surface.

## Workflow 12 — Headless compute/render worker

A worker may receive:

```text
project/study definition
+ input resources
+ environment requirements
```

and return:

- tracked scientific result artifacts;
- experiment artifacts;
- Scene document;
- rendered outputs when renderer is available.

The worker should not need product UI state.

## Workflow 13 — AI authoring

AI is an orchestration/authoring surface.

Example:

> Show a cinematic Schwarzschild geodesic with three initial velocities.

AI may compile this into:

```text
project/model definitions
geodesic study cases
explicit projection view
cinematic presentation intent
```

Then deterministic engine validation/solvers execute it.

AI should not be trusted to directly hand-author final numerical arrays as scientific truth.

## Command model

A future high-level application API may expose conceptual verbs such as:

```text
create
solve
study
compare
calibrate
visualize
present
render
export
```

These are orchestration verbs over existing contracts, not replacements for domains.

Potential conceptual Python API:

```python
project = spectra.create(...)
result = spectra.solve(project.model(...))
scene = spectra.visualize(result, view=...)
scene = spectra.present(scene, preset="cinematic")
spectra.render(scene, backend="blender")
```

The exact API should be designed only after the current core/numerical milestone is validated.

## Product state machine

Useful conceptual project states:

```text
DEFINED
    semantic inputs valid

DIRTY
    inputs changed since last solve

SOLVED
    scientific result matches current inputs

PRESENTED
    one/more presentation variants compiled

EXPORTED
    renderer-specific output produced
```

A UI may show these states, but authoritative validity should come from model/result fingerprints rather than manually toggled flags.

## Cache behavior

Product should distinguish:

- scientific result cache;
- experiment artifact cache;
- base Scene cache;
- presentation Scene cache;
- renderer-native cache.

Changing only presentation should not invalidate numerical results.

Changing a physical parameter must invalidate dependent scientific results and derived scenes.

## Error UX

Engine errors should remain semantic and structured enough for product surfaces to explain them.

Examples:

- missing capability/plugin;
- incompatible unit;
- unsupported solver/problem;
- numerical instability warning;
- missing external data;
- invalid presentation/view request;
- backend capability unavailable.

A UI should not convert every failure into a generic "render failed" message.

## Long-running execution

Future product execution may be synchronous local, background application worker, remote compute, or HPC service.

The engine contract should identify studies/cases/results with stable IDs so progress/result attachment does not depend on UI widget lifetime.

This document does not implement background execution itself.

## Preview vs final

Product may support preview/final presentation quality, but scientific accuracy must be separately controlled.

Good:

```text
same scientific result
preview renderer quality
final renderer quality
```

Potentially valid when explicit:

```text
preview scientific study with reduced grid
final scientific study with full grid
```

but these must be distinct study configurations, not hidden presentation behavior.

## Export types

Future product exports may include:

- `spectra.project`;
- `spectra.scene`;
- experiment artifact JSON;
- Blender scene/file;
- images/video;
- WebGPU bundle;
- numerical tables/data resources;
- publication figures.

Renderer-specific exports should be derived from project/result/presentation state.

## Canonical demo workflow

A flagship end-to-end demo should eventually be possible with minimal product instructions:

```text
1. choose/create scientific problem
2. solve
3. inspect analysis view
4. choose cinematic/publication presentation
5. render/export
```

The same scientific result should be reusable across several presentation outputs.

## What product surfaces must not do

Do not:

- store the only scientific parameters inside UI controls;
- compute physics directly inside button callbacks;
- implement separate science for Blender vs WebGPU;
- make a renderer file the only project format;
- hide solver implementation/provenance when it matters;
- treat presentation LOD as numerical resolution;
- let AI bypass semantic/unit validation;
- silently rerun expensive science when only visual styling changed.

## Success criterion

Spectra should support multiple polished product surfaces while one central semantic/numerical engine remains authoritative.

A user should eventually be able to move from scientific question to computed result to premium presentation without needing to understand whether the final renderer is Blender, WebGPU, or another backend.
