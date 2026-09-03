# Spectra Science — Performance Budgets and Measurement Boundaries

This document defines how Spectra should reason about performance across numerical execution, Scene compilation, presentation, renderer updates, project workflows, and remote execution.

The purpose is not to promise universal numbers prematurely. The purpose is to prevent one subsystem from hiding costs inside another and to establish workload classes that future optimization can target.

## Rule 1 — measure layers separately

Never report one ambiguous "simulation time" when the workflow contains multiple costs.

Measure separately:

```text
input/resource load
semantic/model construction
numerical setup/packing
numerical kernel/solve
host-device transfer
result materialization
derived field/diagnostic computation
view/Scene compilation
presentation composition
renderer native create
renderer incremental update
final render/export
serialization/storage
```

Only combine them when reporting a user-facing end-to-end workflow, and still keep the breakdown available.

## Rule 2 — latency vs throughput

Different workflows optimize different metrics.

### Interactive latency

Examples:

- change presentation preset;
- move camera;
- scrub a solved timeline;
- change display sampling;
- inspect an experiment case.

Goal: minimize response delay.

### Numerical latency

Examples:

- solve one particle trajectory;
- run one reference PDE;
- calculate one small field.

### Throughput

Examples:

- thousands of parameter-sweep cases;
- batched ODE systems;
- large renderer point/vector updates;
- remote/HPC jobs.

A GPU may improve throughput while losing on small-problem latency due to transfer/setup cost.

## Workload classes

Use explicit classes rather than one universal benchmark.

### XS — micro/interactive

Examples:

```text
state size < ~100
small curves/fields
single trajectory
small analysis views
```

Reference Python may be sufficient.

### S — small scientific problem

Examples:

```text
small 1D/2D PDE
16^3 grid
1k visual samples
```

Native CPU may reduce latency.

### M — medium scientific problem

Examples:

```text
32^3–64^3 grid
10k–100k visual samples
hundreds/thousands of sweep cases
```

Native/vectorized/batched execution becomes important.

### L — large

Examples:

```text
128^3+ grid
100k–1M visual samples
large experiment batches
```

GPU/device-resident pipelines and renderer LOD become important.

### XL/HPC

Problems beyond local workstation policy/resource budgets.

Target remote/HPC execution rather than forcing every client to run them locally.

Exact thresholds will evolve by algorithm/device; classes describe product behavior, not rigid scientific limits.

## Numerical budgets

### Reference solvers

Priorities:

1. correctness;
2. deterministic behavior;
3. analytical/reference validation;
4. acceptable developer/test latency.

Do not distort simple reference code solely to chase production performance.

### Native CPU provider

First target:

- clear speedup on M-size first-order ODE/state workloads;
- low enough setup overhead to remain useful on S workloads;
- parity with reference semantics;
- no high-level domain changes.

### GPU provider

Promotion should require a documented crossover point.

Report:

```text
packing
H2D transfer
kernel
D2H/materialization
end-to-end
```

A kernel-only benchmark is insufficient for product selection policy.

## Renderer budgets

### Object count

Dense data object count should stay approximately constant with sample count.

Target principle:

```text
N particles -> O(1) renderer objects
N vector glyphs -> O(1) renderer objects
```

Native sub-elements/instances may scale with N, but high-level object/datablock explosion is prohibited.

### Incremental update

Topology-stable changes should update buffers/attributes in place.

Current verified Blender reference point from one machine:

```text
10k PointCloud update ~96–97 ms
```

This is a baseline to improve, not a target to preserve.

Future premium/Geometry Nodes/WebGPU work should track improvement without sacrificing identity/cleanup correctness.

### Preset switch

Changing presentation preset should be substantially cheaper than recomputing the scientific result.

A preset switch should normally update presentation resources/materials/camera rather than scientific geometry.

## Scene compilation budgets

Scene compilation should scale with display representation, not hidden solver-grid size where display sampling is explicitly reduced.

Example:

```text
256^3 solution
20x20x12 displayed vectors
```

