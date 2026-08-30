from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal

from spectra.domains.partial_differential_equations import (
    BoundaryMode1D,
    ScalarPDEProblem1D,
    ScalarPDESolution1D,
    UniformGrid1D,
    compile_scalar_pde_solution_scene,
)
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class DiffusionProblem1D:
    grid: UniformGrid1D
    initial_values: tuple[float, ...]
    diffusivity: float
    boundary: BoundaryMode1D = "fixed"
    initial_time: float = 0.0
    name: str = "diffusion1d"

    def __post_init__(self) -> None:
        if len(self.initial_values) != self.grid.count:
            raise ValueError("diffusion initial_values length must match grid")
        if not math.isfinite(self.diffusivity) or self.diffusivity <= 0.0:
            raise ValueError("diffusivity must be finite and positive")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown diffusion boundary mode: {self.boundary}")
        if not math.isfinite(self.initial_time):
            raise ValueError("diffusion initial_time must be finite")


@dataclass(frozen=True, slots=True)
class DiffusionSolution1D:
    pde_solution: ScalarPDESolution1D
    diffusivity: float
    boundary: BoundaryMode1D

    @property
    def grid(self) -> UniformGrid1D:
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


def compile_diffusion_solution_scene(solution: DiffusionSolution1D):
    return compile_scalar_pde_solution_scene(solution.pde_solution)


class DiffusionDomain:
    """Diffusion physics expressed entirely through reusable PDE capabilities."""

    name = "physics.diffusion"
    version = "1"
    dependencies = (
        DomainDependency("pde.uniform_grid1d"),
        DomainDependency("pde.second_derivative_1d"),
        DomainDependency("pde.solve_method_of_lines"),
    )

    def register(self, registry: DomainRegistry) -> None:
        laplacian = registry.require("pde.second_derivative_1d")
        solve_pde = registry.require("pde.solve_method_of_lines")

        def solve_diffusion(
            problem: DiffusionProblem1D,
            *,
            end_time: float,
            steps: int = 256,
        ) -> DiffusionSolution1D:
            scalar_problem = ScalarPDEProblem1D(
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
            return DiffusionSolution1D(
                pde_solution=solution,
                diffusivity=problem.diffusivity,
                boundary=problem.boundary,
            )

        registry.register_semantic_type("physics.diffusion.problem1d", DiffusionProblem1D)
        registry.register_semantic_type("physics.diffusion.solution1d", DiffusionSolution1D)
        registry.provide("physics.diffusion.problem1d", DiffusionProblem1D)
        registry.provide("physics.diffusion.solve1d", solve_diffusion)
        registry.register_visualization(DiffusionSolution1D, compile_diffusion_solution_scene)
