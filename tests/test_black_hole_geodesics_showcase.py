from __future__ import annotations

import math
import sys

import pytest

from spectra.core.primitives import Polyline, Surface
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.showcases import (
    BlackHoleGeodesicShowcaseConfig,
    build_black_hole_geodesic_base_scene,
    build_black_hole_geodesic_scene,
    solve_black_hole_geodesic_showcase,
)


def _config() -> BlackHoleGeodesicShowcaseConfig:
    return BlackHoleGeodesicShowcaseConfig(
        photon_orbit_steps=48,
        scatter_steps=64,
        impact_parameters_rs=(2.7, 3.2, 4.0),
        scatter_parameter_length_rs=16.0,
        horizon_latitudes=6,
        horizon_longitudes=16,
    )


@pytest.fixture(scope="module")
def result():
    return solve_black_hole_geodesic_showcase(_config())


@pytest.fixture(scope="module")
def base_scene():
    return build_black_hole_geodesic_base_scene(_config())


def _metric_norm(metric, position, velocity) -> float:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["differential_geometry"])
    inner = registry.require("geometry.metric_inner_product")
    return float(inner(metric, position, velocity, velocity))


def test_black_hole_showcase_solves_null_geodesics_with_generic_engine(result) -> None:
    metric = result.spacetime.metric()
    solutions = (result.photon_orbit, *result.scattering_rays)
    for solution in solutions:
        assert abs(_metric_norm(metric, solution.positions[0], solution.velocities[0])) < 1e-9
        assert solution.metric_dimension == 4
        assert len(solution.positions) >= 2

    radius_s = result.spacetime.schwarzschild_radius
    orbit_radii = tuple(position[1] / radius_s for position in result.photon_orbit.positions)
    assert max(abs(radius - 1.5) for radius in orbit_radii) < 2e-3
    assert result.photon_orbit.positions[-1][3] == pytest.approx(2.0 * math.pi, abs=3e-3)


def test_scattering_rays_bend_outside_the_event_horizon(result) -> None:
    radius_s = result.spacetime.schwarzschild_radius
    for solution in result.scattering_rays:
        radii = tuple(position[1] / radius_s for position in solution.positions)
        assert radii[0] == pytest.approx(_config().scatter_start_radius_rs)
        assert min(radii) > 1.05
        assert min(radii) < radii[0]
        assert radii[-1] > min(radii) + 1.0
        assert solution.positions[-1][3] > solution.positions[0][3]


def test_base_scene_is_explicit_normalized_equatorial_projection(base_scene) -> None:
    assert base_scene.timeline.duration == 0.0
    assert base_scene.timeline.tracks == ()
    assert "bpy" not in sys.modules

    horizon = base_scene.get("showcase.black_hole.event_horizon.surface")
    photon = base_scene.get("showcase.black_hole.photon_orbit.trajectory")
    assert isinstance(horizon, Surface)
    assert isinstance(photon, Polyline)

    photon_radii = tuple(math.hypot(point.x, point.y) for point in photon.points)
    assert max(abs(radius - 1.5) for radius in photon_radii) < 2e-3

    for index in range(len(_config().impact_parameters_rs)):
        ray = base_scene.get(f"showcase.black_hole.scatter_{index:02d}.trajectory")
        assert isinstance(ray, Polyline)
        assert math.hypot(ray.points[0].x, ray.points[0].y) == pytest.approx(
            _config().scatter_start_radius_rs,
            rel=1e-9,
        )
        assert min(math.hypot(point.x, point.y) for point in ray.points) > 1.05

    assert "equatorial projection" in base_scene.get(
        "showcase.black_hole.label.projection"
    ).text
    assert "solved null geodesics" in base_scene.get(
        "showcase.black_hole.label.scale"
    ).text


def test_presented_black_hole_scene_adds_only_presentation_resources() -> None:
    config = _config()
    base = build_black_hole_geodesic_base_scene(config)
    presented = build_black_hole_geodesic_scene(config)

    base_ids = {primitive.id for primitive in base.primitives}
    assert presented.active_camera_id == "presentation.camera.primary"
    assert presented.get("presentation.title.primary").text == (
        "Schwarzschild Black Hole · Null Geodesics"
    )
    assert presented.timeline.duration == 0.0
    assert all(
        primitive.id.startswith("presentation.")
        for primitive in presented.primitives
        if primitive.id not in base_ids
    )

    # Presentation must not rewrite the solver-generated projected paths.
    for trajectory_id in (
        "showcase.black_hole.photon_orbit.trajectory",
        "showcase.black_hole.scatter_00.trajectory",
        "showcase.black_hole.scatter_01.trajectory",
        "showcase.black_hole.scatter_02.trajectory",
    ):
        assert presented.get(trajectory_id) == base.get(trajectory_id)


def test_black_hole_showcase_rejects_captured_ray_configuration() -> None:
    critical = 1.5 * math.sqrt(3.0)
    with pytest.raises(ValueError, match="critical value"):
        BlackHoleGeodesicShowcaseConfig(impact_parameters_rs=(critical,))
    with pytest.raises(ValueError, match="photon sphere"):
        BlackHoleGeodesicShowcaseConfig(scatter_start_radius_rs=1.5)
