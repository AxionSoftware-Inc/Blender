from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import math

from spectra.domains.registry import DomainRegistry


ReactionRateLaw = Callable[[float, tuple[float, ...]], float]


@dataclass(frozen=True, slots=True)
class ChemicalReaction:
    """Local reaction progress rate with stoichiometric concentration changes.

    Concentrations are SI mol/m^3 and the rate law returns reaction progress in
    mol/(m^3*s). Stoichiometric changes are signed dimensionless coefficients.
    """

    name: str
    stoichiometric_change: tuple[float, ...]
    rate_law: ReactionRateLaw

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("reaction name cannot be empty")
        if not self.stoichiometric_change:
            raise ValueError("reaction stoichiometry cannot be empty")
        if any(not math.isfinite(float(value)) for value in self.stoichiometric_change):
            raise ValueError("reaction stoichiometry must be finite")

    def rate(self, time: float, concentrations: tuple[float, ...]) -> float:
        value = float(self.rate_law(float(time), concentrations))
        if not math.isfinite(value) or value < 0.0:
            raise ValueError("reaction rate must be finite and non-negative")
        return value


@dataclass(frozen=True, slots=True)
class ReactionNetwork:
    species: tuple[str, ...]
    reactions: tuple[ChemicalReaction, ...]
    name: str = "reaction_network"

    def __post_init__(self) -> None:
        if not self.species:
            raise ValueError("reaction network requires at least one species")
        if len(self.species) != len(set(self.species)):
            raise ValueError("reaction-network species names must be unique")
        if any(not species for species in self.species):
            raise ValueError("reaction-network species names cannot be empty")
        if any(len(reaction.stoichiometric_change) != len(self.species) for reaction in self.reactions):
            raise ValueError("reaction stoichiometry must match species count")
        if not self.name:
            raise ValueError("reaction-network name cannot be empty")

    def derivative(self, time: float, concentrations: tuple[float, ...]) -> tuple[float, ...]:
        if len(concentrations) != len(self.species):
            raise ValueError("reaction-network concentration count mismatch")
        values = tuple(float(value) for value in concentrations)
        if any(not math.isfinite(value) or value < 0.0 for value in values):
            raise ValueError("reaction concentrations must be finite and non-negative")
        derivative = [0.0] * len(self.species)
        for reaction in self.reactions:
            rate = reaction.rate(time, values)
            for index, coefficient in enumerate(reaction.stoichiometric_change):
                derivative[index] += coefficient * rate
        return tuple(derivative)


def mass_action_reaction(
    *,
    name: str,
    reactant_orders: tuple[float, ...],
    stoichiometric_change: tuple[float, ...],
    rate_constant_si: float,
) -> ChemicalReaction:
    """Create a mass-action rate law using SI-consistent concentration units.

    The dimensional unit of the numerical rate constant depends on total reaction
    order, so the constant is intentionally stored as an SI scalar rather than a
    misleading fixed Unit.
    """

    if len(reactant_orders) != len(stoichiometric_change):
        raise ValueError("mass-action orders and stoichiometry must have equal length")
    orders = tuple(float(value) for value in reactant_orders)
    if any(not math.isfinite(value) or value < 0.0 for value in orders):
        raise ValueError("mass-action reaction orders must be finite and non-negative")
    rate_constant = float(rate_constant_si)
    if not math.isfinite(rate_constant) or rate_constant < 0.0:
        raise ValueError("mass-action rate constant must be finite and non-negative")

    def rate_law(_time: float, concentrations: tuple[float, ...]) -> float:
        if len(concentrations) != len(orders):
            raise ValueError("mass-action concentration count mismatch")
        rate = rate_constant
        for concentration, order in zip(concentrations, orders, strict=True):
            if concentration < 0.0:
                raise ValueError("mass-action concentrations cannot be negative")
            rate *= concentration ** order
        return rate

    return ChemicalReaction(
        name=name,
        stoichiometric_change=tuple(float(value) for value in stoichiometric_change),
        rate_law=rate_law,
    )


class ChemistryDomain:
    name = "chemistry"
    version = "1"
    dependencies = ()

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type("chemistry.reaction", ChemicalReaction)
        registry.register_semantic_type("chemistry.reaction_network", ReactionNetwork)
        registry.provide("chemistry.reaction", ChemicalReaction)
        registry.provide("chemistry.reaction_network", ReactionNetwork)
        registry.provide("chemistry.mass_action_reaction", mass_action_reaction)
        registry.provide(
            "chemistry.reaction_derivative",
            lambda network, time, concentrations: network.derivative(time, concentrations),
        )
