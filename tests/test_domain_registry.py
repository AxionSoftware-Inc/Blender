from dataclasses import dataclass

import pytest

from spectra.domains import DomainRegistry
from spectra.domains.registry import DomainDependency


@dataclass(frozen=True)
class ExampleSemanticObject:
    value: float


class ExampleDomain:
    name = "example"
    version = "1"

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type("example.object", ExampleSemanticObject)
        registry.register_compiler("example.object_to_value", lambda obj: obj.value)


def test_domain_can_register_without_core_knowing_its_subject() -> None:
    registry = DomainRegistry()
    registry.add_domain(ExampleDomain())

    assert "example" in registry.domains
    assert registry.semantic_types["example.object"] is ExampleSemanticObject
    compiler = registry.compiler_for("example.object_to_value")
    assert compiler(ExampleSemanticObject(3.5)) == 3.5


def test_duplicate_domain_registration_is_rejected() -> None:
    registry = DomainRegistry()
    registry.add_domain(ExampleDomain())

    with pytest.raises(ValueError, match="domain already registered"):
        registry.add_domain(ExampleDomain())


def test_one_domain_can_consume_another_domains_capability() -> None:
    registry = DomainRegistry()
    registry.provide("probability.expectation", lambda values: sum(values) / len(values))

    expectation = registry.require("probability.expectation")
    assert expectation([1.0, 2.0, 6.0]) == 3.0


def test_dependency_resolution_supports_required_and_optional_capabilities() -> None:
    registry = DomainRegistry()
    registry.provide("linear_algebra.inner_product", lambda a, b: sum(x * y for x, y in zip(a, b)))

    resolved = registry.resolve_dependencies(
        [
            DomainDependency("linear_algebra.inner_product"),
            DomainDependency("probability.sample", optional=True),
        ]
    )
    assert "linear_algebra.inner_product" in resolved
    assert "probability.sample" not in resolved

    with pytest.raises(KeyError, match="required capability"):
        registry.resolve_dependencies([DomainDependency("complex.norm")])


def test_capability_contract_versions_are_enforced() -> None:
    registry = DomainRegistry()
    registry.provide("linear_algebra.operator", object(), version=2)

    assert registry.capability_version("linear_algebra.operator") == 2
    assert registry.has_capability("linear_algebra.operator", min_version=2)
    assert not registry.has_capability("linear_algebra.operator", min_version=3)
    assert registry.require("linear_algebra.operator", min_version=2) is not None

    with pytest.raises(KeyError, match="version is not available"):
        registry.require("linear_algebra.operator", min_version=3)


def test_optional_dependency_with_insufficient_version_is_skipped() -> None:
    registry = DomainRegistry()
    registry.provide("probability.sample", object(), version=1)

    resolved = registry.resolve_dependencies(
        [DomainDependency("probability.sample", optional=True, min_version=2)]
    )
    assert resolved == {}
