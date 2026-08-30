import pytest

from spectra.core.constants import VACUUM_PERMITTIVITY
from spectra.core.primitives import VectorGlyphSet
from spectra.core.types import Vec3
from spectra.core.units import AMPERE_PER_SQUARE_METER
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.mathematics.fields import TimeDependentVectorField3D
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid3D
from spectra.domains.physics.maxwell3d import MaxwellProblem3D


def _grid() -> UniformGrid3D:
    axis = UniformGrid1D(0.0, 1.0, 3)
    return UniformGrid3D(axis, axis, axis)


def test_uniform_source_free_maxwell_fields_remain_constant_and_conserve_energy() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(
        registry,
        [
            "physics.electromagnetism.maxwell_views3d",
            "physics.electromagnetism.maxwell_diagnostics3d",
        ],
    )
    grid = _grid()
    electric = (Vec3(1.0, 0.0, 0.0),) * grid.count
    magnetic = (Vec3(0.0, 0.0, 1.0e-9),) * grid.count

    solution = registry.require("physics.maxwell.solve3d")(
        MaxwellProblem3D(
            grid=grid,
            initial_electric=electric,
            initial_magnetic=magnetic,
            boundary="periodic",
            name="uniform_em",
        ),
        end_time=1.0e-9,
        steps=4,
    )

    assert "partial_differential_equations.operators3d" in loaded
    assert "differential_equations" in loaded
    assert solution.electric_states[-1] == electric
    assert solution.magnetic_states[-1] == magnetic

    diagnostics = registry.require("physics.maxwell.diagnose3d")(solution)
    first = diagnostics.snapshots[0]
    last = diagnostics.snapshots[-1]
    assert first.max_abs_divergence_electric == pytest.approx(0.0, abs=1e-12)
    assert first.max_abs_divergence_magnetic == pytest.approx(0.0, abs=1e-12)
    assert last.total_field_energy_si == pytest.approx(first.total_field_energy_si, rel=1e-12)
    assert first.total_field_energy_si > 0.0
    assert first.max_poynting_magnitude_si > 0.0

    fields = registry.require("physics.maxwell.fields_from_solution3d")(solution)
    assert fields.electric.evaluate(Vec3(0.5, 0.5, 0.5), 0.5e-9) == Vec3(1.0, 0.0, 0.0)
    assert fields.magnetic.evaluate(Vec3(0.5, 0.5, 0.5), 0.5e-9) == Vec3(0.0, 0.0, 1.0e-9)

    animation = registry.require("physics.maxwell.electric_animation3d")(
        solution,
        temporal_samples=3,
    )
    scene = registry.compile_scene(animation)
    assert len(scene.primitives) == 1
    assert isinstance(scene.primitives[0], VectorGlyphSet)
    assert scene.timeline is not None


def test_uniform_current_density_drives_electric_field_with_ampere_maxwell_sign() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.electromagnetism.maxwell3d"])
    grid = _grid()
    current_value = 1.0e-9
    current = TimeDependentVectorField3D(
        evaluator=lambda _position, _time: Vec3(current_value, 0.0, 0.0),
        name="uniform_current",
        output_unit=AMPERE_PER_SQUARE_METER,
    )
    zero = (Vec3(0.0, 0.0, 0.0),) * grid.count
    end_time = 1.0e-6

    solution = registry.require("physics.maxwell.solve3d")(
        MaxwellProblem3D(
            grid=grid,
            initial_electric=zero,
            initial_magnetic=zero,
            boundary="periodic",
            current_density=current,
            name="current_driven_em",
        ),
        end_time=end_time,
        steps=4,
    )

    expected_electric_x = -current_value * end_time / VACUUM_PERMITTIVITY.si_value
    assert all(
        value.x == pytest.approx(expected_electric_x, rel=1e-10, abs=1e-14)
        for value in solution.electric_states[-1]
    )
    assert all(value.y == pytest.approx(0.0) and value.z == pytest.approx(0.0) for value in solution.electric_states[-1])
    assert solution.magnetic_states[-1] == zero
    assert not solution.source_free


def test_zero_maxwell_fields_stay_zero() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.electromagnetism.maxwell_diagnostics3d"])
    grid = _grid()
    zero = (Vec3(0.0, 0.0, 0.0),) * grid.count
    solution = registry.require("physics.maxwell.solve3d")(
        MaxwellProblem3D(
            grid=grid,
            initial_electric=zero,
            initial_magnetic=zero,
            boundary="fixed",
        ),
        end_time=1.0e-9,
        steps=2,
    )
    assert solution.electric_states[-1] == zero
    assert solution.magnetic_states[-1] == zero
    diagnostics = registry.require("physics.maxwell.diagnose3d")(solution)
    assert diagnostics.snapshots[-1].total_field_energy_si == pytest.approx(0.0)
