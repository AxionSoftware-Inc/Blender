from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.domains.partial_differential_equations import (
    BoundaryMode2D,
    ScalarPDEProblem2D,
    ScalarPDESolution2D,
    UniformGrid2D,
    compile_scalar_pde_solution_2d_scene,
)
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class DiffusionProblem2D:
    grid: UniformGrid2D
    initial_values: tuple[float, ...]
    diffusivity: float
    boundary: BoundaryMode2D = "fixed"
    initial_time: float = 0.0
    name: str = "diffusion2d"

    def __post_init__(self) -> None:
        if len(self.initial_values) != self.grid.count:
            raise ValueError("2D diffusion initial_values length must match grid")
        if not math.isfinite(self.diffusivity) or self.diffusivity <= 0.0:
            raise ValueError("2D diffusivity must be finite and positive")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown 2D diffusion boundary mode: {self.boundary}")
        if not math.isfinite(self.initial_time):
            raise ValueError("2D diffusion initial_time must be finite")


@dataclass(frozen=True, slots=True)
class DiffusionSolution2D:
    pde_solution: ScalarPDESolution2D
    diffusivity: float
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


def compile_diffusion_solution_2d_scene(solution: DiffusionSolution2D):
    return compile_scalar_pde_solution_2d_scene(solution.pde_solution)


class Diffusion2DDomain:
    """2D diffusion physics composed entirely from generic 2D PDE capabilities."""

    name = "physics.diffusion.2d"
    version = "1"
    dependencies = (
        DomainDependency("pde.uniform_grid2d"),
        DomainDependency("pde.laplacian_2d"),
        DomainDependency("pde.solve_method_of_lines_2d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        laplacian = registry.require("pde.laplacian_2d")
        solve_pde = registry.require("pde.solve_method_of_lines_2d")

        def solve_diffusion_2d(
            problem: DiffusionProblem2D,
            *,
            end_time: float,
            steps: int = 256,
        ) -> DiffusionSolution2D:
            scalar_problem = ScalarPDEProblem2D(
                grid=problem.grid,
                initial_values=tuple(float(value) for value in problem.initial_values),
                rhs=lambda _time, grid, values: tuple(
                    problem.diffusivity * curvature
                    for curvature in laplacian(values, grid, boundary=problem.boundary)
                ),
                initial_time=problem.initial_time,
                name=problem.name,
            )
            solution = solve_pde(scalar_problem, end_time=end_time, steps=steps)
            return DiffusionSolution2D(
                pde_solution=solution,
                diffusivity=problem.diffusivity,
                boundary=problem.boundary,
            )

        registry.register_semantic_type("physics.diffusion.problem2d", DiffusionProblem2D)
        registry.register_semantic_type("physics.diffusion.solution2d", DiffusionSolution2D)
        registry.provide("physics.diffusion.problem2d", DiffusionProblem2D)
        registry.provide("physics.diffusion.solve2d", solve_diffusion_2d)
        registry.register_visualization(DiffusionSolution2D, compile_diffusion_solution_2d_scene)
