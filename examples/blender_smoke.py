"""End-to-end Spectra -> Blender smoke scene.

Run inside Blender later, for example:
    blender --python examples/blender_smoke.py

The script intentionally never imports bpy. Blender is reached only through the
Spectra backend boundary.
"""

from dataclasses import replace
import math

from spectra.backends import BlenderBackend
from spectra.core.materials import Material
from spectra.core.primitives import Light, Surface
from spectra.core.scene import Scene
from spectra.core.transforms import Transform3D
from spectra.core.types import Color, Vec3
from spectra.core.framing import with_fitted_camera
from spectra.domains import DomainRegistry
from spectra.domains.mathematics import Function1D, Function2D, Interval, MathematicsDomain, RectDomain2D


registry = DomainRegistry()
registry.add_domain(MathematicsDomain())

curve = Function1D.from_expression("sin(x)", Interval(-2.0 * math.pi, 2.0 * math.pi))
curve_scene = registry.compile_scene(curve)

surface = Function2D.from_expression(
    "sin(x) * cos(y)",
    RectDomain2D(Interval(-math.pi, math.pi), Interval(-math.pi, math.pi)),
)
surface_scene = registry.compile_scene(surface)

surface_material = Material(
    id="surface.lit",
    base_color=Color(0.25, 0.55, 1.0, 1.0),
    shading="lit",
    roughness=0.35,
)

surface_primitive = surface_scene.primitives[0]
assert isinstance(surface_primitive, Surface)
surface_primitive = replace(surface_primitive, material_id="surface.lit")

key_light = Light(
    id="light.key",
    light_type="directional",
    intensity=3.0,
    transform=Transform3D.look_at(
        Vec3(6.0, -8.0, 10.0),
        Vec3(0.0, 0.0, 0.0),
        up=Vec3(0.0, 0.0, 1.0),
    ),
)

scene = Scene(
    primitives=curve_scene.primitives + (surface_primitive, key_light),
    materials=(surface_material,),
)
scene = with_fitted_camera(
    scene,
    camera_id="camera.main",
    aspect_ratio=16.0 / 9.0,
    direction=Vec3(1.0, -1.2, 0.9),
)

backend = BlenderBackend()
handle = backend.create(scene)
print(
    "Spectra Blender smoke scene created:",
    handle.collection_name,
    "with",
    len(scene.primitives),
    "Scene primitives",
)
