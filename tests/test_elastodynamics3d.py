import pytest

from spectra.core.primitives import PointCloud
from spectra.core.types import Vec3
from spectra.core.units import KILOGRAM_PER_CUBIC_METER, PASCAL, Quantity
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid3D
from spectra.domains.physics.elasticity import IsotropicElasticMaterial
from spectra.domains.physics.elastodynamics3d import ElastodynamicsProblem3D


def _grid() -> UniformGrid3D:
    axis = UniformGrid1D(0.0, 1.0, 3)
    return UniformGrid3D(axis, axis, axis)


def _material() -> IsotropicElasticMaterial:
    return IsotropicElasticMaterial(
        young_modulus=Quantity(2.0e6, PASCAL),
        poisson_ratio=0.25,
        name="test_solid",
    )


def test_elastodynamics_catalog_loads_vector_pde_dependency_and_wave_speeds() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(
        registry,
        ["physics.elastodynamics.diagnostics3d", "physics.elastodynamics.views3d"],
    )

    assert "partial_differential_equations.second_order_vector3d" in loaded
    assert "physics.elasticity" in loaded
    assert "physics.elastodynamics.3d" in loaded
    assert "physics.elastodynamics.views3d" in loaded
    assert "physics.elastodynamics.diagnostics3d" in loaded

    longitudinal, shear = registry.require("physics.elastodynamics.wave_speeds")(
        _material(),
        Quantity(1000.0, KILOGRAM_PER_CUBIC_METER),
    )
    assert longitudinal > shear > 0.0


def test_periodic_rigid_translation_has_zero_strain_energy_and_animated_pointcloud() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()
    catalog.load(
        registry,
        ["physics.elastodynamics.diagnostics3d", "physics.elastodynamics.views3d"],
    )
    grid = _grid()
    zero = (Vec3(0.0, 0.0, 0.0),) * grid.count
    velocity = (Vec3(0.2, 0.0, 0.0),) * grid.count

    solution = registry.require("physics.elastodynamics.solve3d")(
        ElastodynamicsProblem3D(
            grid=grid,
            initial_displacement=zero,
            initial_velocity=velocity,
            material=_material(),
            density=Quantity(1000.0, KILOGRAM_PER_CUBIC_METER),
            boundary="periodic",
            name="rigid_translation",
        ),
        end_time=0.5,
        steps=4,
    )

    assert all(value == Vec3(0.2, 0.0, 0.0) for value in solution.velocities[-1])
    assert all(value.x == pytest.approx(0.1) for value in solution.displacements[-1])
    assert all(value.y == pytest.approx(0.0) for value in solution.displacements[-1])
    assert all(value.z == pytest.approx(0.0) for value in solution.displacements[-1])

    diagnostics = registry.require("physics.elastodynamics.diagnose3d")(solution)
    assert diagnostics.snapshots[0].strain_energy_si == pytest.approx(0.0, abs=1e-10)
    assert diagnostics.snapshots[-1].strain_energy_si == pytest.approx(0.0, abs=1e-10)
    assert diagnostics.snapshots[-1].max_von_mises_stress_si == pytest.approx(0.0, abs=1e-8)
    assert diagnostics.snapshots[-1].kinetic_energy_si == pytest.approx(
        diagnostics.snapshots[0].kinetic_energy_si,
        rel=1e-9,
        abs=1e-12,
    )

    view = registry.require("physics.elastodynamics.deformed_grid_view3d")(
        solution,
        displacement_scale=1.0,
    )
    scene = registry.compile_scene(view)
    assert len(scene.primitives) == 1
    assert isinstance(scene.primitives[0], PointCloud)
    assert scene.timeline is not None
    start_positions = scene.sample(0.0).primitives[0].positions
    end_positions = scene.sample(scene.timeline.duration).primitives[0].positions
    assert start_positions != end_positions
    assert end_positions[0].x - start_positions[0].x == pytest.approx(0.1)


def test_fixed_boundary_rejects_nonzero_boundary_velocity() -> None:
    grid = _grid()
    zero = (Vec3(0.0, 0.0, 0.0),) * grid.count
    velocity = tuple(
        Vec3(0.1, 0.0, 0.0) if index == 0 else Vec3(0.0, 0.0, 0.0)
        for index in range(grid.count)
    )

    with pytest.raises(ValueError, match="zero initial velocity"):
        ElastodynamicsProblem3D(
            grid=grid,
            initial_displacement=zero,
            initial_velocity=velocity,
            material=_material(),
            density=Quantity(1000.0, KILOGRAM_PER_CUBIC_METER),
            boundary="fixed",
        )
