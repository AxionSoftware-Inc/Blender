import pytest

from spectra.domains import DomainRegistry, DomainResolutionError, builtin_domain_catalog


def test_catalog_loads_quantum_dependency_closure_automatically() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()

    loaded = catalog.load(registry, ["physics.quantum"])

    assert set(loaded) == {"linear_algebra", "probability", "physics.quantum"}
    assert registry.has_capability("linear_algebra.complex_matrix", min_version=2)
    assert registry.has_capability("probability.discrete_distribution")
    assert registry.has_capability("physics.quantum.expectation_value", min_version=2)


def test_catalog_loads_continuous_probability_through_calculus_and_math() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()

    loaded = catalog.load(registry, ["probability.continuous"])

    assert set(loaded) == {"mathematics", "calculus", "probability.continuous"}
    assert registry.has_capability("mathematics.function1d")
    assert registry.has_capability("calculus.integrate", min_version=2)
    assert registry.has_capability("probability.continuous.cdf")


def test_catalog_does_not_reload_domains_already_present() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()

    first = catalog.load(registry, ["mathematics"])
    second = catalog.load(registry, ["physics.waves"])

    assert first == ("mathematics",)
    assert second == ("physics.waves",)
    assert "mathematics" in registry.domains
    assert "physics.waves" in registry.domains


def test_catalog_can_find_capability_provider() -> None:
    catalog = builtin_domain_catalog()
    provider = catalog.provider_for("calculus.curl_at")

    assert provider is not None
    assert provider.name == "calculus"


def test_catalog_loads_provider_closure_by_capability() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()

    loaded = catalog.load_capabilities(
        registry,
        ("physics.maxwell.solve3d", "experiments.run_sweep_batched"),
    )

    assert "physics.electromagnetism.maxwell3d" in loaded
    assert "experiments.batching" in loaded
    assert registry.has_capability("physics.maxwell.solve3d", min_version=2)
    assert registry.has_capability("experiments.run_sweep_batched")
    assert registry.has_capability("ode.solve_first_order", min_version=2)


def test_catalog_capability_load_is_noop_when_already_available() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()

    first = catalog.load_capabilities(registry, ("ode.solve_first_order",))
    second = catalog.load_capabilities(registry, ("ode.solve_first_order",))

    assert first == ("differential_equations",)
    assert second == ()


def test_catalog_reports_unknown_requested_capability() -> None:
    registry = DomainRegistry()
    catalog = builtin_domain_catalog()

    with pytest.raises(DomainResolutionError, match="no provider"):
        catalog.load_capabilities(registry, ("tests.capability.does_not_exist",))
