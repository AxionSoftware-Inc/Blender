from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.types import Vec2
from spectra.domains.mathematics.fields2d import TimeDependentVectorField2D
from spectra.domains.partial_differential_equations.domain2d import (
    BoundaryMode2D,
    ScalarPDEProblem2D,
    ScalarPDESolution2D,
    UniformGrid2D,
)
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class AdvectionDiffusionProblem2D:
    """Transported scalar satisfying du/dt + v·grad(u) = D laplacian(u)."""

    grid: UniformGrid2D
    initial_values: tuple[float, ...]
    velocity: TimeDependentVectorField2D
    diffusivity: float = 0.0
    boundary: BoundaryMode2D = "fixed"
    initial_time: float = 0.0
    name: str = "advection_diffusion_2d"

    def __post_init__(self) -> None:
        if len(self.initial_values) != self.grid.count:
            raise ValueError("transport initial_values length must match grid")
        if not all(math.isfinite(float(value)) for value in self.initial_values):
            raise ValueError("transport initial values must be finite")
        if not math.isfinite(self.diffusivity) or self.diffusivity < 0.0:
            raise ValueError("transport diffusivity must be finite and non-negative")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown transport boundary mode: {self.boundary}")
        if not math.isfinite(self.initial_time):
            raise ValueError("transport initial_time must be finite")
        if not self.name:
            raise ValueError("transport problem name cannot be empty")


@dataclass(frozen=True, slots=True)
class AdvectionDiffusionSolution2D:
    pde_solution: ScalarPDESolution2D
    diffusivity: float
    velocity_name: str
    boundary: BoundaryMode2D

    @property
    def grid(self) -> UniformGrid2D:
        return self.pde_solution.grid

    @property
    def times(self) -> tuple[float, ...]:
        return self.pde_solution.times

    @property
    def states(self) -> tuple[tuple[float, ...], ...]:
        return self.pde_solution.states

    @property
    def duration(self) -> float:
        return self.pde_solution.duration

    @property
    def name(self) -> str:
        return self.pde_solution.name


def _neighbor(index: int, count: int, direction: int, boundary: BoundaryMode2D) -> int | None:
    candidate = index + direction
    if 0 <= candidate < count:
        return candidate
    if boundary == "fixed":
        return None
    if boundary == "periodic":
        if index == 0 and direction < 0:
            return count - 2
        if index == count - 1 and direction > 0:
            return 1
    if boundary == "zero_gradient":
        if index == 0 and direction < 0:
            return 1
        if index == count - 1 and direction > 0:
            return count - 2
    raise ValueError(f"unknown transport boundary mode: {boundary}")


def upwind_advection_2d(
    values: tuple[float, ...],
    grid: UniformGrid2D,
    velocity: TimeDependentVectorField2D,
    *,
    time: float,
    boundary: BoundaryMode2D = "fixed",
) -> tuple[float, ...]:
    """Return v·grad(u) using first-order upwind spatial derivatives."""

    if len(values) != grid.count:
        raise ValueError("transport values length must match grid")
    result = [0.0] * grid.count
    x_coordinates = grid.x.coordinates
    y_coordinates = grid.y.coordinates

    for y_index, y in enumerate(y_coordinates):
        for x_index, x in enumerate(x_coordinates):
            center_index = grid.flat_index(x_index, y_index)
            if boundary == "fixed" and (
                x_index in {0, grid.x.count - 1}
                or y_index in {0, grid.y.count - 1}
            ):
                continue

            flow = velocity.evaluate(Vec2(x, y), time)
            left = _neighbor(x_index, grid.x.count, -1, boundary)
            right = _neighbor(x_index, grid.x.count, 1, boundary)
            lower = _neighbor(y_index, grid.y.count, -1, boundary)
            upper = _neighbor(y_index, grid.y.count, 1, boundary)
            if None in {left, right, lower, upper}:
                continue

            center = values[center_index]
            if flow.x >= 0.0:
                dudx = (center - values[grid.flat_index(int(left), y_index)]) / grid.x.spacing
            else:
                dudx = (values[grid.flat_index(int(right), y_index)] - center) / grid.x.spacing
            if flow.y >= 0.0:
                dudy = (center - values[grid.flat_index(x_index, int(lower))]) / grid.y.spacing
            else:
                dudy = (values[grid.flat_index(x_index, int(upper))] - center) / grid.y.spacing
            result[center_index] = flow.x * dudx + flow.y * dudy

    return tuple(result)


class Transport2DDomain:
    """Generic scalar transport composed from 2D fields and PDE capabilities."""

    name = "partial_differential_equations.transport2d"
    version = "1"
    dependencies = (
        DomainDependency("mathematics.time_vector_field2d"),
        DomainDependency("pde.uniform_grid2d"),
        DomainDependency("pde.laplacian_2d"),
        DomainDependency("pde.solve_method_of_lines_2d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        from spectra.domains.partial_differential_equations.visualization2d import (
            compile_scalar_pde_solution_2d_scene,
        )

        laplacian = registry.require("pde.laplacian_2d")
        solve_pde = registry.require("pde.solve_method_of_lines_2d")

        def solve_transport(
            problem: AdvectionDiffusionProblem2D,
            *,
            end_time: float,
            steps: int = 256,
        ) -> AdvectionDiffusionSolution2D:
            def rhs(time: float, grid: UniformGrid2D, values: tuple[float, ...]) -> tuple[float, ...]:
                advection = upwind_advection_2d(
                    values,
                    grid,
                    problem.velocity,
                    time=time,
                    boundary=problem.boundary,
                )
                diffusion = laplacian(values, grid, boundary=problem.boundary)
                return tuple(
                    -advective + problem.diffusivity * diffusive
                    for advective, diffusive in zip(advection, diffusion, strict=True)
                )

            pde_solution = solve_pde(
                ScalarPDEProblem2D(
                    grid=problem.grid,
                    initial_values=tuple(float(value) for value in problem.initial_values),
                    rhs=rhs,
                    initial_time=problem.initial_time,
                    name=problem.name,
                ),
                end_time=end_time,
                steps=steps,
            )
            return AdvectionDiffusionSolution2D(
                pde_solution=pde_solution,
                diffusivity=problem.diffusivity,
                velocity_name=problem.velocity.name,
                boundary=problem.boundary,
            )

        def compile_solution(solution: AdvectionDiffusionSolution2D):
            return compile_scalar_pde_solution_2d_scene(solution.pde_solution)

        registry.register_semantic_type(
            "pde.transport2d.problem",
            AdvectionDiffusionProblem2D,
        )
        registry.register_semantic_type(
            "pde.transport2d.solution",
            AdvectionDiffusionSolution2D,
        )
        registry.provide("pde.transport2d.problem", AdvectionDiffusionProblem2D)
        registry.provide("pde.transport2d.upwind_advection", upwind_advection_2d)
        registry.provide("pde.transport2d.solve", solve_transport)
        registry.register_visualization(AdvectionDiffusionSolution2D, compile_solution)
