from __future__ import annotations

import pytest

from spectra.color_scales import resolve_scene_color_scale
from spectra.core.attributes import VisualAttribute, VisualAttributeSet
from spectra.core.primitives import PointCloud, Surface
from spectra.core.scene import Scene
from spectra.core.types import Vec3
from spectra.core.units import CENTIMETER, METER
from spectra.presentation import compose_presentation
from spectra.presentation_models import ColorScalePolicy, PresentationContext


def _cloud(primitive_id: str, value: float, *, unit=None) -> PointCloud:
    scalar = VisualAttribute(
        name="temperature",
        association="instance",
        kind="scalar",
        values=(value,),
        quantity_id="temperature",
        unit=unit,
    )
    return PointCloud(
        id=primitive_id,
        positions=(Vec3(value, 0.0, 0.0),),
        attributes=VisualAttributeSet((scalar,)),
    )


def test_scene_colorization_uses_one_shared_range() -> None:
    scene = Scene(primitives=(_cloud("low", 0.0), _cloud("high", 10.0)))
    composed = compose_presentation(
        scene,
        "presentation",
        context=PresentationContext(quantity_role="temperature"),
    )

    low = composed.get("low")
    high = composed.get("high")
    low_color = low.attributes.get("display_color").values[0]
    high_color = high.attributes.get("display_color").values[0]
    assert low_color != high_color
    assert low.colors == (low_color,)
    assert high.colors == (high_color,)

    scale = resolve_scene_color_scale(
        scene,
        ColorScalePolicy(),
        quantity_role="temperature",
    )
    assert scale is not None
    assert scale.minimum == 0.0
    assert scale.maximum == 10.0


def test_quantitative_presentation_creates_deterministic_legend() -> None:
    scene = Scene(primitives=(_cloud("low", 0.0), _cloud("high", 10.0)))
    composed = compose_presentation(
        scene,
        "presentation",
        context=PresentationContext(quantity_role="temperature"),
    )

    ids = {primitive.id for primitive in composed.primitives}
    assert "presentation.legend.quantitative" in ids
    assert "presentation.legend.scale.00" in ids
    assert "presentation.legend.label.quantity" in ids
    assert "presentation.legend.label.minimum" in ids
    assert "presentation.legend.label.maximum" in ids
    assert composed.get("presentation.legend.label.quantity").text == "temperature"
    assert composed.get("presentation.legend.label.minimum").text == "0"
    assert composed.get("presentation.legend.label.maximum").text == "10"


def test_analysis_preset_materializes_xyz_axes() -> None:
    surface = Surface(
        id="surface",
        vertices=(
            Vec3(0.0, 0.0, 0.0),
            Vec3(1.0, 0.0, 0.0),
            Vec3(0.0, 1.0, 0.0),
        ),
        triangles=((0, 1, 2),),
    )
    composed = compose_presentation(Scene(primitives=(surface,)), "analysis")
    ids = {primitive.id for primitive in composed.primitives}
    assert "presentation.axes.world" in ids
    for axis in "xyz":
        assert f"presentation.axes.{axis}" in ids
        assert f"presentation.axes.{axis}.label" in ids


def test_shared_scale_rejects_mixed_units_until_conversion_policy_exists() -> None:
    left = _cloud("meters", 1.0, unit=METER)
    right = _cloud("centimeters", 100.0, unit=CENTIMETER)
    scene = Scene(primitives=(left, right))

    with pytest.raises(ValueError, match="matching VisualAttribute units"):
        compose_presentation(
            scene,
            "presentation",
            context=PresentationContext(quantity_role="temperature"),
        )
