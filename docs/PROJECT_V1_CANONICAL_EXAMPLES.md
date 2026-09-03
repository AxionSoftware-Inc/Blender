# Spectra Science — Project v1 Canonical Examples

Status: **design examples only; `spectra.project` runtime/schema is not implemented yet**.

These examples make the proposed project model concrete before the persistent schema is frozen. They are intentionally small and avoid large numerical arrays.

The examples use conceptual JSON close to the `PROJECT_RUNTIME_API_DRAFT.md` shape. Field names may still change before schema v1 ships.

## Rules illustrated by all examples

- project JSON is data, never executable code;
- stable IDs, not display labels, link records;
- renderer-native object/datablock names never appear;
- large numerical histories live in referenced artifacts;
- solver selection intent is distinct from captured execution provenance;
- presentation variants do not invalidate numerical results;
- missing plugins are requirements/diagnostics, never auto-installed;
- environment fingerprints come from existing `ScientificEnvironmentSnapshot`/artifact infrastructure.

## Example A — Minimal Maxwell Study

Conceptual project:

```json
{
  "schema": "spectra.project",
  "version": 1,
  "metadata": {
    "project_id": "project.maxwell.demo",
    "title": "Maxwell Wave Demo",
    "description": "A source-free electromagnetic wave reference study",
    "tags": ["electromagnetism", "demo"]
  },
  "models": [
    {
      "model_id": "model.maxwell.primary",
      "semantic_type": "physics.maxwell.problem3d",
      "payload_schema": "physics.maxwell.problem3d.v1",
      "payload": {
        "boundary": "periodic",
        "duration": 1.0,
        "requested_steps": 120
      },
      "resource_ids": []
    }
  ],
  "solver_selections": [
    {
      "role": "ode.first_order",
      "policy_name": "project.default",
      "implementation_id": null,
      "requirements": {
        "minimum_order": 4,
        "allow_reference": true
      }
    }
  ],
  "results": [
    {
      "result_id": "result.maxwell.run_001",
      "model_id": "model.maxwell.primary",
      "artifact_uri": "artifacts/result.maxwell.run_001/manifest.json",
      "artifact_schema": "spectra.result.maxwell3d",
      "environment_fingerprint": "<sha256-from-runtime>",
      "model_fingerprint": "<model-fingerprint>",
      "status": "ready"
    }
  ],
  "views": [
    {
      "view_id": "view.maxwell.eb_vectors",
      "source_result_id": "result.maxwell.run_001",
      "view_type": "physics.maxwell.eb_vector_field3d",
      "parameters": {
        "display_stride": 2
      }
    }
  ],
  "presentations": [
    {
      "presentation_id": "presentation.maxwell.analysis",
      "view_id": "view.maxwell.eb_vectors",
      "preset": "analysis",
      "intent_payload": {}
    },
    {
      "presentation_id": "presentation.maxwell.cinematic",
      "view_id": "view.maxwell.eb_vectors",
      "preset": "cinematic",
      "intent_payload": {
        "annotations": {
          "title": "Electromagnetic Wave"
        }
      }
    }
  ],
  "requirements": [
    {
      "capability": "physics.maxwell.solve3d",
      "min_version": 1,
      "plugin_id": null,
      "plugin_version": null
    }
  ]
}
```

Important behavior:

```text
analysis -> cinematic presentation switch
```

must not stale `result.maxwell.run_001`.

Changing Maxwell initial conditions does stale it.

## Example B — Parameter Sweep With Durable Experiment Artifact

```json
{
  "schema": "spectra.project",
  "version": 1,
  "metadata": {
    "project_id": "project.heat.sweep",
    "title": "Thermal Conductivity Sweep",
    "description": "Compare peak temperature across conductivity values",
    "tags": ["thermal", "experiment"]
  },
  "models": [
    {
      "model_id": "model.heat.base",
      "semantic_type": "physics.heat.problem3d",
      "payload_schema": "physics.heat.problem3d.v1",
      "payload": {
        "duration": 5.0,
        "boundary": "fixed"
      },
      "resource_ids": []
    }
  ],
  "experiments": [
    {
      "experiment_id": "experiment.heat.conductivity",
      "artifact_uri": "artifacts/experiment.heat.conductivity.json",
      "artifact_schema": "spectra.experiment",
      "artifact_version": 1
    }
  ],
  "views": [
    {
      "view_id": "view.heat.peak_vs_conductivity",
      "source_experiment_id": "experiment.heat.conductivity",
      "view_type": "experiments.metric_series2d",
      "parameters": {
        "x_parameter": "thermal_conductivity",
        "metric": "peak_temperature"
      }
    }
  ],
  "presentations": [
    {
      "presentation_id": "presentation.heat.publication",
      "view_id": "view.heat.peak_vs_conductivity",
      "preset": "publication",
      "intent_payload": {}
    }
  ],
  "requirements": []
}
```

The referenced experiment artifact should reuse the implemented `ExperimentArtifact` contract and contain:

