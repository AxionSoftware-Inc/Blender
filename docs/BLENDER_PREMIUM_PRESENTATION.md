# Spectra Science — Blender Premium Presentation Reference Mapping

This document describes how Blender should interpret renderer-neutral Spectra presentation intent. It is a backend implementation guide, not a scientific-domain contract.

Blender remains a reference renderer/backend. The presentation model must stay valid if another backend is used.

## Boundary

```text
scientific result
    -> semantic visualization
    -> generic Scene + Timeline
    -> renderer-neutral presentation intent
    -> Blender presentation adapter
    -> native Blender scene/material/light/camera/compositor state
```

No physics, chemistry, PDE, quantum, or geometry formula belongs in the Blender presentation adapter.

## Current Blender foundation

The existing backend already maps generic Spectra primitives to Blender-native objects and the incremental backend preserves stable IDs/data blocks where possible.

Verified native behaviors include:

- curves and surfaces;
- materials;
- lights;
- cameras;
- animated `Polyline`;
- animated `VectorGlyphSet`;
- batched `PointCloud`;
- stable object/data-block identity;
- topology fallback;
- cleanup;
- repeated-frame leak stability.

Premium presentation should build on these behaviors rather than replace them with a separate Blender-only scene system.

## Presentation adapter architecture

A Blender presentation adapter should conceptually have three stages:

```text
PresentationIntent
    -> resolve backend feature support
    -> derive BlenderPresentationPlan
    -> apply/update native Blender state
```

The plan should be deterministic and inspectable. It should not directly mutate scientific semantic objects.

## World/background mapping

Renderer-neutral themes may map to Blender World/environment settings.

Examples:

### analysis

- neutral world/background;
- low visual distraction;
- predictable color rendering;
- minimal atmospheric effects.

### publication

- white/light or transparent background;
- shadows/lighting controlled to preserve figure readability;
- deterministic output independent of cinematic effects.

### dark_lab

- dark neutral environment;
- modest contrast separation;
- emissive accents allowed as presentation treatment;
- no scientific value encoded only through bloom/glow.

### cinematic

- controlled darker environment;
- depth-enhancing background gradient/environment;
- optional atmosphere/post-processing when supported.

Exact node names/settings remain Blender implementation details.

## Material mapping

Spectra already owns generic material/color resources. Premium Blender mapping may extend the native interpretation while preserving scientific color semantics.

### Flat quantitative data

For scalar colors that must remain quantitatively interpretable:

- prefer low-lighting-distortion or emission/unlit-like interpretation;
- preserve exact colormap values where possible;
- do not let metallic/specular response obscure the legend relationship.

### Context geometry

For non-data geometry:

- Principled-style neutral materials are suitable;
- context geometry should not overpower data;
- roughness/specular choices may follow theme/preset.

### Highlighted scientific objects

Use presentation emphasis deliberately:

- modest emission;
- outline/rim treatment where supported;
- material contrast;
- opacity changes.

Scientific meaning must remain visible without relying exclusively on renderer post effects.

## High-cardinality scalar colors

The existing reference backend is not the final design for very high-cardinality per-instance color.

Premium/dense Blender implementation should prefer a scalable path such as:

```text
Spectra scalar values
    -> normalized/display values
    -> Blender mesh/curve attribute
    -> shader color-map evaluation or precomputed color attribute
```

rather than creating one material slot/object for every value.

Desired properties:

- one or few native objects;
- stable topology;
- in-place attribute updates;
- deterministic range/colormap;
- legend generated from the same color policy.

## PointCloud mapping

Current rule remains:

```text
one Spectra PointCloud != N Blender objects
```

Premium options may include:

- mesh vertices for lightweight analysis;
- Geometry Nodes instancing for visible particles/spheres;
- attribute-driven size/color;
- backend-controlled LOD for display only.

The scientific `PointCloud.positions` remains authoritative.

A Geometry Nodes implementation must preserve a stable single/batched representation and should not cause Blender object-count growth with particle count.

## VectorGlyphSet mapping

Current verified representation uses a batched Curve structure.

Premium implementation options include:

- multi-spline curve arrows;
- Geometry Nodes instanced arrow geometry;
- attribute-driven magnitude/color;
- display-density sampling upstream in presentation/visualization policy.

Never create one Blender object per vector for dense fields.

## Surface/scalar-field mapping

A generic Spectra `Surface` may be presented as:

- solid shaded surface;
- quantitative color-mapped surface;
- transparent slice;
- contour-enhanced surface where presentation semantics provide contours;
- displacement surface when displacement is part of explicit view semantics.

The renderer should not infer scalar values from mesh height unless the view contract states that height encodes that scalar.

## Volume future path

Spectra Core currently does not require a universal volume primitive.

Until a generic volume contract is justified across multiple domains, Blender volume rendering should not force domain-specific volume objects into Core.

When volume semantics are added, likely Blender interpretations may include:

- VDB/OpenVDB-compatible volume data;
- shader-sampled dense grids;
- texture/3D image resources;
- sparse data structures.

The scientific domain should still expose scalar/vector/complex fields independently of Blender volume formats.

## Camera mapping

Renderer-neutral camera policies should resolve using Spectra bounds and semantic framing intent.

### fit_all / fit_primary

The presentation composer determines target bounds; Blender converts generic camera orientation/projection into native transform/lens/orthographic settings.

### analysis orthographic

Prefer orthographic camera for quantitative layouts where perspective would distort comparisons.

### cinematic perspective

Use perspective camera with controlled field of view. Avoid extreme wide-angle distortion unless intentionally requested.

### orbit/reveal

