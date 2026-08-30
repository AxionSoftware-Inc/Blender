import math

import pytest

from spectra.core.types import Vec3
from spectra.core.units import SQUARE_METER_PER_SECOND, Quantity
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.chemistry import ReactionNetwork, mass_action_reaction
from spectra.domains.chemistry.reaction_diffusion3d import ReactionDiffusionProblem3D
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid3D


def _network() -> ReactionNetwork:
    reaction = mass_action_reaction(
        name="A_to_B",
        reactant_orders=(1.0, 0.0),
        stoichiometric_change=(-1.0, 1.0),
        rate_constant_si=0.5,
    )
    return ReactionNetwork(species=("A", "B"), reactions=(reaction,), name="conversion")


def _grid() -> UniformGrid3D:
    axis = UniformGrid1D(0.0, 1.0, 3)
    return UniformGrid3D(axis, axis, axis)


def test_mass_action_network_local_derivative() -> None:
    network = _network()
    derivative = network.derivative(0.0, (3.0, 0.0))
    assert derivative == pytest.approx((-1.5, 1.5))


def test_uniform_reaction_diffusion_reduces_to_local_kinetics_and_conserves_species_sum() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(
        registry,
        ["chemistry.reaction_diffusion.views3d"],
    )
    grid = _grid()
    initial_a = (1.0,) * grid.count
    initial_b = (0.0,) * grid.count
    zero_diffusion = Quantity(0.0, SQUARE_METER_PER_SECOND)

    solution = registry.require("chemistry.reaction_diffusion.solve3d")(
        ReactionDiffusionProblem3D(
            grid=grid,
            network=_network(),
            initial_concentrations=(initial_a, initial_b),
            diffusivities=(zero_diffusion, zero_diffusion),
            boundary="periodic",
            name="uniform_conversion",
        ),
        end_time=1.0,
        steps=32,
    )

    expected_a = math.exp(-0.5)
    final_a = solution.species_solution("A").states[-1]
    final_b = solution.species_solution("B").states[-1]
    assert final_a == pytest.approx((expected_a,) * grid.count, rel=1e-7)
    assert final_b == pytest.approx((1.0 - expected_a,) * grid.count, rel=1e-7)
    assert all(a + b == pytest.approx(1.0, rel=1e-8) for a, b in zip(final_a, final_b, strict=True))
    assert "partial_differential_equations.coupled3d" in loaded
    assert "chemistry" in loaded

    fields = registry.require("chemistry.reaction_diffusion.fields_from_solution3d")(solution)
    assert fields.field_for("A").evaluate(Vec3(0.5, 0.5, 0.5), 1.0) == pytest.approx(expected_a, rel=1e-7)
    view = registry.require("chemistry.reaction_diffusion.species_slice3d")(
        solution,
        "B",
        axis="z",
        index=1,
    )
    scene = registry.compile_scene(view)
    assert scene.timeline is not None
