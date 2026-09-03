from __future__ import annotations

from dataclasses import replace
import math

from spectra.core.attributes import VisualAttribute, VisualAttributeSet
from spectra.core.primitives import PointCloud, Primitive, VectorGlyphSet
from spectra.core.scene import Scene
from spectra.core.types import Color
from spectra.presentation_models import ColorPalette, ColorRangeMode, ColorScalePolicy


_PALETTES: dict[ColorPalette, tuple[Color, ...]] = {
    ColorPalette.VIRIDIS: (
        Color(0.267, 0.005, 0.329),
        Color(0.283, 0.141, 0.458),
        Color(0.254, 0.265, 0.530),
        Color(0.207, 0.372, 0.553),
        Color(0.164, 0.471, 0.558),
        Color(0.128, 0.567, 0.551),
        Color(0.135, 0.659, 0.518),
        Color(0.267, 0.749, 0.441),
        Color(0.478, 0.821, 0.318),
        Color(0.741, 0.873, 0.150),
        Color(0.993, 0.906, 0.144),
    ),
    ColorPalette.MAGMA: (
        Color(0.001, 0.000, 0.014),
        Color(0.079, 0.054, 0.212),
        Color(0.232, 0.060, 0.438),
        Color(0.390, 0.100, 0.502),
        Color(0.550, 0.161, 0.506),
        Color(0.716, 0.215, 0.475),
        Color(0.868, 0.288, 0.409),
        Color(0.955, 0.447, 0.359),
        Color(0.995, 0.624, 0.427),
        Color(0.997, 0.810, 0.573),
        Color(0.987, 0.991, 0.750),
    ),
    ColorPalette.COOLWARM: (
        Color(0.230, 0.299, 0.754),
        Color(0.383, 0.510, 0.918),
        Color(0.554, 0.690, 0.996),
        Color(0.724, 0.814, 0.976),
        Color(0.865, 0.865, 0.865),
        Color(0.959, 0.768, 0.678),
        Color(0.957, 0.598, 0.477),
        Color(0.865, 0.372, 0.297),
        Color(0.706, 0.016, 0.150),
    ),
    ColorPalette.PHASE: (
        Color(1.000, 0.000, 0.000),
        Color(1.000, 1.000, 0.000),
        Color(0.000, 1.000, 0.000),
        Color(0.000, 1.000, 1.000),
        Color(0.000, 0.000, 1.000),
        Color(1.000, 0.000, 1.000),
        Color(1.000, 0.000, 0.000),
    ),
}


def _lerp(left: float, right: float, amount: float) -> float:
    return left + (right - left) * amount


def sample_palette(palette: ColorPalette, position: float) -> Color:
    if not math.isfinite(position):
        raise ValueError("palette position must be finite")
    colors = _PALETTES[palette]
    position = min(max(float(position), 0.0), 1.0)
    scaled = position * (len(colors) - 1)
    index = min(int(math.floor(scaled)), len(colors) - 2)
    amount = scaled - index
    left = colors[index]
    right = colors[index + 1]
    return Color(
        _lerp(left.r, right.r, amount),
        _lerp(left.g, right.g, amount),
        _lerp(left.b, right.b, amount),
        _lerp(left.a, right.a, amount),
    )


def resolve_scalar_range(
    values: tuple[float, ...],
    policy: ColorScalePolicy,
) -> tuple[float, float]:
    if not values:
        raise ValueError("scalar color mapping requires at least one value")
    if any(not math.isfinite(value) for value in values):
        raise ValueError("scalar color mapping values must be finite")

    if policy.range_mode == ColorRangeMode.FIXED:
        assert policy.minimum is not None and policy.maximum is not None
        return policy.minimum, policy.maximum

    minimum = min(values)
    maximum = max(values)
    if policy.range_mode == ColorRangeMode.SYMMETRIC:
        distance = max(abs(minimum - policy.center), abs(maximum - policy.center))
        if distance == 0.0:
            distance = 1.0
        return policy.center - distance, policy.center + distance

    if minimum == maximum:
        padding = max(abs(minimum) * 0.5, 0.5)
        return minimum - padding, maximum + padding
    return minimum, maximum


def map_scalar_values(
    values: tuple[float, ...],
    policy: ColorScalePolicy,
) -> tuple[Color, ...]:
    minimum, maximum = resolve_scalar_range(values, policy)
    span = maximum - minimum
    if span <= 0.0 or not math.isfinite(span):
        raise ValueError("color scale range must be finite and increasing")

    colors: list[Color] = []
    for value in values:
        normalized = (value - minimum) / span
        if policy.clamp:
            normalized = min(max(normalized, 0.0), 1.0)
        elif not 0.0 <= normalized <= 1.0:
            raise ValueError("scalar value lies outside unclamped color scale range")
        colors.append(sample_palette(policy.palette, normalized))
    return tuple(colors)


def _select_scalar_attribute(
    primitive: Primitive,
    policy: ColorScalePolicy,
    quantity_role: str | None,
) -> VisualAttribute | None:
    if policy.scalar_attribute_name is not None:
        try:
            attribute = primitive.attributes.get(policy.scalar_attribute_name)
        except KeyError:
            return None
        return attribute if attribute.kind == "scalar" else None

    if quantity_role is not None:
        for attribute in primitive.attributes.attributes:
            if attribute.kind != "scalar":
                continue
            if attribute.quantity_id == quantity_role or attribute.name == quantity_role:
                return attribute
        return None
    return None


def _replace_attribute(
    attributes: VisualAttributeSet,
    replacement: VisualAttribute,
) -> VisualAttributeSet:
    result = [attribute for attribute in attributes.attributes if attribute.name != replacement.name]
    result.append(replacement)
    return VisualAttributeSet(tuple(result))


def colorize_primitive(
    primitive: Primitive,
    policy: ColorScalePolicy,
    *,
    quantity_role: str | None = None,
) -> Primitive:
    scalar = _select_scalar_attribute(primitive, policy, quantity_role)
    if scalar is None:
        return primitive
    values = tuple(float(value) for value in scalar.values)
    colors = map_scalar_values(values, policy)
    color_attribute = VisualAttribute(
        name=policy.output_attribute_name,
        association=scalar.association,
        kind="color",
        values=colors,
        quantity_id=scalar.quantity_id,
    )
    updated = replace(
        primitive,
        attributes=_replace_attribute(primitive.attributes, color_attribute),
    )

    # Compatibility bridge for current batched backends. Generic color attributes
    # remain the source of truth, but existing PointCloud/VectorGlyphSet renderers
    # can consume the same mapped values through their legacy per-instance colors.
    if scalar.association == "instance" and isinstance(updated, (PointCloud, VectorGlyphSet)):
        return replace(updated, colors=colors)
    return updated


def colorize_scene(
    scene: Scene,
    policy: ColorScalePolicy,
    *,
    quantity_role: str | None = None,
) -> Scene:
    return replace(
        scene,
        primitives=tuple(
            colorize_primitive(primitive, policy, quantity_role=quantity_role)
            for primitive in scene.primitives
        ),
    )


__all__ = [
    "sample_palette",
    "resolve_scalar_range",
    "map_scalar_values",
    "colorize_primitive",
    "colorize_scene",
]
