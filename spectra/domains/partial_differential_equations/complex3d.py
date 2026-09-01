from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
import math

from spectra.domains.partial_differential_equations.domain3d import (
    BoundaryMode3D,
    ScalarPDESolution3D,
    UniformGrid3D,
)
from spectra.domains.registry import DomainDependency, DomainRegistry


ComplexState3D = tuple[complex, ...]
ComplexPDERhs3D = Callable[[float, UniformGrid3D, ComplexState3D], ComplexState3D]


@dataclass(frozen=True, slots=True)
class ComplexPDEProblem3D:
    grid: UniformGrid3D
    initial_values: ComplexState3D
    rhs: ComplexPDERhs3D
    initial_time: float = 0.0
    name: str = "complex_pde_3d"

    def __post_init__(self) -> None:
        if len(self.initial_values) != self.grid.count:
            raise ValueError("complex 3D PDE initial_values length must match grid")
        if not all(
            math.isfinite(complex(value).real) and math.isfinite(complex(value).imag)
            for value in self.initial_values
        ):
            raise ValueError("complex 3D PDE initial values must be finite")
        if not math.isfinite(self.initial_time):
            raise ValueError("complex 3D PDE initial_time must be finite")
        if not self.name:
            raise ValueError("complex 3D PDE problem name cannot be empty")


@dataclass(frozen=True, slots=True)
class ComplexPDESolution3D:
    grid: UniformGrid3D
    times: tuple[float, ...]
    states: tuple[ComplexState3D, ...]
    name: str = "complex_pde_3d"

    def __post_init__(self) -> None:
        if not self.times or not self.states:
            raise ValueError("complex 3D PDE solution cannot be empty")
        if len(self.times) != len(self.states):
            raise ValueError("complex 3D PDE solution times/states length mismatch")
        if any(len(state) != self.grid.count for state in self.states):
            raise ValueError("complex 3D PDE state length must match grid")
        if any(right <= left for left, right in zip(self.times, self.times[1:])):
            raise ValueError("complex 3D PDE solution times must be strictly increasing")

    @property
    def duration(self) -> float:
        return self.times[-1] - self.times[0]

    def magnitude_squared_solution(self) -> ScalarPDESolution3D:
        return ScalarPDESolution3D(
            grid=self.grid,
            times=self.times,
            states=tuple(
                tuple(abs(value) ** 2 for value in state)
                for state in self.states
            ),
            name=f"{self.name}.magnitude_squared",
        )


def _encode_complex_state(values: ComplexState3D) -> tuple[float, ...]:
    return tuple(
        component
        for value in values
        for component in (float(value.real), float(value.imag))
    )


def _decode_complex_state(values: tuple[float, ...], count: int) -> ComplexState3D:
    if len(values) != count * 2:
        raise ValueError("encoded complex 3D PDE state has invalid dimension")
    return tuple(
        complex(values[index], values[index + 1])
        for index in range(0, len(values), 2)
    )


class ComplexPDE3DDomain:
    """Complex-valued 3D PDE dynamics lowered to the selectable real ODE role."""

    name = "partial_differential_equations.complex3d"
    version = "2"
    dependencies = (
        DomainDependency("pde.uniform_grid3d"),
        DomainDependency("pde.laplacian_3d"),
        DomainDependency("ode.first_order_system"),
        DomainDependency("ode.solve_first_order", min_version=2),
    )

    def register(self, registry: DomainRegistry) -> None:
        system_type = registry.require("ode.first_order_system")
        solve_ode = registry.require("ode.solve_first_order", min_version=2)
        real_laplacian = registry.require("pde.laplacian_3d")

        def complex_laplacian_3d(
            values: Iterable[complex],
            grid: UniformGrid3D,
            *,
            boundary: BoundaryMode3D = "fixed",
        ) -> ComplexState3D:
            state = tuple(complex(value) for value in values)
            if len(state) != grid.count:
                raise ValueError("complex 3D field values length must match grid")
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

        def solve_complex_method_of_lines_3d(
            problem: ComplexPDEProblem3D,
            *,
            end_time: float,
            steps: int = 128,
        ) -> ComplexPDESolution3D:
            def derivative(time: float, encoded: tuple[float, ...]) -> tuple[float, ...]:
                state = _decode_complex_state(encoded, problem.grid.count)
                result = tuple(
                    complex(value)
                    for value in problem.rhs(time, problem.grid, state)
                )
                if len(result) != problem.grid.count:
                    raise ValueError("complex 3D PDE rhs returned wrong state dimension")
                if not all(
                    math.isfinite(value.real) and math.isfinite(value.imag)
                    for value in result
                ):
                    raise ValueError("complex 3D PDE rhs returned non-finite derivative")
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
            return ComplexPDESolution3D(
                grid=problem.grid,
                times=ode_solution.times,
                states=tuple(
                    _decode_complex_state(state, problem.grid.count)
                    for state in ode_solution.states
                ),
                name=problem.name,
            )

        registry.register_semantic_type("pde.complex.problem3d", ComplexPDEProblem3D)
        registry.register_semantic_type("pde.complex.solution3d", ComplexPDESolution3D)
        registry.provide("pde.complex.problem3d", ComplexPDEProblem3D)
        registry.provide("pde.complex.solution3d", ComplexPDESolution3D)
        registry.provide("pde.complex.laplacian_3d", complex_laplacian_3d)
        registry.provide(
            "pde.complex.solve_method_of_lines_3d",
            solve_complex_method_of_lines_3d,
            version=2,
        )
