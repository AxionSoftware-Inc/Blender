# Spectra Science — Premium Showcase Acceptance Data

Status: **design/acceptance contract, not implemented runtime**.

This document turns the first premium showcase scenes into repeatable acceptance targets. It separates scientific invariants, generic Scene invariants, presentation invariants, and Blender-native checks.

The goal is to avoid approving premium scenes only because they look attractive in one screenshot.

## Shared acceptance structure

Every showcase should define four layers:

```text
A scientific invariants
B generic Scene invariants
C presentation invariants
D backend/native invariants
```

A scene fails if a premium presentation corrupts or obscures scientific meaning even if the render is visually attractive.

## Shared generic requirements

All five first showcases should satisfy:

- deterministic scientific primitive IDs;
- deterministic `presentation.*` resource IDs;
- repeated composition does not accumulate resources;
- base scientific geometry/value arrays unchanged by presentation-only changes;
- camera derived from Scene-local geometry/explicit semantic context;
- no renderer-specific scientific recomputation;
- presentation timeline does not conflict with scientific timeline ownership;
- preset switching does not rerun the numerical solver;
- backend cleanup removes Spectra-owned resources only;
- result can be sampled through normal `Scene.sample(t)` / `BackendSession` lifecycle.

## Showcase 1 — Maxwell electromagnetic wave

### Scientific content

Expected semantic content:

```text
E vector field
B vector field
time-dependent solution
optional propagation/reference geometry
```

### Scientific invariants

- E/B values come from the Maxwell solution/view contract;
- presentation never changes vector magnitudes/directions;
- E and B identities remain separately inspectable;
- time shown in annotation is derived from engine time, not Blender frame number directly;
- if quantitative vector colors are used, legend/color policy corresponds to the actual chosen quantity (magnitude/component), not decorative E/B colors unless explicitly categorical.

### Generic Scene acceptance

- E and B use batched `VectorGlyphSet` representations where appropriate;
- no one-object-per-arrow explosion;
- active camera valid;
- any title/time labels use `presentation.*` IDs;
- scientific timeline remains authoritative.

### Premium presentation target

For cinematic/presentation preset:

- clear visual distinction between E and B;
- propagation direction legible;
- camera shows field structure without extreme perspective distortion;
- labels sparse enough not to cover vectors;
- studio/rim treatment may add depth but cannot destroy quantitative color integrity.

### Blender acceptance later

- same E/B Spectra primitive maps to stable Blender objects through playback;
- vector geometry updates in place where compatible;
- no object-count growth over repeated samples;
- presentation camera/light objects are deterministic Spectra-owned native resources.

## Showcase 2 — Electrostatic field laboratory

### Scientific content

```text
point charges/source markers
potential and/or electric field vectors
optional field lines/slice
```

### Scientific invariants

- charge signs/magnitudes preserved;
- electric vectors derive from explicit electric-field semantics;
- field lines, if present, come from the scientific visualization algorithm, not Blender forces/particles;
- potential zero/range is not invented by the presentation layer.

### Generic Scene acceptance

- source objects remain visually identifiable separately from field visualization;
- dense arrows remain batched;
- field-line polylines use stable IDs;
- legend exists only if the displayed colors encode a quantitative/categorical quantity requiring explanation.

### Premium presentation target

- charges are focal context, not hidden by dense arrows;
- positive/negative distinction is accessible without relying only on subtle hue differences;
- camera frames source arrangement plus useful field extent;
- analysis preset remains cleaner and more quantitative than cinematic preset.

## Showcase 3 — Quantum probability + phase

### Scientific content

```text
complex wavefunction-derived probability density
phase where explicitly requested
```

### Scientific invariants

- probability density is non-negative;
- phase is treated as cyclic;
- probability and phase must not share an inappropriate single sequential color scale;
- renderer does not infer phase from mesh geometry;
- normalization/units follow the source scientific result.

### Generic Scene acceptance

Current limitation must be respected:

- continuous scalar coloring on one generic `Surface` requires the future visual-attribute path;
- until then, do not fake a premium quantitative surface with a decorative gradient.

Allowed early presentation:

- explicit slice/curve/point representation already carrying correct values/colors;
- title/axes/camera/light improvements independent of quantitative Surface attributes.

### Premium presentation target

- density visualization uses a sequential scale;
- phase visualization uses a cyclic scale;
- legend clearly identifies which quantity is displayed;
- cinematic effects do not imply false density peaks or phase discontinuities.

## Showcase 4 — Thermoelastic solid

### Scientific content

```text
temperature field
deformed geometry/displacement
stress or von Mises diagnostic where requested
```

### Scientific invariants

- geometric deformation derives from displacement field and explicit display scale;
- display deformation scale is labeled if not 1:1;
- temperature/stress color semantics remain separate;
- presentation lighting cannot be the sole means of interpreting deformation;
- original/reference configuration can be shown explicitly when requested.

### Generic Scene acceptance

