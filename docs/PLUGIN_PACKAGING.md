# Spectra Science — Plugin Packaging and Discovery

This document defines the intended packaging/discovery model for third-party Spectra extensions. The external plugin runtime is not yet implemented; this document establishes the contract before implementation.

## Goal

A third-party scientific package should be installable independently from the Spectra repository and should register domains/providers through explicit, deterministic discovery.

Desired flow:

```text
pip / application package install
    -> explicit Spectra plugin entry point
    -> inspect plugin metadata
    -> discover domain/provider factories
    -> DomainCatalog integration
    -> dependency planning
    -> transactional DomainRegistry registration
```

No plugin should need to patch Spectra Core or edit a central built-in manifest.

## Package boundary

A plugin is an installation/distribution unit. A domain is a scientific/runtime capability unit.

One plugin may provide multiple domains:

```text
spectra-optics package
    -> physics.optics.geometric
    -> physics.optics.wave
    -> physics.optics.views
```

Do not equate one pip package with one capability.

## Proposed Python entry point

Conceptual packaging:

```toml
[project.entry-points."spectra.plugins"]
optics = "spectra_optics.plugin:plugin_descriptor"
```

or, if domain-factory-only discovery proves sufficient:

```toml
[project.entry-points."spectra.domains"]
optics = "spectra_optics.plugin:domain_factories"
```

The exact implementation should be chosen after the current numerical milestone is green.

The important requirement is that discovery is explicit through package metadata, not arbitrary recursive importing of everything installed in Python.

## Plugin descriptor

A future plugin descriptor should expose metadata conceptually similar to:

```text
plugin_id
plugin_version
spectra_api_range
domain_factories
optional_backend_factories
optional_presentation_factories
vendor/name metadata
```

Potential conceptual form:

```python
PluginDescriptor(
    plugin_id="org.example.spectra_optics",
    version="1.2.0",
    spectra_api=">=0.1,<0.3",
    domains=(GeometricOpticsDomain, WaveOpticsDomain),
)
```

This is packaging metadata only; scientific capability versions remain registered by the domains themselves.

## Stable plugin ID

Plugin IDs should be globally collision-resistant and vendor/package oriented.

Examples:

```text
org.example.spectra_optics
com.company.materials
edu.university.plasma
```

Domain/capability names may use cleaner scientific namespaces independent from plugin ID.

## Compatibility

Plugin compatibility should distinguish:

- package/plugin version;
- Spectra public API compatibility;
- individual domain versions;
- capability versions;
- optional native ABI version when native providers are present.

Do not use one version number to mean all of these.

## Discovery must not register immediately

Discovery should inspect metadata/factories first.

Bad model:

```text
import plugin
    -> plugin immediately mutates global registry
```

Desired model:

```text
discover descriptor
    -> inspect
    -> decide whether enabled/compatible
    -> instantiate requested domains
    -> DomainRegistry transactional registration
```

This preserves rollback, deterministic startup, debugging, and application control.

## Enable/disable model

Applications should be able to:

- enable a plugin globally;
- disable a plugin;
- load only requested domains;
- inspect provided capabilities before activation;
- report incompatible plugins without breaking the entire engine startup.

Disabling a plugin should mean its provider factories are excluded from the active catalog/environment.

## Provider conflicts

Ordinary scientific capability names currently assume one catalog provider for a capability.

Runtime numerical solver roles intentionally allow multiple implementations.

Therefore plugin conflict policy should distinguish:

### Semantic capability conflict

Two domains claim the same stable capability key.

Default behavior should be a clear conflict/error unless an explicit future provider-priority/override mechanism is designed.

Do not silently choose based on import order.

### Numerical implementation coexistence

Multiple plugins may register different implementation IDs under the same stable solver role.

This is expected:

```text
ode.first_order
    rk4.reference
    native_cpu.rk4
    cuda.rk45
```

Selection occurs through solver policy/requirements.

## Native plugin components

A plugin may include compiled/native libraries.

Rules:

- Python import of the plugin descriptor should avoid initializing GPU/device state;
- native library availability should be probed lazily;
- unsupported platform/device should not corrupt the registry;
- `supports_problem` and execution metadata should describe actual capability;
- native provider validation must follow `docs/NUMERICAL_BACKEND_VALIDATION.md`.

A GPU provider must not pretend to be available when its required runtime/device is missing.

## Optional dependencies

