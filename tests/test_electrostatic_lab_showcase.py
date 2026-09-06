from __future__ import annotations

import pytest

from spectra.core.primitives import Point, Polyline, Surface, VectorGlyphSet
from spectra.core.units import VOLT
from spectra.showcases import (
    ElectrostaticLabShowcaseConfig,
    build_electrostatic_lab_base_scene,
    build_electrostatic_lab_scene,
)


def _config() -> ElectrostaticLabShowcaseConfig:
    return ElectrostaticLabShowcaseConfig(
        extent_m=3.0,
        z_extent_m=1.0,
        source_offset_m=1.5,
        solver_grid_xy_count=9,
        solver_grid_z_count=5,
        slice_samples=13,
        vector_samples=5,
        vector_display_scale=0.12,
        field_line_seed_count=8,
        field_line_seed_radius_m=0.35,
        field_line_parameter_length=4.5,
        field_line_steps=24,
        max_iterations=2500,
        tolerance=1.0e-4,
    )


@pytest.fixture(scope="module")
def base_scene():
    return build_electrostatic_lab_base_scene(_config())


@pytest.fixture(scope="module")
def presented_scene():
    return build_electrostatic_lab_scene(_config())


def test_electrostatic_base_scene_preserves_signed_voltage_and_batched_views(base_scene) -> None:
    surface = base_scene.get("showcase.electrostatic.potential.slice")
    vectors = base_scene.get("showcase.electrostatic.field.vectors")

    assert isinstance(surface, Surface)
    potential = surface.attributes.get("electric_potential")
    assert potential.kind == "scalar"
    assert potential.association == "vertex"
    assert potential.quantity_id == "electric_potential"
    assert potential.unit == VOLT
    assert len(potential.values) == 13 * 13
    assert min(potential.values) < 0.0 < max(potential.values)
    assert max(potential.values) == pytest.approx(-min(potential.values), rel=2e-3, abs=1e-8)

    # The canonical test grid samples both source x positions on the y=0 row.
    center_row = 6 * 13
    assert potential.values[center_row + 3] > 0.0   # +q at x=-1.5 m
    assert potential.values[center_row + 9] < 0.0   # -q at x=+1.5 m

    assert isinstance(vectors, VectorGlyphSet)
    assert vectors.instance_count == 5 * 5
    center_vector = vectors.vectors[12]
    assert center_vector.x > 0.0  # E points from +q toward -q at the dipole center.
    assert abs(center_vector.y) < 1e-10
    assert abs(center_vector.z) < 1e-10
    assert base_scene.timeline.duration == 0.0
    assert base_scene.timeline.tracks == ()


def test_electrostatic_base_scene_contains_sources_and_field_lines(base_scene) -> None:
    positive = base_scene.get("showcase.electrostatic.source.positive")
    negative = base_scene.get("showcase.electrostatic.source.negative")
    assert isinstance(positive, Point)
    assert isinstance(negative, Point)
    assert positive.position.x < 0.0
    assert negative.position.x > 0.0

    lines = tuple(
        primitive
        for primitive in base_scene.primitives
        if isinstance(primitive, Polyline)
        and primitive.id.startswith("showcase.electrostatic.field_lines.curve_")
    )
    assert len(lines) == 8
    assert all(len(line.points) == 25 for line in lines)


def test_presented_electrostatic_scene_uses_symmetric_quantitative_scale(presented_scene) -> None:
    surface = presented_scene.get("showcase.electrostatic.potential.slice")
    display = surface.attributes.get("display_color")
    potential = surface.attributes.get("electric_potential")

    assert display.kind == "color"
    assert display.association == "vertex"
    assert display.quantity_id == "electric_potential"
    assert len(display.values) == len(potential.values)
    assert len(set(display.values)) > 4

    minimum = float(presented_scene.get("presentation.legend.label.minimum").text)
    maximum = float(presented_scene.get("presentation.legend.label.maximum").text)
    assert minimum < 0.0 < maximum
    assert maximum == pytest.approx(-minimum, rel=2e-3, abs=1e-8)
    assert presented_scene.get("presentation.legend.label.quantity").text == "electric_potential [V]"

    assert presented_scene.active_camera_id == "presentation.camera.primary"
    assert presented_scene.get("presentation.axes.world") is not None
    assert presented_scene.get("presentation.title.primary").text == "Electrostatic Field Laboratory"
    assert presented_scene.timeline.duration == 0.0
    assert presented_scene.timeline.tracks == ()


def test_presentation_does_not_rewrite_scientific_potential_values(base_scene, presented_scene) -> None:
    before = base_scene.get("showcase.electrostatic.potential.slice").attributes.get(
        "electric_potential"
    )
    after = presented_scene.get("showcase.electrostatic.potential.slice").attributes.get(
        "electric_potential"
    )
    assert after == before


def test_electrostatic_showcase_configuration_rejects_invalid_geometry() -> None:
    with pytest.raises(ValueError, match="source_offset_m"):
        ElectrostaticLabShowcaseConfig(extent_m=1.0, source_offset_m=1.0)
    with pytest.raises(ValueError, match="seed radius"):
        ElectrostaticLabShowcaseConfig(
            extent_m=2.0,
            source_offset_m=1.5,
            field_line_seed_radius_m=0.75,
        )
