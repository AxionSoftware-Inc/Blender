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
    assert "differential_equations.adaptive_reference" in names
    assert "experiments" in names
    assert "experiments.analysis" in names
    assert "experiments.artifacts" in names
    assert "experiments.batching" in names
    assert "experiments.calibration" in names
    assert "experiments.convergence" in names
    assert "experiments.sensitivity" in names
    assert "experiments.uncertainty" in names
    assert "experiments.views" in names
    assert "physics.electromagnetism.maxwell3d" in names
    assert "physics.electromagnetism.maxwell_sources3d" in names
    assert "physics.electrothermal.3d" in names
    assert "physics.elastodynamics.3d" in names


def test_auto_discovered_catalog_indexes_new_provider_chains() -> None:
    catalog = builtin_domain_catalog()
    assert catalog.provider_for("ode.solve_rk4.method").name == "differential_equations"
    assert catalog.provider_for("ode.solver_role.first_order").name == "differential_equations"
    assert catalog.provider_for("ode.solve_first_order").name == "differential_equations"
    assert catalog.provider_for("ode.first_order.rk45_reference").name == "differential_equations.adaptive_reference"
    assert catalog.provider_for("pde.solve_method_of_lines_3d.method").name == "partial_differential_equations.3d"
    assert catalog.provider_for("pde.solve_coupled_scalar_3d").name == "partial_differential_equations.coupled3d"
    assert catalog.provider_for("chemistry.reaction_diffusion.solve3d").name == "chemistry.reaction_diffusion.3d"
    assert catalog.provider_for("chemistry.thermochemistry.heat_source_field3d").name == "chemistry.thermochemistry.3d"
    assert catalog.provider_for("experiments.run_sweep").name == "experiments"
    assert catalog.provider_for("experiments.run_sweep_tracked").name == "experiments"
    assert catalog.provider_for("experiments.run_sweep_batched").name == "experiments.batching"
    assert catalog.provider_for("experiments.run_solver_convergence").name == "experiments.convergence"
    assert catalog.provider_for("experiments.local_sensitivity").name == "experiments.sensitivity"
    assert catalog.provider_for("experiments.propagate_uncertainty").name == "experiments.uncertainty"
    assert catalog.provider_for("experiments.calibrate_grid").name == "experiments.calibration"
    assert catalog.provider_for("experiments.artifact_to_json").name == "experiments.artifacts"
    assert catalog.provider_for("experiments.metric_series_view2d").name == "experiments.views"
    assert catalog.provider_for("physics.maxwell.solve3d").name == "physics.electromagnetism.maxwell3d"
    assert catalog.provider_for("physics.maxwell.source_diagnostics3d").name == "physics.electromagnetism.maxwell_sources3d"
    assert catalog.provider_for("physics.electrothermal.joule_heat_field3d").name == "physics.electrothermal.3d"
    assert catalog.provider_for("physics.elastodynamics.solve3d").name == "physics.elastodynamics.3d"
