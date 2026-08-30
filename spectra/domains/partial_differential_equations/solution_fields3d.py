from __future__ import annotations

from spectra.core.units import Unit
from spectra.domains.mathematics.fields import TimeDependentScalarField3D
from spectra.domains.partial_differential_equations.domain3d import ScalarPDESolution3D
from spectra.domains.registry import DomainDependency, DomainRegistry


class PDESolutionFields3DDomain:
    """Turn sampled 3D PDE histories back into continuous field semantics."""

    name = "partial_differential_equations.solution_fields3d"
    version = "1"
    dependencies = (
        DomainDependency("pde.scalar_solution3d"),
        DomainDependency("pde.time_scalar_field_from_grid_3d", min_version=2),
    )

    def register(self, registry: DomainRegistry) -> None:
        adapter = registry.require("pde.time_scalar_field_from_grid_3d", min_version=2)

        def from_solution(
            solution: ScalarPDESolution3D,
            *,
            output_unit: Unit | None = None,
            spatial_outside: str = "clamp",
            temporal_outside: str = "clamp",
            name: str | None = None,
        ) -> TimeDependentScalarField3D:
            return adapter(
                solution.grid,
                solution.times,
                solution.states,
                name=name or f"{solution.name}.field",
                output_unit=output_unit,
                spatial_outside=spatial_outside,
                temporal_outside=temporal_outside,
            )

        registry.provide("pde.time_scalar_field_from_solution_3d", from_solution)
