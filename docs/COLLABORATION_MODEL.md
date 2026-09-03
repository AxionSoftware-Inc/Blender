# Spectra Science — Collaboration and Revision Model

This document defines a future collaboration model built on semantic project revisions and commands rather than renderer-native object synchronization.

Collaboration is not an immediate runtime milestone. The goal is to preserve an architecture that can support teams later without rewriting the scientific engine.

## Principle

Collaborate on semantic project state:

```text
models
parameters
solver policies
experiment definitions
views
presentation variants
resource references
```

Do not make Blender object/datablock replication the authoritative collaboration model.

Renderer sessions are derived views of shared project state.

## Revision model

Every committed semantic project edit should create a new revision identity.

Conceptually:

```text
revision id
parent revision(s)
command/transaction
changed semantic paths
result invalidation
actor/session metadata
```

A project may therefore form a history graph rather than one mutable blob.

## Shared vs local state

Shared project state may include:

- scientific model definitions;
- study configuration;
- experiment definitions;
- presentation variants;
- resource references;
- selected saved results/artifacts;
- annotations intended for the team.

Local ephemeral state should normally include:

- viewport navigation;
- unsaved panel layout;
- temporary selections;
- local cache locations;
- local renderer objects;
- local credentials.

Do not synchronize every transient UI event.

## Commands as collaboration operations

Semantic commands from `COMMAND_AND_UNDO_MODEL.md` provide a natural operation format.

Example:

```text
SetParameter(model=A, current=5 A)
SetPresentationPreset(view=B, publication)
AddExperimentMetric(...)
```

A server/workspace may validate commands against a base revision and produce a new committed revision.

## Optimistic concurrency

Conceptual flow:

```text
client edits from revision 42
submit command with base=42
server/current=42 -> accept -> revision 43
```

If current revision advanced, attempt semantic conflict detection instead of blindly overwriting.

## Conflict classes

### Independent edits

Example:

```text
A changes camera preset
B changes solver precision
```

These may merge safely when they touch independent semantic paths.

### Same-field conflict

Example:

```text
A sets temperature boundary to 300 K
B sets same boundary to 350 K
```

Requires explicit resolution.

### Structural conflict

Example:

```text
A deletes a model component
B edits that component
```

Cannot be silently merged.

### Resource conflict

Two users relink the same logical resource to different content hashes.

Requires explicit resolution.

## Scientific result collaboration

Numerical results should be immutable artifacts associated with:

```text
model revision
execution plan/provenance
resource hashes
```

A new project edit does not mutate an old result.

The UI can mark result as:

```text
current
stale
historical
```

This is safer than trying to merge numerical arrays from different model revisions.

## Experiment collaboration

Parameter-sweep definitions are shared semantic configuration.

Case results are immutable artifacts keyed by deterministic case IDs and source definition/environment.

Teams may rerun missing/failed cases without rewriting successful historical artifacts.

## Presentation collaboration

Presentation variants are useful collaboration units:

```text
analysis
paper_figure_1
investor_demo
teaching_scene
```

Multiple users can author different presentation variants over one scientific result without conflict.

## Comments/annotations

Team comments should be separate from scientific semantic annotations.

Distinguish:

```text
scientific annotation
  e.g. label critical point at x=...

collaboration comment
  e.g. "check this boundary before review"
```

A collaboration comment should not alter renderer output unless deliberately promoted to a presentation annotation.

## Resource collaboration

Large resources may be shared by content-addressed storage or workspace resource IDs.

Project revisions reference resource identities/hashes, not each user's local absolute path.

Each client maps shared resource identity to local/cache storage.

## Plugin compatibility

A collaborative workspace should record required plugin/package versions.

A client missing a plugin may:

- inspect project metadata;
- see dependency diagnostics;
- possibly view cached renderer/result artifacts;
- not edit/solve unsupported semantic records until compatible plugin installed/approved.

Do not silently reinterpret unknown plugin data.

## Solver/provider differences between collaborators

Two users may have different execution hardware.

Same scientific model could produce results from:

```text
reference Python
native CPU
GPU
remote worker
```

Results remain separate artifacts with provenance.

The project may designate one result as approved/current for a deliverable.

## Approval/review states

Future team workflow may mark artifacts:

```text
draft
reviewed
approved
superseded
```

This metadata is workflow state, not scientific truth.

Do not overwrite the underlying result/provenance when approval changes.

## Permissions

A future workspace may distinguish:

```text
viewer
editor
solver/operator
plugin/admin
project owner
```

Examples:

- viewer can inspect results;
- editor changes model/presentation;
- operator launches expensive jobs;
- admin enables external plugins/native providers.

Permission policy belongs to product/workspace infrastructure.

## Audit trail

A semantic history can record:

```text
who
when
command/transaction
base/new revision
diagnostics
result/job references
```

Do not rely on Blender undo history as team audit history.

## Offline edits

Future clients may edit offline from a known revision.

On reconnect:

```text
fetch current revision
attempt semantic rebase/merge
surface conflicts
```

Persistent semantic IDs are important for this.

## Renderer collaboration

Blender/WebGPU sessions need not be synchronized at low-level object transform frequency unless a future live co-viewing feature explicitly requires it.

Normal collaboration can synchronize project/presentation commands and let each client rebuild its own renderer state.

## Live co-viewing

A later product could synchronize ephemeral presentation navigation:

- camera;
- time cursor;
- selected semantic object;

as session events.

These should remain separate from durable project revision history unless explicitly saved.

## Remote jobs

Collaboration server may coordinate jobs:

```text
submit from project revision
execute on worker
publish result artifact
notify clients
```

Before accepting returned result as current, verify its model revision still matches or mark it stale/historical.

## Merge safety

Never merge scientific state by generic JSON deep-merge alone.

Semantic paths/types may have constraints and relationships.

A future merge engine should understand command targets and stable semantic IDs.

## Schema migration

Collaborative storage should migrate project schema centrally/transactionally.

Clients with older unsupported schemas should fail clearly rather than write incompatible data into the same workspace.

## Security

Collaboration adds trust concerns:

- authenticated users;
- project authorization;
- resource permissions;
- plugin approval;
- worker/job authorization;
- audit log integrity.

See `TRUST_AND_SECURITY_MODEL.md`.

## Success criterion

Two users should eventually be able to edit independent parts of one Spectra project, run results on different hardware, create separate presentation variants, review historical results, and resolve true scientific edit conflicts without synchronizing raw Blender objects or losing provenance/revision identity.
