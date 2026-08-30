import pytest

from spectra.core.bounds import scene_local_bounds
from spectra.core.materials import Material
from spectra.core.primitives import Light, Point, Surface
from spectra.core.scene import Scene
from spectra.core.serialization import scene_from_json, scene_to_json
from spectra.core.transforms import Transform3D
from spectra.core.types import Color, Vec3
from spectra.presentation import staggered_reveal


def test_scene_validates_material_references() -> None:
    material = Material(
        id="surface.mat",
        base_color=Color(0.2, 0.5, 1.0, 1.0),
        shading="lit",
        roughness=0.3,
    )
    scene = Scene(
        materials=(material,),
        primitives=(Point(id="probe", material_id="surface.mat"),),
    )
    assert scene.material("surface.mat") == material

    with pytest.raises(ValueError, match="unknown material"):
        Scene(primitives=(Point(id="bad", material_id="missing"),))


def test_lights_are_scene_nodes_but_not_scientific_content_bounds() -> None:
    light = Light(
        id="key",
        light_type="directional",
        intensity=3.0,
        transform=Transform3D.look_at(
            Vec3(4.0, 5.0, 6.0),
            Vec3(0.0, 0.0, 0.0),
        ),
    )
    scene = Scene(
        primitives=(
            Point(id="probe", position=Vec3(1.0, 2.0, 3.0), radius=0.25),
            light,
        )
    )
    bounds = scene_local_bounds(scene)
    assert bounds.minimum == Vec3(0.75, 1.75, 2.75)
    assert bounds.maximum == Vec3(1.25, 2.25, 3.25)


def test_materials_and_lights_round_trip_and_survive_presentation() -> None:
    material = Material(
        id="glasslike",
        base_color=Color(0.25, 0.7, 1.0, 0.8),
        shading="lit",
        metallic=0.1,
        roughness=0.15,
        emission_color=Color(0.1, 0.3, 1.0, 1.0),
        emission_strength=0.5,
    )
    scene = Scene(
        materials=(material,),
        primitives=(
            Surface(
                id="surface",
                vertices=(
                    Vec3(0.0, 0.0, 0.0),
                    Vec3(1.0, 0.0, 0.0),
                    Vec3(0.0, 1.0, 0.0),
                ),
                triangles=((0, 1, 2),),
                material_id="glasslike",
            ),
            Light(id="fill", light_type="ambient", intensity=0.4),
        ),
    )

    restored = scene_from_json(scene_to_json(scene))
    assert restored == scene

    presented = staggered_reveal(scene)
    assert presented.materials == scene.materials
    assert all(track.target_id != "fill" for track in presented.timeline.tracks)
