from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.constants import SPEED_OF_LIGHT, VACUUM_PERMITTIVITY
from spectra.core.types import Vec3
from spectra.core.units import CURRENT_DENSITY
from spectra.domains.mathematics.fields import TimeDependentVectorField3D
from spectra.domains.partial_differential_equations.domain3d import BoundaryMode3D, UniformGrid3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class MaxwellProblem3D:
    grid: UniformGrid3D
    initial_electric: tuple[Vec3, ...]
    initial_magnetic: tuple[Vec3, ...]
    boundary: BoundaryMode3D = "fixed"
    current_density: TimeDependentVectorField3D | None = None
    initial_time: float = 0.0
    name: str = "maxwell3d"

    def __post_init__(self) -> None:
        if len(self.initial_electric) != self.grid.count:
            raise ValueError("Maxwell electric sample count must match grid")
        if len(self.initial_magnetic) != self.grid.count:
            raise ValueError("Maxwell magnetic sample count must match grid")
        if any(not isinstance(value, Vec3) for value in self.initial_electric):
            raise TypeError("Maxwell electric samples must be Vec3")
        if any(not isinstance(value, Vec3) for value in self.initial_magnetic):
            raise TypeError("Maxwell magnetic samples must be Vec3")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown Maxwell boundary mode: {self.boundary}")
        if self.current_density is not None and self.current_density.output_unit is not None:
            if self.current_density.output_unit.dimension != CURRENT_DENSITY:
                raise ValueError("Maxwell current-density field has incompatible units")
        if not math.isfinite(self.initial_time):
            raise ValueError("Maxwell initial_time must be finite")
        if not self.name:
            raise ValueError("Maxwell name cannot be empty")


@dataclass(frozen=True, slots=True)
class MaxwellSolution3D:
    grid: UniformGrid3D
    times: tuple[float, ...]
    electric_states: tuple[tuple[Vec3, ...], ...]
    magnetic_states: tuple[tuple[Vec3, ...], ...]
    boundary: BoundaryMode3D
    source_free: bool
    name: str = "maxwell3d"

    def __post_init__(self) -> None:
        if not self.times:
            raise ValueError("Maxwell solution cannot be empty")
        if not (
            len(self.times) == len(self.electric_states) == len(self.magnetic_states)
        ):
            raise ValueError("Maxwell history length mismatch")
        if any(len(state) != self.grid.count for state in self.electric_states):
            raise ValueError("Maxwell electric state length must match grid")
        if any(len(state) != self.grid.count for state in self.magnetic_states):
            raise ValueError("Maxwell magnetic state length must match grid")
        if any(right <= left for left, right in zip(self.times, self.times[1:])):
            raise ValueError("Maxwell times must be strictly increasing")

    @property
    def duration(self) -> float:
        return self.times[-1] - self.times[0]


def _is_boundary(grid: UniformGrid3D, index: int) -> bool:
    xy = grid.x.count * grid.y.count
    z_index = index // xy
    rem = index % xy
    y_index = rem // grid.x.count
    x_index = rem % grid.x.count
    return (
        x_index in {0, grid.x.count - 1}
        or y_index in {0, grid.y.count - 1}
        or z_index in {0, grid.z.count - 1}
    )


def _encode_pair(electric: tuple[Vec3, ...], magnetic: tuple[Vec3, ...]) -> tuple[float, ...]:
    return tuple(
        component
        for state in (electric, magnetic)
        for value in state
        for component in (value.x, value.y, value.z)
    )


def _decode_vectors(values: tuple[float, ...], count: int) -> tuple[Vec3, ...]:
    if len(values) != count * 3:
        raise ValueError("encoded Maxwell vector state has invalid dimension")
    return tuple(
        Vec3(values[index], values[index + 1], values[index + 2])
        for index in range(0, len(values), 3)
    )


