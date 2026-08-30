from __future__ import annotations

from collections.abc import Iterable

from spectra.core.types import Vec2
from spectra.domains.partial_differential_equations.domain2d import BoundaryMode2D, UniformGrid2D
from spectra.domains.registry import DomainDependency, DomainRegistry


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
    raise ValueError(f"unknown 2D boundary mode: {boundary}")


def gradient_grid_2d(
    values: Iterable[float],
    grid: UniformGrid2D,
    *,
    boundary: BoundaryMode2D = "fixed",
) -> tuple[Vec2, ...]:
    """Central-difference gradient of scalar samples on a UniformGrid2D."""

    state = tuple(float(value) for value in values)
    if len(state) != grid.count:
        raise ValueError("2D scalar values length must match grid")
    if boundary not in {"fixed", "periodic", "zero_gradient"}:
        raise ValueError(f"unknown 2D boundary mode: {boundary}")

    result = [Vec2(0.0, 0.0) for _ in range(grid.count)]
    for y_index in range(grid.y.count):
        for x_index in range(grid.x.count):
            center_index = grid.flat_index(x_index, y_index)
            if boundary == "fixed" and (
                x_index in {0, grid.x.count - 1}
                or y_index in {0, grid.y.count - 1}
            ):
                continue

            left = _neighbor(x_index, grid.x.count, -1, boundary)
            right = _neighbor(x_index, grid.x.count, 1, boundary)
            lower = _neighbor(y_index, grid.y.count, -1, boundary)
            upper = _neighbor(y_index, grid.y.count, 1, boundary)
            if None in {left, right, lower, upper}:
                continue

            dudx = (
                state[grid.flat_index(int(right), y_index)]
                - state[grid.flat_index(int(left), y_index)]
            ) / (2.0 * grid.x.spacing)
            dudy = (
                state[grid.flat_index(x_index, int(upper))]
                - state[grid.flat_index(x_index, int(lower))]
            ) / (2.0 * grid.y.spacing)
            result[center_index] = Vec2(dudx, dudy)

    return tuple(result)


def divergence_grid_2d(
    vectors: Iterable[Vec2],
    grid: UniformGrid2D,
    *,
    boundary: BoundaryMode2D = "fixed",
) -> tuple[float, ...]:
    """Central-difference divergence of vector samples on a UniformGrid2D."""

    state = tuple(vectors)
    if len(state) != grid.count:
        raise ValueError("2D vector values length must match grid")
    if any(not isinstance(vector, Vec2) for vector in state):
        raise TypeError("2D divergence values must be Vec2")
    if boundary not in {"fixed", "periodic", "zero_gradient"}:
        raise ValueError(f"unknown 2D boundary mode: {boundary}")

    result = [0.0 for _ in range(grid.count)]
    for y_index in range(grid.y.count):
        for x_index in range(grid.x.count):
            center_index = grid.flat_index(x_index, y_index)
            if boundary == "fixed" and (
                x_index in {0, grid.x.count - 1}
                or y_index in {0, grid.y.count - 1}
            ):
                continue

            left = _neighbor(x_index, grid.x.count, -1, boundary)
            right = _neighbor(x_index, grid.x.count, 1, boundary)
            lower = _neighbor(y_index, grid.y.count, -1, boundary)
            upper = _neighbor(y_index, grid.y.count, 1, boundary)
            if None in {left, right, lower, upper}:
                continue

            du_dx = (
                state[grid.flat_index(int(right), y_index)].x
                - state[grid.flat_index(int(left), y_index)].x
            ) / (2.0 * grid.x.spacing)
            dv_dy = (
                state[grid.flat_index(x_index, int(upper))].y
                - state[grid.flat_index(x_index, int(lower))].y
            ) / (2.0 * grid.y.spacing)
            result[center_index] = du_dx + dv_dy

    return tuple(result)