- deformed-grid PointCloud/current geometry retains stable scientific ID through animation;
- display scale is presentation/view metadata, not a mutation of physical displacement values;
- reference context geometry uses separate IDs/resources.

### Premium presentation target

- silhouette/deformation readable;
- context/reference geometry visually subordinate;
- temperature/stress legends include units;
- camera highlights deformation without hiding global shape.

## Showcase 5 — Schwarzschild geodesics

### Scientific content

```text
metric/geodesic solution trajectories
central-body/horizon context where explicitly represented
```

### Scientific invariants

- trajectories are generated from the relativity/geodesic domain;
- renderer never calculates orbital paths;
- any event-horizon radius/context follows explicit physical parameters;
- coordinate/projection caveats are not hidden by cinematic styling.

### Generic Scene acceptance

- geodesics remain stable `Polyline` IDs;
- multiple trajectories are distinguishable without per-object renderer logic;
- axes/projection labels reflect actual displayed coordinates when known;
- camera movement is presentation-only.

### Premium presentation target

- black-hole/context object does not obscure trajectories;
- depth cues help 3D reading;
- line widths remain readable across distance;
- a publication preset can produce a clean figure without cinematic effects.

## Cross-preset matrix

Each showcase should eventually be checked with at least:

```text
analysis
publication
presentation
cinematic
```

`dark_lab` may be added where useful.

Expected distinction:

### analysis

- quantitative clarity first;
- restrained lighting;
- axes/legends favored;
- no unnecessary reveal/camera movement.

### publication

- deterministic framing;
- low visual distortion;
- print/readability oriented;
- minimal annotation.

### presentation

- teaching/explanation oriented;
- selective reveal;
- larger labels;
- moderate studio lighting.

### cinematic

- stronger depth/composition;
- optional camera movement;
- still scientifically faithful.

## Quantitative color gate

For any scene using quantitative colors, acceptance requires:

1. source quantity explicitly identified;
2. resolved range explicitly inspectable;
3. units/reference recorded where applicable;
4. displayed geometry uses the same mapping as the legend;
5. no backend-only remapping unknown to Spectra;
6. no silent categorical binning for a continuous required scale;
7. cyclic quantities use cyclic semantics;
8. signed diverging quantities have justified center.

If the backend cannot satisfy these rules, the feature should fall back or fail according to capability policy rather than produce misleading pixels.

## Camera gate

For automatic camera composition:

- use `scene_local_bounds()`;
- camera transform remains Scene-local;
- non-default `Scene.frame` must not double-transform framing;
- near/far clip remain valid;
- camera should not clip canonical content at start/middle/end samples;
- scientific primitive IDs unaffected.

## Animation gate

At three minimum samples:

```text
start
middle
end
```

verify:

- scientific state changes when expected;
- presentation resources remain structurally stable where intended;
- no duplicate Timeline target/property ownership;
- reveal does not overwrite scientific opacity/trim tracks;
- time annotation corresponds to engine time;
- native object count remains stable in incremental backend tests.

## Cleanup gate

After session destruction:

- Spectra-owned native objects removed;
- Spectra-owned presentation lights/cameras/materials removed when unused;
- unrelated user Blender objects/resources untouched;
- no orphan accumulation from repeated create/apply/destroy loops.

## Visual-review checklist

Human visual review remains useful after objective gates pass.

Review questions:

- Can the main scientific relationship be identified within a few seconds?
- Is visual hierarchy obvious?
- Are labels/legends readable?
- Are data colors distinguishable and accessible?
- Does lighting help rather than alter interpretation?
- Is the camera intentional rather than arbitrary?
- Is density of arrows/labels appropriate?
- Does the scene still look professional without bloom/glare tricks?
- Does the publication preset remain credible as a scientific figure?

## Acceptance report format

For each showcase record:

```text
showcase ID
source scientific capabilities
source result fingerprint if available
presentation preset
backend/version
Scene primitive counts by kind
presentation resource IDs
quantitative scales/ranges
start/mid/end screenshots or hashes where appropriate
native object/datablock counts
known fallbacks
PASS/FAIL per scientific/generic/presentation/native gate
review notes
```

Do not publish one undifferentiated `premium PASS` if only visual review was performed.

## First implementation order

After the numerical runtime validation and Phase 1 presentation composer:

1. Maxwell — exercises vector animation/camera/lighting;
2. Electrostatics — exercises dense field + sources + field lines;
3. Thermoelasticity — exercises deformation + scalar quantity context;
4. Geodesics — exercises multiple curves/depth/cinematic framing;
5. Quantum — complete quantitative premium acceptance after generic visual attributes are available.

This order deliberately delays the hardest continuous scalar/phase Surface path until its renderer-independent data contract exists.

## Success criterion

The premium showcase suite should demonstrate that Spectra can automatically produce scenes that are simultaneously scientifically faithful, renderer-independent at the engine boundary, presentation-aware, incrementally renderable, and visually professional.
