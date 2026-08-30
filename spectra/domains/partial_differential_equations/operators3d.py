from __future__ import annotations

from collections.abc import Iterable

from spectra.core.types import Vec3
from spectra.domains.partial_differential_equations.domain3d import BoundaryMode3D, UniformGrid3D
from spectra.domains.registry import DomainDependency, DomainRegistry


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
    raise ValueError(f"unknown 3D boundary mode: {boundary}")


def gradient_grid_3d(
    values: Iterable[float],
    grid: UniformGrid3D,
    *,
    boundary: BoundaryMode3D = "fixed",
) -> tuple[Vec3, ...]:
    state = tuple(float(value) for value in values)
    if len(state) != grid.count:
        raise ValueError("3D scalar values length must match grid")
    result = [Vec3(0.0, 0.0, 0.0) for _ in range(grid.count)]

    for z_index in range(grid.z.count):
        for y_index in range(grid.y.count):
            for x_index in range(grid.x.count):
                center = grid.flat_index(x_index, y_index, z_index)
                if boundary == "fixed" and (
                    x_index in {0, grid.x.count - 1}
                    or y_index in {0, grid.y.count - 1}
                    or z_index in {0, grid.z.count - 1}
                ):
                    continue
                left = _neighbor(x_index, grid.x.count, -1, boundary)
                right = _neighbor(x_index, grid.x.count, 1, boundary)
                lower = _neighbor(y_index, grid.y.count, -1, boundary)
                upper = _neighbor(y_index, grid.y.count, 1, boundary)
                back = _neighbor(z_index, grid.z.count, -1, boundary)
                front = _neighbor(z_index, grid.z.count, 1, boundary)
                if None in {left, right, lower, upper, back, front}:
                    continue
                dx = (
                    state[grid.flat_index(int(right), y_index, z_index)]
                    - state[grid.flat_index(int(left), y_index, z_index)]
                ) / (2.0 * grid.x.spacing)
                dy = (
                    state[grid.flat_index(x_index, int(upper), z_index)]
                    - state[grid.flat_index(x_index, int(lower), z_index)]
                ) / (2.0 * grid.y.spacing)
                dz = (
                    state[grid.flat_index(x_index, y_index, int(front))]
                    - state[grid.flat_index(x_index, y_index, int(back))]
                ) / (2.0 * grid.z.spacing)
                result[center] = Vec3(dx, dy, dz)
    return tuple(result)


def divergence_grid_3d(
    vectors: Iterable[Vec3],
    grid: UniformGrid3D,
    *,
    boundary: BoundaryMode3D = "fixed",
) -> tuple[float, ...]:
    state = tuple(vectors)
    if len(state) != grid.count:
        raise ValueError("3D vector values length must match grid")
    if any(not isinstance(value, Vec3) for value in state):
        raise TypeError("3D divergence values must be Vec3")
    result = [0.0 for _ in range(grid.count)]

    for z_index in range(grid.z.count):
        for y_index in range(grid.y.count):
            for x_index in range(grid.x.count):
                center = grid.flat_index(x_index, y_index, z_index)
                if boundary == "fixed" and (
                    x_index in {0, grid.x.count - 1}
                    or y_index in {0, grid.y.count - 1}
                    or z_index in {0, grid.z.count - 1}
                ):
                    continue
                left = _neighbor(x_index, grid.x.count, -1, boundary)
                right = _neighbor(x_index, grid.x.count, 1, boundary)
                lower = _neighbor(y_index, grid.y.count, -1, boundary)
                upper = _neighbor(y_index, grid.y.count, 1, boundary)
                back = _neighbor(z_index, grid.z.count, -1, boundary)
                front = _neighbor(z_index, grid.z.count, 1, boundary)
                if None in {left, right, lower, upper, back, front}:
                    continue
                dx = (
                    state[grid.flat_index(int(right), y_index, z_index)].x
                    - state[grid.flat_index(int(left), y_index, z_index)].x
                ) / (2.0 * grid.x.spacing)
                dy = (
                    state[grid.flat_index(x_index, int(upper), z_index)].y
                    - state[grid.flat_index(x_index, int(lower), z_index)].y
                ) / (2.0 * grid.y.spacing)
                dz = (
                    state[grid.flat_index(x_index, y_index, int(front))].z
                    - state[grid.flat_index(x_index, y_index, int(back))].z
                ) / (2.0 * grid.z.spacing)
                result[center] = dx + dy + dz
    return tuple(result)


def curl_grid_3d(
    vectors: Iterable[Vec3],
    grid: UniformGrid3D,
    *,
    boundary: BoundaryMode3D = "fixed",
) -> tuple[Vec3, ...]:
    state = tuple(vectors)
    if len(state) != grid.count:
        raise ValueError("3D vector values length must match grid")
    if any(not isinstance(value, Vec3) for value in state):
        raise TypeError("3D curl values must be Vec3")
    result = [Vec3(0.0, 0.0, 0.0) for _ in range(grid.count)]

    for z_index in range(grid.z.count):
        for y_index in range(grid.y.count):
            for x_index in range(grid.x.count):
                center = grid.flat_index(x_index, y_index, z_index)
                if boundary == "fixed" and (
                    x_index in {0, grid.x.count - 1}
                    or y_index in {0, grid.y.count - 1}
                    or z_index in {0, grid.z.count - 1}
                ):
                    continue
                left = _neighbor(x_index, grid.x.count, -1, boundary)
                right = _neighbor(x_index, grid.x.count, 1, boundary)
                lower = _neighbor(y_index, grid.y.count, -1, boundary)
                upper = _neighbor(y_index, grid.y.count, 1, boundary)
                back = _neighbor(z_index, grid.z.count, -1, boundary)
                front = _neighbor(z_index, grid.z.count, 1, boundary)
                if None in {left, right, lower, upper, back, front}:
                    continue

                left_v = state[grid.flat_index(int(left), y_index, z_index)]
                right_v = state[grid.flat_index(int(right), y_index, z_index)]
                lower_v = state[grid.flat_index(x_index, int(lower), z_index)]
                upper_v = state[grid.flat_index(x_index, int(upper), z_index)]
                back_v = state[grid.flat_index(x_index, y_index, int(back))]
                front_v = state[grid.flat_index(x_index, y_index, int(front))]

                dw_dy = (upper_v.z - lower_v.z) / (2.0 * grid.y.spacing)
                dv_dz = (front_v.y - back_v.y) / (2.0 * grid.z.spacing)
                du_dz = (front_v.x - back_v.x) / (2.0 * grid.z.spacing)
                dw_dx = (right_v.z - left_v.z) / (2.0 * grid.x.spacing)
                dv_dx = (right_v.y - left_v.y) / (2.0 * grid.x.spacing)
                du_dy = (upper_v.x - lower_v.x) / (2.0 * grid.y.spacing)
                result[center] = Vec3(
                    dw_dy - dv_dz,
                    du_dz - dw_dx,
                    dv_dx - du_dy,
                )
    return tuple(result)


class PDEOperators3DDomain:
    name = "partial_differential_equations.operators3d"
    version = "1"
    dependencies = (DomainDependency("pde.uniform_grid3d"),)

    def register(self, registry: DomainRegistry) -> None:
        registry.provide("pde.gradient_grid_3d", gradient_grid_3d)
        registry.provide("pde.divergence_grid_3d", divergence_grid_3d)
        registry.provide("pde.curl_grid_3d", curl_grid_3d)
