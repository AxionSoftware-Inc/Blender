# Spectra Science — Project Runtime API Draft

Status: **design draft, not implemented runtime**.

This document translates the project/document/state/workflow architecture into a concrete first Python runtime shape while reusing the provenance and experiment-artifact contracts that already exist in the runtime.

## Goal

A Spectra project must be the scientific/product source of truth above renderer-native files.

A `.blend` file may be an output/cache/workspace, but the project model owns:

- scientific model definitions;
- parameters and resources;
- solver-selection intent;
- result/artifact references;
- experiments;
- views;
- presentation variants;
- environment/plugin requirements;
- durable metadata.

## Existing runtime contracts that project MUST reuse

Current runtime already owns durable provenance/artifact types:

```text
spectra.reproducibility.ScientificEnvironmentSnapshot
spectra.reproducibility.SolverPolicyRecord
spectra.reproducibility.capture_environment(...)

spectra.domains.experiments.artifacts.ExperimentArtifact
spectra.domains.experiments.artifacts.NumericalRunArtifact
```

Important distinction:

```text
ProjectSolverSelection
    = desired/configured solver-selection intent before a run

ScientificEnvironmentSnapshot
    = actual loaded scientific/numerical environment captured for provenance

reproducibility.SolverPolicyRecord
    = actual active numerical policy captured inside that environment snapshot

ExperimentArtifact / NumericalRunArtifact
    = durable result-time experiment/run provenance
```

Do not create another environment snapshot format or another `SolverPolicyRecord` in `spectra.project`.

## First implementation scope

Do not attempt large binary-array storage in project schema v1.

Initial runtime should support:

1. project metadata;
2. model records;
3. project solver-selection intent;
4. result/artifact references;
5. view records;
6. presentation variants;
7. plugin/environment requirements;
8. dirty/invalidation states;
9. deterministic JSON round-trip.

## Proposed modules

```text
spectra/project/
    __init__.py
    models.py
    document.py
    runtime.py
    commands.py        later
    storage.py         later
```

## Core identifiers

Use stable opaque string IDs. Do not use display names as references.

```python
ProjectId = str
ModelId = str
ResultId = str
ViewId = str
PresentationVariantId = str
ExperimentId = str
ResourceId = str
```

Recommended namespaces may remain human-readable:

```text
model.maxwell.primary
result.maxwell.run_001
view.maxwell.vector_field
presentation.demo.cinematic
```

## Project metadata

```python
@dataclass(frozen=True)
class ProjectMetadata:
    project_id: str
    title: str
    description: str = ""
    created_with: str | None = None
    tags: tuple[str, ...] = ()
```

Timestamps may be persisted as metadata, but deterministic scientific fingerprints should not include volatile timestamps unless explicitly intended.

## ModelRecord

A project model record references a serializable semantic payload rather than renderer objects.

```python
@dataclass(frozen=True)
class ModelRecord:
    model_id: str
    semantic_type: str
    payload_schema: str
    payload: dict[str, object]
    resource_ids: tuple[str, ...] = ()
```

For first implementation, only semantic models with explicit serializers should be persistable.

Do not automatically serialize arbitrary dataclasses, Python callables, plugin class instances, Blender objects, or native handles.

## ProjectSolverSelection

This is configuration intent, deliberately distinct from the existing reproducibility `SolverPolicyRecord`.

Suggested shape:

```python
@dataclass(frozen=True)
class ProjectSolverSelection:
    role: str
    policy_name: str | None = None
    implementation_id: str | None = None
    requirements: NumericalSolverRequirements | None = None
```

Persistent representation may encode the requirements fields rather than serialize the Python object directly.

Rules:

- exact implementation selection and policy/requirements selection are explicit;
- no native solver object/handle is persisted;
- changing selection intent invalidates affected numerical results;
- the actual selected implementation is recorded later in `NumericalRunRecord` / `NumericalRunArtifact`;
- the actual active policy/environment is captured later in `ScientificEnvironmentSnapshot`.

This separation prevents project configuration from being confused with result provenance.

## ResultRecord

Durable project JSON should reference result artifacts rather than inline all numerical history.

