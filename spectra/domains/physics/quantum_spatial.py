from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import math

from spectra.core.primitives import Polyline
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.domains.mathematics import ComplexFunction1D, Interval
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class SpatialWavefunction1D:
    """Normalized complex wavefunction over a finite real spatial interval."""

    function: ComplexFunction1D
    source_norm: float
    name: str = "wavefunction"

    def __post_init__(self) -> None:
        if not math.isfinite(self.source_norm) or self.source_norm <= 0.0:
            raise ValueError("wavefunction source_norm must be finite and positive")
        if not self.name:
            raise ValueError("wavefunction name cannot be empty")

    @property
    def domain(self) -> Interval:
        return self.function.domain

    def evaluate(self, x: float) -> complex:
        return self.function.evaluate(x)

    def probability_density(self, x: float) -> float:
        return abs(self.evaluate(x)) ** 2


def compile_spatial_wavefunction_scene(
    wavefunction: SpatialWavefunction1D,
    *,
    samples: int = 192,
) -> Scene:
    """Show real part, imaginary part, and probability density together."""

    if samples < 2:
        raise ValueError("wavefunction visualization samples must be >= 2")
    step = wavefunction.domain.length / (samples - 1)
    real_points: list[Vec3] = []
    imag_points: list[Vec3] = []
    density_points: list[Vec3] = []
    for index in range(samples):
        x = wavefunction.domain.start + step * index
        value = wavefunction.evaluate(x)
        real_points.append(Vec3(x, value.real, 0.0))
        imag_points.append(Vec3(x, value.imag, 0.0))
        density_points.append(Vec3(x, abs(value) ** 2, 0.0))

    prefix = wavefunction.name
    return Scene(
        primitives=(
            Polyline(
                id=f"{prefix}.real",
                points=tuple(real_points),
                color=Color(0.35, 0.7, 1.0, 1.0),
            ),
            Polyline(
                id=f"{prefix}.imaginary",
                points=tuple(imag_points),
                color=Color(1.0, 0.55, 0.3, 1.0),
            ),
            Polyline(
                id=f"{prefix}.probability_density",
                points=tuple(density_points),
                color=Color(0.55, 1.0, 0.55, 1.0),
            ),
        )
    )


class SpatialQuantumDomain:
    """Spatial quantum semantics composed from complex math, calculus, and probability."""

    name = "physics.quantum.spatial"
    version = "1"
    dependencies = (
        DomainDependency("mathematics.complex_function1d"),
        DomainDependency("calculus.integrate", min_version=3),
        DomainDependency("probability.continuous.make_distribution"),
        DomainDependency("probability.continuous.probability_between"),
    )

    def register(self, registry: DomainRegistry) -> None:
        complex_function_type = registry.require("mathematics.complex_function1d")
        integrate = registry.require("calculus.integrate", min_version=3)
        make_distribution = registry.require("probability.continuous.make_distribution")
        probability_between_distribution = registry.require(
            "probability.continuous.probability_between"
        )

        def normalize(
            source: ComplexFunction1D,
            *,
            name: str = "wavefunction",
            integration_steps: int = 1024,
        ) -> SpatialWavefunction1D:
            density = source.magnitude_squared(name=f"{name}.source_density")
            total_probability = float(integrate(density, steps=integration_steps))
            if not math.isfinite(total_probability) or total_probability <= 0.0:
                raise ValueError("wavefunction has zero or invalid total probability")
            norm = math.sqrt(total_probability)
            normalized = complex_function_type(
                evaluator=lambda x, **parameters: source.evaluate(x, **parameters) / norm,
                domain=source.domain,
                name=name,
            )
            return SpatialWavefunction1D(
                function=normalized,
                source_norm=norm,
                name=name,
            )

        def make_wavefunction(
            evaluator: Callable[..., complex],
            domain: Interval,
            *,
            name: str = "wavefunction",
            integration_steps: int = 1024,
        ) -> SpatialWavefunction1D:
            source = complex_function_type(evaluator=evaluator, domain=domain, name=name)
            return normalize(source, name=name, integration_steps=integration_steps)

        def position_distribution(wavefunction: SpatialWavefunction1D):
            density = wavefunction.function.magnitude_squared(
                name=f"{wavefunction.name}.position_density"
            )
            return make_distribution(
                density,
                name=f"{wavefunction.name}.position_distribution",
            )

        def probability_between(
            wavefunction: SpatialWavefunction1D,
            start: float,
            end: float,
        ) -> float:
            return float(
                probability_between_distribution(
                    position_distribution(wavefunction),
                    start,
                    end,
                )
            )

        registry.register_semantic_type(
            "physics.quantum.spatial.wavefunction1d",
            SpatialWavefunction1D,
        )
        registry.provide("physics.quantum.spatial.make_wavefunction", make_wavefunction)
        registry.provide("physics.quantum.spatial.normalize", normalize)
        registry.provide(
            "physics.quantum.spatial.position_distribution",
            position_distribution,
        )
        registry.provide(
            "physics.quantum.spatial.probability_between",
            probability_between,
        )
        registry.register_visualization(
            SpatialWavefunction1D,
            compile_spatial_wavefunction_scene,
        )
