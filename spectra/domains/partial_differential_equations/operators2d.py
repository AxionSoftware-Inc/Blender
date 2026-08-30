from __future__ import annotations

from collections.abc import Iterable

from spectra.core.types import Vec2
from spectra.domains.partial_differential_equations.domain2d import BoundaryMode2D, UniformGrid2D


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
