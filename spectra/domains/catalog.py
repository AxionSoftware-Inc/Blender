from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from spectra.domains.registry import DomainResolutionError, DomainRegistry

if TYPE_CHECKING:
    from spectra.domains.base import DomainModule


DomainFactory = Callable[[], "DomainModule"]


@dataclass(frozen=True, slots=True)
class DomainDescriptor:
    """Discoverable metadata for a pluggable scientific domain."""

    name: str
    factory: DomainFactory
    provides: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("domain descriptor name cannot be empty")
        if len(self.provides) != len(set(self.provides)):
            raise ValueError(f"domain descriptor '{self.name}' contains duplicate capabilities")
        if any(not capability for capability in self.provides):
            raise ValueError("domain descriptor capabilities cannot be empty")


@dataclass
class DomainCatalog:
    """Find and load domain providers without hard-coding dependency order."""

    descriptors: dict[str, DomainDescriptor] = field(default_factory=dict)
    providers: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_factories(
        cls,
        factories: Iterable[DomainFactory],
        *,
        tags: dict[str, tuple[str, ...]] | None = None,
    ) -> "DomainCatalog":
        """Build a catalog by probing actual domain registration contracts.

        A private registry loads every supplied domain transactionally and records
        which domain published each capability. This makes the runtime
        `provide()` calls the source of truth and removes the need to duplicate
        large hand-maintained capability manifests in a built-in catalog.
        """

        factory_list = tuple(factories)
        instances = tuple(factory() for factory in factory_list)
        names = tuple(domain.name for domain in instances)
        if len(names) != len(set(names)):
            raise ValueError("catalog factory list contains duplicate domain names")

        probe = DomainRegistry()
        probe.add_domains(instances)
        tag_map = tags or {}
        catalog = cls()
        for factory, domain in zip(factory_list, instances, strict=True):
            catalog.register(
                DomainDescriptor(
                    name=domain.name,
                    factory=factory,
                    provides=probe.provided_capabilities(domain.name),
                    tags=tuple(tag_map.get(domain.name, ())),
                )
            )
        return catalog

    def register(self, descriptor: DomainDescriptor) -> None:
        if descriptor.name in self.descriptors:
            raise ValueError(f"domain descriptor already registered: {descriptor.name}")

        instance = descriptor.factory()
        if instance.name != descriptor.name:
            raise ValueError(
                f"domain descriptor name '{descriptor.name}' does not match factory domain "
                f"name '{instance.name}'"
            )

        for capability in descriptor.provides:
            existing = self.providers.get(capability)
            if existing is not None:
                raise ValueError(
                    f"capability provider is ambiguous: {capability} provided by "
                    f"{existing} and {descriptor.name}"
                )

        self.descriptors[descriptor.name] = descriptor
        for capability in descriptor.provides:
            self.providers[capability] = descriptor.name

    def register_many(self, descriptors: Iterable[DomainDescriptor]) -> None:
        for descriptor in descriptors:
            self.register(descriptor)

    def provider_for(self, capability: str) -> DomainDescriptor | None:
        name = self.providers.get(capability)
        return self.descriptors.get(name) if name is not None else None

    def instantiate(self, name: str) -> "DomainModule":
        try:
            descriptor = self.descriptors[name]
        except KeyError as exc:
            raise KeyError(f"unknown domain: {name}") from exc
        return descriptor.factory()

    def plan(
        self,
        registry: DomainRegistry,
        requested_domains: Iterable[str],
    ) -> tuple["DomainModule", ...]:
        """Compute required domain closure without mutating the registry."""

        planned: dict[str, "DomainModule"] = {}
        visiting: list[str] = []

        def visit(name: str) -> None:
            if name in registry.domains or name in planned:
                return
            if name in visiting:
                cycle_start = visiting.index(name)
                cycle = " -> ".join((*visiting[cycle_start:], name))
                raise DomainResolutionError(f"domain catalog dependency cycle: {cycle}")

            domain = self.instantiate(name)
            visiting.append(name)
            try:
                for dependency in tuple(getattr(domain, "dependencies", ())):
                    if dependency.optional:
                        continue
                    if registry.has_capability(
                        dependency.capability,
                        min_version=dependency.min_version,
                    ):
                        continue
                    provider_name = self.providers.get(dependency.capability)
                    if provider_name is None:
                        raise DomainResolutionError(
                            "domain catalog has no provider for required capability: "
                            f"{dependency.capability} (required by {name})"
                        )
                    visit(provider_name)
            finally:
                visiting.pop()
            planned[name] = domain

        for requested in requested_domains:
            visit(requested)
        return tuple(planned.values())

    def load(
        self,
        registry: DomainRegistry,
        requested_domains: Iterable[str],
    ) -> tuple[str, ...]:
        """Resolve providers and atomically load all missing required domains."""

        plan = self.plan(registry, requested_domains)
        if not plan:
            return ()
        registry.add_domains(plan)
        return tuple(domain.name for domain in plan)