def _decode_pair(values: tuple[float, ...], count: int) -> tuple[tuple[Vec3, ...], tuple[Vec3, ...]]:
    vector_components = count * 3
    if len(values) != vector_components * 2:
        raise ValueError("encoded Maxwell state has invalid dimension")
    return (
        _decode_vectors(tuple(values[:vector_components]), count),
        _decode_vectors(tuple(values[vector_components:]), count),
    )


def _vector_to_si(field: TimeDependentVectorField3D, value: Vec3) -> Vec3:
    unit = field.output_unit
    if unit is None:
        return value
    return Vec3(unit.to_si(value.x), unit.to_si(value.y), unit.to_si(value.z))


class Maxwell3DDomain:
    """Vacuum/source Maxwell evolution lowered to the selectable real ODE role."""

    name = "physics.electromagnetism.maxwell3d"
    version = "2"
    dependencies = (
        DomainDependency("pde.uniform_grid3d"),
        DomainDependency("pde.curl_grid_3d"),
        DomainDependency("ode.first_order_system"),
        DomainDependency("ode.solve_first_order", min_version=2),
    )

    def register(self, registry: DomainRegistry) -> None:
        curl = registry.require("pde.curl_grid_3d")
        system_type = registry.require("ode.first_order_system")
        solve_ode = registry.require("ode.solve_first_order", min_version=2)
        c_squared = SPEED_OF_LIGHT.si_value ** 2
        inverse_epsilon = 1.0 / VACUUM_PERMITTIVITY.si_value

        def solve(
            problem: MaxwellProblem3D,
            *,
            end_time: float,
            steps: int = 128,
        ) -> MaxwellSolution3D:
            count = problem.grid.count

            def derivative(time: float, state: tuple[float, ...]) -> tuple[float, ...]:
                electric, magnetic = _decode_pair(state, count)
                curl_b = curl(magnetic, problem.grid, boundary=problem.boundary)
                curl_e = curl(electric, problem.grid, boundary=problem.boundary)
                d_e = []
                d_b = []
                for index, (cb, ce) in enumerate(zip(curl_b, curl_e, strict=True)):
                    if problem.boundary == "fixed" and _is_boundary(problem.grid, index):
                        d_e.append(Vec3(0.0, 0.0, 0.0))
                        d_b.append(Vec3(0.0, 0.0, 0.0))
                        continue
                    current = Vec3(0.0, 0.0, 0.0)
                    if problem.current_density is not None:
                        x, y, z = problem.grid.coordinates[index]
                        current = _vector_to_si(
                            problem.current_density,
                            problem.current_density.evaluate(Vec3(x, y, z), time),
                        )
                    d_e.append(cb * c_squared - current * inverse_epsilon)
                    d_b.append(ce * -1.0)
                return _encode_pair(tuple(d_e), tuple(d_b))

            solution = solve_ode(
                system_type(
                    derivative=derivative,
                    initial_time=problem.initial_time,
                    initial_state=_encode_pair(problem.initial_electric, problem.initial_magnetic),
                    name=problem.name,
                ),
                end_time=end_time,
                steps=steps,
            )
            electric_states = []
            magnetic_states = []
            for state in solution.states:
                electric, magnetic = _decode_pair(tuple(state), count)
                electric_states.append(electric)
                magnetic_states.append(magnetic)
            return MaxwellSolution3D(
                grid=problem.grid,
                times=solution.times,
                electric_states=tuple(electric_states),
                magnetic_states=tuple(magnetic_states),
                boundary=problem.boundary,
                source_free=problem.current_density is None,
                name=problem.name,
            )

        registry.register_semantic_type("physics.maxwell.problem3d", MaxwellProblem3D)
        registry.register_semantic_type("physics.maxwell.solution3d", MaxwellSolution3D)
        registry.provide("physics.maxwell.problem3d", MaxwellProblem3D)
        registry.provide("physics.maxwell.solution3d", MaxwellSolution3D)
        registry.provide("physics.maxwell.solve3d", solve, version=2)
