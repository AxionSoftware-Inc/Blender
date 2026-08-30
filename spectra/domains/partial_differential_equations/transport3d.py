from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.types import Vec3
from spectra.domains.mathematics.fields import TimeDependentVectorField3D
from spectra.domains.partial_differential_equations.domain3d import (
    BoundaryMode3D,
    ScalarPDESolution3D,
    UniformGrid3D,
)
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class AdvectionDiffusionProblem3D:
    """Transported scalar satisfying du/dt + v·grad(u) = D laplacian(u)."""

    grid: UniformGrid3D
    initial_values: tuple[float, ...]
    velocity: TimeDependentVectorField3D
    diffusivity: float = 0.0
    boundary: BoundaryMode3D = "fixed"
    initial_time: float = 0.0
    name: str = "advection_diffusion_3d"

    def __post_init__(self) -> None:
        if len(self.initial_values) != self.grid.count:
            raise ValueError("3D transport initial_values length must match grid")
        if not all(math.isfinite(float(value)) for value in self.initial_values):
            raise ValueError("3D transport initial values must be finite")
        if not math.isfinite(self.diffusivity) or self.diffusivity < 0.0:
            raise ValueError("3D transport diffusivity must be finite and non-negative")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown 3D transport boundary mode: {self.boundary}")
        if not math.isfinite(self.initial_time):
            raise ValueError("3D transport initial_time must be finite")
        if not self.name:
            raise ValueError("3D transport problem name cannot be empty")


@dataclass(frozen=True, slots=True)
class AdvectionDiffusionSolution3D:
    pde_solution: ScalarPDESolution3D
    diffusivity: float
    velocity_name: str
    boundary: BoundaryMode3D

    @property
    def grid(self) -> UniformGrid3D:
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


def _neighbor(index: int, count: int, direction: int, boundary: BoundaryMode3D) -> int | None:
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
    raise ValueError(f"unknown 3D transport boundary mode: {boundary}")


def upwind_advection_3d(
    values: tuple[float, ...],
    grid: UniformGrid3D,
    velocity: TimeDependentVectorField3D,
    *,
    time: float,
    boundary: BoundaryMode3D = "fixed",
) -> tuple[float, ...]:
    """Return v·grad(u) using first-order upwind derivatives on a 3D grid."""

    if len(values) != grid.count:
        raise ValueError("3D transport values length must match grid")
    result = [0.0] * grid.count

    for z_index, z in enumerate(grid.z.coordinates):
        for y_index, y in enumerate(grid.y.coordinates):
            for x_index, x in enumerate(grid.x.coordinates):
                center_index = grid.flat_index(x_index, y_index, z_index)
                if boundary == "fixed" and (
                    x_index in {0, grid.x.count - 1}
                    or y_index in {0, grid.y.count - 1}
                    or z_index in {0, grid.z.count - 1}
                ):
                    continue

                flow = velocity.evaluate(Vec3(x, y, z), time)
                left = _neighbor(x_index, grid.x.count, -1, boundary)
                right = _neighbor(x_index, grid.x.count, 1, boundary)
                lower = _neighbor(y_index, grid.y.count, -1, boundary)
                upper = _neighbor(y_index, grid.y.count, 1, boundary)
                back = _neighbor(z_index, grid.z.count, -1, boundary)
                front = _neighbor(z_index, grid.z.count, 1, boundary)
                if None in {left, right, lower, upper, back, front}:
                    continue

                center = values[center_index]
                if flow.x >= 0.0:
                    dudx = (
                        center - values[grid.flat_index(int(left), y_index, z_index)]
                    ) / grid.x.spacing
                else:
                    dudx = (
                        values[grid.flat_index(int(right), y_index, z_index)] - center
                    ) / grid.x.spacing
                if flow.y >= 0.0:
                    dudy = (
                        center - values[grid.flat_index(x_index, int(lower), z_index)]
                    ) / grid.y.spacing
                else:
                    dudy = (
                        values[grid.flat_index(x_index, int(upper), z_index)] - center
                    ) / grid.y.spacing
                if flow.z >= 0.0:
                    dudz = (
                        center - values[grid.flat_index(x_index, y_index, int(back))]
                    ) / grid.z.spacing
                else:
                    dudz = (
                        values[grid.flat_index(x_index, y_index, int(front))] - center
                    ) / grid.z.spacing
                result[center_index] = flow.x * dudx + flow.y * dudy + flow.z * dudz

    return tuple(result)


class Transport3DDomain:
    """Generic 3D scalar transport composed from field and PDE capabilities."""

    name = "partial_differential_equations.transport3d"
    version = "1"
    dependencies = (
        DomainDependency("mathematics.time_vector_field3d"),
        DomainDependency("pde.scalar_problem3d"),
        DomainDependency("pde.laplacian_3d"),
        DomainDependency("pde.solve_method_of_lines_3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        scalar_problem_type = registry.require("pde.scalar_problem3d")
        laplacian = registry.require("pde.laplacian_3d")
        solve_pde = registry.require("pde.solve_method_of_lines_3d")

        def solve_transport(
            problem: AdvectionDiffusionProblem3D,
            *,
            end_time: float,
            steps: int = 128,
        ) -> AdvectionDiffusionSolution3D:
            def rhs(time: float, grid: UniformGrid3D, values: tuple[float, ...]) -> tuple[float, ...]:
                advection = upwind_advection_3d(
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
                scalar_problem_type(
                    grid=problem.grid,
                    initial_values=tuple(float(value) for value in problem.initial_values),
                    rhs=rhs,
                    initial_time=problem.initial_time,
                    name=problem.name,
                ),
                end_time=end_time,
                steps=steps,
            )
            return AdvectionDiffusionSolution3D(
                pde_solution=pde_solution,
                diffusivity=problem.diffusivity,
                velocity_name=problem.velocity.name,
                boundary=problem.boundary,
            )

        registry.register_semantic_type("pde.transport3d.problem", AdvectionDiffusionProblem3D)
        registry.register_semantic_type("pde.transport3d.solution", AdvectionDiffusionSolution3D)
        registry.provide("pde.transport3d.problem", AdvectionDiffusionProblem3D)
        registry.provide("pde.transport3d.solution", AdvectionDiffusionSolution3D)
        registry.provide("pde.transport3d.upwind_advection", upwind_advection_3d)
        registry.provide("pde.transport3d.solve", solve_transport)
