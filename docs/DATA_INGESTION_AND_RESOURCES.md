# Spectra Science — Data Ingestion and External Resource Model

This document defines how Spectra should ingest scientific data and large external resources without turning file formats into scientific semantics or renderer state.

## Goal

Spectra should accept data from many ecosystems while keeping one internal semantic model.

Conceptual flow:

```text
external file / stream / database / service
        ↓
format adapter
        ↓
validated neutral data resource
        ↓
scientific semantic adapter
        ↓
field / mesh / trajectory / dataset / project model
        ↓
computation / visualization / experiments
```

File-format code should not leak into physics or presentation domains.

## Resource categories

Useful categories include:

```text
tabular data
structured grids
unstructured meshes
point clouds
vector/scalar fields
time series
images/volumes
geometry/CAD references
experiment datasets
solver result archives
project attachments
```

A resource may be embedded, local, remote, or generated.

## External resource identity

A project should refer to resources by logical IDs rather than hardcoding renderer/native paths throughout semantic objects.

Conceptual metadata:

```text
resource_id
uri/path
media/data type
format
size
content hash if known
required/optional
unit metadata
coordinate/frame metadata
time metadata
```

The same logical resource may later be relocated while preserving project references.

## Format adapters

Format adapters should be narrow translation layers.

Examples of possible future adapters:

```text
CSV/TSV
JSON
NumPy arrays
VTK/VTU/VTI
HDF5
NetCDF
PLY/OBJ/glTF for geometry context
medical/scientific volume formats where appropriate
custom laboratory exports
```

Support for a format is not equivalent to scientific understanding of every field stored in that format.

An adapter should expose metadata and raw structured values; a subject/domain adapter assigns scientific meaning.

## Tabular data

A table should preserve:

- column names;
- units where available;
- missing values;
- categorical vs numeric type;
- time/index semantics;
- uncertainty/error columns where declared.

Do not infer units from column names unless a user/import profile explicitly enables a convention.

## Grid data

Structured grid import should preserve:

```text
shape
axis coordinates/spacing
origin
coordinate frame
scalar/vector component layout
units
time dimension if present
```

Do not silently reorder axes merely to match a renderer convention.

If conversion is necessary, record it explicitly.

## Unstructured meshes

A future mesh resource should distinguish:

- node coordinates;
- element/connectivity topology;
- cell/point fields;
- material/region tags;
- boundary groups;
- coordinate system;
- units.

Scientific mesh semantics should remain independent from Blender mesh topology choices.

A Blender mesh may visualize an imported scientific mesh, but Blender is not the canonical mesh data store.

## Point clouds

Imported point clouds may carry:

```text
positions
scalar attributes
vector attributes
categories
weights
uncertainties
IDs
```

Renderer display sampling may decimate a point cloud without changing the source resource.

## Time-series data

Time metadata must be explicit:

```text
time values
unit
calendar/reference if relevant
sampling regular/irregular
missing intervals
```

Do not assume array index equals seconds.

Time-series resources can be adapted into Spectra Timeline/field history only after time semantics are known.

## Units

Imported data should preserve original units when available and convert to canonical/internal units explicitly when scientific domains require it.

A resource adapter may report:

```text
value array
unit metadata
```

A domain adapter then validates the unit dimension.

Do not bury unit conversion inside renderer import code.

## Coordinate systems

External data may use:

- local Cartesian coordinates;
- geographic coordinates;
- medical/image voxel coordinates;
- CAD coordinate systems;
- simulation-native frames.

Coordinate-frame metadata should be part of resource/semantic adaptation.

Renderer conversion occurs after scientific coordinates are resolved.

## Data validation

Import validation should cover:

```text
file/schema readability
shape consistency
finite/non-finite policy
unit metadata
coordinate metadata
connectivity bounds
component count
monotonic time where required
missing-value policy
```

Invalid data should generate diagnostics from `DIAGNOSTICS_AND_ERRORS.md` rather than vague import failures.

## Missing data

Missing/invalid values should be represented explicitly.

Possible policies:

```text
reject
mask
interpolate with explicit method
fill with declared value
exclude from analysis
```

Do not silently replace NaN with zero.

## Lazy loading

Large datasets should support lazy/chunked loading eventually.

Conceptual resource lifecycle:

```text
metadata available
    ↓
requested chunk/field/time window
    ↓
load/materialize
    ↓
cache/release
```

Scientific semantics should be able to reference a resource view without forcing every byte into memory at project-open time.

## Streaming

Future laboratory/live simulation integrations may produce streams.

A streaming resource contract should distinguish:

- append-only observations;
- mutable latest state;
- timestamp/order guarantees;
- reconnect behavior;
- provenance/source identity.

Streaming should feed semantic data adapters, not mutate Blender objects directly.

## Resource caching

Caches may include:

```text
parsed metadata
converted SI arrays
spatial index
mesh adjacency
render-display decimation
GPU/native buffer
```

Each cache must be invalidatable independently from source data.

A presentation decimation cache should not be reused as solver input unless explicitly equivalent.

## Content hashes

Where practical, large external resources should have content hashes for:

- reproducibility;
- cache invalidation;
- remote worker transfer;
- stale-resource detection.

Hashing very large resources may be optional/deferred, but absence should be explicit.

## Project portability

A future project format may support:

```text
external references
project-relative references
embedded small resources
project archive bundles
```

Large simulation datasets should not automatically be embedded into JSON.

## Remote resources

Remote URI support should be explicit and security-aware.

A project should not automatically fetch arbitrary remote resources merely because a serialized document contains a URL.

The product layer should enforce trust/auth/policy.

## Import profiles

Repeated domain-specific imports may use explicit profiles.

Example:

```text
CSV columns:
  x -> position.x [mm]
  y -> position.y [mm]
  z -> position.z [mm]
  T -> temperature [degC]
```

Profiles are project/import configuration, not hardcoded format assumptions.

## Scientific semantic adapters

Examples:

```text
structured grid + scalar values + K
    -> ScalarField3D / heat initial state

particle CSV + time
    -> trajectory collection

VTK vector field
    -> VectorField3D view/input

experiment table
    -> Dataset / calibration observations
```

The adapter validates scientific meaning after raw format parsing.

## Export

Data export should mirror the same separation:

```text
semantic result
    ↓
export adapter
    ↓
file/resource format
```

Exporting a field to VTK/CSV/HDF5 should not require Blender.

Presentation export (image/video) is a separate renderer path.

## Provenance

Imported resources should be traceable when scientific reproducibility matters:

```text
resource id
source path/URI
content hash if known
import adapter/version
unit/frame conversion
selected fields/time range
```

This metadata can become part of future project/result provenance.

## Security

Importers must treat external files as untrusted data.

Avoid:

- executing code embedded in data files;
- unsafe object deserialization;
- arbitrary plugin activation from file contents;
- automatic network access from untrusted project/resource metadata.

## Success criterion

Spectra should be able to ingest the same scientific dataset for numerical analysis, experiments, Blender visualization, and future WebGPU presentation through one validated semantic resource pipeline rather than separate renderer-specific import systems.
