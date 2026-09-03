# Spectra Science — Scientific Color Policy

Status: **design contract; quantitative presentation runtime not yet implemented**.

This document defines how Spectra should choose and describe scientific color mappings without letting renderers invent quantity semantics.

## Core rule

Color can encode scientific values, categories, phase, uncertainty, selection, or presentation emphasis. These roles must remain distinguishable.

A renderer must never infer a scientific colormap solely from primitive type or object name.

## Color roles

```text
quantitative sequential
quantitative diverging
quantitative cyclic
categorical
uncertainty/confidence
selection/highlight
presentation decoration
```

Only the last two may be chosen primarily for aesthetics.

## Sequential quantities

Use when values have an ordered magnitude and no scientifically privileged center.

Typical examples:

```text
probability density
concentration
speed
energy density
mass density
non-negative temperature above absolute zero when absolute magnitude is the message
error magnitude
```

Policy:

```text
low -> high luminance/chroma progression
```

Avoid rainbow-like arbitrary hue ordering for quantitative reading.

## Diverging quantities

Use when a meaningful center/reference exists.

Examples:

```text
electric potential around zero
signed pressure difference around reference
normal displacement around undeformed position
signed residual
positive/negative vorticity component
```

Required metadata:

```text
center value
range mode
unit
```

Default range should often be symmetric about center when comparison of signs is important.

Do not zero-center a field merely because it contains positive and negative samples; the semantic view or user intent should establish that zero/reference is meaningful.

## Cyclic quantities

Use for periodic variables where endpoints represent the same state.

Examples:

```text
quantum phase
angle
orientation phase
wave phase when explicitly visualized as phase
```

Rules:

- palette endpoints must join perceptually;
- legend should indicate periodicity;
- do not show cyclic phase with an ordinary sequential scale;
- phase wrapping belongs to semantic/view logic, not renderer guessing.

## Categorical quantities

Use for discrete classes with no numerical order.

Examples:

```text
material regions
species identity
solver implementation comparison
boundary-condition types
selected experiment groups
```

Rules:

- colors should remain distinguishable;
- color should not imply magnitude;
- use labels/legend;
- repeated category IDs map deterministically to the same color within one presentation policy.

## Uncertainty

Uncertainty should not be confused with the measured quantity itself.

Preferred encodings may include:

```text
opacity range
error band
outline thickness
secondary saturation channel
explicit uncertainty surface/band
```

If opacity interferes with spatial interpretation, use a separate uncertainty view rather than hiding uncertain data.

## Missing/invalid data

Missing values require explicit policy.

Suggested states:

```text
masked
missing
non-finite
outside-domain
clamped-for-display
```

Do not map NaN to the same color as a valid minimum.

A legend/diagnostic should make masked or invalid states inspectable when relevant.

## Range policies

### Data range

```text
min(data) -> max(data)
```

Good for one-off exploration but unstable across time/parameter comparisons.

### Explicit range

```text
user/view provided [min, max]
```

Best for comparisons and publication.

### Symmetric around center

```text
center ± max(abs(data-center))
```

Useful for signed/reference-centered quantities.

### Robust percentile

May be used for exploratory visualization of outlier-heavy fields, but:

- exact percentile rule must be recorded;
- clipped values must be indicated;
- publication/quantitative exports should not hide clipping.

## Time-dependent fields

Do not independently rescale every frame by default for scientific animation.

Per-frame autoscaling can make a constant-magnitude structure look as if it changes amplitude.

Preferred policies:

```text
global time-history range
explicit fixed range
reference-centered fixed range
```

Per-frame adaptive range must be an explicit exploratory choice and visibly indicated.

## Multi-panel comparison

All compared panels should use the same quantitative scale when values are meant to be compared directly.

Examples:

```text
solver A vs solver B
before vs after
parameter case 1 vs case 2
reference vs native/GPU result
```

Independent normalization is allowed only when direct magnitude comparison is not the goal and should be clear to the viewer.

## Quantity metadata draft

