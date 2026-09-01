# Domain Catalog and Automatic Dependency Loading

Spectra's `DomainRegistry` is the runtime authority for scientific capabilities. `DomainCatalog` is the discovery/planning layer above it.

The catalog exists so product/UI/AI code does not need to know registration order or manually assemble transitive provider sets.

## Runtime model

A domain declares runtime dependencies through stable capability names.

Example:

```text
high-level physics domain
    -> mathematical capability
    -> numerical capability
    -> visualization capability
```

A caller can request only the high-level domain:

```python
registry = DomainRegistry()
builtin_domain_catalog().load(registry, ["physics.quantum"])
```

The catalog computes the missing provider closure, then `DomainRegistry` performs dependency-resolved atomic registration.

## Built-in discovery model

Built-in domain factories are no longer maintained as a giant manual capability manifest.

Discovery scans the `spectra.domains` package for classes that satisfy the built-in domain convention:

- class is defined by the module being inspected;
- class name ends in `Domain`;
- class can be constructed with no arguments;
- constructed object exposes the normal domain contract (`name`, `version`, `dependencies`, `register`).

Infrastructure modules such as registry/catalog/discovery helpers are excluded.

Discovered domains are sorted deterministically by domain name and duplicate names are rejected.

Conceptually:

```text
spectra.domains package
       ↓ deterministic discovery
Domain factory set
       ↓ probe registration
actual registry.provide(...) calls
       ↓
capability -> provider ownership index
```

This removes duplicated capability declarations from the central catalog.

## Provider probing

Capability ownership comes from real domain registration behavior rather than a second hand-written list.

`DomainCatalog.from_factories(...)` uses a probe registry and dependency-resolved registration to learn which capabilities each domain actually provides.

This is important because a domain may register many versioned capabilities and semantic contracts. The catalog should not require every one of those strings to be duplicated elsewhere.

The runtime `DomainRegistry` remains authoritative; probing only builds discovery metadata.

## Capability-driven loading

In addition to loading by domain name, the catalog can load by requested capability.

Conceptually:

```text
requested capability
       ↓
provider_for(capability)
       ↓
provider dependency closure
       ↓
atomic DomainRegistry registration
```

This is especially useful for optional numerical providers. A future native/GPU solver package can expose a discoverable capability; product code asks for that capability, then runtime solver selection chooses among the implementations the provider registered.

Capability discovery and numerical implementation selection are intentionally different layers.

## Architectural responsibilities

### `DomainCatalog`

- knows discoverable domain factories;
- indexes capability -> provider domain ownership;
- computes required-domain closure;
- supports domain-driven and capability-driven loading;
- plans missing providers without mutating scientific runtime state;
- does not bypass dependency capability versions;
- does not own selected numerical solver implementations;
- does not own visualization/runtime objects.

### `DomainRegistry`

- owns registered domain instances;
- owns semantic types;
- owns actual capability objects and versions;
- records capability provider ownership;
- validates dependency capability versions;
- performs atomic batch registration/rollback;
- owns visualization dispatch;
- owns the numerical-solver runtime registry.

This separation allows discovery to evolve independently from runtime scientific semantics.

## Adding a built-in domain

For a normal bundled domain:

1. create a zero-argument `...Domain` class under `spectra.domains`;
2. give it a unique stable `name` and version;
3. declare dependencies using `DomainDependency` capability names;
4. register semantic types/capabilities/visualizers normally;
5. publish any semantic type that another domain uses as a dependency through `registry.provide(...)`, not only `register_semantic_type(...)`;
6. add regression coverage for its capability/dependency behavior.

Normally there is no central factory tuple or capability manifest to edit.

## Important semantic-type rule

`register_semantic_type(...)` and `provide(...)` are different operations.

A semantic type may be available for introspection/visualization registration without being a dependency capability.

If another domain declares:

```text
DomainDependency("some.semantic_type")
```

then the provider must also call:

```python
registry.provide("some.semantic_type", SemanticType)
```

Missing this distinction previously caused catalog probe cascades; regression tests should preserve the rule.

## One provider per capability

The catalog currently indexes one domain provider for a capability key. Competing numerical implementations should usually not create competing capability providers for the same key.

Instead:

```text
provider capability
       ↓ load provider domain
NumericalSolverRegistry
       ↓ multiple implementations of one stable solver role
```

For example, RK4, Heun, native CPU, and GPU ODE implementations can coexist under the `ode.first_order` runtime role without making DomainCatalog choose the numerical implementation.

If true multi-provider capability semantics become necessary outside numerical execution, that should be introduced deliberately with explicit priority/version rules rather than by accidental duplicate registration.

## Transactionality

Catalog planning must not leave the runtime registry partially mutated when dependency resolution fails.

`DomainRegistry.add_domains(...)` is the atomic authority. Domain registration failures roll back semantic types, capabilities, visualization registrations, capability ownership, and numerical-solver registry mutations to the pre-batch state.

Provider probing should follow the same dependency-resolved behavior so discovery metadata reflects realistic registration.

## Scalability target

The catalog architecture is intended to make the hundredth domain no harder to discover than the tenth.

Adding a domain should normally require changes only in:

```text
new domain module
its tests
domain-specific docs/examples when useful
```

It should not require editing a giant central subject switch or duplicating hundreds of capability strings.

## Future plugin discovery

The current built-in scanner handles bundled modules. Future external/plugin discovery may use mechanisms such as package entry points or application-provided provider lists.

Whatever discovery mechanism is added should still produce ordinary domain factories/descriptors and feed the same `DomainCatalog`/`DomainRegistry` contracts.

Do not make plugin/package discovery another scientific runtime system.
