# Spectra Science — Persistent Schema Versioning and Migration Policy

This document defines how Spectra should evolve serialized scientific/project/presentation artifacts while preserving historical interpretability.

Persistent data outlives Python objects and renderer sessions, so schema compatibility must be deliberate.

## Persistent formats

Current or planned persistent families include:

```text
spectra.scene
spectra.experiment
spectra.project
presentation configuration
plugin/project requirements
future numerical/reference datasets
```

Each family should have an explicit schema identifier and version independent from the Python package version.

## Schema identity

A serialized document should identify at least:

```text
schema
version
```

Example:

```json
{
  "schema": "spectra.scene",
  "version": 4
}
```

Do not infer schema version from package version or filename extension alone.

## Compatibility goals

Preferred default policy:

- current writer emits the newest supported schema;
- current reader can read a documented range of older schemas;
- older readers are not expected to understand unknown future schemas;
- migrations are explicit and testable;
- scientific meaning is never guessed silently.

## Version bump rules

### No schema bump

Internal implementation changes that do not alter serialized structure/meaning.

### Compatible additive change

If old readers are explicitly designed to ignore unknown fields safely, an additive field may not require a major migration boundary. However, the schema contract must define this behavior.

When in doubt, bump the schema version rather than relying on accidental tolerance.

### Schema version bump

Required when:

- required field is added;
- field meaning changes;
- representation shape changes;
- enum/value semantics change;
- units/coordinate meaning changes;
- references/ownership model changes;
- defaults would produce scientifically different interpretation.

## Reader-first compatibility

Migration logic should live near deserialization/format adapters, not be scattered through scientific domains.

Conceptual flow:

```text
serialized vN
   -> validate envelope
   -> migrate vN -> current semantic representation
   -> construct current objects
```

Avoid constructing half-old/half-new runtime objects.

## Scene schema

`spectra.scene` already demonstrates the intended model: current schema is v4 with backward readers for older versions.

Future Scene migrations must preserve:

- primitive semantics;
- coordinate meaning;
- material meaning;
- timeline interpretation;
- stable IDs where represented.

Do not use a migration to silently change a scientific coordinate convention.

## Experiment artifacts

Experiment artifacts should preserve:

```text
parameter axes
case ids
parameter values/units
metric values/units
failure records
environment snapshot/fingerprint
numerical run summaries where present
```

If numerical provenance representation expands, old artifacts should remain readable even if new fields are unavailable.

Unknown historical solver implementations should remain representable as identifiers/metadata; loading an old artifact should not require that solver to still be installed merely to inspect results.

## Project schema

Future `spectra.project` should separate durable source-of-truth from caches.

Recommended sections conceptually:

```text
project metadata
scientific model records
solver policies/requirements
experiment definitions/artifact references
view definitions
presentation variants
external resource references
cache descriptors
```

Cache formats may evolve more aggressively than durable semantic project records.

A project reader should be able to discard unsupported/stale caches and recompute them from durable source data where possible.

## Presentation schema

Presentation configuration should persist semantic policy identifiers rather than renderer-native settings.

Persist:

```text
preset id
camera policy
theme/color/legend policy
annotation policy
quality/display sampling policy
explicit overrides
```

Do not persist Blender node socket paths as the renderer-independent presentation source of truth.

Renderer-specific cached settings may live in optional backend sections with independent compatibility expectations.

## Units

Serialized physical values must preserve enough information to recover dimension and scale semantics.

If a schema stores values in canonical SI only, that rule must be explicit.

If it stores original user units, preserve:

```text
value
unit identity/symbol
dimension
scale/offset where needed
```

Never migrate units by treating a numeric value as unitless and assigning a new unit string.

## Coordinates and frames

Coordinate-system migrations are scientifically sensitive.

Any change involving:

- axis order;
- handedness;
- frame origin;
- basis;
- projection;
- renderer unit scale

must be explicit and tested with known points/vectors.