def curl_grid_2d(
    vectors: Iterable[Vec2],
    grid: UniformGrid2D,
    *,
    boundary: BoundaryMode2D = "fixed",
) -> tuple[float, ...]:
    """Scalar z-curl dv/dx - du/dy of a sampled planar vector field."""

    state = tuple(vectors)
    if len(state) != grid.count:
        raise ValueError("2D vector values length must match grid")
    if any(not isinstance(vector, Vec2) for vector in state):
        raise TypeError("2D curl values must be Vec2")
    if boundary not in {"fixed", "periodic", "zero_gradient"}:
        raise ValueError(f"unknown 2D boundary mode: {boundary}")

    result = [0.0 for _ in range(grid.count)]
    for y_index in range(grid.y.count):
        for x_index in range(grid.x.count):
            center_index = grid.flat_index(x_index, y_index)
            if boundary == "fixed" and (
                x_index in {0, grid.x.count - 1}
                or y_index in {0, grid.y.count - 1}
            ):
                continue

            left = _neighbor(x_index, grid.x.count, -1, boundary)
            right = _neighbor(x_index, grid.x.count, 1, boundary)
            lower = _neighbor(y_index, grid.y.count, -1, boundary)
            upper = _neighbor(y_index, grid.y.count, 1, boundary)
            if None in {left, right, lower, upper}:
                continue

            dv_dx = (
                state[grid.flat_index(int(right), y_index)].y
                - state[grid.flat_index(int(left), y_index)].y
            ) / (2.0 * grid.x.spacing)
            du_dy = (
                state[grid.flat_index(x_index, int(upper))].x
                - state[grid.flat_index(x_index, int(lower))].x
            ) / (2.0 * grid.y.spacing)
            result[center_index] = dv_dx - du_dy

    return tuple(result)


def vector_upwind_advection_grid_2d(
    vectors: Iterable[Vec2],
    grid: UniformGrid2D,
    *,
    boundary: BoundaryMode2D = "fixed",
) -> tuple[Vec2, ...]:
    """Return (v·grad)v for a sampled vector field using first-order upwinding."""

    state = tuple(vectors)
    if len(state) != grid.count:
        raise ValueError("2D vector values length must match grid")
    if any(not isinstance(vector, Vec2) for vector in state):
        raise TypeError("2D vector advection values must be Vec2")
    if boundary not in {"fixed", "periodic", "zero_gradient"}:
        raise ValueError(f"unknown 2D boundary mode: {boundary}")

    result = [Vec2(0.0, 0.0) for _ in range(grid.count)]
    for y_index in range(grid.y.count):
        for x_index in range(grid.x.count):
            center_index = grid.flat_index(x_index, y_index)
            if boundary == "fixed" and (
                x_index in {0, grid.x.count - 1}
                or y_index in {0, grid.y.count - 1}
            ):
                continue

            left = _neighbor(x_index, grid.x.count, -1, boundary)
            right = _neighbor(x_index, grid.x.count, 1, boundary)
            lower = _neighbor(y_index, grid.y.count, -1, boundary)
            upper = _neighbor(y_index, grid.y.count, 1, boundary)
            if None in {left, right, lower, upper}:
                continue

            center = state[center_index]
            left_value = state[grid.flat_index(int(left), y_index)]
            right_value = state[grid.flat_index(int(right), y_index)]
            lower_value = state[grid.flat_index(x_index, int(lower))]
            upper_value = state[grid.flat_index(x_index, int(upper))]

            if center.x >= 0.0:
                du_dx = (center.x - left_value.x) / grid.x.spacing
                dv_dx = (center.y - left_value.y) / grid.x.spacing
            else:
                du_dx = (right_value.x - center.x) / grid.x.spacing
                dv_dx = (right_value.y - center.y) / grid.x.spacing

            if center.y >= 0.0:
                du_dy = (center.x - lower_value.x) / grid.y.spacing
                dv_dy = (center.y - lower_value.y) / grid.y.spacing
            else:
                du_dy = (upper_value.x - center.x) / grid.y.spacing
                dv_dy = (upper_value.y - center.y) / grid.y.spacing

            result[center_index] = Vec2(
                center.x * du_dx + center.y * du_dy,
                center.x * dv_dx + center.y * dv_dy,
            )

    return tuple(result)


class PDEOperators2DDomain:
    """Reusable sampled-grid differential operators for 2D PDE consumers."""

    name = "partial_differential_equations.operators2d"
    version = "2"
    dependencies = (DomainDependency("pde.uniform_grid2d"),)

    def register(self, registry: DomainRegistry) -> None:
        registry.provide("pde.gradient_grid_2d", gradient_grid_2d)
        registry.provide("pde.divergence_grid_2d", divergence_grid_2d)
        registry.provide("pde.curl_grid_2d", curl_grid_2d, version=2)
        registry.provide("pde.vector_upwind_advection_grid_2d", vector_upwind_advection_grid_2d)
