from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.units import ENERGY, JOULE, MASS, Quantity
from spectra.domains.physics.mechanics import Trajectory
from spectra.domains.potential_fields import PotentialField3D
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class ParticleEnergyHistory:
    times: tuple[float, ...]
    kinetic_joules: tuple[float, ...]
    potential_joules: tuple[float, ...]
    total_joules: tuple[float, ...]
    name: str = "particle_energy"

    def __post_init__(self) -> None:
        size = len(self.times)
        if size == 0:
            raise ValueError("particle energy history cannot be empty")
        if not (
            len(self.kinetic_joules)
            == len(self.potential_joules)
            == len(self.total_joules)
            == size
        ):
            raise ValueError("particle energy history arrays must have equal lengths")
        if any(not math.isfinite(value) for values in (
            self.kinetic_joules,
            self.potential_joules,
            self.total_joules,
        ) for value in values):
            raise ValueError("particle energy history values must be finite")

    @property
    def absolute_total_drift(self) -> float:
        return max(self.total_joules) - min(self.total_joules)

    @property
    def relative_total_drift(self) -> float:
        reference = max(abs(value) for value in self.total_joules)
        if reference == 0.0:
            return 0.0 if self.absolute_total_drift == 0.0 else math.inf
        return self.absolute_total_drift / reference


class PotentialEnergyDiagnosticsDomain:
    """Energy diagnostics for Newtonian trajectories in static scalar potentials."""

    name = "physics.potential_energy"
    version = "1"
    dependencies = (
        DomainDependency("physics.mechanics.trajectory", min_version=2),
        DomainDependency("physics.potential_field3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        def energy_history(
            trajectory: Trajectory,
            potential_field: PotentialField3D,
            *,
            mass: Quantity,
            coupling: Quantity,
            name: str | None = None,
        ) -> ParticleEnergyHistory:
            if mass.unit.dimension != MASS or mass.si_value <= 0.0:
                raise ValueError("energy diagnostics mass must be a positive mass quantity")
            potential_unit = potential_field.potential.output_unit
            if potential_unit is None:
                raise ValueError("potential field must declare a physical output unit")
            coupling_energy_unit = coupling.unit * potential_unit
            if coupling_energy_unit.dimension != ENERGY:
                raise ValueError("coupling × potential does not have energy dimension")

            kinetic = tuple(
                0.5 * mass.si_value * velocity.dot(velocity)
                for velocity in trajectory.velocities
            )
            potential = tuple(
                (Quantity(potential_field.potential.evaluate(position), potential_unit) * coupling).to(JOULE).value
                for position in trajectory.positions
            )
            total = tuple(
                kinetic_value + potential_value
                for kinetic_value, potential_value in zip(kinetic, potential, strict=True)
            )
            return ParticleEnergyHistory(
                times=trajectory.times,
                kinetic_joules=kinetic,
                potential_joules=potential,
                total_joules=total,
                name=name or f"{trajectory.name}.energy",
            )

        registry.register_semantic_type(
            "physics.potential_energy.history",
            ParticleEnergyHistory,
        )
        registry.provide("physics.potential_energy.history", ParticleEnergyHistory)
        registry.provide("physics.potential_energy.compute_history", energy_history)