Renderer-native coordinate conventions should not leak into durable scientific schemas.

## IDs and references

Persistent IDs should remain stable enough to support:

- timeline targets;
- groups;
- presentation resources;
- project references;
- cache/reference links.

A migration that rewrites IDs must also rewrite every dependent reference transactionally.

## Unknown fields

Each schema should define whether unknown fields are:

- allowed and preserved/ignored;
- rejected;
- allowed only in extension namespaces.

For plugin extensibility, a namespaced extension section may be safer than arbitrary unknown top-level fields.

Conceptually:

```text
extensions: {
  "vendor.plugin": {...}
}
```

Extension payloads should declare their own version/compatibility where necessary.

## Unknown enum/policy values

Do not silently map an unknown future value to a random current default.

Possible behaviors:

- reject with clear unsupported-value diagnostic;
- preserve as opaque metadata if the document can still be inspected safely;
- use an explicit documented fallback only for non-scientific presentation effects.

Scientific semantics require stricter behavior than decorative presentation effects.

## Migration functions

Recommended pattern:

```text
migrate_v1_to_v2
migrate_v2_to_v3
migrate_v3_to_v4
```

or a direct normalized migration layer when simpler.

Requirements:

- deterministic;
- pure where practical;
- no network dependency;
- no renderer dependency for scientific/project formats;
- validated with historical fixtures.

## Historical fixtures

Keep small representative serialized fixtures for supported historical versions.

For every reader compatibility promise, test at least:

```text
old fixture -> current object
current object -> current format
semantic equivalence for important fields
```

Do not rely only on constructing fake old payloads in the current test code if real historical fixtures are available.

## Forward compatibility

An old Spectra version encountering a future schema should fail clearly:

> Unsupported `spectra.project` version 5; this build supports versions 1–3.

Do not attempt speculative parsing of unknown future scientific schema versions.

## Fingerprints and integrity

When an artifact includes a fingerprint/hash:

- define canonical serialization used for hashing;
- verify it on read when intended as integrity metadata;
- schema migration may necessarily produce a new fingerprint for the migrated representation;
- preserve original fingerprint as historical provenance if useful.

A fingerprint is not a digital signature unless cryptographic signing is explicitly implemented.

## External resources

Projects may reference large external datasets instead of embedding them.

Resource references should eventually support metadata such as:

```text
logical resource id
URI/path
content hash if known
size/type
required/optional
```

Migration must distinguish changing the reference representation from changing the scientific dataset itself.

## Cache invalidation

Persistent caches should include enough version/fingerprint information to detect staleness.

Examples:

```text
source model fingerprint
solver environment fingerprint
view definition fingerprint
presentation policy fingerprint
cache format version
```

If incompatible, discard/recompute cache rather than pretending it is current.

## Plugin data

A project may contain plugin-owned semantic records.

Rules:

- plugin namespace must be explicit;
- plugin version/schema requirements recorded;
- missing plugin should yield a clear dependency diagnostic;
- base project metadata should remain inspectable where possible;
- do not execute arbitrary plugin code merely to inspect unknown payload metadata.

## Breaking schema policy

Removing backward-read support should be a deliberate major compatibility decision.

Before dropping a historical version:

- document last version that can migrate it;
- provide a migration/export path where practical;
- consider long-lived scientific project value;
- avoid forcing users to preserve old Blender/render environments merely to recover scientific data.

## Human-readable vs binary formats

JSON is suitable for many metadata/semantic envelopes, but large numerical arrays may eventually require binary/chunked formats.

If binary storage is introduced, keep a versioned semantic envelope separate from raw buffer encoding where possible.

Conceptually:

```text
project/solution metadata
    -> references typed binary chunks
```

Do not let a performance-oriented binary layout become the only definition of scientific semantics.

## Success criterion

A Spectra project, Scene, or experiment saved today should remain scientifically interpretable by future versions through explicit migration rules, even if renderers, numerical implementations, internal Python modules, and performance storage formats change substantially.
