from __future__ import annotations

from dataclasses import dataclass

from spectra.core.primitives import Polyline
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.domains.mathematics.functions import Function1D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True)
class ContinuousDistribution1D:
    """Finite-domain continuous probability distribution.

    The source density does not need to be pre-normalized. `normalization` is
    computed through the calculus integration capability and PDF values are
    exposed as density / normalization.
    """

    density: Function1D
    normalization: float
    name: str = "distribution"

    def __post_init__(self) -> None:
        if self.normalization <= 0.0:
            raise ValueError("continuous distribution normalization must be positive")

    @property
    def domain(self):
        return self.density.domain

    def pdf(self, x: float) -> float:
        value = self.density.evaluate(x) / self.normalization
        if value < -1e-12:
            raise ValueError("continuous distribution density became negative")
        return max(value, 0.0)


def compile_continuous_distribution_scene(
    distribution: ContinuousDistribution1D,
    *,
    samples: int = 128,
    primitive_id: str = "probability.continuous.pdf",
) -> Scene:
    if samples < 2:
        raise ValueError("samples must be >= 2")
    start = distribution.domain.start
    step = distribution.domain.length / (samples - 1)
    points = tuple(
        Vec3(
            x := start + index * step,
            distribution.pdf(x),
            0.0,
        )
        for index in range(samples)
    )
    return Scene(
        primitives=(
            Polyline(
                id=primitive_id,
                points=points,
                color=Color(0.45, 0.75, 1.0, 1.0),
            ),
        )
    )


class ContinuousProbabilityDomain:
    name = "probability.continuous"
    version = "1"
    dependencies = (
        DomainDependency("mathematics.function1d"),
        DomainDependency("calculus.integrate", min_version=2),
    )

    def register(self, registry: DomainRegistry) -> None:
        integrate = registry.require("calculus.integrate", min_version=2)

        def make_distribution(
            density: Function1D,
            *,
            name: str = "distribution",
            validation_samples: int = 65,
        ) -> ContinuousDistribution1D:
            if validation_samples < 2:
                raise ValueError("validation_samples must be >= 2")
            step = density.domain.length / (validation_samples - 1)
            for index in range(validation_samples):
                x = density.domain.start + index * step
                if density.evaluate(x) < -1e-10:
                    raise ValueError("probability density cannot be negative")
            normalization = integrate(density)
            if normalization <= 0.0:
                raise ValueError("probability density must have positive total mass")
            return ContinuousDistribution1D(
                density=density,
                normalization=float(normalization),
                name=name,
            )

        def probability_between(
            distribution: ContinuousDistribution1D,
            start: float,
            end: float,
        ) -> float:
            if end < start:
                raise ValueError("probability interval end must be >= start")
            if end == start:
                return 0.0
            mass = integrate(distribution.density, start=start, end=end)
            return min(max(float(mass / distribution.normalization), 0.0), 1.0)

        def cdf(distribution: ContinuousDistribution1D, x: float) -> float:
            if x <= distribution.domain.start:
                return 0.0
            if x >= distribution.domain.end:
                return 1.0
            return probability_between(distribution, distribution.domain.start, x)

        registry.register_semantic_type(
            "probability.continuous.distribution1d",
            ContinuousDistribution1D,
        )
        registry.provide(
            "probability.continuous.make_distribution",
            make_distribution,
        )
        registry.provide(
            "probability.continuous.probability_between",
            probability_between,
        )
        registry.provide("probability.continuous.cdf", cdf)
        registry.register_visualization(
            ContinuousDistribution1D,
            compile_continuous_distribution_scene,
        )
