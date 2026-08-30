import pytest

from spectra.core.units import (
    JOULE,
    JOULE_PER_KILOGRAM_KELVIN,
    KILOGRAM_PER_CUBIC_METER,
    MOLE,
    Quantity,
    WATT_PER_METER_KELVIN,
)
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.chemistry import ChemicalReaction, ReactionNetwork
from spectra.domains.chemistry.reaction_diffusion3d import ReactionDiffusionSolution3D
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid3D
from spectra.domains.partial_differential_equations.coupled3d import CoupledScalarPDESolution3D
from spectra.domains.physics import ThermalMaterial3D


def _grid() -> UniformGrid3D:
    axis = UniformGrid1D(0.0, 1.0, 3)
    return UniformGrid3D(axis, axis, axis)


def _reaction_solution() -> ReactionDiffusionSolution3D:
    grid = _grid()
    network = ReactionNetwork(
        species=("A", "B"),
        reactions=(
            ChemicalReaction(
                name="A_to_B",
                stoichiometric_change=(-1.0, 1.0),
                rate_law=lambda _time, _concentrations: 2.0,
            ),
        ),
        name="constant_reaction",
    )
    states = (
        ((1.0,) * grid.count, (0.0,) * grid.count),
        ((1.0,) * grid.count, (0.0,) * grid.count),
    )
    coupled = CoupledScalarPDESolution3D(
        grid=grid,
        component_names=network.species,
        times=(0.0, 1.0),
        states=states,
        name="constant_reaction_history",
    )
    return ReactionDiffusionSolution3D(
        coupled_solution=coupled,
        network=network,
        diffusivities_si=(0.0, 0.0),
        boundary="periodic",
    )


def test_exothermic_reaction_history_becomes_positive_heat_source() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(registry, ["chemistry.thermochemistry.3d"])
    solution = _reaction_solution()

    source = registry.require("chemistry.thermochemistry.source_from_solution3d")(
        solution,
        (Quantity(-100.0, JOULE / MOLE),),
    )
    field = registry.require("chemistry.thermochemistry.heat_source_field3d")(source)

    assert "chemistry.reaction_diffusion.3d" in loaded
    assert "physics.heat_conduction.3d" in loaded
    assert field.evaluate(solution.grid_coordinate if False else __import__("spectra").core.types.Vec3(0.5, 0.5, 0.5), 0.5) == pytest.approx(200.0)


def test_thermochemical_heat_problem_reuses_heat_solver() -> None:
    from spectra.core.types import Vec3

    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["chemistry.thermochemistry.3d"])
    reaction_solution = _reaction_solution()
    material = ThermalMaterial3D(
        density=Quantity(1.0, KILOGRAM_PER_CUBIC_METER),
        specific_heat=Quantity(1.0, JOULE_PER_KILOGRAM_KELVIN),
        thermal_conductivity=Quantity(1.0, WATT_PER_METER_KELVIN),
    )
    problem = registry.require(
        "chemistry.thermochemistry.heat_problem_from_reaction_solution3d"
    )(
        reaction_solution,
        (Quantity(-100.0, JOULE / MOLE),),
        initial_temperature=(300.0,) * reaction_solution.grid.count,
        material=material,
        boundary="periodic",
    )
    assert problem.volumetric_heat_source is not None
    assert problem.volumetric_heat_source.evaluate(Vec3(0.5, 0.5, 0.5), 0.05) == pytest.approx(200.0)

    solve_heat = registry.require("physics.heat_conduction.solve3d")
    heat = solve_heat(problem, end_time=0.1, steps=2)
    assert heat.temperature_states[-1] == pytest.approx((320.0,) * reaction_solution.grid.count)
