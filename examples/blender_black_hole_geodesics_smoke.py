"""Targeted Blender 5.2 smoke for the Schwarzschild null-geodesic flagship.

Run from the repository root:

    blender --background --python examples/blender_black_hole_geodesics_smoke.py
"""

from __future__ import annotations

import math

import bpy

from spectra.backends import IncrementalBlenderBackend
from spectra.showcases import (
    BlackHoleGeodesicShowcaseConfig,
    build_black_hole_geodesic_scene,
)


config = BlackHoleGeodesicShowcaseConfig(
    photon_orbit_steps=48,
    scatter_steps=64,
    impact_parameters_rs=(2.7, 3.2, 4.0),
    horizon_latitudes=6,
    horizon_longitudes=16,
)
scene = build_black_hole_geodesic_scene(config)
backend = IncrementalBlenderBackend()
handle = backend.create(scene)

horizon_id = "showcase.black_hole.event_horizon.surface"
photon_id = "showcase.black_hole.photon_orbit.trajectory"
horizon = bpy.data.objects[handle.object_names[horizon_id]]
photon = bpy.data.objects[handle.object_names[photon_id]]

horizon_object_pointer = horizon.as_pointer()
horizon_data_pointer = horizon.data.as_pointer()
photon_object_pointer = photon.as_pointer()
photon_data_pointer = photon.data.as_pointer()

assert len(handle.object_names) < 40, "black-hole showcase expanded into too many objects"
assert len(horizon.data.vertices) > 40
assert len(photon.data.splines) == 1
assert len(photon.data.splines[0].points) >= 2

# The renderer receives normalized r/r_s coordinates. The solved photon orbit
# should therefore remain at radius ~1.5 in the native XY projection.
photon_points = tuple(
    point.co
    for point in photon.data.splines[0].points
)
photon_radii = tuple(math.hypot(float(point.x), float(point.y)) for point in photon_points)
assert max(abs(radius - 1.5) for radius in photon_radii) < 2e-3

for index in range(len(config.impact_parameters_rs)):
    ray_id = f"showcase.black_hole.scatter_{index:02d}.trajectory"
    ray = bpy.data.objects[handle.object_names[ray_id]]
    assert len(ray.data.splines) == 1
    assert len(ray.data.splines[0].points) >= 2
    radii = tuple(
        math.hypot(float(point.co.x), float(point.co.y))
        for point in ray.data.splines[0].points
    )
    assert min(radii) > 1.05
    assert min(radii) < config.scatter_start_radius_rs

# No-op re-application must preserve stable native identities for the main
# context mesh and one representative solver-generated trajectory.
backend.apply(handle, scene)
updated_horizon = bpy.data.objects[handle.object_names[horizon_id]]
updated_photon = bpy.data.objects[handle.object_names[photon_id]]
assert updated_horizon.as_pointer() == horizon_object_pointer
assert updated_horizon.data.as_pointer() == horizon_data_pointer
assert updated_photon.as_pointer() == photon_object_pointer
assert updated_photon.data.as_pointer() == photon_data_pointer

collection_name = handle.collection_name
backend.destroy(handle)
assert bpy.data.collections.get(collection_name) is None

print(
    "Spectra black-hole geodesics Blender smoke PASS:",
    f"{len(config.impact_parameters_rs)} bending rays + photon orbit,",
    "explicit r/r_s projection, native identity preserved, cleanup PASS",
)
