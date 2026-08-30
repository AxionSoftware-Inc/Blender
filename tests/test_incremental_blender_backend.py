from spectra.backends import IncrementalBlenderBackend
from spectra.backends.blender.incremental import (
    _common_only_change,
    _fast_update_polyline,
    _structure_compatible,
)
from spectra.core.materials import Material
from spectra.core.primitives import Point, Polyline
from spectra.core.scene import Scene
from spectra.core.transforms import Transform3D
from spectra.core.types import Color, Vec3


def test_incremental_backend_imports_without_blender_runtime() -> None:
    backend = IncrementalBlenderBackend()
    assert backend.name == "blender"
    assert "point_cloud" in backend.capabilities.primitive_kinds
    assert "vector_glyph_set" in backend.capabilities.primitive_kinds


def test_structure_compatibility_allows_value_changes_but_not_identity_changes() -> None:
    first = Scene(primitives=(Point(id="p", position=Vec3(0.0, 0.0, 0.0)),))
    moved = Scene(primitives=(Point(id="p", position=Vec3(1.0, 0.0, 0.0)),))
    renamed = Scene(primitives=(Point(id="q"),))
    changed_kind = Scene(
        primitives=(
            Polyline(
                id="p",
                points=(Vec3(0.0, 0.0, 0.0), Vec3(1.0, 0.0, 0.0)),
            ),
        )
    )

    assert _structure_compatible(first, moved)
    assert not _structure_compatible(first, renamed)
    assert not _structure_compatible(first, changed_kind)


def test_structure_compatibility_tracks_material_resource_identity() -> None:
    red = Material(id="main", base_color=Color(1.0, 0.0, 0.0, 1.0))
    blue_same_id = Material(id="main", base_color=Color(0.0, 0.0, 1.0, 1.0))
    other_id = Material(id="other")

    first = Scene(primitives=(Point(id="p", material_id="main"),), materials=(red,))
    recolored = Scene(
        primitives=(Point(id="p", material_id="main"),),
        materials=(blue_same_id,),
    )
    replaced_resource = Scene(
        primitives=(Point(id="p", material_id="other"),),
        materials=(other_id,),
    )

    assert _structure_compatible(first, recolored)
    assert not _structure_compatible(first, replaced_resource)


def test_common_only_change_detects_transform_updates() -> None:
    first = Point(id="p", position=Vec3(1.0, 2.0, 3.0))
    moved_object = Point(
        id="p",
        position=first.position,
        transform=Transform3D(translation=Vec3(5.0, 0.0, 0.0)),
    )
    changed_geometry = Point(id="p", position=Vec3(2.0, 2.0, 3.0))

    assert _common_only_change(first, moved_object)
    assert not _common_only_change(first, changed_geometry)


class _FakeSplinePoint:
    def __init__(self) -> None:
        self.co = None


class _FakeSpline:
    def __init__(self, count: int) -> None:
        self.points = [_FakeSplinePoint() for _ in range(count)]


class _FakeCurve:
    def __init__(self, count: int) -> None:
        self.splines = [_FakeSpline(count)]


class _FakeNativeObject:
    def __init__(self, count: int) -> None:
        self.data = _FakeCurve(count)


def test_dynamic_polyline_points_update_existing_native_buffer() -> None:
    previous = Polyline(
        id="wave",
        points=(
            Vec3(0.0, 0.0, 0.0),
            Vec3(1.0, 0.0, 0.0),
            Vec3(2.0, 0.0, 0.0),
        ),
    )
    current = Polyline(
        id="wave",
        points=(
            Vec3(0.0, 1.0, 0.0),
            Vec3(1.0, 2.0, 0.0),
            Vec3(2.0, 1.0, 0.0),
        ),
    )
    native = _FakeNativeObject(3)

    assert _fast_update_polyline(native, previous, current)
    assert native.data.splines[0].points[0].co == (0.0, 1.0, 0.0, 1.0)
    assert native.data.splines[0].points[1].co == (1.0, 2.0, 0.0, 1.0)
    assert native.data.splines[0].points[2].co == (2.0, 1.0, 0.0, 1.0)
