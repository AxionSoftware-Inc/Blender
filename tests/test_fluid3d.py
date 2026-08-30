import pytest

from spectra.core.types import Vec3
from spectra.core.units import METER_PER_SECOND
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.mathematics import VectorField3D
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid3D
from spectra.domains.physics import PassiveScalarProblem3D, SteadyFlow3D


def _grid() -> UniformGrid3D:
    axis = UniformGrid1D(0.0, 1.0, 3)
    return UniformGrid3D(axis, axis, axis)


def test_fluid_kinematics_3d_reuses_generic_vector_calculus() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(registry, ["physics.fluid_kinematics.3d"])
    flow = SteadyFlow3D(
        VectorField3D(
            evaluator=lambda p: Vec3(-p.y, p.x, 0.0),
            name="solid_rotation",
            output_unit=METER_PER_SECOND,
        )
    )
    position = Vec3(0.25, -0.5, 0.1)

    divergence = registry.require("physics.fluid.divergence_at_3d")(flow, position)
    vorticity = registry.require("physics.fluid.vorticity_at_3d")(flow, position)
    incompressible = registry.require("physics.fluid.is_locally_incompressible_3d")(
        flow,
        position,
        tolerance=1e-8,
    )

    assert "calculus" in loaded
    assert "field_dynamics" in loaded
    assert divergence == pytest.approx(0.0, abs=1e-9)
    assert vorticity.x == pytest.approx(0.0, abs=1e-9)
    assert vorticity.y == pytest.approx(0.0, abs=1e-9)
    assert vorticity.z == pytest.approx(2.0, rel=1e-6)
    assert incompressible


def test_fluid_kinematics_3d_streamline_uses_generic_field_dynamics() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.fluid_kinematics.3d"])
    flow = SteadyFlow3D(
        VectorField3D(
            evaluator=lambda _p: Vec3(1.0, 0.0, 0.0),
            name="uniform_flow",
            output_unit=METER_PER_SECOND,
        )
    )
    problem = registry.require("physics.fluid.streamline_problem_3d")(
        flow,
        Vec3(0.0, 0.0, 0.0),
    )
    solution = registry.require("field_dynamics.solve_integral_curve")(
        problem,
        end_parameter=1.0,
        steps=4,
    )

    assert solution.positions[-1].x == pytest.approx(1.0)
    assert solution.positions[-1].y == pytest.approx(0.0)
    assert solution.positions[-1].z == pytest.approx(0.0)


def test_passive_scalar_3d_zero_flow_zero_diffusion_is_invariant() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(registry, ["physics.fluid_transport.3d"])
    grid = _grid()
    steady = SteadyFlow3D(
        VectorField3D(
            evaluator=lambda _p: Vec3(0.0, 0.0, 0.0),
            name="still",
            output_unit=METER_PER_SECOND,
        )
    )
    initial = tuple(float(index) for index in range(grid.count))
    problem = PassiveScalarProblem3D.in_steady_flow(
        steady,
        grid,
        initial,
        diffusivity=0.0,
    )
    solution = registry.require("physics.fluid.solve_passive_scalar3d")(
        problem,
        end_time=0.1,
        steps=2,
    )

    assert "partial_differential_equations.transport3d" in loaded
    assert solution.states[-1] == pytest.approx(initial)


def test_explicit_stability_3d_conservative_cfl_envelope() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["partial_differential_equations.stability3d"])
    grid = _grid()
    field = VectorField3D(
        evaluator=lambda _p: Vec3(1.0, 2.0, 3.0),
        name="constant_velocity",
    )
    diagnostic = registry.require("pde.explicit_stability_for_field_3d")(
        grid,
        field,
        dt=0.05,
        diffusivity=0.0,
        safety=0.9,
    )

    assert diagnostic.cfl_x == pytest.approx(0.1)
    assert diagnostic.cfl_y == pytest.approx(0.2)
    assert diagnostic.cfl_z == pytest.approx(0.3)
    assert diagnostic.cfl_sum == pytest.approx(0.6)
    assert diagnostic.suggested_max_dt == pytest.approx(0.075)
    assert diagnostic.within_conservative_envelope
