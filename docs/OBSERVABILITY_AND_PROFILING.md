# Spectra Science — Observability and Profiling Architecture

This document defines how Spectra should expose timing, resource, cache, solver, renderer, and workflow observability without polluting scientific semantics with logging/performance code.

## Goal

When a workflow is slow or fails, developers and advanced users should be able to answer:

```text
Was time spent loading data?
Building the semantic model?
Packing buffers?
Solving numerically?
Moving data to/from GPU?
Computing derived fields?
Compiling the Scene?
Applying presentation?
Updating Blender/WebGPU?
Rendering final pixels?
Waiting for a remote worker?
```

Without this separation, optimization becomes guesswork.

## Observability layers

Useful layers:

```text
project/workflow
resource/data
capability/domain
numerical execution
experiment
cache/storage
view/Scene
presentation
renderer/backend
remote worker
export
```

## Event model

A future generic event may contain:

```text
event name
category
start/end or duration
project/study/result id
operation id
component/provider/backend
context tags
resource counts/sizes
status
```

Events should be optional instrumentation, not scientific state.

## Timing spans

Recommended high-level spans:

```text
project.validate
resource.load
model.build
solver.select
solver.pack
solver.execute
solver.transfer_h2d
solver.transfer_d2h
solver.materialize
derived.compute
view.compile
presentation.compose
backend.create
backend.apply
backend.destroy
render.frame
render.final
artifact.serialize
artifact.write
remote.queue
remote.stage
remote.execute
remote.download
```

Nested spans can show a complete end-to-end trace.

## Numerical metrics

Useful metrics:

```text
state size
grid shape
requested steps
accepted steps
rejected adaptive steps if available
iterations
residual
solver method/implementation
precision
batch size
kernel time
transfer time
```

Numerical correctness metrics such as energy drift or divergence residual remain scientific diagnostics, but can be linked to performance traces.

## Renderer metrics

Useful backend metrics:

```text
Spectra primitive count
native object count
mesh/curve/material/light/camera count
created/updated/rebuilt resource count
bytes/vertices/instances updated when available
apply time
frame scrub/update time
cleanup delta
```

For dense primitives report both semantic sample count and native object count.

Example:

```text
VectorGlyphSet samples: 10000
Blender objects: 1
```

## Presentation metrics

Useful metrics:

```text
presentation resource count
legend/annotation count
color-scale build time
camera fit time
label layout time
presentation composition time
preset-switch diff create/update/delete counts
```

Presentation metrics must be separate from base Scene compilation.

## Cache metrics

Track:

```text
hit/miss
cache class
bytes
load/materialization time
evictions
stale rejects
```

A repeated slow view may be caused by cache misses rather than renderer performance.

## Resource/data metrics

Examples:

```text
resource bytes read
parse time
conversion time
unit/frame adaptation time
chunk count
network download time
```

Do not attribute network/resource latency to solver performance.

## Experiment metrics

Track orchestration separately from scientific metrics:

```text
case count
batch count
successful/failed cases
worker utilization
per-case solve time distribution
metric extraction time
artifact assembly time
```

This helps tune batch size and provider selection.

## Remote metrics

Separate:

```text
queue wait
staging/upload
worker startup
execution
result finalize
result download
```

A remote GPU may have a fast kernel and poor total latency.

## Memory metrics

Where available track:

```text
host RSS/heap approximation
native buffer bytes
GPU allocated bytes
result history bytes
Scene array bytes
renderer-native bytes
cache bytes
```

Avoid claiming exact memory if the runtime cannot measure it accurately; label estimates appropriately.

## Copy counts

Future high-performance work should instrument copies across boundaries:

```text
semantic -> packed host
host -> native
host -> device
device -> host
result -> Scene
Scene -> renderer
```

Reducing redundant copies may matter more than optimizing one arithmetic kernel.

## Profiling modes

Suggested levels:

### Off

Minimal overhead for normal users.

### Basic

High-level operation durations and selected providers.

### Detailed

Nested spans, counts, cache/resource metrics.

### Development/native

Backend/provider-specific detailed instrumentation.

Do not force heavy profiler overhead in ordinary scientific runs.

## Structured trace export

Future profiling may export a machine-readable trace suitable for:

- internal inspector;
- Chrome trace-like viewers;
- JSON analysis;
- benchmark reports.

The exact format can be chosen later.

## Correlation IDs

Useful identities:

```text
project revision
solve attempt id
result id
experiment case id
renderer session id
remote job id
```

This allows a trace from user command through remote solve to final render.

## Logging vs metrics vs diagnostics

### Diagnostics

Explain correctness/failure/warnings.

### Metrics/traces

Explain timing/resource behavior.

### Logs

Provide developer narrative/details.

Do not use one system for all three.

## User-facing performance inspector

An advanced UI could display:

```text
Solve: 2.41 s
  pack: 40 ms
  GPU transfer: 75 ms
  kernel: 2.12 s
  materialize: 175 ms

View compile: 120 ms
Presentation: 18 ms
Blender update: 96 ms
```

This is far more actionable than "Total 2.64 s".

## Solver policy feedback

Performance traces can inform future policy recommendations.

Example:

```text
For state size < 200, reference CPU was faster than GPU due to transfer overhead.
```

Policy adaptation must remain explicit/deterministic enough for provenance; do not silently change solver selection based on opaque historical heuristics without recording it.

## Benchmark integration

Canonical benchmark runs should use observability spans to report the breakdown required by `PERFORMANCE_BUDGETS.md`.

This prevents different providers/backends from publishing incomparable numbers.

## Regression detection

Dedicated benchmark tooling may compare:

```text
median timing
memory
copy counts
native object counts
cache behavior
```

against recorded baselines with environment metadata.

Do not put strict wall-clock assertions into ordinary unit tests.

## Native backend instrumentation

A native provider may expose internal counters/timings through a provider diagnostics interface, but scientific domains should not import those native APIs.

The numerical execution layer can normalize provider observability into generic events/metrics.

## Blender instrumentation

Useful future Blender spans:

```text
material creation/update
mesh foreach_set/bulk update
curve update
Geometry Nodes attribute update
camera/light update
depsgraph update
cleanup
```

Keep instrumentation optional to avoid perturbing normal playback excessively.

## WebGPU instrumentation

Future WebGPU backend may track:

- buffer upload bytes/time;
- pipeline creation/cache;
- draw/dispatch counts;
- GPU timestamp queries where supported;
- frame time.

Again, renderer-specific metrics feed generic profiling, not scientific semantics.

## Privacy

Telemetry sent outside the local process is a separate product decision.

Default engine observability can remain local/in-memory/file-based.

Do not transmit project names, scientific parameters, resource paths, or proprietary datasets without explicit product/privacy policy.

## Success criterion

When Spectra performance changes, developers can identify the responsible layer and optimize it behind stable scientific contracts instead of guessing whether the bottleneck is the solver, data movement, Scene compilation, presentation, Blender, cache behavior, or remote infrastructure.