Plugins may expose optional integration domains rather than making every dependency mandatory.

Example:

```text
spectra-optics base
    -> geometric optics

optional:
    -> GPU ray batch provider
    -> premium Blender presentation extension
```

The base scientific module should remain usable without Blender/GPU extras when scientifically possible.

## Recommended package layout

```text
spectra-optics/
    pyproject.toml
    README.md
    src/
        spectra_optics/
            __init__.py
            plugin.py
            domains/
                geometric.py
                wave.py
                views.py
            providers/
                native_cpu.py
                gpu.py
            presentation/
                presets.py
    tests/
        test_domain_contracts.py
        test_catalog_loading.py
        test_numerical_parity.py
```

## Public API usage

Third-party plugins should import documented/public Spectra APIs rather than private repository modules.

A later Spectra release should provide a clearly curated SDK import surface, conceptually:

```python
from spectra.sdk import (
    DomainDependency,
    DomainRegistry,
    Scene,
    ...
)
```

Until that facade is implemented, `docs/MODULE_SDK.md` defines the intended stable concepts.

## Plugin data/resources

Plugin-owned static assets may include:

- scientific reference datasets;
- default parameter tables;
- templates;
- presentation resources.

Generated caches, simulation results, downloaded datasets, and renderer outputs should not be bundled into source packages by default.

Large external datasets should use explicit data management rather than hidden import-time downloads.

## Security/trust boundary

A Python plugin is executable code and therefore should be treated as trusted code unless a sandboxed plugin architecture is introduced later.

Do not describe arbitrary installed Python plugins as sandboxed.

A future product UI should distinguish:

- built-in/trusted plugins;
- signed/verified organization plugins if supported;
- user-installed third-party plugins.

Plugin metadata validation does not make arbitrary Python execution safe.

## Determinism

Given the same installed/enabled plugin set, discovery order should be deterministic.

Suggested ordering inputs:

```text
plugin_id
then domain name
```

Capability ownership/conflicts should produce the same result regardless of filesystem/import ordering.

## Reproducibility integration

Scientific environment snapshots should eventually include plugin/package provenance in addition to domain/capability/solver inventory.

Potential records:

```text
plugin_id
plugin_version
package distribution name/version
optional source revision/build id
native backend build/ABI id
```

This should extend, not replace, existing domain/capability/solver provenance.

## Application/plugin lifecycle

Conceptual lifecycle:

```text
DISCOVER
    metadata only

INSPECT
    compatibility / capabilities / platform

ENABLE
    include factories in active catalog

LOAD
    dependency-resolved domain registration

EXECUTE
    scientific/numerical work

UNLOAD PROJECT / DESTROY SESSION
    clean runtime resources
```

Python modules themselves may remain imported; runtime domain/backend resources must still have clear ownership and cleanup.

## Backend plugins

Renderer/backend plugins should implement generic Scene consumption and remain separate from scientific domains.

A hypothetical WebGPU backend plugin should not publish `physics.webgpu.*` scientific semantics.

Similarly, a Blender presentation extension should not be a required dependency of an optics solver.

## Presentation plugins

Third-party presentation packages may provide:

- presentation presets;
- themes;
- color maps;
- renderer-specific premium mappings.

They must not alter numerical data or scientific semantics.

Renderer-specific presentation should declare which backend it targets while generic presentation policies remain renderer-neutral.

## Plugin acceptance tests

A serious plugin should test:

1. descriptor discovery without side effects;
2. compatibility metadata;
3. deterministic domain factory list;
4. dependency-resolved registration;
5. rollback on registration failure;
6. capability ownership;
7. public semantic validation;
8. visualization compilation where provided;
9. native solver parity/provenance when applicable;
10. no renderer import leakage into plain scientific modules.

## Future implementation phases

### Phase 1

Define plugin descriptor dataclasses and explicit in-process discovery API.

### Phase 2

Integrate Python package entry points.

### Phase 3

Add application enable/disable/configuration state.

### Phase 4

Extend reproducibility snapshots with plugin distribution provenance.

### Phase 5

Add curated public `spectra.sdk` facade and compatibility policy.

### Phase 6

Consider signing/trust UX only when a real distribution ecosystem exists.

## Success criterion

Installing a new scientific package should be able to extend Spectra with new semantics, views, and solver providers without modifying Spectra Core, Blender backend code, or a central built-in domain list.
