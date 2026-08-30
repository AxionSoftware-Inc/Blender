import pytest

from spectra.core.types import Vec3
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import (
    PointSource3D,
    UniformGrid1D,
    UniformGrid3D,
    deposit_point_density_3d,
    deposit_point_weights_3d,
)


def _grid() -> UniformGrid3D:
    axis = UniformGrid1D(0.0, 1.0, 3)
    return UniformGrid3D(axis, axis, axis)


def test_cloud_in_cell_preserves_source_strength_and_splits_cell_center_equally() -> None:
    grid = _grid()
    source = PointSource3D(Vec3(0.25, 0.25, 0.25), 8.0)

    weights = deposit_point_weights_3d(grid, (source,), scheme="cloud_in_cell")
    nonzero = tuple(value for value in weights if abs(value) > 1e-12)

    assert len(nonzero) == 8
    assert all(value == pytest.approx(1.0) for value in nonzero)
    assert sum(weights) == pytest.approx(8.0)

    density = deposit_point_density_3d(grid, (source,), scheme="cloud_in_cell")
    cell_volume = grid.x.spacing * grid.y.spacing * grid.z.spacing
    assert sum(density) * cell_volume == pytest.approx(8.0)


def test_nearest_deposition_targets_one_node_and_catalog_auto_loads_grid() -> None:
    grid = _grid()
    source = PointSource3D(Vec3(0.12, 0.12, 0.12), 3.0)
    values = deposit_point_weights_3d(grid, (source,), scheme="nearest")

    assert sum(1 for value in values if abs(value) > 1e-12) == 1
    assert sum(values) == pytest.approx(3.0)

    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(
        registry,
        ["partial_differential_equations.deposition3d"],
    )
    assert "partial_differential_equations" in loaded
    assert "partial_differential_equations.3d" in loaded
    assert "partial_differential_equations.deposition3d" in loaded
    assert registry.has_capability("pde.deposit_point_density_3d")
