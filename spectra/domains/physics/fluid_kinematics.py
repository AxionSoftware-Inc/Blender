from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.types import Vec2
from spectra.core.units import VELOCITY
from spectra.domains.mathematics.fields2d import (
    ScalarField2D,
    TimeDependentVectorField2D,
    VectorField2D,
)
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class SteadyFlow2D:
    velocity: VectorField2D
    name: str = "steady_flow2d"

    def __post_init__(self) -> None:
        if self.velocity.output_unit is not None and self.velocity.output_unit.dimension != VELOCITY:
            raise ValueError("fluid velocity field must use a velocity unit")
        if not self.name:
            raise ValueError("flow name cannot be empty")


@dataclass(frozen=True, slots=True)
class UnsteadyFlow2D:
    velocity: TimeDependentVectorField2D
    name: str = "unsteady_flow2d"

    def __post_init__(self) -> None:
        if self.velocity.output_unit is not None and self.velocity.output_unit.dimension != VELOCITY:
            raise ValueError("fluid velocity field must use a velocity unit")
        if not self.name:
            raise ValueError("flow name cannot be empty")

    def at_time(self, time: float) -> SteadyFlow2D:
        sampled = float(time)
        if not math.isfinite(sampled):
            raise ValueError("flow sample time must be finite")
        return SteadyFlow2D(
            velocity=self.velocity.at_time(sampled),
            name=f"{self.name}@{sampled:g}",
        )


class FluidKinematics2DDomain:
    """Fluid kinematics composed from generic vector calculus and field dynamics."""

    name = "physics.fluid_kinematics.2d"
    version = "1"
    dependencies = (
        DomainDependency("mathematics.scalar_field2d"),
        DomainDependency("mathematics.vector_field2d"),
        DomainDependency("mathematics.time_vector_field2d"),
        DomainDependency("calculus.divergence_at_2d"),
        DomainDependency("calculus.scalar_curl_at_2d"),
        DomainDependency("field_dynamics.integral_curve_problem2d"),
        DomainDependency("field_dynamics.pathline_problem2d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        divergence = registry.require("calculus.divergence_at_2d")
        curl = registry.require("calculus.scalar_curl_at_2d")
        integral_curve_type = registry.require("field_dynamics.integral_curve_problem2d")
        pathline_type = registry.require("field_dynamics.pathline_problem2d")

        def speed_at(flow: SteadyFlow2D, position: Vec2) -> float:
            vector = flow.velocity.evaluate(position)
            return math.hypot(vector.x, vector.y)

        def divergence_at(flow: SteadyFlow2D, position: Vec2, *, step: float = 1e-5) -> float:
            return float(divergence(flow.velocity, position, step=step))

        def vorticity_at(flow: SteadyFlow2D, position: Vec2, *, step: float = 1e-5) -> float:
            return float(curl(flow.velocity, position, step=step))

        def is_locally_incompressible(
            flow: SteadyFlow2D,
            position: Vec2,
            *,
            tolerance: float = 1e-8,
            step: float = 1e-5,
        ) -> bool:
            if tolerance < 0.0 or not math.isfinite(tolerance):
                raise ValueError("incompressibility tolerance must be finite and non-negative")
            return abs(divergence_at(flow, position, step=step)) <= tolerance

        def speed_field(flow: SteadyFlow2D) -> ScalarField2D:
            return ScalarField2D(
                evaluator=lambda position: speed_at(flow, position),
                name=f"{flow.name}.speed",
                output_unit=flow.velocity.output_unit,
            )

        def divergence_field(flow: SteadyFlow2D, *, step: float = 1e-5) -> ScalarField2D:
            return ScalarField2D(
                evaluator=lambda position: divergence_at(flow, position, step=step),
                name=f"{flow.name}.divergence",
            )

        def vorticity_field(flow: SteadyFlow2D, *, step: float = 1e-5) -> ScalarField2D:
            return ScalarField2D(
                evaluator=lambda position: vorticity_at(flow, position, step=step),
                name=f"{flow.name}.vorticity",
            )

        def streamline_problem(
            flow: SteadyFlow2D,
            initial_position: Vec2,
            *,
            normalized: bool = True,
            name: str = "streamline",
        ):
            return integral_curve_type(
                field=flow.velocity,
                initial_position=initial_position,
                mode="normalized" if normalized else "field",
                name=name,
            )

        def pathline_problem(
            flow: UnsteadyFlow2D,
            initial_position: Vec2,
            *,
            initial_time: float = 0.0,
            name: str = "pathline",
        ):
            return pathline_type(
                field=flow.velocity,
                initial_position=initial_position,
                initial_time=initial_time,
                name=name,
            )

        registry.register_semantic_type("physics.fluid.steady_flow2d", SteadyFlow2D)
        registry.register_semantic_type("physics.fluid.unsteady_flow2d", UnsteadyFlow2D)
        registry.provide("physics.fluid.steady_flow2d", SteadyFlow2D)
        registry.provide("physics.fluid.unsteady_flow2d", UnsteadyFlow2D)
        registry.provide("physics.fluid.speed_at", speed_at)
        registry.provide("physics.fluid.divergence_at", divergence_at)
        registry.provide("physics.fluid.vorticity_at", vorticity_at)
        registry.provide("physics.fluid.is_locally_incompressible", is_locally_incompressible)
        registry.provide("physics.fluid.speed_field", speed_field)
        registry.provide("physics.fluid.divergence_field", divergence_field)
        registry.provide("physics.fluid.vorticity_field", vorticity_field)
        registry.provide("physics.fluid.streamline_problem", streamline_problem)
        registry.provide("physics.fluid.pathline_problem", pathline_problem)
