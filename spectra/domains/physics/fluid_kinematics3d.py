from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.types import Vec3
from spectra.core.units import VELOCITY
from spectra.domains.mathematics.fields import (
    ScalarField3D,
    TimeDependentVectorField3D,
    VectorField3D,
)
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class SteadyFlow3D:
    velocity: VectorField3D
    name: str = "steady_flow3d"

    def __post_init__(self) -> None:
        if self.velocity.output_unit is not None and self.velocity.output_unit.dimension != VELOCITY:
            raise ValueError("3D fluid velocity field must use a velocity unit")
        if not self.name:
            raise ValueError("3D flow name cannot be empty")


@dataclass(frozen=True, slots=True)
class UnsteadyFlow3D:
    velocity: TimeDependentVectorField3D
    name: str = "unsteady_flow3d"

    def __post_init__(self) -> None:
        if self.velocity.output_unit is not None and self.velocity.output_unit.dimension != VELOCITY:
            raise ValueError("3D fluid velocity field must use a velocity unit")
        if not self.name:
            raise ValueError("3D flow name cannot be empty")

    def at_time(self, time: float) -> SteadyFlow3D:
        sampled = float(time)
        if not math.isfinite(sampled):
            raise ValueError("3D flow sample time must be finite")
        return SteadyFlow3D(
            velocity=self.velocity.at_time(sampled),
            name=f"{self.name}@{sampled:g}",
        )


class FluidKinematics3DDomain:
    """3D fluid kinematics composed from generic vector calculus and field dynamics."""

    name = "physics.fluid_kinematics.3d"
    version = "1"
    dependencies = (
        DomainDependency("mathematics.scalar_field3d"),
        DomainDependency("mathematics.vector_field3d"),
        DomainDependency("mathematics.time_vector_field3d"),
        DomainDependency("calculus.divergence_at"),
        DomainDependency("calculus.curl_at"),
        DomainDependency("field_dynamics.integral_curve_problem3d"),
        DomainDependency("field_dynamics.pathline_problem3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        divergence = registry.require("calculus.divergence_at")
        curl = registry.require("calculus.curl_at")
        integral_curve_type = registry.require("field_dynamics.integral_curve_problem3d")
        pathline_type = registry.require("field_dynamics.pathline_problem3d")

        def speed_at(flow: SteadyFlow3D, position: Vec3) -> float:
            return flow.velocity.evaluate(position).magnitude

        def divergence_at(flow: SteadyFlow3D, position: Vec3, *, step: float = 1e-5) -> float:
            return float(divergence(flow.velocity, position, step=step))

        def vorticity_at(flow: SteadyFlow3D, position: Vec3, *, step: float = 1e-5) -> Vec3:
            return curl(flow.velocity, position, step=step)

        def is_locally_incompressible(
            flow: SteadyFlow3D,
            position: Vec3,
            *,
            tolerance: float = 1e-8,
            step: float = 1e-5,
        ) -> bool:
            if tolerance < 0.0 or not math.isfinite(tolerance):
                raise ValueError("3D incompressibility tolerance must be finite and non-negative")
            return abs(divergence_at(flow, position, step=step)) <= tolerance

        def speed_field(flow: SteadyFlow3D) -> ScalarField3D:
            return ScalarField3D(
                evaluator=lambda position: speed_at(flow, position),
                name=f"{flow.name}.speed",
                output_unit=flow.velocity.output_unit,
            )

        def divergence_field(flow: SteadyFlow3D, *, step: float = 1e-5) -> ScalarField3D:
            return ScalarField3D(
                evaluator=lambda position: divergence_at(flow, position, step=step),
                name=f"{flow.name}.divergence",
            )

        def vorticity_field(flow: SteadyFlow3D, *, step: float = 1e-5) -> VectorField3D:
            return VectorField3D(
                evaluator=lambda position: vorticity_at(flow, position, step=step),
                name=f"{flow.name}.vorticity",
            )

        def streamline_problem(
            flow: SteadyFlow3D,
            initial_position: Vec3,
            *,
            normalized: bool = True,
            name: str = "streamline3d",
        ):
            return integral_curve_type(
                field=flow.velocity,
                initial_position=initial_position,
                mode="normalized" if normalized else "field",
                name=name,
            )

        def pathline_problem(
            flow: UnsteadyFlow3D,
            initial_position: Vec3,
            *,
            initial_time: float = 0.0,
            name: str = "pathline3d",
        ):
            return pathline_type(
                field=flow.velocity,
                initial_position=initial_position,
                initial_time=initial_time,
                name=name,
            )

        registry.register_semantic_type("physics.fluid.steady_flow3d", SteadyFlow3D)
        registry.register_semantic_type("physics.fluid.unsteady_flow3d", UnsteadyFlow3D)
        registry.provide("physics.fluid.steady_flow3d", SteadyFlow3D)
        registry.provide("physics.fluid.unsteady_flow3d", UnsteadyFlow3D)
        registry.provide("physics.fluid.speed_at_3d", speed_at)
        registry.provide("physics.fluid.divergence_at_3d", divergence_at)
        registry.provide("physics.fluid.vorticity_at_3d", vorticity_at)
        registry.provide("physics.fluid.is_locally_incompressible_3d", is_locally_incompressible)
        registry.provide("physics.fluid.speed_field_3d", speed_field)
        registry.provide("physics.fluid.divergence_field_3d", divergence_field)
        registry.provide("physics.fluid.vorticity_field_3d", vorticity_field)
        registry.provide("physics.fluid.streamline_problem_3d", streamline_problem)
        registry.provide("physics.fluid.pathline_problem_3d", pathline_problem)
