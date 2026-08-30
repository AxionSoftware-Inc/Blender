import math

import pytest

from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.chemistry import (
    ReactionKineticsProblem,
    ReactionNetwork,
    mass_action_reaction,
)


def _network() -> ReactionNetwork:
    return ReactionNetwork(
        species=("A", "B"),
        reactions=(
            mass_action_reaction(
                name="A_to_B",
                reactant_orders=(1.0, 0.0),
                stoichiometric_change=(-1.0, 1.0),
                rate_constant_si=0.5,
            ),
        ),
        name="well_mixed_conversion",
    )


def test_well_mixed_reaction_kinetics_reuses_generic_ode() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(registry, ["chemistry.kinetics"])
    solution = registry.require("chemistry.kinetics.solve")(
        ReactionKineticsProblem(
            network=_network(),
            initial_concentrations=(1.0, 0.0),
        ),
        end_time=1.0,
        steps=32,
    )

    expected_a = math.exp(-0.5)
    assert solution.species_history("A")[-1] == pytest.approx(expected_a, rel=1e-7)
    assert solution.species_history("B")[-1] == pytest.approx(1.0 - expected_a, rel=1e-7)
    assert all(
        a + b == pytest.approx(1.0, rel=1e-8)
        for a, b in solution.states
    )
    assert "differential_equations" in loaded
    assert "chemistry" in loaded
