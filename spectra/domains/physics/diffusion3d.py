from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.domains.partial_differential_equations.domain3d import (
    BoundaryMode3D,
    ScalarPDEProblem3D,
    ScalarPDESolution3D,
    UniformGrid3D,
)
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class DiffusionProblem3D:
    grid: UniformGrid3D
    initial_values: tuple[float, ...]
    diffusivity: float
    boundary: BoundaryMode3D = "fixed"
    initial_time: float = 0.0
    name: str = "diffusion3d"

    def __post_init__(self) -> None:
        if len(self.initial_values) != self.grid.count:
            raise ValueError("3D diffusion initial_values length must match grid")
        if not all(math.isfinite(float(value)) for value in self.initial_values):
            raise ValueError("3D diffusion initial values must be finite")
        if not math.isfinite(self.diffusivity) or self.diffusivity <= 0.0:
            raise ValueError("3D diffusivity must be finite and positive")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown 3D diffusion boundary mode: {self.boundary}")
        if not math.isfinite(self.initial_time):
            raise ValueError("3D diffusion initial time must be finite")
        if not self.name:
            raise ValueError("3D diffusion name cannot be empty")


@dataclass(frozen=True, slots=True)
class DiffusionSolution3D:
    pde_solution: ScalarPDESolution3D
    diffusivity: float
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


class Diffusion3DDomain:
    name = "physics.diffusion.3d"
    version = "1"
    dependencies = (
        DomainDependency("pde.scalar_problem3d"),
        DomainDependency("pde.laplacian_3d"),
        DomainDependency("pde.solve_method_of_lines_3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        problem_type = registry.require("pde.scalar_problem3d")
        laplacian = registry.require("pde.laplacian_3d")
        solve_pde = registry.require("pde.solve_method_of_lines_3d")

        def solve_diffusion(
            problem: DiffusionProblem3D,
            *,
            end_time: float,
            steps: int = 128,
        ) -> DiffusionSolution3D:
            def rhs(_time, grid, values):
                return tuple(
                    problem.diffusivity * value
                    for value in laplacian(
                        values,
                        grid,
                        boundary=problem.boundary,
                    )
                )

            solution = solve_pde(
                problem_type(
                    grid=problem.grid,
                    initial_values=tuple(float(value) for value in problem.initial_values),
                    rhs=rhs,
                    initial_time=problem.initial_time,
                    name=problem.name,
                ),
                end_time=end_time,
                steps=steps,
            )
            return DiffusionSolution3D(
                pde_solution=solution,
                diffusivity=problem.diffusivity,
                boundary=problem.boundary,
            )

        registry.register_semantic_type(
            "physics.diffusion.problem3d",
            DiffusionProblem3D,
        )
        registry.register_semantic_type(
            "physics.diffusion.solution3d",
            DiffusionSolution3D,
        )
        registry.provide("physics.diffusion.problem3d", DiffusionProblem3D)
        registry.provide("physics.diffusion.solve3d", solve_diffusion)