Camera animation should be generated from a generic presentation path/timeline, not handwritten as unrelated Blender keyframes.

### follow subject

The target subject should be identified by stable Spectra primitive/group ID. Blender may implement tracking natively, but Spectra presentation semantics remain authoritative.

## Lighting rigs

Suggested backend interpretations:

### flat_analysis

- minimal or environment-like light;
- predictable data color;
- shallow shadows or no shadows.

### scientific_studio

- key area light;
- softer fill;
- optional rim/back light;
- context geometry readable without washing out scientific data.

### rim_emphasis

Useful for transparent/sparse geometry where silhouette matters.

### unlit_data

Data material should remain largely independent of scene lights; context may still be lit.

Light objects created by the presentation adapter should use deterministic presentation-prefixed IDs/names and be cleaned up as Spectra-owned state.

## Legends

For first implementation, legends can be represented with ordinary generic Spectra primitives where practical:

- labels;
- small color-bar geometry;
- tick labels;
- min/max/reference values.

A later Blender-specific screen-space overlay may improve readability, but the legend content/range/unit must remain renderer-neutral.

A Blender legend must use exactly the same color policy/range as the displayed geometry.

## Axes and grids

Axes should be generated by the presentation layer as explicit Scene content or a generic axes resource when that abstraction is introduced.

Blender should not silently add world axes because:

- projected geometry may not be in ordinary world coordinates;
- units may differ;
- scientific axes may be named quantities rather than x/y/z;
- publication views may intentionally hide axes.

## Text and typography

Backend mapping should support a small stable typography hierarchy:

```text
title
subtitle
body/annotation
legend label
numeric/tick label
```

Typography policy should specify relative size/contrast/alignment intent. Font-family choice may remain backend/application policy.

Text should face the camera or use a screen-space strategy only when the presentation policy calls for it.

## Animation

Blender playback remains transport; Spectra owns scientific/presentation time semantics.

Premium presentation may compose:

- `staggered_reveal`;
- path draw;
- fade;
- camera animation;
- label reveal;
- scientific timeline evolution.

The backend should continue sampling the Spectra Scene rather than duplicating scientific animation with independent Blender-only curves.

If native Blender animation is cached/baked for rendering performance, it must be generated from the Spectra timeline and remain reproducible from it.

## Compositor and post-processing

Post-processing is backend-specific and optional.

Cinematic Blender interpretation may use controlled:

- bloom/glare;
- vignette;
- color management;
- depth of field;
- mist/depth cues;
- motion blur.

Rules:

1. effects must not be required to understand quantitative values;
2. publication/analysis presets should disable or minimize them;
3. effects must never mutate scientific data;
4. fallback without compositor must remain scientifically valid.

## Render engine abstraction

Premium presentation should not assume one Blender render engine in scientific or generic presentation code.

A Blender backend profile may advertise capabilities/performance for available engines.

Presentation policy may request conceptual quality features, while Blender mapping chooses the most appropriate native implementation.

## Geometry Nodes

Geometry Nodes is a promising premium implementation mechanism for:

- particle instancing;
- arrow instancing;
- per-instance attributes;
- efficient display-scale geometry generation;
- reusable presentation rigs.

Rules:

- Geometry Nodes remains backend implementation;
- node group topology/name is not part of scientific semantics;
- stable inputs should be mapped from Spectra attributes/resources;
- changing scientific values should update inputs/buffers, not rebuild thousands of nodes/objects.

## Collections and ownership

Premium adapter should keep Spectra-owned native state organized into deterministic collections/namespaces, conceptually separating:

```text
SPECTRA_SCIENCE
SPECTRA_PRESENTATION
SPECTRA_LIGHTS
SPECTRA_ANNOTATIONS
```

Exact Blender collection names are implementation details, but ownership separation is valuable for cleanup/debugging.

`destroy()` or session cleanup must remove only Spectra-owned state and leave unrelated user content intact.

## Incremental updates

Presentation changes should classify into:

### value-only

Examples:

- scalar color attribute update;
- label text change;
- time indicator;
- light intensity;
- camera transform;
- point/vector positions.

Prefer in-place update.

### style-only

Examples:

- theme change;
- line width;
- roughness;
- background.

Avoid rebuilding scientific geometry.

### structural presentation change

Examples:

- adding/removing legend;
- switching arrow representation;
- enabling axes;
- changing camera rig topology.

May add/remove presentation-owned objects while leaving scientific primitives stable.

## Quality levels

Suggested Blender backend quality profiles:

### interactive

- prioritize viewport responsiveness;
- reduced expensive effects;
- same scientific state.

### preview

- representative materials/lights;
- moderate quality;
- quick render.

### high

- full presentation rig;
- high-quality shading/AA;
- reasonable post-processing.

### final

- output-oriented render settings;
- maximum presentation quality allowed by requested profile;
- never alters solver data or precision.

## Premium validation suite

After runtime implementation begins, Blender presentation should be validated against canonical scenarios from `docs/SHOWCASE_SCENARIOS.md`.

At minimum:

```text
Electrostatic field laboratory
Maxwell wave
Quantum wavepacket
Thermoelastic solid
Black-hole geodesics
```

Validation should include:

- correct units/legends;
- deterministic camera framing;
- stable scientific primitive identity;
- no object leaks over animation;
- display decimation independent of numerical resolution;
- preset switching without recomputing science;
- cleanup safety.

## Success criterion

A premium Blender result should feel intentionally authored while still being generated from generic Spectra scientific/presentation contracts.

The Blender implementation may be sophisticated; the scientific domains should remain unaware that Blender was used.
