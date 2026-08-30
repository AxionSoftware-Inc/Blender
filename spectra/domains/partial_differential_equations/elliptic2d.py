from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.domains.partial_differential_equations.domain2d import BoundaryMode2D, UniformGrid2D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class PoissonProblem2D:
    """Solve laplacian(u) = source on a UniformGrid2D."""

    grid: UniformGrid2D
    source: tuple[float, ...]
    boundary: BoundaryMode2D = "fixed"
    initial_values: tuple[float, ...] | None = None
    name: str = "poisson2d"

    def __post_init__(self) -> None:
        if len(self.source) != self.grid.count:
            raise ValueError("Poisson source length must match grid")
        if not all(math.isfinite(float(value)) for value in self.source):
            raise ValueError("Poisson source must be finite")
        if self.initial_values is not None:
            if len(self.initial_values) != self.grid.count:
                raise ValueError("Poisson initial_values length must match grid")
            if not all(math.isfinite(float(value)) for value in self.initial_values):
                raise ValueError("Poisson initial values must be finite")
        if self.boundary not in {"fixed", "periodic", "zero_gradient"}:
            raise ValueError(f"unknown Poisson boundary mode: {self.boundary}")
        if self.boundary in {"periodic", "zero_gradient"}:
            mean_source = sum(self.source) / len(self.source)
            if abs(mean_source) > 1e-9:
                raise ValueError(
                    "periodic/zero-gradient Poisson source must have approximately zero mean"
                )
        if not self.name:
            raise ValueError("Poisson problem name cannot be empty")


@dataclass(frozen=True, slots=True)
class PoissonSolution2D:
    grid: UniformGrid2D
    values: tuple[float, ...]
    iterations: int
    residual_inf: float
    converged: bool
    name: str = "poisson2d"

    def __post_init__(self) -> None:
        if len(self.values) != self.grid.count:
            raise ValueError("Poisson solution length must match grid")
        if self.iterations < 0:
            raise ValueError("Poisson iteration count cannot be negative")
        if not math.isfinite(self.residual_inf) or self.residual_inf < 0.0:
            raise ValueError("Poisson residual must be finite and non-negative")


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
    raise ValueError(f"unknown Poisson boundary mode: {boundary}")


def _remove_mean(values: list[float]) -> None:
    center = sum(values) / len(values)
    for index in range(len(values)):
        values[index] -= center


class EllipticPDE2DDomain:
    """Reference elliptic solver layer for pressure/potential/steady-state problems."""

    name = "partial_differential_equations.elliptic2d"
    version = "1"
    dependencies = (
        DomainDependency("pde.uniform_grid2d"),
        DomainDependency("pde.laplacian_2d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        laplacian = registry.require("pde.laplacian_2d")

        def solve_poisson(
            problem: PoissonProblem2D,
            *,
            max_iterations: int = 10_000,
            tolerance: float = 1e-8,
        ) -> PoissonSolution2D:
            if max_iterations < 1:
                raise ValueError("Poisson max_iterations must be >= 1")
            if not math.isfinite(tolerance) or tolerance <= 0.0:
                raise ValueError("Poisson tolerance must be finite and positive")

            grid = problem.grid
            source = tuple(float(value) for value in problem.source)
            values = list(problem.initial_values or (0.0 for _ in range(grid.count)))
            fixed_values = tuple(values)
            inv_dx2 = 1.0 / (grid.x.spacing * grid.x.spacing)
            inv_dy2 = 1.0 / (grid.y.spacing * grid.y.spacing)
            denominator = 2.0 * inv_dx2 + 2.0 * inv_dy2

            converged = False
            residual_inf = math.inf
            completed = 0

            for iteration in range(1, max_iterations + 1):
                next_values = list(values)
                for y_index in range(grid.y.count):
                    for x_index in range(grid.x.count):
                        center_index = grid.flat_index(x_index, y_index)
                        if problem.boundary == "fixed" and (
                            x_index in {0, grid.x.count - 1}
                            or y_index in {0, grid.y.count - 1}
                        ):
                            next_values[center_index] = fixed_values[center_index]
                            continue

                        left = _neighbor(x_index, grid.x.count, -1, problem.boundary)
                        right = _neighbor(x_index, grid.x.count, 1, problem.boundary)
                        lower = _neighbor(y_index, grid.y.count, -1, problem.boundary)
                        upper = _neighbor(y_index, grid.y.count, 1, problem.boundary)
                        if None in {left, right, lower, upper}:
                            continue

                        horizontal = (
                            values[grid.flat_index(int(left), y_index)]
                            + values[grid.flat_index(int(right), y_index)]
                        ) * inv_dx2
                        vertical = (
                            values[grid.flat_index(x_index, int(lower))]
                            + values[grid.flat_index(x_index, int(upper))]
                        ) * inv_dy2
                        next_values[center_index] = (
                            horizontal + vertical - source[center_index]
                        ) / denominator

                if problem.boundary in {"periodic", "zero_gradient"}:
                    _remove_mean(next_values)

                values = next_values
                residual = laplacian(values, grid, boundary=problem.boundary)
                if problem.boundary == "fixed":
                    residual_inf = max(
                        abs(residual[grid.flat_index(x_index, y_index)] - source[grid.flat_index(x_index, y_index)])
                        for y_index in range(1, grid.y.count - 1)
                        for x_index in range(1, grid.x.count - 1)
                    )
                else:
                    residual_inf = max(
                        abs(left - right)
                        for left, right in zip(residual, source, strict=True)
                    )
                completed = iteration
                if residual_inf <= tolerance:
                    converged = True
                    break

            return PoissonSolution2D(
                grid=grid,
                values=tuple(values),
                iterations=completed,
                residual_inf=float(residual_inf),
                converged=converged,
                name=problem.name,
            )

        registry.register_semantic_type("pde.poisson_problem2d", PoissonProblem2D)
        registry.register_semantic_type("pde.poisson_solution2d", PoissonSolution2D)
        registry.provide("pde.poisson_problem2d", PoissonProblem2D)
        registry.provide("pde.solve_poisson_2d", solve_poisson)
