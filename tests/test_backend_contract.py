from __future__ import annotations

import math

import pytest

from spectra.backends import (
    BackendCapabilities,
    BackendCompatibilityError,
    BackendSession,
    MemoryBackend,
    validate_backend_compatibility,
)
from spectra.core.animation import Timeline, move_track
from spectra.core.materials import Material
from spectra.core.primitives import Point, Surface
from spectra.core.scene import Scene
from spectra.core.types import Vec3


def test_backend_session_receives_static_sampled_scenes() -> None:
    scene = Scene(
        primitives=(Point(id="probe"),),
        timeline=Timeline(
            duration=2.0,
            tracks=(
                move_track(
                    "probe",
                    Vec3(0.0, 0.0, 0.0),
                    Vec3(4.0, 0.0, 0.0),
                    start_time=0.0,
                    end_time=2.0,
                ),
            ),
        ),
    )
    backend = MemoryBackend()
    session = BackendSession.open(backend, scene)

    assert session.handle.scene.timeline.tracks == ()
    sampled = session.seek(1.0)
    assert sampled.timeline.tracks == ()
    assert session.handle.scene == sampled
    assert math.isclose(session.handle.scene.get("probe").transform.translation.x, 2.0)

    session.close()
    assert session.handle.destroyed is True
    with pytest.raises(RuntimeError, match="closed"):
        session.seek(1.5)


def test_backend_capabilities_reject_unsupported_primitive_kind() -> None:
    scene = Scene(
        primitives=(
            Surface(
                id="surface",
                vertices=(
                    Vec3(0.0, 0.0, 0.0),
                    Vec3(1.0, 0.0, 0.0),
                    Vec3(0.0, 1.0, 0.0),
                ),
                triangles=((0, 1, 2),),
            ),
        )
    )
    point_only = BackendCapabilities(frozenset({"point"}))

    with pytest.raises(BackendCompatibilityError, match="surface"):
        validate_backend_compatibility(scene, point_only)


def test_backend_can_explicitly_reject_material_resources() -> None:
    scene = Scene(
        materials=(Material(id="scientific"),),
        primitives=(Point(id="probe", material_id="scientific"),),
    )
    no_materials = BackendCapabilities(
        frozenset({"point"}),
        supports_materials=False,
    )

    with pytest.raises(BackendCompatibilityError, match="materials"):
        validate_backend_compatibility(scene, no_materials)
