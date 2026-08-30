from __future__ import annotations

from dataclasses import dataclass

import pytest

from spectra.core.scene import Scene
from spectra.domains import DomainDependency, DomainRegistry
from spectra.domains.registry import DomainResolutionError


@dataclass(frozen=True)
class BrokenSemantic:
    value: float


class BrokenDomain:
    name = "broken"
    version = "1"
    dependencies = ()

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type("broken.semantic", BrokenSemantic)
        registry.provide("broken.capability", object())
        registry.register_visualization(BrokenSemantic, lambda _value: Scene())
        raise RuntimeError("registration failed")


class GoodDomain:
    name = "good"
    version = "1"
    dependencies = ()

    def register(self, registry: DomainRegistry) -> None:
        registry.provide("good.capability", object())


class MissingDependencyDomain:
    name = "missing"
    version = "1"
    dependencies = (DomainDependency("does.not.exist"),)

    def register(self, registry: DomainRegistry) -> None:
        raise AssertionError("must never register")


def test_failed_domain_registration_is_fully_rolled_back() -> None:
    registry = DomainRegistry()

    with pytest.raises(RuntimeError, match="registration failed"):
        registry.add_domain(BrokenDomain())

    assert "broken" not in registry.domains
    assert "broken.semantic" not in registry.semantic_types
    assert "broken.capability" not in registry.capabilities
    assert not registry.can_visualize(BrokenSemantic)


def test_failed_domain_batch_is_atomic() -> None:
    registry = DomainRegistry()

    with pytest.raises(DomainResolutionError):
        registry.add_domains([GoodDomain(), MissingDependencyDomain()])

    assert "good" not in registry.domains
    assert "good.capability" not in registry.capabilities
