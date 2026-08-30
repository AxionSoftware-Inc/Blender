from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.types import Vec2, Vec3
from spectra.core.units import METER_PER_SECOND
from spectra.domains.mathematics.fields2d import VectorField2D
from spectra.domains.partial_differential_equations.domain2d import BoundaryMode2D, UniformGrid2D
from spectra.domains.physics.fluid_kinematics import SteadyFlow2D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class VorticityStreamfunctionProblem2D:
    grid: UniformGrid2D
    vorticity: tuple[float, ...]
    boundary: BoundaryMode2D = "fixed"
    name: str = "vorticity_streamfunction2d"

    def __post_init__(self) -> None:
        if len(self.vorticity) != self.grid.count:
            raise ValueError("vorticity sample count must match grid")
        if not all(math.isfinite(float(value)) for value in self.vorticity):
            raise ValueError("vorticity samples must be finite")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown vorticity boundary mode: {self.boundary}")
        if not self.name:
            raise ValueError("vorticity-streamfunction problem name cannot be empty")


@dataclass(frozen=True, slots=True)
class VorticityStreamfunctionSolution2D:
    grid: UniformGrid2D
    streamfunction: tuple[float, ...]
    velocity: tuple[Vec2, ...]
    residual_inf: float
    converged: bool
    name: str = "vorticity_streamfunction2d"

    def __post_init__(self) -> None:
        if len(self.streamfunction) != self.grid.count:
            raise ValueError("streamfunction sample count must match grid")
        if len(self.velocity) != self.grid.count:
            raise ValueError("velocity sample count must match grid")
        if not math.isfinite(self.residual_inf) or self.residual_inf < 0.0:
            raise ValueError("streamfunction residual must be finite and non-negative")

    def as_steady_flow(self) -> SteadyFlow2D:
        x_values = self.grid.x.coordinates
        y_values = self.grid.y.coordinates

        def nearest(position: Vec2) -> Vec2:
            x_index = min(range(len(x_values)), key=lambda index: abs(x_values[index] - position.x))
            y_index = min(range(len(y_values)), key=lambda index: abs(y_values[index] - position.y))
            return self.velocity[self.grid.flat_index(x_index, y_index)]

        return SteadyFlow2D(
            VectorField2D(
                evaluator=nearest,
                name=f"{self.name}.velocity",
                output_unit=METER_PER_SECOND,
            ),
            name=self.name,
        )


class VorticityStreamfunction2DDomain:
    """Reconstruct incompressible planar flow from vorticity via Poisson solve."""

    name = "physics.vorticity_streamfunction.2d"
    version = "1"
    dependencies = (
        DomainDependency("pde.poisson_problem2d"),
        DomainDependency("pde.solve_poisson_2d"),
        DomainDependency("pde.gradient_grid_2d"),
        DomainDependency("physics.fluid.steady_flow2d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        from spectra.core.primitives import VectorGlyphSet
        from spectra.core.scene import Scene
        from spectra.core.types import Color

        poisson_problem_type = registry.require("pde.poisson_problem2d")
        solve_poisson = registry.require("pde.solve_poisson_2d")
        gradient = registry.require("pde.gradient_grid_2d")

        def solve_vorticity_flow(
            problem: VorticityStreamfunctionProblem2D,
            *,
            max_iterations: int = 10_000,
            tolerance: float = 1e-8,
        ) -> VorticityStreamfunctionSolution2D:
            source = tuple(-float(value) for value in problem.vorticity)
            if problem.boundary in {"periodic", "zero_gradient"}:
                mean = sum(source) / len(source)
                source = tuple(value - mean for value in source)
            poisson = solve_poisson(
                poisson_problem_type(
                    grid=problem.grid,
                    source=source,
                    boundary=problem.boundary,
                    name=f"{problem.name}.streamfunction",
                ),
                max_iterations=max_iterations,
                tolerance=tolerance,
            )
            grad = gradient(poisson.values, problem.grid, boundary=problem.boundary)
            velocity = tuple(Vec2(value.y, -value.x) for value in grad)
            return VorticityStreamfunctionSolution2D(
                grid=problem.grid,
                streamfunction=poisson.values,
                velocity=velocity,
                residual_inf=poisson.residual_inf,
                converged=poisson.converged,
                name=problem.name,
            )

        def compile_solution(solution: VorticityStreamfunctionSolution2D) -> Scene:
            return Scene(
                primitives=(
                    VectorGlyphSet(
                        id=f"{solution.name}.velocity",
                        origins=tuple(Vec3(x, y, 0.0) for x, y in solution.grid.coordinates),
                        vectors=tuple(Vec3(value.x, value.y, 0.0) for value in solution.velocity),
                        color=Color(0.35, 0.78, 1.0, 1.0),
                    ),
                )
            )

        registry.register_semantic_type(
            "physics.vorticity_streamfunction.problem2d",
            VorticityStreamfunctionProblem2D,
        )
        registry.register_semantic_type(
            "physics.vorticity_streamfunction.solution2d",
            VorticityStreamfunctionSolution2D,
        )
        registry.provide(
            "physics.vorticity_streamfunction.problem2d",
            VorticityStreamfunctionProblem2D,
        )
        registry.provide("physics.vorticity_streamfunction.solve2d", solve_vorticity_flow)
        registry.register_visualization(VorticityStreamfunctionSolution2D, compile_solution)
