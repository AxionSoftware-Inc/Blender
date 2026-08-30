from spectra.domains import DomainRegistry, builtin_domain_catalog


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
