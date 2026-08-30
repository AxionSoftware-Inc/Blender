from spectra.domains import builtin_domain_catalog
from spectra.domains.builtin_catalog import BUILTIN_DOMAIN_FACTORIES


def test_builtin_domain_factories_are_auto_discovered_unique_and_sorted() -> None:
    names = tuple(factory().name for factory in BUILTIN_DOMAIN_FACTORIES)
    assert names == tuple(sorted(names))
    assert len(names) == len(set(names))
    assert "chemistry" in names
    assert "chemistry.reaction_diffusion.3d" in names
    assert "chemistry.reaction_diffusion.views3d" in names
    assert "chemistry.thermochemistry.3d" in names
    assert "physics.electromagnetism.maxwell3d" in names
    assert "physics.electromagnetism.maxwell_sources3d" in names
    assert "physics.electrothermal.3d" in names
    assert "physics.elastodynamics.3d" in names


def test_auto_discovered_catalog_indexes_new_provider_chains() -> None:
    catalog = builtin_domain_catalog()
    assert catalog.provider_for("ode.solve_rk4.method").name == "differential_equations"
    assert catalog.provider_for("pde.solve_method_of_lines_3d.method").name == "partial_differential_equations.3d"
    assert catalog.provider_for("pde.solve_coupled_scalar_3d").name == "partial_differential_equations.coupled3d"
    assert catalog.provider_for("chemistry.reaction_diffusion.solve3d").name == "chemistry.reaction_diffusion.3d"
    assert catalog.provider_for("chemistry.thermochemistry.heat_source_field3d").name == "chemistry.thermochemistry.3d"
    assert catalog.provider_for("physics.maxwell.solve3d").name == "physics.electromagnetism.maxwell3d"
    assert catalog.provider_for("physics.maxwell.source_diagnostics3d").name == "physics.electromagnetism.maxwell_sources3d"
    assert catalog.provider_for("physics.electrothermal.joule_heat_field3d").name == "physics.electrothermal.3d"
    assert catalog.provider_for("physics.elastodynamics.solve3d").name == "physics.elastodynamics.3d"
