from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
import math

from spectra.domains.partial_differential_equations.domain2d import (
    BoundaryMode2D,
    ScalarPDESolution2D,
    UniformGrid2D,
)
from spectra.domains.registry import DomainDependency, DomainRegistry


ComplexState2D = tuple[complex, ...]
ComplexPDERhs2D = Callable[[float, UniformGrid2D, ComplexState2D], ComplexState2D]


@dataclass(frozen=True, slots=True)
class ComplexPDEProblem2D:
    grid: UniformGrid2D
    initial_values: ComplexState2D
    rhs: ComplexPDERhs2D
    initial_time: float = 0.0
    name: str = "complex_pde_2d"

    def __post_init__(self) -> None:
        if len(self.initial_values) != self.grid.count:
            raise ValueError("complex 2D PDE initial_values length must match grid")
        if not all(
            math.isfinite(complex(value).real) and math.isfinite(complex(value).imag)
            for value in self.initial_values
        ):
            raise ValueError("complex 2D PDE initial values must be finite")
        if not math.isfinite(self.initial_time):
            raise ValueError("complex 2D PDE initial_time must be finite")
        if not self.name:
            raise ValueError("complex 2D PDE problem name cannot be empty")


@dataclass(frozen=True, slots=True)
class ComplexPDESolution2D:
    grid: UniformGrid2D
    times: tuple[float, ...]
    states: tuple[ComplexState2D, ...]
    name: str = "complex_pde_2d"

    def __post_init__(self) -> None:
        if not self.times or not self.states:
            raise ValueError("complex 2D PDE solution cannot be empty")
        if len(self.times) != len(self.states):
            raise ValueError("complex 2D PDE solution times/states length mismatch")
        if any(len(state) != self.grid.count for state in self.states):
            raise ValueError("complex 2D PDE state length must match grid")
        if any(right <= left for left, right in zip(self.times, self.times[1:])):
            raise ValueError("complex 2D PDE solution times must be strictly increasing")

    @property
    def duration(self) -> float:
        return self.times[-1] - self.times[0]

    def magnitude_squared_solution(self) -> ScalarPDESolution2D:
        return ScalarPDESolution2D(
            grid=self.grid,
            times=self.times,
            states=tuple(
                tuple(abs(value) ** 2 for value in state)
                for state in self.states
            ),
            name=f"{self.name}.magnitude_squared",
        )


def _encode_complex_state(values: ComplexState2D) -> tuple[float, ...]:
    return tuple(
        component
        for value in values
        for component in (float(value.real), float(value.imag))
    )


def _decode_complex_state(values: tuple[float, ...], count: int) -> ComplexState2D:
    if len(values) != count * 2:
        raise ValueError("encoded complex 2D PDE state has invalid dimension")
    return tuple(
        complex(values[index], values[index + 1])
        for index in range(0, len(values), 2)
    )


class ComplexPDE2DDomain:
    name = "partial_differential_equations.complex2d"
    version = "2"
    dependencies = (
        DomainDependency("pde.uniform_grid2d"),
        DomainDependency("pde.laplacian_2d"),
        DomainDependency("ode.first_order_system"),
        DomainDependency("ode.solve_first_order", min_version=2),
    )

    def register(self, registry: DomainRegistry) -> None:
        from spectra.domains.partial_differential_equations.visualization2d import (
            compile_scalar_pde_solution_2d_scene,
        )

        system_type = registry.require("ode.first_order_system")
        solve_ode = registry.require("ode.solve_first_order", min_version=2)
        real_laplacian = registry.require("pde.laplacian_2d")

        def complex_laplacian_2d(
            values: Iterable[complex],
            grid: UniformGrid2D,
            *,
            boundary: BoundaryMode2D = "fixed",
        ) -> ComplexState2D:
            state = tuple(complex(value) for value in values)
            if len(state) != grid.count:
                raise ValueError("complex 2D field values length must match grid")
            real = real_laplacian(
                tuple(value.real for value in state),
                grid,
                boundary=boundary,
            )
            imaginary = real_laplacian(
                tuple(value.imag for value in state),
                grid,
                boundary=boundary,
            )
            return tuple(
                complex(real_part, imaginary_part)
                for real_part, imaginary_part in zip(real, imaginary, strict=True)
            )

        def solve_complex_method_of_lines_2d(
            problem: ComplexPDEProblem2D,
            *,
            end_time: float,
            steps: int = 256,
        ) -> ComplexPDESolution2D:
            def derivative(time: float, encoded: tuple[float, ...]) -> tuple[float, ...]:
                state = _decode_complex_state(encoded, problem.grid.count)
                result = tuple(
                    complex(value)
                    for value in problem.rhs(time, problem.grid, state)
                )
                if len(result) != problem.grid.count:
                    raise ValueError("complex 2D PDE rhs returned wrong state dimension")
                if not all(
                    math.isfinite(value.real) and math.isfinite(value.imag)
                    for value in result
                ):
                    raise ValueError("complex 2D PDE rhs returned non-finite derivative")
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
            return ComplexPDESolution2D(
                grid=problem.grid,
                times=ode_solution.times,
                states=tuple(
                    _decode_complex_state(state, problem.grid.count)
                    for state in ode_solution.states
                ),
                name=problem.name,
            )

        def compile_solution(solution: ComplexPDESolution2D):
            return compile_scalar_pde_solution_2d_scene(
                solution.magnitude_squared_solution()
            )

        registry.register_semantic_type("pde.complex.problem2d", ComplexPDEProblem2D)
        registry.register_semantic_type("pde.complex.solution2d", ComplexPDESolution2D)
        registry.provide("pde.complex.problem2d", ComplexPDEProblem2D)
        registry.provide("pde.complex.laplacian_2d", complex_laplacian_2d)
        registry.provide(
            "pde.complex.solve_method_of_lines_2d",
            solve_complex_method_of_lines_2d,
            version=2,
        )
        registry.register_visualization(ComplexPDESolution2D, compile_solution)
