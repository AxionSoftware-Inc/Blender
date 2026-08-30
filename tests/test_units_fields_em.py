import math

import pytest

from spectra.core.coordinates import CoordinateFrame3D
from spectra.core.primitives import VectorGlyphSet
from spectra.core.types import Vec3
from spectra.core.units import CENTIMETER, METER, Quantity
from spectra.domains import DomainRegistry
from spectra.domains.mathematics import AxisSample, MathematicsDomain, RegularGrid3D, VectorField3D
from spectra.domains.mathematics.visualization import compile_vector_field_scene
from spectra.domains.physics.electromagnetism import (
    ElectromagnetismDomain,
    PointCharge,
    electric_field_from_point_charges,
)


def test_quantity_conversion_preserves_dimension() -> None:
    assert Quantity(250.0, CENTIMETER).to(METER).value == pytest.approx(2.5)


def test_coordinate_frame_maps_local_points_without_renderer_state() -> None:
    frame = CoordinateFrame3D(
        origin=Vec3(10.0, 20.0, 30.0),
        basis_x=Vec3(2.0, 0.0, 0.0),
        basis_y=Vec3(0.0, 3.0, 0.0),
        basis_z=Vec3(0.0, 0.0, 4.0),
    )
    assert frame.point_to_parent(Vec3(1.0, 2.0, 3.0)) == Vec3(12.0, 26.0, 42.0)


def test_vector_field_compiles_to_one_batched_glyph_scene() -> None:
    field = VectorField3D(lambda point: Vec3(-point.y, point.x, 0.0), name="rotation")
    grid = RegularGrid3D(
        AxisSample(-1.0, 1.0, 3),
        AxisSample(0.0, 0.0, 1),
        AxisSample(0.0, 0.0, 1),
    )
    scene = compile_vector_field_scene(field, grid)

    assert len(scene.primitives) == 1
    glyphs = scene.primitives[0]
    assert isinstance(glyphs, VectorGlyphSet)
    assert glyphs.kind == "vector_glyph_set"
    assert glyphs.instance_count == 3
    assert glyphs.origins[0] == Vec3(-1.0, 0.0, 0.0)
    assert glyphs.vectors[0] == Vec3(0.0, -1.0, 0.0)


def test_electromagnetism_reuses_mathematical_vector_field_contract() -> None:
    registry = DomainRegistry()
    with pytest.raises(KeyError, match="mathematics.vector_field3d"):
        registry.add_domain(ElectromagnetismDomain())

    registry.add_domain(MathematicsDomain())
    registry.add_domain(ElectromagnetismDomain())

    charge = PointCharge.coulombs(Vec3(0.0, 0.0, 0.0), 1e-9)
    field = electric_field_from_point_charges([charge])
    value = field.evaluate(Vec3(1.0, 0.0, 0.0))

    assert value.x == pytest.approx(8.9875517923)
    assert value.y == pytest.approx(0.0)
    assert value.z == pytest.approx(0.0)
    assert math.isfinite(value.magnitude)
