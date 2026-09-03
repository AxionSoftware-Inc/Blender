# Spectra Science — Project and Workflow State Model

This document defines the conceptual lifecycle of a Spectra project/study without committing to a UI framework or persistent schema implementation yet.

The same state model should support:

- Blender panel workflows;
- standalone desktop/WebGPU clients;
- Python API;
- CLI/headless workers;
- notebook-like environments;
- future AI authoring.

## Why a state model is needed

Scientific software becomes fragile when UI state, solver state, renderer state, and project state are mixed together.

Spectra should instead distinguish:

```text
Project definition
Scientific model
Numerical configuration
Computed result
Visualization/view
Presentation variant
Renderer session
Export artifact
```

These objects have different lifetimes and invalidation rules.

## Project lifecycle

Conceptual states:

```text
empty
  ↓
authored
  ↓
validated
  ↓
ready_to_solve
  ↓
solving
  ↓
solved
  ↓
view_compiled
  ↓
presented
  ↓
rendered/exported
```

A project may move backward when inputs change.

Example:

```text
solved
  ↓ change material property
validated
  ↓
ready_to_solve
```

Changing only presentation should not invalidate the scientific solution.

## Layer 1 — project definition

Owns durable user intent:

- project identity/title;
- selected scientific model(s);
- parameter values;
- external data references;
- requested outputs;
- experiment definitions;
- solver policy preferences;
- saved presentation variants.

The project definition should not contain live Blender objects or GPU handles.

## Layer 2 — scientific model

Resolved semantic objects produced from project definition.

Examples:

```text
MaxwellProblem3D
HeatConductionProblem3D
ParticleProblem
ReactionNetwork
MetricTensorField
ParameterSweep
```

Scientific model validation checks:

- units;
- shapes;
- boundaries;
- required capability availability;
- semantic consistency.

## Layer 3 — numerical execution plan

Derived from scientific model plus solver policy.

Conceptually contains:

```text
required solver role(s)
selected implementation(s)
execution requirements
precision
fixed/adaptive settings
step/tolerance hints
batching opportunity
provenance context
```

The plan may be recomputed without changing the scientific model.

Example:

```text
same Maxwell semantics
    -> reference Python policy
    -> native CPU policy
    -> GPU-first policy
```

Scientific meaning remains unchanged.

## Layer 4 — computed result

Immutable/result-oriented semantic outputs such as:

- field histories;
- trajectories;
- PDE solutions;
- diagnostics;
- experiment results;
- convergence studies.

Results should carry or reference numerical provenance.

A result may be cached independently from presentation/render output.

## Layer 5 — view definition

A scientific result can have multiple valid views.

Examples:

```text
Maxwell result
  -> E vectors
  -> B vectors
  -> Poynting vectors
  -> scalar energy slice

Quantum state
  -> probability density
  -> phase
  -> probability current

CFD result
  -> velocity arrows
  -> streamlines
  -> vorticity slice
  -> pressure slice
```

Changing view does not recompute the underlying solution unless the requested view requires missing derived scientific data.

## Layer 6 — base Scene

The view compiler creates renderer-independent:

```text
Scene + Timeline
```

This is scientific visualization output, not yet premium presentation.

Changing renderer should not require recompiling science when the same Scene representation is sufficient.

## Layer 7 — presentation variant

A project may save multiple presentation variants over the same base Scene/result:

```text
analysis
publication
presentation
cinematic
custom_team_preset
```

Presentation owns:

- camera policy;
- theme;
- legends;
- annotation density;
- lighting intent;
- reveal/camera animation;
- display decimation.

Changing presentation should not invalidate numerical results.

## Layer 8 — renderer session

A renderer session is ephemeral execution state.

Examples:

- Blender objects/datablocks;
- WebGPU buffers;
- native material handles;
- viewport camera state;
- render-engine resources.

Renderer session state should be reconstructible from project/result/Scene/presentation data.

A `.blend` file may cache a renderer session, but it should not be the only scientific source of truth.

## Layer 9 — exports

Exports are derived artifacts:

- PNG/JPEG/EXR;
- video;
- `.blend`;
- Scene JSON;
- experiment JSON;
- report figure;
- project archive.

Exports should reference enough metadata to identify the scientific project/result/presentation that produced them when reproducibility matters.

## Invalidation matrix

### Change scientific input

Examples:

