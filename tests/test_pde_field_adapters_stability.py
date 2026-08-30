import pytest

from spectra.core.types import Vec2
from spectra.domains.partial_differential_equations import (
    UniformGrid1D,
    UniformGrid2D,
    explicit_stability_from_samples_2d,
    scalar_field_from_grid_2d,
    time_scalar_field_from_grid_2d,
    time_vector_field_from_grid_2d,
)


def _grid() -> UniformGrid2D:
    return UniformGrid2D(
        UniformGrid1D(0.0, 1.0, 3),
        UniformGrid1D(0.0, 1.0, 3),
    )


def test_bilinear_grid_field_and_time_interpolation() -> None:
    grid = _grid()
    base = tuple(x + y for x, y in grid.coordinates)
    field = scalar_field_from_grid_2d(grid, base)
    assert field.evaluate(Vec2(0.25, 0.75)) == pytest.approx(1.0)

    time_field = time_scalar_field_from_grid_2d(
        grid,
        (0.0, 1.0),
        (base, tuple(2.0 * value for value in base)),
    )
    assert time_field.evaluate(Vec2(0.25, 0.75), 0.5) == pytest.approx(1.5)

    vectors0 = tuple(Vec2(1.0, 0.0) for _ in range(grid.count))
    vectors1 = tuple(Vec2(3.0, 2.0) for _ in range(grid.count))
    vector_field = time_vector_field_from_grid_2d(
        grid,
        (0.0, 1.0),
        (vectors0, vectors1),
    )
    sampled = vector_field.evaluate(Vec2(0.4, 0.6), 0.5)
    assert sampled.x == pytest.approx(2.0)
    assert sampled.y == pytest.approx(1.0)


def test_conservative_explicit_stability_metrics() -> None:
    grid = _grid()
    velocities = tuple(Vec2(1.0, 0.5) for _ in range(grid.count))
    diagnostics = explicit_stability_from_samples_2d(
        grid,
        velocities,
        dt=0.1,
        diffusivity=0.0,
        safety=0.9,
    )
    assert diagnostics.cfl_x == pytest.approx(0.2)
    assert diagnostics.cfl_y == pytest.approx(0.1)
    assert diagnostics.cfl_sum == pytest.approx(0.3)
    assert diagnostics.diffusion_number == pytest.approx(0.0)
    assert diagnostics.within_conservative_envelope
    assert Vec2(3.0, 4.0).magnitude == pytest.approx(5.0)
