# Spectra Science — Quantitative Color Scale Algorithms

Status: **design algorithm, not implemented runtime**.

This document defines renderer-neutral normalization/range rules for future quantitative scientific color mapping. It complements `SCIENTIFIC_COLOR_POLICY.md` and the visual-attribute design.

## Core rule

Presentation color mapping may transform scientific values into display coordinates/colors, but it never changes the underlying scientific values.

Conceptual pipeline:

```text
scientific scalar values
    -> validate finite/display-eligible values
    -> resolve semantic display range
    -> normalize to display coordinate
    -> palette lookup
    -> colors/attributes
    -> legend from the same resolved scale
```

The renderer must not independently choose a different range.

## ResolvedColorScale

Conceptual immutable output of range resolution:

```python
@dataclass(frozen=True)
class ResolvedColorScale:
    kind: str
    palette_id: str
    minimum: float
    maximum: float
    center: float | None = None
    clamp: bool = True
    unit_symbol: str | None = None
    quantity_id: str | None = None
```

All numeric fields must be finite and `minimum < maximum`.

## Sequential scale

Use for quantities with ordered magnitude and no semantically meaningful central sign transition.

Typical examples:

```text
probability density
temperature absolute scale
speed magnitude
energy density
concentration
```

Normalization:

```text
u = (x - minimum) / (maximum - minimum)
```

If `clamp=True`:

```text
u = min(max(u, 0), 1)
```

If clipping values, legend/range metadata must still expose the actual resolved display range.

## Diverging scale

Use when a meaningful center/reference exists.

Examples:

```text
pressure perturbation around 0
signed displacement component
electric potential when 0 is semantically chosen reference
temperature difference relative to reference
```

A center must be explicit or supplied by semantic metadata. Do not assume zero for every signed quantity.

For symmetric range around center `c`:

```text
extent = max(abs(data_min - c), abs(data_max - c))
minimum = c - extent
maximum = c + extent
```

Normalization may remain linear over `[minimum, maximum]`, with the palette midpoint representing `center`.

For asymmetric explicitly requested diverging range, normalization should still map center to palette midpoint using a piecewise transform:

```text
x <= center:
    u = 0.5 * (x - minimum) / (center - minimum)

x >= center:
    u = 0.5 + 0.5 * (x - center) / (maximum - center)
```

Require:

```text
minimum < center < maximum
```

## Cyclic scale

Use for periodic quantities such as phase/angle.

Examples:

```text
quantum phase
orientation angle
wrapped phase field
```

Given period `P > 0` and origin `o`:

```text
u = ((x - o) mod P) / P
```

Do not clamp cyclic values at range endpoints in the sequential sense.

The palette must be continuous at `u=0` / `u=1` within accepted perceptual tolerance.

Legend should communicate periodicity.

## Categorical scale

Use for discrete semantic categories, not discretized continuous scientific values unless the view explicitly defines bins/classes.

Mapping:

```text
stable category ID -> stable palette entry
```

Category order is semantic/deterministic.

Do not use dictionary/process iteration accidents to assign colors.

## Range modes

### DATA

```text
minimum = finite minimum of display values
maximum = finite maximum
```

If all finite values are identical, expand by deterministic epsilon around the constant value rather than produce divide-by-zero.

Conceptual:

```text
epsilon = max(abs(value) * 1e-6, 1e-12)
minimum = value - epsilon
maximum = value + epsilon
```

For quantities constrained non-negative, range expansion should avoid inventing negative display semantics where inappropriate; e.g. constant zero may use `[0, epsilon]`.

### EXPLICIT

User/view supplies:

```text
minimum
maximum
```

Require finite `minimum < maximum`.

For diverging scale, center must also satisfy range requirements.

### SYMMETRIC_ZERO

Only valid when zero is scientifically meaningful.

```text
extent = max(abs(data_min), abs(data_max))
minimum = -extent
maximum = +extent
center = 0
```

If extent is zero, use deterministic epsilon.

### ROBUST_PERCENTILE

Used for visualization robustness when extreme outliers would destroy display contrast.

The policy must explicitly request percentiles, for example:

```text
low = 2%
high = 98%
```

Rules:

- percentiles operate on finite display values only;
- exact deterministic interpolation method should be specified once implemented;
- clipping/robust range is presentation metadata and must be visible in legend/inspection;
- source values remain unchanged;
- publication/scientific audit may choose explicit/full-data range instead.

Do not silently enable robust percentile clipping.

## Missing/non-finite values

Scientific solvers generally should diagnose non-finite numerical results upstream.

For imported or masked scientific data, presentation may support missing values explicitly.

Possible semantics:

```text
masked/missing -> transparent or reserved missing color
NaN/inf unexpectedly present -> diagnostic/failure by default
```

Do not silently map NaN to zero.

## Unit normalization

Range resolution occurs in one explicit unit representation.

If input data are `Quantity` values or a view has unit metadata:

```text
convert to chosen display unit
resolve range in that unit
legend reports same unit
```

Do not mix numerical values from different units before conversion.

The palette coordinate itself is dimensionless.

## Shared scales