```python
@dataclass(frozen=True)
class ResultRecord:
    result_id: str
    model_id: str
    artifact_uri: str
    artifact_schema: str
    environment_fingerprint: str | None = None
    model_fingerprint: str | None = None
    status: str = "ready"
```

`environment_fingerprint` should, when applicable, come from:

```python
ScientificEnvironmentSnapshot.fingerprint
```

rather than a second project-specific environment hash algorithm.

The artifact URI may later refer to:

```text
local chunked storage
project archive member
remote object storage
```

## Experiment results

Do not define a second project experiment-result schema.

Project should reference existing:

```text
spectra.experiment v1 / ExperimentArtifact
```

Conceptual project record:

```python
@dataclass(frozen=True)
class ExperimentRecord:
    experiment_id: str
    artifact_uri: str
    artifact_schema: str = "spectra.experiment"
    environment_fingerprint: str | None = None
```

The referenced `ExperimentArtifact` already contains:

- axes;
- metrics;
- cases;
- failures;
- numerical run summaries;
- `ScientificEnvironmentSnapshot`;
- environment fingerprint.

Project should not duplicate those fields unless indexing requires a small summary cache.

## ViewRecord

```python
@dataclass(frozen=True)
class ViewRecord:
    view_id: str
    source_result_id: str
    view_type: str
    parameters: dict[str, object]
```

A view is semantic visualization intent. It must not contain Blender object IDs or shader node names.

A later project version may allow views sourced from experiment artifacts or model semantics directly; v1 can remain narrower if that keeps references simple.

## Presentation variant

```python
@dataclass(frozen=True)
class PresentationVariantRecord:
    presentation_id: str
    view_id: str
    preset: str
    intent_payload: dict[str, object]
```

One scientific result/view may have many presentation variants:

```text
analysis
publication
presentation
cinematic
```

without rerunning the solve.

Once `PresentationIntent` becomes stable/serializable, `intent_payload` should use its canonical serializer rather than a parallel ad-hoc presentation schema.

## Environment requirements vs captured environment

These are different concepts.

### Declarative project requirement

What must be available to open/solve the project:

```python
@dataclass(frozen=True)
class EnvironmentRequirement:
    capability: str | None = None
    min_version: int | None = None
    plugin_id: str | None = None
    plugin_version: str | None = None
```

### Captured result environment

What was actually loaded/selected when a result was produced:

```text
ScientificEnvironmentSnapshot
```

Project open compares current runtime against declarative requirements.

Project/result inspection may compare current runtime against a historical captured snapshot.

It must not silently install or enable missing code.

## ProjectDocument

Suggested first shape:

```python
@dataclass(frozen=True)
class ProjectDocument:
    schema: str
    metadata: ProjectMetadata
    models: tuple[ModelRecord, ...] = ()
    solver_selections: tuple[ProjectSolverSelection, ...] = ()
    results: tuple[ResultRecord, ...] = ()
    experiments: tuple[ExperimentRecord, ...] = ()
    views: tuple[ViewRecord, ...] = ()
    presentations: tuple[PresentationVariantRecord, ...] = ()
    requirements: tuple[EnvironmentRequirement, ...] = ()
```

Initial persistent schema could be:

```text
spectra.project v1
```

Do not ship/freeze it until migrations/fixtures are ready.

## ProjectRuntime

`ProjectDocument` is immutable persisted state. `ProjectRuntime` coordinates loaded semantic objects, derived state, caches, and operations.

Conceptual API:

```python
class ProjectRuntime:
    @classmethod
    def from_document(
        cls,
        document: ProjectDocument,
        *,
        domain_registry: DomainRegistry,
    ) -> "ProjectRuntime": ...

    def document(self) -> ProjectDocument: ...
    def validate_environment(self) -> tuple[Diagnostic, ...]: ...
    def current_environment(self) -> ScientificEnvironmentSnapshot: ...
    def model_state(self, model_id: str) -> object: ...
    def result_status(self, result_id: str) -> str: ...
    def invalidate_model(self, model_id: str) -> None: ...
    def attach_result(self, result: ResultRecord) -> None: ...
    def compile_view(self, view_id: str) -> Scene: ...
    def present(self, presentation_id: str) -> Scene: ...
```

