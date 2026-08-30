import pytest

from spectra.core.primitives import Surface
from spectra.core.types import Vec3
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.mathematics import AxisSample, ScalarField3D


def test_scalar_field_slice_surface_preserves_plane_axes_and_topology() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["mathematics.field_slices3d"])

    view_type = registry.require("mathematics.scalar_field_slice_surface3d")
    field = ScalarField3D(lambda position: position.x + position.y, name="linear")
    view = view_type(
        field=field,
        axis="z",
        coordinate=2.0,
        u=AxisSample(0.0, 1.0, 2),
        v=AxisSample(0.0, 1.0, 2),
        height_scale=0.5,
        name="slice",
    )

    scene = registry.compile_scene(view)
    surface = scene.primitives[0]
    assert isinstance(surface, Surface)
    assert len(surface.vertices) == 4
    assert len(surface.triangles) == 2
    assert surface.vertices[0] == Vec3(0.0, 0.0, 2.0)
    assert surface.vertices[-1].x == pytest.approx(1.0)
    assert surface.vertices[-1].y == pytest.approx(1.0)
    assert surface.vertices[-1].z == pytest.approx(3.0)