Comparison views may request one shared scale across multiple datasets.

Algorithm:

```text
convert all compared values to compatible chosen unit
combine finite values
resolve one range
apply same ResolvedColorScale to each view
```

This enables valid visual comparison.

If units/dimensions are incompatible, fail rather than force a shared legend.

## Independent scales

Independent scales are allowed when comparison semantics require local contrast, but must be visibly distinct/labelled.

Do not make two panels look quantitatively comparable with hidden different ranges.

## Time-dependent data

Range strategy must be explicit:

```text
per_frame
fixed_reference
full_history
author_explicit
```

For scientific animation, a fixed range is often preferable because per-frame normalization can create false visual changes in magnitude.

Phase 1 should avoid automatic full-history scans unless the source view/result already exposes a safe range/envelope.

Recommended default for canonical animated quantitative scenes:

```text
fixed reference/explicit range where available
```

## Vector fields

If vectors are colored quantitatively, metadata must specify what scalar quantity drives color:

```text
magnitude
x component
y component
z component
signed projection
another diagnostic
```

Do not color vectors by magnitude while labelling legend as a vector quantity without saying `|E|`, `|v|`, etc.

Vector direction and color encoding remain separate semantics.

## Complex fields

Complex values are not directly mapped to one scalar colormap without explicit semantic projection.

Possible views:

```text
magnitude -> sequential
phase -> cyclic
real part -> diverging/sequential depending semantics
imaginary part -> same
```

Presentation must consume explicit view metadata rather than choose arbitrarily.

## Quantitative color vs lighting

Once palette colors are computed, backend lighting must not materially alter the perceived quantitative mapping beyond the accepted presentation profile.

For strict quantitative views, prefer unlit/emissive/low-distortion mapping.

Context geometry may use ordinary lit materials separately.

## Palette requirements

Palette IDs should be stable renderer-neutral semantic identifiers.

Requirements for quantitative defaults:

- perceptually ordered for sequential scales;
- neutral midpoint for diverging scales where appropriate;
- cyclic endpoint continuity for cyclic scales;
- reasonable color-vision accessibility;
- grayscale/print behavior considered for publication presets where possible.

Do not bake Blender-specific color-management names into palette IDs.

## Palette lookup

Generic implementation may define a palette as ordered control points:

```text
(u0, Color0), ... (un, Colorn)
```

with deterministic interpolation in a chosen color space.

The first implementation may use linear RGB interpolation if documented, but perceptual interpolation can be introduced later without changing quantity/range semantics if palette versioning is explicit.

Palette behavior affecting published output should have stable IDs/versions.

## Legend derivation

Legend ticks/labels derive from the exact resolved scale.

Never separately compute legend min/max from source data after a robust/explicit scale has already been resolved.

Minimal legend metadata:

```text
quantity label
unit
minimum
maximum
center/reference if relevant
palette ID
range mode
clipping note if relevant
```

## Deterministic ticks

Tick formatting is product/presentation logic, but tick values should be deterministic.

A later utility may select “nice” decimal intervals from the numeric range.

Until implemented, a minimal robust legend can show:

```text
minimum
center if relevant
maximum
```

This avoids premature complex tick-layout algorithms.

## Visual attribute integration

When renderer-neutral visual attributes exist:

```text
source scalar channel
+ ResolvedColorScale
-> optional precomputed Color channel or renderer palette evaluation
```

Two valid backend paths:

1. Spectra precomputes per-element colors;
2. Spectra provides normalized scalar attribute + palette resource and renderer evaluates colors.

Both must yield the same semantic mapping within tolerance.

The renderer may not choose a new min/max.

## Blender current limitation

Current reference Blender batched per-instance color uses bounded material-slot creation and is not a final continuous high-cardinality mapping.

Therefore a future attribute shader/Geometry Nodes path is preferred for dense scalar data.

This design is one reason the range/color algorithm must remain renderer-neutral.

## Tests after implementation gate

- sequential normalization endpoints/midpoint;
- explicit range validation;
- constant-value range expansion;
- non-negative constant zero handling;
- symmetric zero diverging range;
- asymmetric diverging center maps to 0.5;
- cyclic wrap equivalence (`x` and `x+P`);
- categorical stable ordering;
- unit conversion before range resolution;
- shared-scale compatible unit conversion;
- incompatible shared dimensions fail;
- robust percentile never mutates source values;
- NaN not silently treated as zero;
- legend metadata exactly matches resolved scale;
- renderer backend cannot alter resolved numeric range.

## Canonical scientific cases

Use cross-domain examples:

```text
temperature -> sequential
pressure delta -> diverging centered at 0
probability density -> non-negative sequential
quantum phase -> cyclic period 2*pi
von Mises stress -> non-negative sequential
velocity magnitude -> sequential
electric potential -> diverging only when zero/reference semantics explicitly justify it
```

## Success criterion

A user should be able to inspect a rendered scientific color and trace it back through one deterministic renderer-neutral mapping:

```text
scientific value -> chosen display unit -> resolved range -> normalized coordinate -> palette color -> matching legend
```

without a hidden renderer-specific normalization step changing the scientific interpretation.
