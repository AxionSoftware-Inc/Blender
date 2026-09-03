# Spectra Science — Plugin Runtime API Draft

Status: **design draft, not implemented runtime**.

This document defines a conservative first in-process plugin API using the current `DomainCatalog` / `DomainRegistry` implementation rather than inventing a second scientific registration model.

## Source-of-truth result

Current runtime already provides:

```text
DomainCatalog.from_factories(...)
DomainCatalog.register(...)
DomainCatalog.register_many(...)
DomainCatalog.provider_for(...)
DomainCatalog.plan(...)
DomainCatalog.plan_capabilities(...)
DomainCatalog.load(...)
DomainCatalog.load_capabilities(...)

DomainRegistry.add_domains(...)
transactional rollback
```

Built-in catalog creation already uses:

```text
discover_domain_factories()
  -> BUILTIN_DOMAIN_FACTORIES
  -> DomainCatalog.from_factories(...)
```

`DomainCatalog.from_factories()` probe-loads all supplied domains in a private `DomainRegistry`, derives actual capability ownership from `registry.provide()`, and rejects duplicate domain/provider conflicts.

Therefore the safest plugin integration is to build a **fresh active catalog from the union of enabled factories**, not incrementally mutate the built-in catalog in place.

## First plugin runtime scope

The first implementation should support:

- explicit plugin descriptors supplied by application code;
- deterministic enable/disable state;
- plugin dependency/compatibility validation;
- contribution of ordinary `DomainFactory` values;
- rebuilding an active `DomainCatalog` from built-ins + enabled plugin factories;
- capability-driven domain loading through existing `load_capabilities()`;
- transactional scientific registration through existing `DomainRegistry`;
- structured plugin diagnostics.

Explicitly defer:

- arbitrary environment scanning;
- Python entry-point discovery;
- automatic installation;
- automatic native library loading;
- process sandboxing;
- hot-unloading domains from an already-mutated live `DomainRegistry`.

## PluginDescriptor

```python
from dataclasses import dataclass
from collections.abc import Callable

DomainFactory = Callable[[], DomainModule]

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

- `plugin_id` stable/unique;
- display name not identity;
- descriptor construction side-effect free;
- domain factories are ordinary zero-argument DomainModule factories;
- no Core-global mutation during import/descriptor construction;
- executable native hooks outside first implementation.

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

Clarification for first implementation:

`ACTIVE` means the plugin contributes to the currently constructed active catalog/environment definition. It does not imply domains have all been eagerly loaded into `DomainRegistry`; capability/domain loading may remain lazy through the catalog.

## PluginRegistry

Conceptual product/package registry:

```python
class PluginRegistry:
    def add_descriptor(self, descriptor: PluginDescriptor) -> None: ...
    def remove_descriptor(self, plugin_id: str) -> None: ...
    def enable(self, plugin_id: str) -> None: ...
    def disable(self, plugin_id: str) -> None: ...
    def descriptor(self, plugin_id: str) -> PluginDescriptor: ...
    def list_plugins(self) -> tuple[PluginStatus, ...]: ...
    def enabled_descriptors(self) -> tuple[PluginDescriptor, ...]: ...
    def plan_activation(self) -> PluginLoadPlan: ...
```

`PluginRegistry` owns installed/discovered/enabled package state.

`DomainRegistry` remains the only scientific runtime authority.

## Active catalog composition

Recommended first implementation should use the current built-in factory source directly.

Conceptually:

```python
from spectra.domains.builtin_catalog import (
    BUILTIN_DOMAIN_FACTORIES,
    BUILTIN_DOMAIN_TAGS,
)
from spectra.domains.catalog import DomainCatalog


def active_domain_catalog(
    plugins: PluginRegistry,
) -> DomainCatalog:
    enabled = plugins.enabled_descriptors()
    plugin_factories = tuple(
        factory
        for descriptor in enabled
        for factory in descriptor.domain_factories
    )

    factories = (
        *BUILTIN_DOMAIN_FACTORIES,
        *plugin_factories,
    )

    return DomainCatalog.from_factories(
        factories,
        tags=BUILTIN_DOMAIN_TAGS,
    )
```

The exact helper location/name may differ.

### Why rebuild rather than mutate

Current `DomainCatalog.register_many()` performs sequential registration; if descriptor N conflicts after earlier descriptors were registered, the catalog object itself does not provide a transaction rollback layer.

`DomainCatalog.from_factories()` instead builds a new catalog from scratch and probe-validates the entire factory set before that new catalog is used.

Therefore plugin activation should prefer:

```text
old active catalog remains untouched
        ↓
build candidate factory union
        ↓
probe new DomainCatalog
        ↓
if success: replace active catalog reference
if failure: keep old active catalog
```

This gives product-level atomic activation without changing `DomainCatalog` internals in the first plugin phase.

## Plugin dependencies before domain probe

Plugin-level dependencies are package/environment concerns and should be resolved before building the candidate domain catalog.

Flow:

```text
PluginRegistry descriptors
   ↓
validate plugin IDs/versions/dependency graph
   ↓
determine enabled descriptor order/set
   ↓
unify domain factories
   ↓
DomainCatalog.from_factories(...)
```

Domain-level capability dependencies are then handled by the existing scientific catalog/registry.

Do not translate plugin dependency ordering into manual domain initialization ordering.

## Capability-driven use

Once the active catalog exists, plugin science uses the exact existing runtime:

```python
catalog.load_capabilities(
    registry,
    ["physics.optics.trace_ray"],
)
```

The catalog resolves:

```text
requested capability
 -> provider domain
 -> required capability providers
 -> dependency closure
 -> DomainRegistry.add_domains(...)
