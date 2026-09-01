from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
import math

from spectra.core.animation import Keyframe, Timeline, Track
from spectra.core.primitives import Polyline
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.domains.partial_differential_equations.domain import (
    BoundaryMode1D,
    UniformGrid1D,
)
from spectra.domains.registry import DomainDependency, DomainRegistry


ComplexState1D = tuple[complex, ...]
ComplexPDERhs1D = Callable[[float, UniformGrid1D, ComplexState1D], ComplexState1D]


@dataclass(frozen=True, slots=True)
class ComplexPDEProblem1D:
    grid: UniformGrid1D
    initial_values: ComplexState1D
    rhs: ComplexPDERhs1D
    initial_time: float = 0.0
    name: str = "complex_pde_1d"

    def __post_init__(self) -> None:
        if len(self.initial_values) != self.grid.count:
            raise ValueError("complex PDE initial_values length must match grid")
        if not all(
            math.isfinite(complex(value).real) and math.isfinite(complex(value).imag)
            for value in self.initial_values
        ):
            raise ValueError("complex PDE initial values must be finite")
        if not math.isfinite(self.initial_time):
            raise ValueError("complex PDE initial_time must be finite")
        if not self.name:
            raise ValueError("complex PDE problem name cannot be empty")


@dataclass(frozen=True, slots=True)
class ComplexPDESolution1D:
    grid: UniformGrid1D
    times: tuple[float, ...]
    states: tuple[ComplexState1D, ...]
    name: str = "complex_pde_1d"

    def __post_init__(self) -> None:
        if not self.times or not self.states:
            raise ValueError("complex PDE solution cannot be empty")
        if len(self.times) != len(self.states):
            raise ValueError("complex PDE solution times/states length mismatch")
        if any(len(state) != self.grid.count for state in self.states):
            raise ValueError("complex PDE state length must match grid")
        if any(right <= left for left, right in zip(self.times, self.times[1:])):
            raise ValueError("complex PDE solution times must be strictly increasing")

    @property
    def duration(self) -> float:
        return self.times[-1] - self.times[0]


def complex_second_derivative_1d(
    values: Iterable[complex],
    grid: UniformGrid1D,
    *,
    boundary: BoundaryMode1D = "fixed",
) -> ComplexState1D:
    state = tuple(complex(value) for value in values)
    if len(state) != grid.count:
        raise ValueError("complex field values length must match grid")
    if boundary not in {"fixed", "periodic", "zero_gradient"}:
        raise ValueError(f"unknown 1D boundary mode: {boundary}")

    inv_h2 = 1.0 / (grid.spacing * grid.spacing)
    result = [0.0j] * grid.count
    for index in range(1, grid.count - 1):
        result[index] = (
            state[index - 1] - 2.0 * state[index] + state[index + 1]
        ) * inv_h2

    if boundary == "periodic":
        result[0] = (state[-2] - 2.0 * state[0] + state[1]) * inv_h2
        result[-1] = (state[-2] - 2.0 * state[-1] + state[1]) * inv_h2
    elif boundary == "zero_gradient":
        result[0] = 2.0 * (state[1] - state[0]) * inv_h2
        result[-1] = 2.0 * (state[-2] - state[-1]) * inv_h2
    return tuple(result)


def _encode_complex_state(values: ComplexState1D) -> tuple[float, ...]:
    return tuple(
        component
        for value in values
        for component in (float(value.real), float(value.imag))
    )


def _decode_complex_state(values: tuple[float, ...], count: int) -> ComplexState1D:
    if len(values) != count * 2:
        raise ValueError("encoded complex PDE state has invalid dimension")
    return tuple(
        complex(values[index], values[index + 1])
        for index in range(0, len(values), 2)
    )


def compile_complex_pde_solution_scene(
    solution: ComplexPDESolution1D,
) -> Scene:
    coordinates = solution.grid.coordinates
    names = (
        f"{solution.name}.real",
        f"{solution.name}.imaginary",
        f"{solution.name}.magnitude_squared",
    )

    def points(state: ComplexState1D, component: str) -> tuple[Vec3, ...]:
        if component == "real":
            values = (value.real for value in state)
        elif component == "imaginary":
            values = (value.imag for value in state)
        else:
            values = (abs(value) ** 2 for value in state)
        return tuple(
            Vec3(x, float(value), 0.0)
            for x, value in zip(coordinates, values, strict=True)
        )

    start = solution.times[0]
    components = ("real", "imaginary", "magnitude_squared")
    colors = (
        Color(0.35, 0.7, 1.0, 1.0),
        Color(1.0, 0.55, 0.3, 1.0),
        Color(0.55, 1.0, 0.55, 1.0),
    )
    primitives = []
    tracks = []
    for name, component, color in zip(names, components, colors, strict=True):
        keyframes = tuple(
            Keyframe(time - start, points(state, component), "linear")
            for time, state in zip(solution.times, solution.states, strict=True)
        )
        primitives.append(Polyline(id=name, points=keyframes[0].value, color=color))
        if solution.duration > 0.0:
            tracks.append(
                Track(
                    target_id=name,
                    property_path="points",
                    keyframes=keyframes,
                )
            )

    return Scene(
        primitives=tuple(primitives),
        timeline=Timeline(duration=solution.duration, tracks=tuple(tracks)),
    )


class ComplexPartialDifferentialEquationsDomain:
    name = "partial_differential_equations.complex"
    version = "2"
    dependencies = (
        DomainDependency("pde.uniform_grid1d"),
        DomainDependency("ode.first_order_system"),
        DomainDependency("ode.solve_first_order", min_version=2),
    )

    def register(self, registry: DomainRegistry) -> None:
        system_type = registry.require("ode.first_order_system")
        solve_ode = registry.require("ode.solve_first_order", min_version=2)

        def solve_complex_method_of_lines(
            problem: ComplexPDEProblem1D,
            *,
            end_time: float,
            steps: int = 256,
        ) -> ComplexPDESolution1D:
            def derivative(time: float, encoded: tuple[float, ...]) -> tuple[float, ...]:
                state = _decode_complex_state(encoded, problem.grid.count)
                result = tuple(complex(value) for value in problem.rhs(time, problem.grid, state))
                if len(result) != problem.grid.count:
                    raise ValueError("complex PDE rhs returned wrong state dimension")
                if not all(math.isfinite(value.real) and math.isfinite(value.imag) for value in result):
                    raise ValueError("complex PDE rhs returned non-finite derivative")
                return _encode_complex_state(result)

            ode_solution = solve_ode(
                system_type(
                    derivative=derivative,
                    initial_time=problem.initial_time,
                    initial_state=_encode_complex_state(problem.initial_values),
                    name=problem.name,
                ),
                end_time=end_time,
                steps=steps,
            )
            return ComplexPDESolution1D(
                grid=problem.grid,
                times=ode_solution.times,
                states=tuple(
                    _decode_complex_state(state, problem.grid.count)
                    for state in ode_solution.states
                ),
                name=problem.name,
            )

        registry.register_semantic_type("pde.complex.problem1d", ComplexPDEProblem1D)
        registry.register_semantic_type("pde.complex.solution1d", ComplexPDESolution1D)
        registry.provide("pde.complex.problem1d", ComplexPDEProblem1D)
        registry.provide("pde.complex.second_derivative_1d", complex_second_derivative_1d)
        registry.provide("pde.complex.solve_method_of_lines", solve_complex_method_of_lines, version=2)
        registry.register_visualization(
            ComplexPDESolution1D,
            compile_complex_pde_solution_scene,
        )