- axes;
- cases;
- metric definitions;
- per-case numerical run traces where tracked;
- `ScientificEnvironmentSnapshot`;
- environment fingerprint.

Project v1 must not invent a second experiment provenance format.

## Example C — Plugin-dependent Geometric Optics Project

```json
{
  "schema": "spectra.project",
  "version": 1,
  "metadata": {
    "project_id": "project.optics.rays",
    "title": "Lens Ray Study",
    "description": "Third-party optics plugin project",
    "tags": ["optics", "plugin"]
  },
  "models": [
    {
      "model_id": "model.optics.primary",
      "semantic_type": "optics.ray_problem",
      "payload_schema": "spectra_optics.ray_problem.v1",
      "payload": {
        "wavelength_nm": 532.0,
        "ray_count": 25
      },
      "resource_ids": ["resource.optics.lens_profile"]
    }
  ],
  "requirements": [
    {
      "capability": "optics.raytrace.solve",
      "min_version": 1,
      "plugin_id": "org.example.spectra_optics",
      "plugin_version": ">=1.0,<2.0"
    }
  ],
  "resources": [
    {
      "resource_id": "resource.optics.lens_profile",
      "uri": "resources/lens_profile.json",
      "checksum": "sha256:<checksum>",
      "media_type": "application/json"
    }
  ],
  "results": [],
  "views": [],
  "presentations": []
}
```

Open behavior when plugin is missing:

- parse succeeds because project is data;
- no plugin installation/enable occurs;
- environment validation reports `missing_required_plugin`;
- application may allow metadata/resource inspection;
- solving or constructing plugin semantic objects remains unavailable until user/app resolves the plugin requirement.

## Example D — Same Scientific Result, Multiple Presentation Variants

This is a core product invariant.

```json
{
  "result_id": "result.thermoelastic.run_001",
  "views": [
    {
      "view_id": "view.solid.deformation",
      "source_result_id": "result.thermoelastic.run_001",
      "view_type": "physics.elastodynamics.deformed_grid3d",
      "parameters": {"displacement_scale": 25.0}
    }
  ],
  "presentations": [
    {
      "presentation_id": "presentation.solid.analysis",
      "view_id": "view.solid.deformation",
      "preset": "analysis",
      "intent_payload": {}
    },
    {
      "presentation_id": "presentation.solid.publication",
      "view_id": "view.solid.deformation",
      "preset": "publication",
      "intent_payload": {}
    },
    {
      "presentation_id": "presentation.solid.cinematic",
      "view_id": "view.solid.deformation",
      "preset": "cinematic",
      "intent_payload": {
        "annotations": {"title": "Thermal Deformation"}
      }
    }
  ]
}
```

All three presentation records point at the same view/result. No solver rerun is implied.

## Example E — Stale Result After Model Change

Initial relationship:

```text
model.heat.base revision A
  -> result.heat.run_001 fingerprint A
```

User changes conductivity/source/boundary condition, producing model revision B.

Project runtime should mark:

```text
result.heat.run_001 = stale
view(s) from result = stale/using-stale-result
presentation(s) = stale/using-stale-view
```

but preserve the old artifact for comparison/history unless application policy removes it.

A camera or presentation color-scale change must not stale the numerical result.

## Example F — Remote Result Arrives Late

```text
revision A -> remote job J1
user edits -> revision B
J1 returns result for A
```

Attach rule:

- artifact can be stored/history-listed;
- it must not become the active result for model revision B automatically;
- source model fingerprint/revision mismatch must be diagnosed.

## Model payload safety

Forbidden in project JSON:

```text
pickled Python callables
Python module/class imports to execute
raw native pointers
Blender datablock references
CUDA device pointers
arbitrary plugin object blobs
```

Allowed semantic payloads require an explicit schema/serializer owned by the domain/plugin contract.

## Canonical ordering

Deterministic serialization should choose a clear ordering policy:

- preserve meaningful user list order where semantics/UI rely on it;
- sort map/object keys in canonical JSON output;
- stable IDs must make references independent of list index.

Fingerprinting should use canonical payloads, not pretty-print whitespace.

## Project v1 fixture files after implementation

Once `spectra.project` lands, turn examples into checked fixtures such as:

```text
tests/fixtures/projects/minimal_maxwell_v1.json
tests/fixtures/projects/experiment_heat_v1.json
tests/fixtures/projects/plugin_optics_missing_v1.json
tests/fixtures/projects/multi_presentation_v1.json
```

Required tests:

- parse/round-trip;
- deterministic canonical serialization;
- duplicate IDs rejected;
- broken references rejected;
- missing plugin diagnosed without execution;
- presentation-only edit preserves result validity;
- model edit stales dependent results;
- old experiment/environment artifacts preserved exactly.

## Success criterion

Project v1 should persist scientific intent, references, environment requirements, results/artifacts, views, and presentation variants without becoming a renderer file, an executable plugin container, or a second provenance system.