```

No plugin-specific scientific loader is needed.

## Built-in discovery vs external plugin discovery

Current `discover_domain_factories()` scans the built-in `spectra.domains` package using the strict built-in convention.

External plugin domains should **not** be made visible by widening that recursive built-in scanner over arbitrary installed packages.

External packages contribute explicit factory tuples through `PluginDescriptor`.

This keeps discovery:

- deterministic;
- user/application controlled;
- inspectable;
- safe to disable.

## Conflict behavior from current DomainCatalog

Current `DomainCatalog` already detects:

### Duplicate domain names

`from_factories()` instantiates supplied factories and rejects duplicate `domain.name` values.

### Ambiguous capability providers

`register()` rejects a capability supplied by more than one descriptor/provider.

Therefore plugin diagnostics should map these existing failures into structured product errors such as:

```text
duplicate_domain_name
capability_provider_conflict
```

Do not catch and hide the underlying provider names/capability key.

## Domain transaction behavior

Once catalog planning succeeds, `DomainRegistry.add_domains(...)` is already atomic.

A plugin domain registration failure therefore rolls scientific runtime back to the prior registry snapshot.

Plugin layer should preserve that guarantee and add context:

```text
plugin ID
domain name
underlying registration diagnostic
```

## Enable/disable semantics

First implementation should avoid risky hot-unload semantics.

Recommended model:

```text
PluginRegistry state changes
   ↓
new active catalog/environment for a fresh ProjectRuntime/engine session
```

If a plugin has already loaded domains/capabilities into a live `DomainRegistry`, disabling the plugin should not attempt to surgically remove those capabilities from that registry unless a future explicit unload transaction is designed.

Instead:

- mark plugin disabled for subsequent environment construction;
- create/restart a fresh runtime environment when strict removal is required;
- surface this clearly in UI/CLI.

This is safer for domains that may have interdependent loaded capabilities.

## Plugin compatibility diagnostics

Structured categories:

```text
plugin_version_incompatible
missing_required_plugin
plugin_dependency_cycle
duplicate_plugin_id
duplicate_domain_name
capability_provider_conflict
domain_probe_failed
domain_registration_failed
```

The diagnostic should include plugin/domain/capability identity where relevant.

## Python entry-point adapter later

Future packaging:

```toml
[project.entry-points."spectra.plugins"]
optics = "spectra_optics.plugin:descriptor"
```

Adapter:

```python
def discover_python_entrypoint_plugins() -> tuple[PluginDescriptor, ...]:
    ...
```

This adapter only discovers descriptors.

Normal validation/enable/catalog composition remains in `PluginRegistry` + active catalog builder.

## Trust boundary

Python plugins are executable code.

Project files may declare required plugin IDs/versions but must never:

- import arbitrary code on parse;
- install missing packages automatically;
- enable a disabled plugin silently.

Application/user policy decides installation/trust/enable state.

## Native provider plugins

A plugin may contribute a normal domain that registers a numerical implementation through the existing:

```python
DomainRegistry.register_numerical_solver(...)
```

Example:

```text
spectra-native-cpu plugin
 -> NativeCpuOdeDomain factory
 -> active catalog
 -> capability requested
 -> domain registered
 -> ode.first_order / rk4.native_cpu available
```

No plugin-specific native solver registry/ABI.

## Project interaction

Project stores declarative plugin requirements only:

```python
@dataclass(frozen=True)
class ProjectPluginRequirement:
    plugin_id: str
    version_constraint: str | None = None
```

On open:

```text
project requirement
 -> compare PluginRegistry
 -> ready / missing / incompatible diagnostic
```

Project does not deserialize plugin objects.

## First acceptance proof

Use the geometric-optics sample extension.

Flow:

```text
built-in factory set
+ enabled optics PluginDescriptor factories
 -> build candidate DomainCatalog.from_factories(...)
 -> request optics capability with load_capabilities(...)
 -> dependencies load automatically
 -> construct ray problem/view
 -> fresh environment with plugin disabled
 -> optics provider absent
 -> built-in engine unaffected
```

## Tests after implementation gate

### Plugin state

- duplicate plugin IDs rejected;
- enable/disable deterministic;
- required plugin dependency validated;
- optional dependency does not block;
- plugin dependency cycle diagnosed.

### Catalog integration

- built-ins + plugin factory union probes successfully;
- duplicate domain name rejected before replacing active catalog;
- provider conflict rejected before replacing active catalog;
- failed candidate catalog leaves previous active catalog usable;
- plugin capability loads via existing `load_capabilities()`;
- plugin domain registration failure rolls back `DomainRegistry`.

### Disable behavior

- fresh environment with plugin disabled cannot resolve plugin capability;
- disabling does not corrupt already-loaded registry;
- strict removal requires fresh runtime/session in first implementation.

### Security/project

- project requirement inspection never auto-installs/enables code.

## Public API direction

Later curated facade may expose:

```python
from spectra.sdk import (
    PluginDescriptor,
    PluginRequirement,
    PluginRegistry,
    PluginState,
)
```

Do not expose mutable DomainCatalog internal dictionaries as plugin API.

## Success criterion

A third-party package contributes ordinary DomainModule factories. The active environment is constructed from built-ins plus explicitly enabled plugin factories, probe-validated by the existing `DomainCatalog`, and executed through the same transactional `DomainRegistry` used by built-in science.