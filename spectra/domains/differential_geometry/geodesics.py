from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import math

from spectra.domains.differential_geometry.domain import MetricTensorField
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class GeodesicProblem:
    metric: MetricTensorField
    initial_position: tuple[float, ...]
    initial_velocity: tuple[float, ...]
    initial_parameter: float = 0.0
    name: str = "geodesic"

    def __post_init__(self) -> None:
        if len(self.initial_position) != self.metric.dimension:
            raise ValueError("geodesic position dimension must match metric")
        if len(self.initial_velocity) != self.metric.dimension:
            raise ValueError("geodesic velocity dimension must match metric")
        if not all(math.isfinite(value) for value in self.initial_position):
            raise ValueError("geodesic initial position must be finite")
        if not all(math.isfinite(value) for value in self.initial_velocity):
            raise ValueError("geodesic initial velocity must be finite")
        if not math.isfinite(self.initial_parameter):
            raise ValueError("geodesic initial parameter must be finite")
        if not self.name:
            raise ValueError("geodesic name cannot be empty")

    @classmethod
    def of(
        cls,
        metric: MetricTensorField,
        position: Iterable[float],
        velocity: Iterable[float],
        *,
        initial_parameter: float = 0.0,
        name: str = "geodesic",
    ) -> "GeodesicProblem":
        return cls(
            metric=metric,
            initial_position=tuple(float(value) for value in position),
            initial_velocity=tuple(float(value) for value in velocity),
            initial_parameter=float(initial_parameter),
            name=name,
        )


@dataclass(frozen=True, slots=True)
class GeodesicSolution:
    parameters: tuple[float, ...]
    positions: tuple[tuple[float, ...], ...]
    velocities: tuple[tuple[float, ...], ...]
    metric_dimension: int
    name: str = "geodesic"

    def __post_init__(self) -> None:
        if not self.parameters:
            raise ValueError("geodesic solution cannot be empty")
        if not (
            len(self.parameters) == len(self.positions) == len(self.velocities)
        ):
            raise ValueError("geodesic solution arrays must have equal length")
        if self.metric_dimension < 1:
            raise ValueError("geodesic metric dimension must be positive")
        if any(len(value) != self.metric_dimension for value in self.positions):
            raise ValueError("geodesic position dimension mismatch")
        if any(len(value) != self.metric_dimension for value in self.velocities):
            raise ValueError("geodesic velocity dimension mismatch")

    @property
    def duration(self) -> float:
        return self.parameters[-1] - self.parameters[0]


@dataclass(frozen=True, slots=True)
class GeodesicView3D:
    """Explicit projection of an N-dimensional geodesic into visual 3-space.

    Each axis is either a source coordinate index or None, which maps that visual
    axis to zero. Projection stays explicit so a renderer never guesses how to
    display 4D spacetime or higher-dimensional geometry.
    """

    solution: GeodesicSolution
    axes: tuple[int | None, int | None, int | None] = (0, 1, None)
    name: str = "geodesic_view"

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("geodesic view name cannot be empty")
        for axis in self.axes:
            if axis is not None and not 0 <= axis < self.solution.metric_dimension:
                raise ValueError("geodesic projection axis is out of range")


class GeodesicsDomain:
    """Geodesic dynamics built from geometry connection + generic ODE solver."""

    name = "differential_geometry.geodesics"
    version = "2"
    dependencies = (
        DomainDependency("geometry.metric_tensor_field"),
        DomainDependency("geometry.christoffel_symbols"),
        DomainDependency("ode.first_order_system"),
        DomainDependency("ode.solve_rk4"),
    )

    def register(self, registry: DomainRegistry) -> None:
        from spectra.domains.differential_geometry.visualization import (
            compile_geodesic_view_scene,
        )

        christoffel = registry.require("geometry.christoffel_symbols")
        system_type = registry.require("ode.first_order_system")
        solve_ode = registry.require("ode.solve_rk4")

        def solve_geodesic(
            problem: GeodesicProblem,
            *,
            end_parameter: float,
            steps: int = 256,
            derivative_step: float = 1e-5,
        ) -> GeodesicSolution:
            dimension = problem.metric.dimension
            if end_parameter <= problem.initial_parameter:
                raise ValueError("geodesic end_parameter must be greater than initial_parameter")
            if derivative_step <= 0.0 or not math.isfinite(derivative_step):
                raise ValueError("geodesic derivative_step must be finite and positive")

            initial_state = problem.initial_position + problem.initial_velocity

            def derivative(_parameter: float, state: tuple[float, ...]) -> tuple[float, ...]:
                if len(state) != dimension * 2:
                    raise ValueError("geodesic ODE state has invalid dimension")
                position = tuple(state[:dimension])
                velocity = tuple(state[dimension:])
                gamma = christoffel(
                    problem.metric,
                    position,
                    step=derivative_step,
                )
                acceleration = tuple(
                    -sum(
                        gamma.at(upper, lower_a, lower_b)
                        * velocity[lower_a]
                        * velocity[lower_b]
                        for lower_a in range(dimension)
                        for lower_b in range(dimension)
                    )
                    for upper in range(dimension)
                )
                return velocity + acceleration

            solution = solve_ode(
                system_type(
                    derivative=derivative,
                    initial_time=problem.initial_parameter,
                    initial_state=initial_state,
                    name=problem.name,
                ),
                end_time=float(end_parameter),
                steps=steps,
            )
            positions = tuple(tuple(state[:dimension]) for state in solution.states)
            velocities = tuple(tuple(state[dimension:]) for state in solution.states)
            return GeodesicSolution(
                parameters=solution.times,
                positions=positions,
                velocities=velocities,
                metric_dimension=dimension,
                name=problem.name,
            )

        registry.register_semantic_type("geometry.geodesic_problem", GeodesicProblem)
        registry.register_semantic_type("geometry.geodesic_solution", GeodesicSolution)
        registry.register_semantic_type("geometry.geodesic_view3d", GeodesicView3D)
        registry.provide("geometry.geodesic_problem", GeodesicProblem)
        registry.provide("geometry.geodesic_view3d", GeodesicView3D, version=2)
        registry.provide("geometry.solve_geodesic", solve_geodesic)
        registry.register_visualization(GeodesicView3D, compile_geodesic_view_scene)
