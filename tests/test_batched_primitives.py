import pytest

from spectra.core.bounds import scene_local_bounds
from spectra.core.primitives import PointCloud, VectorGlyphSet
from spectra.core.scene import Scene
from spectra.core.serialization import scene_from_json, scene_to_json
from spectra.core.types import Color, Vec3


def test_point_cloud_is_one_scene_node_for_many_instances() -> None:
    cloud = PointCloud(
        id="particles",
        positions=(
            Vec3(-2.0, 0.0, 0.0),
            Vec3(0.0, 1.0, 0.0),
            Vec3(3.0, 0.0, 0.0),
        ),
        radius=0.1,
        radii=(0.1, 0.2, 0.3),
    )
    scene = Scene(primitives=(cloud,))

    assert cloud.instance_count == 3
    assert len(scene.primitives) == 1
    bounds = scene_local_bounds(scene)
    assert bounds.minimum == Vec3(-2.1, -0.1, -0.1)
    assert bounds.maximum == Vec3(3.3, 1.2, 0.3)


def test_batched_primitives_round_trip_through_scene_json() -> None:
    scene = Scene(
        primitives=(
            PointCloud(
                id="samples",
                positions=(Vec3(0.0, 0.0, 0.0), Vec3(1.0, 2.0, 3.0)),
                colors=(Color(1.0, 0.0, 0.0, 1.0), Color(0.0, 1.0, 0.0, 1.0)),
            ),
            VectorGlyphSet(
                id="field",
                origins=(Vec3(0.0, 0.0, 0.0), Vec3(1.0, 0.0, 0.0)),
                vectors=(Vec3(1.0, 0.0, 0.0), Vec3(0.0, 1.0, 0.0)),
            ),
        )
    )

    restored = scene_from_json(scene_to_json(scene))
    assert restored == scene


def test_batched_primitives_validate_parallel_arrays() -> None:
    with pytest.raises(ValueError, match="origins and vectors"):
        VectorGlyphSet(
            id="bad-field",
            origins=(Vec3(0.0, 0.0, 0.0),),
            vectors=(Vec3(1.0, 0.0, 0.0), Vec3(0.0, 1.0, 0.0)),
        )

    with pytest.raises(ValueError, match="radii"):
        PointCloud(
            id="bad-cloud",
            positions=(Vec3(0.0, 0.0, 0.0), Vec3(1.0, 0.0, 0.0)),
            radii=(0.1,),
        )
