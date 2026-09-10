"""Open the canonical Spectra Schwarzschild null-geodesic showcase in Blender.

Run inside Blender from the repository root:

    blender --python examples/blender_black_hole_geodesics.py

The trajectories are solved by Spectra before Blender receives the generic Scene.
Blender is only the native renderer for the explicit equatorial projection.
"""

from spectra.backends import IncrementalBlenderBackend
from spectra.showcases import (
    BlackHoleGeodesicShowcaseConfig,
    build_black_hole_geodesic_scene,
)


config = BlackHoleGeodesicShowcaseConfig()
scene = build_black_hole_geodesic_scene(config)
backend = IncrementalBlenderBackend()
handle = backend.create(scene)

print(
    "Spectra black-hole geodesics created:",
    f"r_s={config.schwarzschild_radius_m:.6g} m,",
    f"{len(config.impact_parameters_rs)} scattering rays + photon-sphere orbit,",
    len(scene.primitives),
    "Scene primitives",
)
