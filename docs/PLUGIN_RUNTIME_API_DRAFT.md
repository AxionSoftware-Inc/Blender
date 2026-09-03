# Spectra Science — Plugin Runtime API Draft

Status: **design draft, not implemented runtime**.

This document turns `PLUGIN_PACKAGING.md`, `MODULE_SDK.md`, and `PUBLIC_SDK_FACADE.md` into a concrete first in-process plugin API that can be implemented after the current runtime batch is validated.

## Scope of the first plugin runtime

The first implementation should be deliberately conservative:

- explicit plugin descriptors supplied by application code;
- no arbitrary recursive environment scanning;
- no automatic native-library loading;
- deterministic compatibility checks;
- plugin enable/disable;
- domain factory contribution;
- optional solver-provider contribution through normal domain registration;
- transactional integration with `DomainCatalog` / `DomainRegistry`.

Python package entry-point discovery should be a later adapter over this in-process model.

## Public concepts

```text
PluginId
PluginVersion
PluginRequirement
PluginDescriptor
PluginStatus
PluginRegistry
PluginLoadPlan
PluginDiagnostic
```

## PluginDescriptor

Suggested immutable shape:

```python
from dataclasses import dataclass
from collections.abc import Callable, Sequence

DomainFactory = Callable[[], object]

@dataclass(frozen=True)
class PluginRequirement:
    plugin_id: str
    min_version: str | None = None
    optional: bool = False

@dataclass(frozen=True)
class PluginDescriptor:
    plugin_id: str
    version: str
    display_name: str
    domain_factories: tuple[DomainFactory, ...] = ()
    requires: tuple[PluginRequirement, ...] = ()
    spectra_min_version: str | None = None
    spectra_max_version_exclusive: str | None = None
    metadata: tuple[tuple[str, str], ...] = ()
```

Rules:

- `plugin_id` is stable and globally unique within one environment;
- display name is not an identity key;
- descriptor construction must be side-effect free;
- `domain_factories` return normal zero-argument domain modules;
- plugins do not receive direct mutation access to Core globals;
- native executable hooks are outside first implementation scope.

## Plugin state

```python
class PluginState(str, Enum):
    DISCOVERED = "discovered"
    DISABLED = "disabled"
    READY = "ready"
    ACTIVE = "active"
    INCOMPATIBLE = "incompatible"
    FAILED = "failed"
```

State should be inspectable by UI/CLI without loading scientific domains unnecessarily.

## PluginRegistry

Conceptual API:

```python
class PluginRegistry:
    def add_descriptor(self, descriptor: PluginDescriptor) -> None: ...
    def remove_descriptor(self, plugin_id: str) -> None: ...
    def enable(self, plugin_id: str) -> None: ...
    def disable(self, plugin_id: str) -> None: ...
    def descriptor(self, plugin_id: str) -> PluginDescriptor: ...
    def list_plugins(self) -> tuple[PluginStatus, ...]: ...
    def plan_activation(self) -> PluginLoadPlan: ...
```

The registry is product/package state. Scientific runtime capabilities remain owned by `DomainRegistry`.

## Activation model

```text
PluginDescriptor(s)
       ↓
compatibility + dependency plan
       ↓
domain factory set
       ↓
DomainCatalog.from_factories(...)
       ↓
capability provider closure
       ↓
DomainRegistry.add_domains(...)
```

Do not invent a second scientific registration mechanism for plugins.

## Built-in + plugin catalog composition

Suggested helper:

```python
def catalog_with_plugins(
    builtin: DomainCatalog,
    plugin_registry: PluginRegistry,
) -> DomainCatalog:
    ...
```

The exact implementation may reconstruct a catalog from the union of factory classes rather than mutating an existing immutable catalog.

Requirements:

- deterministic ordering by plugin/domain identity;
- duplicate domain names fail clearly;
- duplicate capability provider ambiguity follows existing catalog rules;
- disabled plugins contribute nothing;
- incompatible plugins contribute nothing and expose diagnostics;
- activation planning must not leave partially registered domains.

## Compatibility diagnostics

Plugin activation should produce structured reasons such as:

```text
plugin_version_incompatible
missing_required_plugin
plugin_dependency_cycle
duplicate_plugin_id
duplicate_domain_name
capability_provider_conflict
domain_registration_failed
```

Do not collapse everything into `ImportError` strings.

## Entry-point adapter later

Future Python packaging adapter:

```toml
[project.entry-points."spectra.plugins"]
optics = "spectra_optics.plugin:descriptor"
```

Conceptual adapter:

```python
def discover_python_entrypoint_plugins() -> tuple[PluginDescriptor, ...]:
    ...
```

This function should only discover descriptors. Normal validation and activation still go through `PluginRegistry`.

## Trust boundary

A Python plugin is executable code and should be treated as trusted only if the user/application chooses to install/enable it.

Project files must never silently enable missing plugins or install code.

A project may declare:

```text
required plugin IDs + version constraints
```

but application policy decides how to satisfy them.

## Native providers

Native CPU/GPU providers may eventually ship inside plugins, but first plugin runtime must not define a separate ABI.

A plugin may expose a normal domain factory whose registration adds a numerical solver implementation through the existing numerical registry.

Conceptual:

```text
spectra-native-cpu plugin
    -> NativeCpuOdeDomain
    -> register role ode.first_order / rk4.native_cpu
```

Native library loading, signing, platform compatibility, and crash isolation remain governed by `TRUST_AND_SECURITY_MODEL.md` and `NATIVE_NUMERICAL_BACKENDS.md`.

## Project interaction

A project may record environment requirements:

```python
@dataclass(frozen=True)
class ProjectPluginRequirement:
    plugin_id: str
    version_constraint: str | None = None
```

On open:

```text
read project requirements
   ↓
compare active plugin environment
   ↓
ready / degraded-view-only / missing-plugin diagnostic
```

Never deserialize arbitrary plugin Python objects from a project document.

## First acceptance test package

Use the documented geometric-optics sample as the first external-plugin proof.

Expected flow:

```text
create PluginDescriptor
→ enable descriptor
→ compose catalog
→ request optics capability
→ dependencies load automatically
→ construct ray problem
→ compile explicit ray view
→ disable plugin in fresh environment
→ built-in engine still works
```

## Public API draft

Potential future imports:

```python
from spectra.sdk import (
    PluginDescriptor,
    PluginRequirement,
    PluginRegistry,
    PluginState,
)
```

Do not expose catalog internals or plugin-manager mutable dictionaries as public API.

## Tests after validation gate

- duplicate plugin IDs rejected;
- enable/disable deterministic;
- missing required plugin diagnosed;
- optional plugin requirement does not block activation;
- dependency cycle diagnosed;
- plugin factory domain auto-discovered into provider graph;
- failed plugin domain registration rolls back;
- disabled plugin cannot satisfy capability lookup;
- plugin removal from a fresh environment restores base catalog behavior;
- project requirement inspection never auto-installs/enables code.

## Success criterion

A third-party scientific package should be able to contribute normal Spectra domains without editing the Spectra repository, while the central engine retains one domain/capability runtime model and one transaction/diagnostic model.