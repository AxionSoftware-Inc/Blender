from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.constants import GRAVITATIONAL_CONSTANT, SPEED_OF_LIGHT
from spectra.core.units import KILOGRAM, MASS, Quantity
from spectra.domains.differential_geometry import MetricTensorField
from spectra.domains.registry import DomainDependency, DomainRegistry
from spectra.domains.tensor_algebra import Tensor


_G = GRAVITATIONAL_CONSTANT.si_value
_C = SPEED_OF_LIGHT.si_value


@dataclass(frozen=True, slots=True)
class SchwarzschildSpacetime:
    """Exterior Schwarzschild spacetime in coordinates (ct, r, theta, phi)."""

    mass: Quantity
    name: str = "schwarzschild"

    def __post_init__(self) -> None:
        if self.mass.unit.dimension != MASS:
            raise ValueError("Schwarzschild mass must have mass dimension")
        if self.mass.si_value <= 0.0:
            raise ValueError("Schwarzschild mass must be positive")
        if not self.name:
            raise ValueError("Schwarzschild spacetime name cannot be empty")

    @classmethod
    def kilograms(cls, mass: float, *, name: str = "schwarzschild") -> "SchwarzschildSpacetime":
        return cls(Quantity(float(mass), KILOGRAM), name=name)

    @property
    def schwarzschild_radius(self) -> float:
        return 2.0 * _G * self.mass.si_value / (_C * _C)

    def metric(self) -> MetricTensorField:
        radius_s = self.schwarzschild_radius
        name = self.name

        def evaluate(point: tuple[float, ...]) -> Tensor:
            _ct, radius, theta, _phi = point
            if radius <= radius_s:
                raise ValueError("reference Schwarzschild chart requires r > Schwarzschild radius")
            factor = 1.0 - radius_s / radius
            sin_theta = math.sin(theta)
            return Tensor.matrix(
                (
                    (-factor, 0.0, 0.0, 0.0),
                    (0.0, 1.0 / factor, 0.0, 0.0),
                    (0.0, 0.0, radius * radius, 0.0),
                    (0.0, 0.0, 0.0, radius * radius * sin_theta * sin_theta),
                ),
                name=f"{name}.metric",
            )

        return MetricTensorField(4, evaluate, name=f"{name}.metric")


class GeneralRelativityDomain:
    """Relativity-specific tensors composed from generic differential geometry."""

    name = "physics.relativity.general"
    version = "1"
    dependencies = (
        DomainDependency("geometry.metric_tensor_field"),
        DomainDependency("geometry.ricci_tensor", min_version=2),
        DomainDependency("geometry.scalar_curvature", min_version=2),
    )

    def register(self, registry: DomainRegistry) -> None:
        ricci_tensor = registry.require("geometry.ricci_tensor", min_version=2)
        scalar_curvature = registry.require("geometry.scalar_curvature", min_version=2)

        def einstein_tensor(
            metric: MetricTensorField,
            point: tuple[float, ...],
            *,
            step: float = 1e-4,
        ) -> Tensor:
            ricci = ricci_tensor(metric, point, step=step)
            scalar = scalar_curvature(metric, point, step=step)
            covariant_metric = metric.evaluate(point)
            values = tuple(
                ricci.at(row, column)
                - 0.5 * scalar * covariant_metric.at(row, column)
                for row in range(metric.dimension)
                for column in range(metric.dimension)
            )
            return Tensor(
                (metric.dimension, metric.dimension),
                values,
                name=f"{metric.name}.einstein",
            )

        def vacuum_residual(
            metric: MetricTensorField,
            point: tuple[float, ...],
            *,
            step: float = 1e-4,
        ) -> float:
            tensor = einstein_tensor(metric, point, step=step)
            return math.sqrt(sum(value * value for value in tensor.values))

        registry.register_semantic_type("physics.relativity.schwarzschild", SchwarzschildSpacetime)
        registry.provide("physics.relativity.schwarzschild", SchwarzschildSpacetime)
        registry.provide("physics.relativity.einstein_tensor", einstein_tensor)
        registry.provide("physics.relativity.vacuum_residual", vacuum_residual)
