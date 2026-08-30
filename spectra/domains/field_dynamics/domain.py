from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal

from spectra.core.types import Vec3
from spectra.domains.mathematics.fields import TimeDependentVectorField3D, VectorField3D
from spectra.domains.registry import DomainDependency, DomainRegistry


IntegralCurveMode = Literal["field", "normalized"]


@dataclass(frozen=True, slots=True)
class IntegralCurveProblem3D:
    """Integral curve of a steady vector field.

    In `field` mode the parameterization satisfies dx/ds = F(x). In
    `normalized` mode only the field direction is used, which is useful for
    field-line/streamline visualization when vector magnitude should not control
    sampling density.
    """

    field: VectorField3D
    initial_position: Vec3
    initial_parameter: float = 0.0
    mode: IntegralCurveMode = "normalized"
    name: str = "integral_curve"

    def __post_init__(self) -> None:
        if not math.isfinite(self.initial_parameter):
            raise ValueError("integral-curve initial parameter must be finite")
        if self.mode not in {"field", "normalized"}:
            raise ValueError(f"unknown integral-curve mode: {self.mode}")
        if not self.name:
            raise ValueError("integral-curve name cannot be empty")


@dataclass(frozen=True, slots=True)
class PathlineProblem3D:
    """Trajectory through a time-dependent vector field: dx/dt = F(x,t)."""

    field: TimeDependentVectorField3D
    initial_position: Vec3
    initial_time: float = 0.0
    name: str = "pathline"

    def __post_init__(self) -> None:
        if not math.isfinite(self.initial_time):
            raise ValueError("pathline initial time must be finite")
        if not self.name:
            raise ValueError("pathline name cannot be empty")


@dataclass(frozen=True, slots=True)
class CurveSolution3D:
    parameters: tuple[float, ...]
    positions: tuple[Vec3, ...]
    name: str = "curve"

    def __post_init__(self) -> None:
        if not self.parameters or not self.positions:
            raise ValueError("field-curve solution cannot be empty")
        if len(self.parameters) != len(self.positions):
            raise ValueError("field-curve parameters/positions length mismatch")
        if any(right <= left for left, right in zip(self.parameters, self.parameters[1:])):
            raise ValueError("field-curve parameters must be strictly increasing")
        if not self.name:
            raise ValueError("field-curve name cannot be empty")

    @property
    def duration(self) -> float:
        return self.parameters[-1] - self.parameters[0]


class FieldDynamicsDomain:
    """ODE-backed integral curves shared by fields, fluids, and other domains."""

    name = "field_dynamics"
    version = "1"
    dependencies = (
        DomainDependency("mathematics.vector_field3d"),
        DomainDependency("mathematics.time_vector_field3d"),
        DomainDependency("ode.first_order_system"),
        DomainDependency("ode.solve_rk4"),
    )

    def register(self, registry: DomainRegistry) -> None:
        from spectra.domains.field_dynamics.visualization import compile_curve_solution_scene

        system_type = registry.require("ode.first_order_system")
        solve_ode = registry.require("ode.solve_rk4")

        def solve_integral_curve(
            problem: IntegralCurveProblem3D,
            *,
            end_parameter: float,
            steps: int = 256,
            zero_tolerance: float = 1e-12,
        ) -> CurveSolution3D:
            if end_parameter <= problem.initial_parameter:
                raise ValueError("integral-curve end parameter must exceed initial parameter")
            if not math.isfinite(zero_tolerance) or zero_tolerance < 0.0:
                raise ValueError("zero_tolerance must be finite and non-negative")

            def derivative(_parameter: float, state: tuple[float, ...]) -> tuple[float, ...]:
                if len(state) != 3:
                    raise ValueError("integral-curve ODE state must have dimension 3")
                vector = problem.field.evaluate(Vec3(*state))
                if problem.mode == "normalized":
                    magnitude = vector.magnitude
                    if magnitude <= zero_tolerance:
                        return (0.0, 0.0, 0.0)
                    vector = vector * (1.0 / magnitude)
                return (vector.x, vector.y, vector.z)

            solution = solve_ode(
                system_type(
                    derivative=derivative,
                    initial_time=problem.initial_parameter,
                    initial_state=(
                        problem.initial_position.x,
                        problem.initial_position.y,
                        problem.initial_position.z,
                    ),
                    name=problem.name,
                ),
                end_time=float(end_parameter),
                steps=steps,
            )
            return CurveSolution3D(
                parameters=solution.times,
                positions=tuple(Vec3(*state) for state in solution.states),
                name=problem.name,
            )

        def solve_pathline(
            problem: PathlineProblem3D,
            *,
            end_time: float,
            steps: int = 256,
        ) -> CurveSolution3D:
            if end_time <= problem.initial_time:
                raise ValueError("pathline end time must exceed initial time")

            def derivative(time: float, state: tuple[float, ...]) -> tuple[float, ...]:
                if len(state) != 3:
                    raise ValueError("pathline ODE state must have dimension 3")
                vector = problem.field.evaluate(Vec3(*state), time)
                return (vector.x, vector.y, vector.z)

            solution = solve_ode(
                system_type(
                    derivative=derivative,
                    initial_time=problem.initial_time,
                    initial_state=(
                        problem.initial_position.x,
                        problem.initial_position.y,
                        problem.initial_position.z,
                    ),
                    name=problem.name,
                ),
                end_time=float(end_time),
                steps=steps,
            )
            return CurveSolution3D(
                parameters=solution.times,
                positions=tuple(Vec3(*state) for state in solution.states),
                name=problem.name,
            )

        registry.register_semantic_type("field_dynamics.integral_curve_problem3d", IntegralCurveProblem3D)
        registry.register_semantic_type("field_dynamics.pathline_problem3d", PathlineProblem3D)
        registry.register_semantic_type("field_dynamics.curve_solution3d", CurveSolution3D)
        registry.provide("field_dynamics.integral_curve_problem3d", IntegralCurveProblem3D)
        registry.provide("field_dynamics.pathline_problem3d", PathlineProblem3D)
        registry.provide("field_dynamics.solve_integral_curve", solve_integral_curve)
        registry.provide("field_dynamics.solve_pathline", solve_pathline)
        registry.register_visualization(CurveSolution3D, compile_curve_solution_scene)
