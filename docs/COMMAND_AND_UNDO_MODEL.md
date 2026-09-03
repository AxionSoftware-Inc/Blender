# Spectra Science — Command, Undo, and Automation Model

This document defines how user actions, UI operations, AI authoring, scripts, and collaboration should modify Spectra project state without making renderer-native edits the authoritative history.

## Goal

Every meaningful project edit should be representable conceptually as a semantic command:

```text
command
  -> validate
  -> apply to project/model/view/presentation state
  -> produce new revision
  -> invalidate only affected downstream layers
```

The same command model should support:

- Blender UI;
- standalone UI;
- Python automation;
- CLI;
- AI authoring;
- future collaboration/history.

## Command categories

Useful categories:

```text
project commands
model commands
solver/execution commands
experiment commands
view commands
presentation commands
resource commands
plugin/project-environment commands
```

## Examples

### Project command

```text
RenameProject("Magnetic Lens Study")
```

Does not invalidate solve.

### Model command

```text
SetParameter(model="coil", name="current", value=5 A)
```

Invalidates numerical result and downstream views/presentation/render.

### Solver command

```text
SetSolverPolicy("gpu_preferred")
```

Keeps semantic model, invalidates execution/result downstream.

### View command

```text
SetViewSampling(view="electric_field", glyph_count=(20,20,12))
```

Keeps result, recompiles view/presentation only.

### Presentation command

```text
SetPresentationPreset("cinematic")
```

Keeps science/result/base view if compatible.

## Command result

A command application may return conceptually:

```text
new project revision
changed paths/semantic IDs
invalidation set
diagnostics
undo inverse or previous-value record
```

This allows product UI to update only affected panels/caches.

## Immutable state preference

Where practical, commands should produce new immutable/revisioned semantic objects rather than mutate hidden state in place.

Renderer sessions may update in place for performance, but project/source state should remain explicit.

## Invalidation integration

Commands should map to dirty layers from `PROJECT_STATE_MODEL.md`.

Example:

```text
SetPresentationPreset
  -> PRESENTATION_DIRTY
  -> RENDER_DIRTY

SetMaterialYoungsModulus
  -> MODEL_DIRTY
  -> SOLVER_DIRTY
  -> RESULT_DIRTY
  -> VIEW_DIRTY
  -> PRESENTATION_DIRTY
  -> RENDER_DIRTY
```

## Undo/redo

Undo should operate on semantic/project commands.

Conceptual history:

```text
revision 10
  SetCharge(+1 C)
revision 11
  SetSolverPolicy(RK45)
revision 12
  SetPresentationPreset(cinematic)
```

Undoing revision 12 should not restore old numerical arrays if they were unaffected.

## Inverse commands vs snapshots

Two implementation strategies:

### Inverse command

Store enough previous value to apply an inverse.

Efficient for small deterministic edits.

### State snapshot/diff

Store revisioned state/delta.

Useful for complex multi-object edits.

The runtime can combine both, but public command semantics should remain independent from storage strategy.

## Transactions

Some user actions consist of multiple semantic edits that should be atomic.

Example:

```text
AddPointCharge
  -> create source
  -> assign position
  -> assign charge
  -> add to active electrostatic model
```

A transaction should either commit the complete valid edit or leave previous project state intact.

This mirrors transactional domain registration philosophy.

## Preview edits

Interactive UI may need transient previews:

- dragging a source;
- adjusting camera;
- color range slider;
- glyph-density slider.

Do not add one undo record for every mouse pixel.

Conceptual model:

```text
begin_preview
update_preview many times
commit one semantic command
```

Renderer can show transient state while project history remains clean.

## Camera navigation vs presentation edit

Viewport orbit/pan may be temporary navigation.

It becomes a project/presentation command only when user explicitly saves/applies it as presentation camera configuration.

This prevents ordinary viewport navigation from polluting scientific project history.

## Solve commands

`Solve` is not the same kind of mutation as `SetParameter`.

Conceptually:

```text
RunStudy(model_revision=X, execution_plan=Y)
  -> result revision Z
```

The command/job produces a result associated with source revision X.

It should not mutate the semantic model.

## Failed solve

Failure records:

```text
attempt id
source revision
execution plan
structured diagnostics
partial trace if valid
```

The last successful result remains available.

## Experiment commands

Examples:

```text
CreateSweep
AddParameterAxis
SetMetric
RunExperiment
SetObjective
CreateParetoView
```

Experiment definition edits invalidate experiment results, not unrelated base scientific results unless coupled explicitly.

## Resource commands

Examples:

```text
AttachResource
RelinkResource
ChangeImportProfile
ReloadResource
```

Relinking to identical content hash may avoid invalidating numerical results; changing actual resource content should invalidate dependent models/results.

## Plugin/environment commands

Project may record requirements, but installing/enabling executable plugins is environment administration, not an ordinary untrusted project command.

A UI command may request enablement through approved product policy.

Do not make project history silently install code.

## Command metadata

A command may carry:

```text
command id/type
timestamp
author/session
human label
source UI/AI/API
project revision before/after
```

Scientific semantics should not depend on author identity.

## AI authoring

AI should emit high-level commands, for example:

```text
SetParameter(...)
AddView(...)
RunSweep(...)
SetPresentationPreset(...)
```

rather than arbitrary object mutations.

Benefits:

- validation applies equally;
- undo works;
- diagnostics are structured;
- AI changes are inspectable;
- collaboration/history becomes possible.

## Command validation

Before apply:

- target exists;
- value type/unit valid;
- capability available;
- command allowed in current project state;
- resource/plugin trust policy satisfied.

A command should fail atomically with diagnostics.

## Batch commands

Automation may submit a sequence:

```text
SetParameter A
SetParameter B
SetSolverPolicy
RunStudy
CompileView
```

A batch may specify whether edits are one transaction or sequential revisions.

Solve/export operations usually occur after state-changing transaction commits.

## Collaboration future

A semantic command history is a better collaboration substrate than raw Blender object diffs.

Future collaboration may use:

- revision IDs;
- command logs;
- conflict detection;
- semantic merges for independent model/view/presentation edits.

Do not implement collaboration until core project state is stable, but avoid architecture that makes it impossible.

## Conflict examples

Potentially mergeable:

```text
User A changes presentation preset
User B changes solver policy
```

Potential conflict:

```text
User A sets charge to 1 C
User B sets same charge to 2 C from same base revision
```

Renderer-native edits are much harder to reason about semantically.

## Headless replay

A command log could replay project edits for:

- reproducible tutorials;
- regression scenarios;
- AI workflows;
- collaboration audit;
- debugging.

Replay must still validate against current/stated API/schema compatibility.

## Renderer synchronization

After command invalidation/commit:

```text
project state
  -> recompute only needed semantic/view/presentation layers
  -> renderer session diff/apply
```

The renderer is downstream of command state, not the command source of truth.

## Success criterion

A parameter edit, solver change, view change, presentation change, AI instruction, or future collaboration edit should all flow through inspectable semantic commands with predictable invalidation and undo behavior rather than direct ad-hoc mutation of global/renderer/UI state.
