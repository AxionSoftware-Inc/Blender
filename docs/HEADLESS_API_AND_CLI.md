# Spectra Science — Headless API and CLI Contract

This document defines how Spectra should support scripting, automation, batch execution, CI-like validation, remote workers, and non-Blender product surfaces through a stable headless contract.

The headless path must exercise the same semantic/project/numerical engine as interactive clients.

## Goal

A project/study should be runnable without Blender or a graphical UI:

```text
project/model input
    -> validate
    -> solve
    -> inspect results/diagnostics
    -> compile view
    -> apply presentation intent
    -> export Scene/data/report artifacts
```

Rendering to final pixels may require a renderer, but scientific execution must not.

## Python API layers

A future curated API should conceptually separate:

```text
low-level semantic/domain APIs
project/study orchestration
solver/experiment APIs
view/presentation APIs
renderer/export adapters
```

A typical high-level script should not need to manipulate `DomainRegistry` manually unless doing advanced extension work.

Conceptual usage:

```python
project = load_project("study.spectra")
report = project.validate()
result = project.solve()
scene = project.compile_view("temperature_slice")
presented = project.present(scene, preset="publication")
export_scene(presented, "scene.json")
```

Exact runtime API will be implemented later; this file defines orchestration expectations.

## CLI design principles

CLI commands should map to semantic/product operations, not renderer implementation details.

Recommended command families:

```text
spectra project ...
spectra validate ...
spectra solve ...
spectra experiment ...
spectra view ...
spectra present ...
spectra export ...
spectra inspect ...
spectra plugins ...
spectra doctor ...
```

## `spectra validate`

Purpose:

- parse project/model;
- validate semantics/units/resources;
- resolve required capabilities/plugins;
- check solver compatibility without running expensive solve.

Output modes:

```text
human-readable
JSON structured diagnostics
```

Exit code should be nonzero for validation errors, not warnings.

## `spectra solve`

Conceptual options:

```text
project path
study/model id
solver policy
execution target
precision
steps/tolerance overrides
output/result destination
```

CLI overrides should be explicit and recorded in provenance.

Do not silently mutate the saved project unless `--save`/equivalent is requested.

## `spectra experiment`

Subcommands may include:

```text
run
compare-solvers
convergence
sensitivity
uncertainty
calibrate
pareto
```

Outputs should use durable experiment artifact formats where appropriate.

## `spectra view`

Compile a semantic result/view into renderer-neutral Scene.

Useful for:

- debugging;
- headless tests;
- WebGPU/remote clients;
- renderer handoff.

Conceptual:

```text
spectra view result.something --view pressure_slice --out scene.json
```

## `spectra present`

Apply presentation policy to a base Scene/view without recomputing science.

Examples:

```text
--preset publication
--preset cinematic
--camera orthographic_analysis
--annotations important_only
```

Renderer-specific tuning belongs to renderer/export commands, not the generic presentation command.

## `spectra export`

Potential targets:

```text
scene-json
experiment-json
project-package
csv/hdf5/vtk data
image/video via configured renderer
blend via Blender backend
report bundle
```

Export command should state when it requires an external renderer/application.

## `spectra inspect`

Inspect without executing:

```text
project metadata
models/studies
required capabilities/plugins
results
provenance
environment fingerprint
Scene contents
presentation variants
resource references
```

This is important for safe project inspection and debugging.

## `spectra plugins`

Future plugin operations:

```text
list
describe
enable/disable
check compatibility
show capabilities
```

Installation may be delegated to the Python/package/product environment rather than hidden inside Spectra CLI.

Do not auto-install arbitrary project-requested plugins.

## `spectra doctor`

Environment diagnostics may report:

```text
Spectra version
Python version
available built-in domains
plugin compatibility
native providers
GPU/runtime availability
Blender executable/version if configured
remote worker connectivity
```

This command should not modify the environment by default.

## Structured output

Automation needs stable machine-readable results.

Many commands should support:

```text
--json
```

with schema-versioned output for important contracts.

Structured output should include diagnostic codes/categories rather than requiring log scraping.

## Exit codes

Conceptual categories:

```text
0 success
validation failure
capability/plugin failure
numerical failure
resource/input failure
backend/export failure
usage/configuration error
```

Exact numeric mapping can be defined later.

Warnings should normally retain exit code 0 unless a strict policy promotes them.

## Progress output

Long-running commands may emit progress to stderr/event stream while preserving clean JSON/result output on stdout/file.

For machine automation, structured event output may later be useful.

Do not mix arbitrary `print()` logs into a JSON result stream.

## Reproducibility

A headless solve should be able to emit:

```text
result artifact
numerical provenance
environment snapshot
input resource hashes where known
project/model revision
```

This makes CLI/HPC runs first-class scientific executions, not second-class scripts.

## Local/remote symmetry

Conceptual:

```text
spectra solve project --target local
spectra solve project --target worker:gpu-cluster
```

should differ in execution target/provider, not scientific project type.

The resulting result semantics should remain compatible.

## Renderer independence

Plain commands:

```text
validate
solve
experiment
inspect
view
```

must not require Blender.

A Blender export command may invoke/configure Blender explicitly.

This preserves the engine's renderer independence.

## Batch directories

A convenience batch runner may process multiple projects/studies, but should preserve independent result/provenance identity.

Do not treat directory order as semantic case identity.

## Scripting hooks

Prefer stable Python APIs and explicit project commands over arbitrary shell hooks embedded in project files.

A trusted expert may write normal Python scripts importing Spectra, but those scripts are executable code outside the safe project document contract.

## Environment variables/config

Product configuration may use environment/config files for:

- cache location;
- remote endpoints;
- renderer executable paths;
- plugin policy;
- default execution target.

Scientific parameters should remain in project/model semantics, not hidden environment variables.

## Blender integration

A Blender helper command may eventually:

```text
spectra export project --renderer blender --out result.blend
```

or launch Blender background mode with a generated/serialized Scene.

The scientific computation need not happen inside Blender unless explicitly configured.

## CI/developer use

Headless API is useful for:

- canonical reference cases;
- plugin compatibility checks;
- schema migration fixtures;
- numerical provider parity;
- export validation;
- docs examples.

GitHub Actions is intentionally absent in the current repository policy, but headless tooling should remain CI-capable for future environments if policy changes.

## Security

CLI must treat project/resource files as untrusted data.

Do not:

- execute scripts embedded in projects;
- auto-install plugins;
- expose secrets in provenance/JSON output;
- fetch arbitrary remote resources without policy.

See `TRUST_AND_SECURITY_MODEL.md`.

## Success criterion

Anything scientifically meaningful that can be solved/inspected in an interactive Spectra product should also be runnable headlessly through the same engine contracts, enabling reproducible batch, remote, and automated workflows without depending on Blender UI state.
