import math

import pytest

from spectra.core.primitives import Polyline
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.differential_geometry import (
    GeodesicProblem,
    GeodesicView3D,
    MetricTensorField,
)
from spectra.domains.tensor_algebra import Tensor


def test_flat_metric_has_zero_curvature() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["differential_geometry"])
    metric = MetricTensorField.constant(((1.0, 0.0), (0.0, 1.0)), name="plane")

    riemann = registry.require("geometry.riemann_curvature", min_version=2)(metric, (0.2, -0.4))
    ricci = registry.require("geometry.ricci_tensor", min_version=2)(metric, (0.2, -0.4))
    scalar = registry.require("geometry.scalar_curvature", min_version=2)(metric, (0.2, -0.4))

    assert max(abs(value) for value in riemann.values) < 1e-8
    assert max(abs(value) for value in ricci.values) < 1e-8
    assert scalar == pytest.approx(0.0, abs=1e-8)


def test_unit_sphere_scalar_curvature_is_two() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["differential_geometry"])

    metric = MetricTensorField(
        2,
        lambda point: Tensor.matrix(
            (
                (1.0, 0.0),
                (0.0, math.sin(point[0]) ** 2),
            ),
            name="sphere.metric",
        ),
        name="sphere",
    )
    scalar = registry.require("geometry.scalar_curvature", min_version=2)(
        metric,
        (math.pi / 2.0, 0.3),
        step=2e-4,
    )
    assert scalar == pytest.approx(2.0, rel=2e-3, abs=2e-3)


def test_euclidean_geodesic_is_straight_and_visualizable() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["differential_geometry.geodesics"])
    metric = MetricTensorField.constant(((1.0, 0.0), (0.0, 1.0)), name="plane")
    problem = GeodesicProblem.of(metric, (0.0, 0.0), (1.0, 2.0), name="straight")

    solve = registry.require("geometry.solve_geodesic")
    solution = solve(problem, end_parameter=2.0, steps=20)
    assert solution.positions[-1][0] == pytest.approx(2.0, abs=1e-8)
    assert solution.positions[-1][1] == pytest.approx(4.0, abs=1e-8)

    scene = registry.compile_scene(GeodesicView3D(solution, axes=(0, 1, None), name="path"))
    assert len(scene.primitives) == 1
    assert isinstance(scene.primitives[0], Polyline)
    assert scene.primitives[0].points[-1].x == pytest.approx(2.0, abs=1e-8)
    assert scene.primitives[0].points[-1].y == pytest.approx(4.0, abs=1e-8)
