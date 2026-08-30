from dataclasses import dataclass

import pytest

from spectra.domains import DomainRegistry


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
