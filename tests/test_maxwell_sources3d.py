import pytest

from spectra.core.constants import VACUUM_PERMITTIVITY
from spectra.core.types import Vec3
from spectra.core.units import COULOMB_PER_CUBIC_METER
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.mathematics.fields import TimeDependentScalarField3D
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid3D
from spectra.domains.physics.maxwell import MaxwellSolution3D, MaxwellSourceFields3D


def _grid() -> UniformGrid3D:
    axis = UniformGrid1D(0.0, 1.0, 3)
    return UniformGrid3D(axis, axis, axis)


def _zero_solution() -> MaxwellSolution3D:
    grid = _grid()
    zero = (Vec3(0.0, 0.0, 0.0),) * grid.count
    return MaxwellSolution3D(
        grid=grid,
        times=(0.0, 1.0),
        electric_states=(zero, zero),
        magnetic_states=(zero, zero),
        boundary="periodic",
        source_free=False,
        name="zero_fields",
    )


def _charge_source(value: float) -> MaxwellSourceFields3D:
    return MaxwellSourceFields3D(
        charge_density=TimeDependentScalarField3D(
            evaluator=lambda _position, _time: value,
            name="rho",
            output_unit=COULOMB_PER_CUBIC_METER,
        ),
        name="static_charge",
    )


def test_zero_source_has_zero_gauss_and_continuity_residuals() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(
        registry,
        ["physics.electromagnetism.maxwell_sources3d"],
    )
    diagnostics = registry.require("physics.maxwell.source_diagnostics3d")(
        _zero_solution(),
        _charge_source(0.0),
    )

    assert "partial_differential_equations.conservation3d" in loaded
    assert all(
        snapshot.max_abs_electric_gauss_residual == pytest.approx(0.0)
        and snapshot.max_abs_magnetic_divergence == pytest.approx(0.0)
        for snapshot in diagnostics.gauss_snapshots
    )
    assert diagnostics.continuity.worst_max_abs_residual == pytest.approx(0.0)


def test_static_charge_exposes_gauss_residual_without_breaking_continuity() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(
        registry,
        ["physics.electromagnetism.maxwell_sources3d"],
    )
    charge_density = 2.0
    diagnostics = registry.require("physics.maxwell.source_diagnostics3d")(
        _zero_solution(),
        _charge_source(charge_density),
    )

    expected = charge_density / VACUUM_PERMITTIVITY.si_value
    assert diagnostics.gauss_snapshots[0].max_abs_electric_gauss_residual == pytest.approx(expected)
    assert diagnostics.continuity.worst_max_abs_residual == pytest.approx(0.0)
