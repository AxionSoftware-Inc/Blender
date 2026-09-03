# Spectra Science — Project Runtime API Draft

Status: **design draft, not implemented runtime**.

This document translates the project/document/state/workflow architecture into a concrete first Python runtime shape.

## Goal

A Spectra project must be the scientific/product source of truth above renderer-native files.

A `.blend` file may be an output/cache/workspace, but the project model owns:

- scientific model definitions;
- parameters and resources;
- solver policy;
- result references;
- experiments;
- views;
- presentation variants;
- environment/plugin requirements;
- durable metadata.

## First implementation scope

Do not attempt large binary-array storage in project schema v1.

Initial runtime should support:

1. project metadata;
2. model records;
3. result/artifact references;
4. view records;
5. presentation variants;
6. plugin/environment requirements;
7. dirty/invalidation states;
8. deterministic JSON round-trip.

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

Recommended namespaces remain human-readable where useful:

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

A project model record should reference a serializable semantic payload rather than hold renderer objects.

```python
@dataclass(frozen=True)
class ModelRecord:
    model_id: str
    semantic_type: str
    payload_schema: str
    payload: dict[str, object]
    resource_ids: tuple[str, ...] = ()
```

For first implementation, only semantic models with an explicit serializer should be persistable.

Do not automatically serialize arbitrary dataclasses or Python callables.

## Solver policy record

```python
@dataclass(frozen=True)
class SolverPolicyRecord:
    role: str
    policy_id: str | None = None
    implementation_id: str | None = None
    requirements: dict[str, object] | None = None
```

This record describes selection intent, not a native solver handle.

## Result reference

Durable project JSON should not necessarily inline large numerical histories.

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

The artifact URI may later refer to local chunked storage, a project archive member, or remote object storage.

## View record

```python
@dataclass(frozen=True)
class ViewRecord:
    view_id: str
    source_result_id: str
    view_type: str
    parameters: dict[str, object]
```

A view is semantic visualization intent. It should not contain Blender object IDs.

## Presentation variant

```python
@dataclass(frozen=True)
class PresentationVariantRecord:
    presentation_id: str
    view_id: str
    preset: str
    intent_payload: dict[str, object]
```

One scientific result/view can have many presentation variants:

```text
analysis
publication
presentation
cinematic
```

without rerunning the numerical solve.

## Environment requirements

```python
@dataclass(frozen=True)
class EnvironmentRequirement:
    capability: str | None = None
    min_version: int | None = None
    plugin_id: str | None = None
    plugin_version: str | None = None
```

Project open should inspect requirements and produce diagnostics. It must not silently install or enable code.

## ProjectDocument

```python
@dataclass(frozen=True)
class ProjectDocument:
    schema: str
    metadata: ProjectMetadata
    models: tuple[ModelRecord, ...] = ()
    solver_policies: tuple[SolverPolicyRecord, ...] = ()
    results: tuple[ResultRecord, ...] = ()
    views: tuple[ViewRecord, ...] = ()
    presentations: tuple[PresentationVariantRecord, ...] = ()
    requirements: tuple[EnvironmentRequirement, ...] = ()
```

Initial schema name could be:

```text
spectra.project v1
```

Do not ship this schema until migrations/fixtures are ready.

## ProjectRuntime

`ProjectDocument` is immutable persisted state. `ProjectRuntime` coordinates loaded scientific objects, derived state, caches, and operations.

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
    def model_state(self, model_id: str) -> object: ...
    def result_status(self, result_id: str) -> str: ...
    def invalidate_model(self, model_id: str) -> None: ...
    def attach_result(self, result: ResultRecord) -> None: ...
    def compile_view(self, view_id: str) -> Scene: ...
    def present(self, presentation_id: str) -> Scene: ...
```

Runtime mutation should eventually occur through semantic commands/transactions rather than arbitrary attribute mutation.

## Dirty/invalidation rules

Separate dependencies:

```text
model change
  -> numerical result stale
  -> dependent views stale
  -> presentation result stale
  -> renderer cache stale

presentation-only change
  -> presentation result stale
  -> renderer cache stale
  -> numerical result remains valid

camera-only presentation change
  -> no numerical recompute

solver policy change
  -> affected numerical result stale

renderer/backend switch
  -> scientific result/view remain valid
  -> native renderer cache rebuilt
```

This separation is a product requirement, not just an optimization.

## Model fingerprint

A future deterministic model fingerprint should include scientific inputs that affect computation:

```text
semantic payload
resources/checksums
solver selection intent
relevant plugin/capability versions
```

It should exclude:

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
- schema identifier required;
- unknown future schema fails with a structured diagnostic;
- backward migrations explicit;
- no execution during parse.

## Artifact storage boundary

Project JSON references durable result artifacts. Large arrays should later use chunked/binary storage with checksums.

Do not encode giant PDE histories as nested JSON lists merely because JSON serialization is easy.

Conceptual:

```text
project.json
artifacts/
  result_001/manifest.json
  result_001/state.bin or chunked arrays
resources/
  ...
```

Exact archive format comes later.

## Blender interaction

Blender integration should consume project views/presentations:

```text
ProjectRuntime.present(id)
    -> generic Scene
    -> IncrementalBlenderBackend.apply(...)
```

The project must not persist Blender datablock pointers as scientific state.

A `.blend` may optionally store:

- a project path/reference;
- a project revision/fingerprint;
- backend cache metadata;

but it remains secondary.

## Remote execution interaction

The same model/result contracts should support:

```text
Project model
  -> ExecutionRequest
  -> remote worker
  -> Result artifact
  -> attach only if source model revision still matches
```

Late remote jobs must not overwrite results for a newer model revision.

## First test matrix after implementation gate

- empty project round-trip;
- one model round-trip;
- duplicate IDs rejected;
- unknown references rejected;
- missing plugin/capability requirement diagnosed;
- presentation change does not invalidate numerical result;
- model change invalidates dependent result/view/presentation;
- renderer switch does not invalidate scientific result;
- malformed/unknown schema does not execute code;
- deterministic serialization;
- one project can own multiple presentation variants for one view.

## Success criterion

A future user should be able to open a Spectra project on a machine without Blender, inspect/solve it headlessly, then open the same project in Blender and receive the same scientific Scene semantics with a Blender-native premium presentation.