Vector Scene compilation cost should scale with the chosen display sample count, while derived field extraction cost is reported separately.

## Presentation budgets

Presentation composition should remain lightweight compared with solving/rendering.

Potential expensive operations such as:

- collision-aware label layout;
- large legend/annotation generation;
- complex multi-panel composition;

should be measurable separately.

Cinematic post-processing cost belongs to renderer/final render, not generic presentation composition.

## Project workflow budgets

Important user-facing actions:

### Open project

Separate:

```text
metadata parse
resource metadata inspection
cache discovery
actual large resource materialization
renderer-session recreation
```

Opening a project should not automatically load every huge dataset into RAM/VRAM unless needed.

### Change physical parameter

May invalidate solve; UI should update project state immediately even if recompute is deferred.

### Change view

Should reuse numerical result.

### Change presentation

Should reuse numerical result and usually base Scene where possible.

### Change renderer

Should reuse semantic result/Scene.

## Remote execution budgets

Track:

```text
queue delay
resource staging/upload
worker startup
solve
result upload/download
materialization
```

Remote GPU can lose to local CPU for small jobs due to queue/transfer latency.

Scheduling policy should consider total latency/cost, not theoretical GPU FLOPS alone.

## Memory budgets

Track separately:

```text
semantic object memory
host execution buffers
solver history
cache memory
device memory
renderer-native memory
presentation resources
```

Avoid retaining multiple full copies of the same large field accidentally across:

```text
Python tuples
NumPy/native buffer
GPU buffer
Scene arrays
renderer mesh
```

The future buffer/resource model should make copies/ownership explicit.

## History/storage budgets

Time-dependent simulations can multiply memory by number of stored timesteps.

Policies may eventually support:

- store every accepted step;
- fixed output sampling independent of adaptive internal steps;
- checkpoint-only storage;
- streamed/chunked history;
- derived metrics without retaining full state.

Do not force every adaptive solver to store all internal steps forever merely because the reference solution type currently carries a full history.

## Experiment budgets

Large sweeps require:

```text
case scheduling
batch size
failure isolation
metric extraction
result summary storage
optional raw-result retention
```

Not every case needs its full high-dimensional field persisted if only a metric is required.

The experiment definition should distinguish:

```text
metrics to retain
raw outputs to retain
trace/provenance to retain
```

## Performance regression policy

When a hot path is intentionally optimized, record a representative baseline and workload.

Regression checks should allow environment noise and should not turn ordinary correctness tests into flaky microbenchmarks.

Use dedicated benchmark runs for timing-sensitive promotion decisions.

## Performance vs correctness

Never trade away:

- unit correctness;
- boundary semantics;
- solver precision contract;
- provenance;
- deterministic IDs/ownership;
- resource cleanup;

for an unqualified speedup.

A faster result with silently different numerical semantics is a different provider/model, not an optimization.

## Performance vs visual quality

Display LOD may reduce:

- glyph count;
- label density;
- surface display subdivision;
- post-processing quality;

but must not silently reduce scientific solver resolution.

Presentation quality policies should expose these tradeoffs explicitly.

## Benchmark reporting template

For a meaningful performance result report:

```text
commit
machine/OS
CPU
GPU/driver/runtime if relevant
Blender/renderer version if relevant
provider/precision
reference case/workload size
setup time
kernel/solve time
transfer time
materialization time
Scene compile time
renderer update time
memory/VRAM when available
result error/parity metric
```

## Initial optimization priorities after validation

Recommended order:

1. preserve solver-role correctness/provenance;
2. implement native CPU first-order provider;
3. establish real buffer/copy measurements;
4. improve Blender dense update path/presentation batching;
5. GPU batched ODE/grid operators;
6. reduce host-device round trips;
7. large-data Scene/renderer LOD;
8. remote/HPC scheduling for workloads beyond local budgets.

## Success criterion

Spectra performance should improve by replacing execution/storage/rendering mechanisms behind stable semantic contracts, while measurements make it clear whether time is spent computing science, moving data, compiling views, updating a renderer, or producing final pixels.