`current_environment()` should call/reuse `capture_environment(registry)` rather than rebuild provider/solver inventory logic.

Runtime mutation should eventually occur through semantic commands/transactions rather than arbitrary attribute mutation.

## Dirty/invalidation rules

```text
model change
  -> numerical result stale
  -> dependent views stale
  -> presentation result stale
  -> renderer cache stale

ProjectSolverSelection change
  -> affected numerical result stale
  -> dependent views/presentation stale

presentation-only change
  -> presentation result stale
  -> renderer cache stale
  -> numerical result remains valid

camera-only presentation change
  -> no numerical recompute

renderer/backend switch
  -> scientific result/view remain valid
  -> native renderer cache rebuilt
```

This separation is a product correctness requirement, not merely an optimization.

## Model fingerprint

A future deterministic model fingerprint should include scientific inputs affecting computation:

```text
semantic payload
resource checksums
ProjectSolverSelection
relevant explicit scientific options
```

Result provenance separately records the **actual environment** through `ScientificEnvironmentSnapshot`.

Exclude:

```text
camera
lighting
presentation preset
Blender object names
window/UI state
```

## Serialization API draft

```python
def project_to_dict(project: ProjectDocument) -> dict[str, object]: ...
def project_from_dict(payload: dict[str, object]) -> ProjectDocument: ...
def project_to_json(project: ProjectDocument) -> str: ...
def project_from_json(text: str) -> ProjectDocument: ...
```

Requirements:

- deterministic canonical ordering where meaningful;
- finite numeric validation;
- schema identifier/version required;
- unknown future schema fails diagnostically;
- backward migrations explicit;
- no execution during parse;
- reuse existing serializers for stable embedded/reference records instead of copying their encoding logic.

## Artifact storage boundary

Project JSON references durable result artifacts.

Do not encode giant PDE histories as nested JSON lists merely because JSON is convenient.

Conceptually:

```text
project.json
artifacts/
  experiment_001.json        # existing spectra.experiment artifact
  result_001/manifest.json
  result_001/state.bin or chunked arrays
resources/
  ...
```

Large general result artifact format remains a later design; experiment artifacts already have a working schema.

## Historical environment comparison

A project/result inspector may expose:

```text
historical result environment fingerprint
current environment fingerprint
```

and report differences in:

```text
domain versions
capability provider/versions
solver implementation inventory
active/default policies
```

Use the existing snapshot structure for this comparison.

## Blender interaction

```text
ProjectRuntime.present(id)
    -> generic Scene
    -> IncrementalBlenderBackend.apply(...)
```

Project state never persists Blender datablock pointers as scientific state.

A `.blend` may optionally store:

- project path/reference;
- project revision/fingerprint;
- backend cache metadata;

but remains secondary.

## Remote execution

```text
Project model + ProjectSolverSelection
  -> ExecutionRequest
  -> remote worker
  -> result artifact + ScientificEnvironmentSnapshot
  -> attach only if source model revision/fingerprint still matches
```

Late remote jobs must not overwrite results for newer model revisions.

## First test matrix after implementation gate

- empty project round-trip;
- one model round-trip;
- duplicate IDs rejected;
- unknown references rejected;
- missing plugin/capability requirement diagnosed;
- project solver selection round-trip;
- project selection intent remains distinct from captured `SolverPolicyRecord`;
- `current_environment()` equals `capture_environment(registry)`;
- `ResultRecord.environment_fingerprint` accepts existing snapshot fingerprint;
- existing `ExperimentArtifact` can be referenced without re-encoding its internals;
- presentation change does not invalidate numerical result;
- model/solver-selection change invalidates dependent result/view/presentation;
- renderer switch does not invalidate scientific result;
- malformed/unknown schema does not execute code;
- deterministic serialization;
- one project owns multiple presentation variants for one view.

## Success criterion

A user can open a Spectra project without Blender, inspect/solve it headlessly, retain exact environment/experiment provenance using existing runtime artifact formats, then open the same project in Blender and receive the same scientific Scene semantics with a Blender-native presentation.