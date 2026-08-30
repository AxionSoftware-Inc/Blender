from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal

from spectra.core.constants import SPEED_OF_LIGHT
from spectra.core.types import Vec3
from spectra.domains.differential_geometry import MetricTensorField
from spectra.domains.registry import DomainDependency, DomainRegistry


IntervalKind = Literal["timelike", "lightlike", "spacelike"]
_C = SPEED_OF_LIGHT.si_value


@dataclass(frozen=True, slots=True)
class SpacetimeEvent:
    """Event in SI coordinates: time in seconds, space in meters."""

    time: float
    position: Vec3
    name: str = "event"

    def __post_init__(self) -> None:
        if not math.isfinite(self.time):
            raise ValueError("event time must be finite")
        if not all(math.isfinite(value) for value in (self.position.x, self.position.y, self.position.z)):
            raise ValueError("event position must be finite")
        if not self.name:
            raise ValueError("event name cannot be empty")

    @property
    def ct_coordinates(self) -> tuple[float, float, float, float]:
        return (_C * self.time, self.position.x, self.position.y, self.position.z)


def minkowski_metric(*, name: str = "minkowski") -> MetricTensorField:
    """Flat spacetime metric with signature (-,+,+,+) on (ct,x,y,z)."""

    return MetricTensorField.constant(
        (
            (-1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        ),
        name=name,
    )


def lorentz_factor(speed: float) -> float:
    value = abs(float(speed))
    if not math.isfinite(value):
        raise ValueError("speed must be finite")
    if value >= _C:
        raise ValueError("massive-object speed must be below the speed of light")
    beta = value / _C
    return 1.0 / math.sqrt(1.0 - beta * beta)


def four_velocity(velocity: Vec3) -> tuple[float, float, float, float]:
    speed = velocity.magnitude
    gamma = lorentz_factor(speed)
    return (
        gamma * _C,
        gamma * velocity.x,
        gamma * velocity.y,
        gamma * velocity.z,
    )


class RelativityDomain:
    """Special-relativity semantics composed from generic metric geometry."""

    name = "physics.relativity"
    version = "1"
    dependencies = (
        DomainDependency("geometry.metric_tensor_field"),
        DomainDependency("geometry.metric_inner_product"),
    )

    def register(self, registry: DomainRegistry) -> None:
        metric_inner_product = registry.require("geometry.metric_inner_product")
        metric = minkowski_metric()

        def interval_squared(left: SpacetimeEvent, right: SpacetimeEvent) -> float:
            left_ct = left.ct_coordinates
            right_ct = right.ct_coordinates
            displacement = tuple(
                right_value - left_value
                for left_value, right_value in zip(left_ct, right_ct, strict=True)
            )
            return float(
                metric_inner_product(
                    metric,
                    (0.0, 0.0, 0.0, 0.0),
                    displacement,
                    displacement,
                )
            )

        def classify_interval(
            left: SpacetimeEvent,
            right: SpacetimeEvent,
            *,
            tolerance: float = 1e-9,
        ) -> IntervalKind:
            if tolerance < 0.0 or not math.isfinite(tolerance):
                raise ValueError("interval tolerance must be finite and non-negative")
            value = interval_squared(left, right)
            scale = max(1.0, max(abs(component) for component in left.ct_coordinates + right.ct_coordinates) ** 2)
            threshold = tolerance * scale
            if value < -threshold:
                return "timelike"
            if value > threshold:
                return "spacelike"
            return "lightlike"

        def proper_time_between(left: SpacetimeEvent, right: SpacetimeEvent) -> float:
            interval = interval_squared(left, right)
            if interval >= 0.0:
                raise ValueError("proper time is defined here only for timelike separation")
            return math.sqrt(-interval) / _C

        registry.register_semantic_type("physics.relativity.event", SpacetimeEvent)
        registry.provide("physics.relativity.event", SpacetimeEvent)
        registry.provide("physics.relativity.minkowski_metric", minkowski_metric)
        registry.provide("physics.relativity.interval_squared", interval_squared)
        registry.provide("physics.relativity.classify_interval", classify_interval)
        registry.provide("physics.relativity.proper_time_between", proper_time_between)
        registry.provide("physics.relativity.lorentz_factor", lorentz_factor)
        registry.provide("physics.relativity.four_velocity", four_velocity)
