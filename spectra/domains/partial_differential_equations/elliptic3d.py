from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.domains.partial_differential_equations.domain3d import (
    BoundaryMode3D,
    UniformGrid3D,
)
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class PoissonProblem3D:
    grid: UniformGrid3D
    source: tuple[float, ...]
    boundary: BoundaryMode3D = "fixed"
    initial_values: tuple[float, ...] | None = None
    name: str = "poisson3d"

    def __post_init__(self) -> None:
        if len(self.source) != self.grid.count:
            raise ValueError("3D Poisson source length must match grid")
        if not all(math.isfinite(float(value)) for value in self.source):
            raise ValueError("3D Poisson source must be finite")
        if self.initial_values is not None:
            if len(self.initial_values) != self.grid.count:
                raise ValueError("3D Poisson initial_values length must match grid")
            if not all(math.isfinite(float(value)) for value in self.initial_values):
                raise ValueError("3D Poisson initial values must be finite")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown 3D Poisson boundary mode: {self.boundary}")
        if self.boundary in {"periodic", "zero_gradient"}:
            mean_source = sum(self.source) / len(self.source)
            if abs(mean_source) > 1e-9:
                raise ValueError(
                    "periodic/zero-gradient 3D Poisson source must have approximately zero mean"
                )
        if not self.name:
            raise ValueError("3D Poisson name cannot be empty")


@dataclass(frozen=True, slots=True)
class PoissonSolution3D:
    grid: UniformGrid3D
    values: tuple[float, ...]
    iterations: int
    residual_inf: float
    converged: bool
    name: str = "poisson3d"

    def __post_init__(self) -> None:
        if len(self.values) != self.grid.count:
            raise ValueError("3D Poisson solution length must match grid")
        if self.iterations < 0:
            raise ValueError("3D Poisson iteration count cannot be negative")
        if not math.isfinite(self.residual_inf) or self.residual_inf < 0.0:
            raise ValueError("3D Poisson residual must be finite and non-negative")


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
    raise ValueError(f"unknown 3D Poisson boundary mode: {boundary}")


def _remove_mean(values: list[float]) -> None:
    mean = sum(values) / len(values)
    for index in range(len(values)):
        values[index] -= mean


class EllipticPDE3DDomain:
    name = "partial_differential_equations.elliptic3d"
    version = "1"
    dependencies = (
        DomainDependency("pde.uniform_grid3d"),
        DomainDependency("pde.laplacian_3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        laplacian = registry.require("pde.laplacian_3d")

        def solve_poisson(
            problem: PoissonProblem3D,
            *,
            max_iterations: int = 10_000,
            tolerance: float = 1e-8,
        ) -> PoissonSolution3D:
            if max_iterations < 1:
                raise ValueError("3D Poisson max_iterations must be >= 1")
            if not math.isfinite(tolerance) or tolerance <= 0.0:
                raise ValueError("3D Poisson tolerance must be finite and positive")

            grid = problem.grid
            source = tuple(float(value) for value in problem.source)
            values = list(problem.initial_values or (0.0 for _ in range(grid.count)))
            fixed_values = tuple(values)
            inv_dx2 = 1.0 / (grid.x.spacing * grid.x.spacing)
            inv_dy2 = 1.0 / (grid.y.spacing * grid.y.spacing)
            inv_dz2 = 1.0 / (grid.z.spacing * grid.z.spacing)
            denominator = 2.0 * (inv_dx2 + inv_dy2 + inv_dz2)

            converged = False
            residual_inf = math.inf
            completed = 0

            for iteration in range(1, max_iterations + 1):
                next_values = list(values)
                for z_index in range(grid.z.count):
                    for y_index in range(grid.y.count):
                        for x_index in range(grid.x.count):
                            center_index = grid.flat_index(x_index, y_index, z_index)
                            if problem.boundary == "fixed" and (
                                x_index in {0, grid.x.count - 1}
                                or y_index in {0, grid.y.count - 1}
                                or z_index in {0, grid.z.count - 1}
                            ):
                                next_values[center_index] = fixed_values[center_index]
                                continue

                            left = _neighbor(x_index, grid.x.count, -1, problem.boundary)
                            right = _neighbor(x_index, grid.x.count, 1, problem.boundary)
                            lower = _neighbor(y_index, grid.y.count, -1, problem.boundary)
                            upper = _neighbor(y_index, grid.y.count, 1, problem.boundary)
                            back = _neighbor(z_index, grid.z.count, -1, problem.boundary)
                            front = _neighbor(z_index, grid.z.count, 1, problem.boundary)
                            if None in {left, right, lower, upper, back, front}:
                                continue

                            x_sum = (
                                values[grid.flat_index(int(left), y_index, z_index)]
                                + values[grid.flat_index(int(right), y_index, z_index)]
                            ) * inv_dx2
                            y_sum = (
                                values[grid.flat_index(x_index, int(lower), z_index)]
                                + values[grid.flat_index(x_index, int(upper), z_index)]
                            ) * inv_dy2
                            z_sum = (
                                values[grid.flat_index(x_index, y_index, int(back))]
                                + values[grid.flat_index(x_index, y_index, int(front))]
                            ) * inv_dz2
                            next_values[center_index] = (
                                x_sum + y_sum + z_sum - source[center_index]
                            ) / denominator

                if problem.boundary in {"periodic", "zero_gradient"}:
                    _remove_mean(next_values)

                values = next_values
                residual = laplacian(values, grid, boundary=problem.boundary)
                if problem.boundary == "fixed":
                    interior = [
                        abs(
                            residual[grid.flat_index(x_index, y_index, z_index)]
                            - source[grid.flat_index(x_index, y_index, z_index)]
                        )
                        for z_index in range(1, grid.z.count - 1)
                        for y_index in range(1, grid.y.count - 1)
                        for x_index in range(1, grid.x.count - 1)
                    ]
                    residual_inf = max(interior, default=0.0)
                else:
                    residual_inf = max(
                        abs(left - right)
                        for left, right in zip(residual, source, strict=True)
                    )
                completed = iteration
                if residual_inf <= tolerance:
                    converged = True
                    break

            return PoissonSolution3D(
                grid=grid,
                values=tuple(values),
                iterations=completed,
                residual_inf=float(residual_inf),
                converged=converged,
                name=problem.name,
            )

        registry.register_semantic_type("pde.poisson_problem3d", PoissonProblem3D)
        registry.register_semantic_type("pde.poisson_solution3d", PoissonSolution3D)
        registry.provide("pde.poisson_problem3d", PoissonProblem3D)
        registry.provide("pde.solve_poisson_3d", solve_poisson)
