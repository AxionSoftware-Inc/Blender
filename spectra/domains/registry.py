from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from spectra.domains.base import DomainModule


Compiler = Callable[[Any], Any]
Capability = Any


@dataclass(frozen=True)
class DomainDependency:
    """A stable capability dependency declared by a scientific domain."""

    capability: str
    optional: bool = False


class DomainResolutionError(RuntimeError):
    pass


@dataclass
class DomainRegistry:
    """Registry shared by independently-developed scientific domains.

    The registry intentionally knows nothing about calculus, probability,
    statistics, physics, or any other particular field. Domains publish
    semantics, compilers, and reusable capabilities under stable string keys.
    Other domains consume those capabilities without importing implementation
    internals from one another.
    """

    domains: dict[str, "DomainModule"] = field(default_factory=dict)
    semantic_types: dict[str, type[Any]] = field(default_factory=dict)
    compilers: dict[str, Compiler] = field(default_factory=dict)
    capabilities: dict[str, Capability] = field(default_factory=dict)

    def add_domain(self, domain: "DomainModule") -> None:
        if domain.name in self.domains:
            raise ValueError(f"domain already registered: {domain.name}")

        dependencies = tuple(getattr(domain, "dependencies", ()))
        self.resolve_dependencies(dependencies)

        self.domains[domain.name] = domain
        try:
            domain.register(self)
        except Exception:
            self.domains.pop(domain.name, None)
            raise

    def add_domains(self, domains: Iterable["DomainModule"]) -> None:
        """Register a set of domains in dependency-resolved order.

        Callers may supply domains in arbitrary order. Required capability
        dependencies are resolved iteratively; unresolved cycles or missing
        providers are reported with a compact diagnostic.
        """
        pending = list(domains)
        names = [domain.name for domain in pending]
        if len(names) != len(set(names)):
            raise ValueError("domain batch contains duplicate names")
        already_registered = set(names).intersection(self.domains)
        if already_registered:
            duplicate = sorted(already_registered)[0]
            raise ValueError(f"domain already registered: {duplicate}")

        while pending:
            progress = False
            next_pending: list["DomainModule"] = []

            for domain in pending:
                required = tuple(
                    dependency.capability
                    for dependency in getattr(domain, "dependencies", ())
                    if not dependency.optional
                )
                if all(capability in self.capabilities for capability in required):
                    self.add_domain(domain)
                    progress = True
                else:
                    next_pending.append(domain)

            if progress:
                pending = next_pending
                continue

            missing_by_domain = {
                domain.name: tuple(
                    dependency.capability
                    for dependency in getattr(domain, "dependencies", ())
                    if not dependency.optional and dependency.capability not in self.capabilities
                )
                for domain in next_pending
            }
            detail = "; ".join(
                f"{name}: {', '.join(missing) if missing else 'unresolved dependency'}"
                for name, missing in sorted(missing_by_domain.items())
            )
            raise DomainResolutionError(f"could not resolve domain dependencies: {detail}")

    def register_semantic_type(self, key: str, semantic_type: type[Any]) -> None:
        if key in self.semantic_types:
            raise ValueError(f"semantic type already registered: {key}")
        self.semantic_types[key] = semantic_type

    def register_compiler(self, key: str, compiler: Compiler) -> None:
        if key in self.compilers:
            raise ValueError(f"compiler already registered: {key}")
        self.compilers[key] = compiler

    def compiler_for(self, key: str) -> Compiler:
        try:
            return self.compilers[key]
        except KeyError as exc:
            raise KeyError(f"unknown compiler capability: {key}") from exc

    def provide(self, key: str, capability: Capability) -> None:
        """Publish reusable scientific/computation functionality.

        Examples: probability.expectation, linear_algebra.eigensystem,
        complex.inner_product, ode.solve, units.convert.
        """
        if key in self.capabilities:
            raise ValueError(f"capability already registered: {key}")
        self.capabilities[key] = capability

    def has_capability(self, key: str) -> bool:
        return key in self.capabilities

    def require(self, key: str) -> Capability:
        """Resolve a capability required by another domain."""
        try:
            return self.capabilities[key]
        except KeyError as exc:
            raise KeyError(f"required capability is not registered: {key}") from exc

    def resolve_dependencies(self, dependencies: Iterable[DomainDependency]) -> dict[str, Capability]:
        resolved: dict[str, Capability] = {}
        for dependency in dependencies:
            if dependency.capability in self.capabilities:
                resolved[dependency.capability] = self.capabilities[dependency.capability]
            elif not dependency.optional:
                raise KeyError(
                    f"required capability is not registered: {dependency.capability}"
                )
        return resolved