- source strength;
- material constant;
- geometry/boundary;
- initial condition.

Invalidate:

```text
execution plan
result
view Scene
presentation enrichment
renderer session
exports
```

Keep project identity and unrelated model records.

### Change solver implementation/policy

Invalidate:

```text
execution plan
result
all result-derived views/presentations/exports
```

Do not invalidate semantic model.

### Change solver tolerance/steps

Same invalidation behavior as solver policy.

### Change view

Invalidate:

```text
base Scene for that view
presentation derived from that Scene
renderer representation for that view
```

Do not invalidate result.

### Change presentation preset

Invalidate only:

```text
presentation-enriched Scene/resources
renderer presentation resources
presentation export
```

Scientific result/base semantics remain valid.

### Change renderer

Invalidate renderer session/export only.

### Change camera interactively

If camera is temporary user navigation, project science remains untouched.

If user saves the camera into a presentation variant, update that presentation configuration only.

## Dirty-state model

A product UI may expose semantic dirty states conceptually:

```text
MODEL_DIRTY
SOLVER_DIRTY
RESULT_DIRTY
VIEW_DIRTY
PRESENTATION_DIRTY
RENDER_DIRTY
```

Do not use one generic `dirty=True` flag for the entire product; it causes unnecessary recomputation and renderer rebuilds.

## Compute actions

Useful product-level commands:

```text
validate_project
prepare_execution
solve
recompute_derived_fields
compile_view
apply_presentation
open_renderer_session
render/export
```

Each command should have a clear input/output boundary and not silently perform unrelated destructive work.

## Cancel and failure behavior

A failed solve should not destroy the last successful result automatically.

Conceptual project state may keep:

```text
last_successful_result
current_attempt_error
current_model_revision
result_model_revision
```

The UI can then show that the visible result is stale relative to current inputs instead of deleting it.

## Revision identity

Future project runtime may assign deterministic/revision IDs to:

```text
model revision
numerical plan revision
result revision
view revision
presentation revision
```

This helps:

- caching;
- worker scheduling;
- distributed execution;
- stale-result detection;
- undo/redo;
- collaboration.

## Caching

Recommended cache hierarchy:

```text
semantic model cache
numerical result cache
derived-field cache
base Scene cache
presentation Scene cache
renderer-native cache
```

Cache keys should include only the upstream state that actually affects each layer.

Example: changing cinematic camera should not invalidate a three-hour CFD solution cache.

## Asynchronous product execution

A future application may execute numerical work in background workers, but the engine contract should remain synchronous/deterministic at the solver boundary.

The product layer may wrap it with:

```text
job id
progress
cancel request
resource request
result publication
```

Do not put UI task queues into scientific semantic domains.

## Local vs remote execution

The same execution plan may target:

```text
local Python
local native CPU
local GPU
remote/HPC worker
```

The result contract should remain semantic and provenance-aware.

Remote execution should not require different physics types.

## Multi-model projects

A project may contain several coupled or independent studies:

```text
thermal model
solid model
Maxwell model
experiment sweep
```

Relationships should be explicit:

```text
Maxwell J·E -> heat source
heat result -> thermoelastic forcing
```

Do not infer couplings merely because compatible result types coexist in one project.

## Multiple presentation variants

A single result might generate:

```text
technical_analysis
paper_figure
executive_slide
cinematic_demo
web_interactive
```

These should share scientific source/result identity while preserving independent presentation configuration.

## Undo/redo boundary

Product undo should preferably operate on project/model/view/presentation commands, not raw Blender object mutations.

Blender-native undo may still be useful for renderer-side authoring, but scientific project truth should remain reconstructible.

## AI authoring boundary

An AI surface may propose commands such as:

```text
add point charge
change boundary
run sweep
show probability density
switch to cinematic preset
```

AI should modify the same project/semantic contracts as UI or Python code.

It must not directly mutate hidden Blender objects as the authoritative state.

## Suggested product status indicators

A polished client can show states such as:

```text
Valid
Needs recompute
Solving
Result current
Result stale
View current
Presentation current
Render stale
```

This is more useful than one global spinner.

## Success criterion

A user should be able to change only the visual preset of a solved three-dimensional simulation and get a new Blender/WebGPU presentation without recomputing science; conversely, changing a physical parameter should clearly invalidate downstream results while leaving unrelated project state intact.