```python
@dataclass(frozen=True)
class QuantityPresentationMetadata:
    name: str
    unit_symbol: str | None = None
    quantity_kind: str | None = None
    signed: bool | None = None
    cyclic: bool = False
    non_negative: bool = False
    meaningful_center: float | None = None
    preferred_color_role: str | None = None
```

The view/domain supplies semantic hints. Presentation resolves actual palette/range.

## Initial quantity guidance

### Temperature

Default role:

```text
sequential
```

Use diverging only for:

```text
ΔT around a reference temperature
```

### Pressure

Absolute pressure:

```text
sequential
```

Pressure perturbation/difference around reference:

```text
diverging
```

### Velocity magnitude / speed

```text
sequential, non-negative
```

### Velocity vector direction

Do not automatically encode direction into scalar color unless view explicitly requests it.

Vector arrows may use:

```text
uniform color + size = magnitude
or quantitative magnitude color
```

with an explicit vector-scale legend.

### Vorticity

Magnitude:

```text
sequential
```

Signed component:

```text
diverging around zero
```

### Electric potential

Often:

```text
diverging around zero/reference
```

but reference choice must be explicit for gauge-dependent contexts.

### Electric/magnetic field magnitude

```text
sequential
```

E vs B identity should normally use categorical/semantic style separation rather than pretending they share one scalar scale.

### Probability density

```text
sequential, non-negative, lower bound 0
```

### Quantum phase

```text
cyclic
```

Probability density and phase should not share one color scale.

### Stress

Von Mises:

```text
sequential, non-negative
```

Signed normal stress component:

```text
diverging around zero
```

### Displacement

Magnitude:

```text
sequential
```

Signed component:

```text
diverging
```

### Concentration

```text
sequential, normally non-negative
```

Multiple species identities:

```text
categorical identity + separate magnitude treatment
```

### Error/residual

Absolute error:

```text
sequential
```

Signed residual:

```text
diverging around zero
```

Log error range may be appropriate when orders of magnitude matter, but log mapping must be explicit.

## Palette identity

Palette identifiers should be semantic/stable names owned by presentation configuration.

Conceptual:

```text
sequential.viridis_like
sequential.blue_heat
diverging.cool_warm_zero
cyclic.phase
categorical.standard
```

Do not expose renderer node-group names as palette IDs.

Exact RGB/transfer tables should later live in one shared presentation resource catalog and be testable.

## Accessibility

Quantitative palettes should:

- remain readable for common color-vision deficiencies where possible;
- retain useful luminance ordering;
- not rely on red/green distinction alone;
- work against chosen background/theme;
- permit grayscale-friendly publication choices.

Categorical displays should use redundant labels/shape where ambiguity is high.

## Lighting interaction

For quantitatively colored surfaces:

```text
color meaning > dramatic lighting
```

Presentation may choose `unlit_data` or restrained lighting so the rendered RGB remains interpretable.

Cinematic lighting may enhance geometry around quantitatively colored elements, but must not distort the scale beyond recognition.

## Legend contract

A quantitative legend should share exactly the same resolved mapping as the data.

It should expose:

```text
quantity name
unit
minimum
maximum
center if relevant
clipping/range mode
palette role
```

The renderer should not construct a legend from an independent range calculation.

## Export/provenance

Publication/report exports should be able to record resolved color-policy metadata alongside the image/Scene:

```text
quantity
unit
palette ID
range mode
resolved min/max/center
clamp status
```

This is presentation provenance, separate from numerical provenance.

## First runtime implementation

Do not implement all quantity-specific mappings immediately.

Phase after generic presentation composer:

1. `ColorScaleKind`;
2. `RangeMode`;
3. `ColorScalePolicy`;
4. deterministic range resolution from explicit scalar samples/metadata;
5. generic legend metadata;
6. proof with two cases:
   - probability density sequential;
   - signed electric potential diverging around zero.

Then add cyclic quantum phase.

## Success criterion

If the same electric-potential result is shown in Blender, WebGPU, and a publication export, each backend may shade differently at the rendering level, but the quantitative mapping, resolved range, units, and scientific interpretation must remain the same.