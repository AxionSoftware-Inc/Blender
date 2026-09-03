from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from spectra.domains.builtin_catalog import BUILTIN_DOMAIN_FACTORIES, BUILTIN_DOMAIN_TAGS
from spectra.domains.catalog import DomainCatalog, DomainFactory


@dataclass(frozen=True, slots=True)
class PluginRequirement:
    plugin_id: str
    min_version: str | None = None
    optional: bool = False


@dataclass(frozen=True, slots=True)
class PluginDescriptor:
    plugin_id: str
    version: str
    display_name: str
    domain_factories: tuple[DomainFactory, ...] = ()
    requires: tuple[PluginRequirement, ...] = ()
    spectra_min_version: str | None = None
    spectra_max_version_exclusive: str | None = None
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.plugin_id or not self.version or not self.display_name:
            raise ValueError("plugin id, version, and display_name are required")


class PluginState(str, Enum):
    DISCOVERED = "discovered"
    DISABLED = "disabled"
    READY = "ready"
    ACTIVE = "active"
    INCOMPATIBLE = "incompatible"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class PluginStatus:
    descriptor: PluginDescriptor
    state: PluginState
    diagnostics: tuple[str, ...] = ()


class PluginRegistry:
    def __init__(self) -> None:
        self._descriptors: dict[str, PluginDescriptor] = {}
        self._enabled: set[str] = set()

    def add_descriptor(self, descriptor: PluginDescriptor) -> None:
        if descriptor.plugin_id in self._descriptors:
            raise ValueError(f"plugin already registered: {descriptor.plugin_id}")
        self._descriptors[descriptor.plugin_id] = descriptor

    def remove_descriptor(self, plugin_id: str) -> None:
        self._enabled.discard(plugin_id)
        del self._descriptors[plugin_id]

    def enable(self, plugin_id: str) -> None:
        self.descriptor(plugin_id)
        self._enabled.add(plugin_id)

    def disable(self, plugin_id: str) -> None:
        self.descriptor(plugin_id)
        self._enabled.discard(plugin_id)

    def descriptor(self, plugin_id: str) -> PluginDescriptor:
        try:
            return self._descriptors[plugin_id]
        except KeyError as exc:
            raise KeyError(f"unknown plugin: {plugin_id}") from exc

    def enabled_descriptors(self) -> tuple[PluginDescriptor, ...]:
        return tuple(self._descriptors[key] for key in sorted(self._enabled))

    def list_plugins(self) -> tuple[PluginStatus, ...]:
        result = []
        for plugin_id in sorted(self._descriptors):
            descriptor = self._descriptors[plugin_id]
            result.append(PluginStatus(descriptor, PluginState.ACTIVE if plugin_id in self._enabled else PluginState.DISABLED))
        return tuple(result)

    def plan_activation(self) -> tuple[PluginDescriptor, ...]:
        enabled = self.enabled_descriptors()
        ids = {d.plugin_id for d in enabled}
        for descriptor in enabled:
            for requirement in descriptor.requires:
                if requirement.plugin_id not in ids and not requirement.optional:
                    raise ValueError(f"plugin '{descriptor.plugin_id}' requires '{requirement.plugin_id}'")
        return enabled


def active_domain_catalog(plugins: PluginRegistry) -> DomainCatalog:
    factories = list(BUILTIN_DOMAIN_FACTORIES)
    for descriptor in plugins.plan_activation():
        factories.extend(descriptor.domain_factories)
    return DomainCatalog.from_factories(factories, tags=BUILTIN_DOMAIN_TAGS)


__all__ = ["PluginRequirement", "PluginDescriptor", "PluginState", "PluginStatus", "PluginRegistry", "active_domain_catalog"]
