from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal

from spectra.core.types import Vec2
from spectra.domains.mathematics.fields2d import TimeDependentVectorField2D, VectorField2D
from spectra.domains.registry import DomainDependency, DomainRegistry


IntegralCurveMode2D = Literal["field", "normalized"]


@dataclass(frozen=True, slots=True)
class IntegralCurveProblem2D:
    field: VectorField2D
    initial_position: Vec2
    initial_parameter: float = 0.0
    mode: IntegralCurveMode2D = "normalized"
    name: str = "integral_curve2d"

    def __post_init__(self) -> None:
        if not math.isfinite(self.initial_parameter):
            raise ValueError("2D integral-curve initial parameter must be finite")
        if self.mode not in {"field", "normalized"}:
            raise ValueError(f"unknown 2D integral-curve mode: {self.mode}")
        if not self.name:
            raise ValueError("2D integral-curve name cannot be empty")


@dataclass(frozen=True, slots=True)
class PathlineProblem2D:
    field: TimeDependentVectorField2D
    initial_position: Vec2
    initial_time: float = 0.0
    name: str = "pathline2d"

    def __post_init__(self) -> None:
        if not math.isfinite(self.initial_time):
            raise ValueError("2D pathline initial time must be finite")
        if not self.name:
            raise ValueError("2D pathline name cannot be empty")


@dataclass(frozen=True, slots=True)
class CurveSolution2D:
    parameters: tuple[float, ...]
    positions: tuple[Vec2, ...]
    name: str = "curve2d"

    def __post_init__(self) -> None:
        if not self.parameters or not self.positions:
            raise ValueError("2D field-curve solution cannot be empty")
        if len(self.parameters) != len(self.positions):
            raise ValueError("2D field-curve parameters/positions length mismatch")
        if any(right <= left for left, right in zip(self.parameters, self.parameters[1:])):
            raise ValueError("2D field-curve parameters must be strictly increasing")
        if not self.name:
            raise ValueError("2D field-curve name cannot be empty")


class FieldDynamics2DDomain:
    name = "field_dynamics.2d"
    version = "2"
    dependencies = (
        DomainDependency("mathematics.vector_field2d"),
        DomainDependency("mathematics.time_vector_field2d"),
        DomainDependency("ode.first_order_system"),
        DomainDependency("ode.solve_first_order", min_version=2),
    )

    def register(self, registry: DomainRegistry) -> None:
        from spectra.domains.field_dynamics.visualization2d import compile_curve_solution_2d_scene

        system_type = registry.require("ode.first_order_system")
        solve_ode = registry.require("ode.solve_first_order", min_version=2)

        def solve_integral_curve_2d(
            problem: IntegralCurveProblem2D,
            *,
            end_parameter: float,
            steps: int = 256,
            zero_tolerance: float = 1e-12,
        ) -> CurveSolution2D:
            if end_parameter <= problem.initial_parameter:
                raise ValueError("2D integral-curve end parameter must exceed initial parameter")
            if not math.isfinite(zero_tolerance) or zero_tolerance < 0.0:
                raise ValueError("zero_tolerance must be finite and non-negative")

            def derivative(_parameter: float, state: tuple[float, ...]) -> tuple[float, ...]:
                if len(state) != 2:
                    raise ValueError("2D integral-curve state must have dimension 2")
                vector = problem.field.evaluate(Vec2(*state))
                if problem.mode == "normalized":
                    magnitude = math.hypot(vector.x, vector.y)
                    if magnitude <= zero_tolerance:
                        return (0.0, 0.0)
                    vector = vector * (1.0 / magnitude)
                return (vector.x, vector.y)

            solution = solve_ode(
                system_type(
                    derivative=derivative,
                    initial_time=problem.initial_parameter,
                    initial_state=(problem.initial_position.x, problem.initial_position.y),
                    name=problem.name,
                ),
                end_time=float(end_parameter),
                steps=steps,
            )
            return CurveSolution2D(
                parameters=solution.times,
                positions=tuple(Vec2(*state) for state in solution.states),
                name=problem.name,
            )

        def solve_pathline_2d(
            problem: PathlineProblem2D,
            *,
            end_time: float,
            steps: int = 256,
        ) -> CurveSolution2D:
            if end_time <= problem.initial_time:
                raise ValueError("2D pathline end time must exceed initial time")

            def derivative(time: float, state: tuple[float, ...]) -> tuple[float, ...]:
                if len(state) != 2:
                    raise ValueError("2D pathline state must have dimension 2")
                vector = problem.field.evaluate(Vec2(*state), time)
                return (vector.x, vector.y)

            solution = solve_ode(
                system_type(
                    derivative=derivative,
                    initial_time=problem.initial_time,
                    initial_state=(problem.initial_position.x, problem.initial_position.y),
                    name=problem.name,
                ),
                end_time=float(end_time),
                steps=steps,
            )
            return CurveSolution2D(
                parameters=solution.times,
                positions=tuple(Vec2(*state) for state in solution.states),
                name=problem.name,
            )

        registry.register_semantic_type("field_dynamics.integral_curve_problem2d", IntegralCurveProblem2D)
        registry.register_semantic_type("field_dynamics.pathline_problem2d", PathlineProblem2D)
        registry.register_semantic_type("field_dynamics.curve_solution2d", CurveSolution2D)
        registry.provide("field_dynamics.integral_curve_problem2d", IntegralCurveProblem2D)
        registry.provide("field_dynamics.pathline_problem2d", PathlineProblem2D)
        registry.provide("field_dynamics.solve_integral_curve_2d", solve_integral_curve_2d, version=2)
        registry.provide("field_dynamics.solve_pathline_2d", solve_pathline_2d, version=2)
        registry.register_visualization(CurveSolution2D, compile_curve_solution_2d_scene)
