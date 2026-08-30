from __future__ import annotations

from dataclasses import dataclass

from spectra.core.types import Vec3
from spectra.core.units import CHARGE, KILOGRAM_PER_CUBIC_METER, MASS, Quantity
from spectra.domains.partial_differential_equations.domain3d import BoundaryMode3D, UniformGrid3D
from spectra.domains.physics.electrostatic_potential3d import COULOMB_PER_CUBIC_METER
from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class PointChargeSource3D:
    position: Vec3
    charge: Quantity

    def __post_init__(self) -> None:
        if self.charge.unit.dimension != CHARGE:
            raise ValueError("point charge source requires a charge quantity")


@dataclass(frozen=True, slots=True)
class PointMassSource3D:
    position: Vec3
    mass: Quantity

    def __post_init__(self) -> None:
        if self.mass.unit.dimension != MASS or self.mass.si_value < 0.0:
            raise ValueError("point mass source requires a non-negative mass quantity")


class PotentialSources3DDomain:
    """Bridge discrete typed sources into generic deposited-density potential problems."""

    name = "physics.potential_sources.3d"
    version = "1"
    dependencies = (
        DomainDependency("pde.point_source3d"),
        DomainDependency("pde.deposit_point_density_3d"),
        DomainDependency("physics.electrostatic_potential.problem3d"),
        DomainDependency("physics.gravitational_potential.problem3d"),
    )

    def register(self, registry: DomainRegistry) -> None:
        point_source_type = registry.require("pde.point_source3d")
        deposit_density = registry.require("pde.deposit_point_density_3d")
        electrostatic_problem_type = registry.require("physics.electrostatic_potential.problem3d")
        gravity_problem_type = registry.require("physics.gravitational_potential.problem3d")

        def electrostatic_problem(
            grid: UniformGrid3D,
            sources: tuple[PointChargeSource3D, ...],
            *,
            boundary: BoundaryMode3D = "fixed",
            potential_initial_values: tuple[float, ...] | None = None,
            scheme: str = "cloud_in_cell",
            outside: str = "error",
            name: str = "point_charge_potential3d",
        ):
            deposited = deposit_density(
                grid,
                tuple(
                    point_source_type(source.position, source.charge.si_value)
                    for source in sources
                ),
                scheme=scheme,
                outside=outside,
            )
            return electrostatic_problem_type(
                grid=grid,
                charge_density=deposited,
                charge_density_unit=COULOMB_PER_CUBIC_METER,
                boundary=boundary,
                potential_initial_values=potential_initial_values,
                name=name,
            )

        def gravitational_problem(
            grid: UniformGrid3D,
            sources: tuple[PointMassSource3D, ...],
            *,
            boundary: BoundaryMode3D = "fixed",
            potential_initial_values: tuple[float, ...] | None = None,
            scheme: str = "cloud_in_cell",
            outside: str = "error",
            name: str = "point_mass_potential3d",
        ):
            deposited = deposit_density(
                grid,
                tuple(
                    point_source_type(source.position, source.mass.si_value)
                    for source in sources
                ),
                scheme=scheme,
                outside=outside,
            )
            return gravity_problem_type(
                grid=grid,
                mass_density=deposited,
                mass_density_unit=KILOGRAM_PER_CUBIC_METER,
                boundary=boundary,
                potential_initial_values=potential_initial_values,
                name=name,
            )

        registry.register_semantic_type(
            "physics.potential_sources.point_charge3d",
            PointChargeSource3D,
        )
        registry.register_semantic_type(
            "physics.potential_sources.point_mass3d",
            PointMassSource3D,
        )
        registry.provide("physics.potential_sources.point_charge3d", PointChargeSource3D)
        registry.provide("physics.potential_sources.point_mass3d", PointMassSource3D)
        registry.provide(
            "physics.potential_sources.electrostatic_problem3d",
            electrostatic_problem,
        )
        registry.provide(
            "physics.potential_sources.gravitational_problem3d",
            gravitational_problem,
        )
