import math

import pytest

from spectra.core.constants import SPEED_OF_LIGHT
from spectra.core.types import Vec3
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.differential_geometry import MetricTensorField
from spectra.domains.physics import SchwarzschildSpacetime, SpacetimeEvent


C = SPEED_OF_LIGHT.si_value


def test_special_relativity_interval_classification_and_proper_time() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.relativity"])
    classify = registry.require("physics.relativity.classify_interval")
    interval_squared = registry.require("physics.relativity.interval_squared")
    proper_time = registry.require("physics.relativity.proper_time_between")

    origin = SpacetimeEvent(0.0, Vec3(0.0, 0.0, 0.0), name="origin")
    one_second_here = SpacetimeEvent(1.0, Vec3(0.0, 0.0, 0.0), name="later")
    light_event = SpacetimeEvent(1.0, Vec3(C, 0.0, 0.0), name="light")
    far_event = SpacetimeEvent(0.0, Vec3(10.0, 0.0, 0.0), name="far")

    assert classify(origin, one_second_here) == "timelike"
    assert classify(origin, light_event) == "lightlike"
    assert classify(origin, far_event) == "spacelike"
    assert interval_squared(origin, one_second_here) == pytest.approx(-(C * C))
    assert proper_time(origin, one_second_here) == pytest.approx(1.0)


def test_four_velocity_has_minkowski_norm_minus_c_squared() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.relativity"])
    four_velocity = registry.require("physics.relativity.four_velocity")
    inner = registry.require("geometry.metric_inner_product")
    metric = registry.require("physics.relativity.minkowski_metric")()

    value = four_velocity(Vec3(0.3 * C, 0.0, 0.0))
    norm = inner(metric, (0.0, 0.0, 0.0, 0.0), value, value)
    assert norm == pytest.approx(-(C * C), rel=1e-12)


def test_general_relativity_einstein_tensor_is_zero_for_flat_spacetime() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.relativity.general"])
    einstein = registry.require("physics.relativity.einstein_tensor")
    flat = MetricTensorField.constant(
        (
            (-1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        ),
        name="minkowski",
    )
    tensor = einstein(flat, (0.0, 1.0, 0.5, 0.2))
    assert max(abs(value) for value in tensor.values) < 1e-8


def test_schwarzschild_metric_uses_physical_mass_and_expected_radius() -> None:
    sun = SchwarzschildSpacetime.kilograms(1.98847e30)
    assert sun.schwarzschild_radius == pytest.approx(2953.34, rel=2e-4)

    metric = sun.metric()
    radius = 10.0 * sun.schwarzschild_radius
    value = metric.evaluate((0.0, radius, math.pi / 2.0, 0.0))
    factor = 1.0 - sun.schwarzschild_radius / radius
    assert value.at(0, 0) == pytest.approx(-factor)
    assert value.at(1, 1) == pytest.approx(1.0 / factor)
    assert value.at(2, 2) == pytest.approx(radius * radius)
