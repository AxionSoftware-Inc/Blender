# Domain Catalog and Automatic Dependency Loading

Spectra's `DomainRegistry` is the runtime authority for scientific capabilities. The `DomainCatalog` is a discovery layer above it.

The catalog exists so product/UI/AI code does not need to manually know domain registration order.

## Runtime model

A domain declares runtime dependencies through `DomainDependency` capability names. Example:

```text
physics.quantum
  -> linear_algebra.complex_vector
  -> linear_algebra.complex_matrix >= 2
  -> probability.discrete_distribution
```

The built-in catalog maps those capability names to provider factories. Therefore a caller can request only:

```python
registry = DomainRegistry()
builtin_domain_catalog().load(registry, ["physics.quantum"])
```

and the catalog plans the missing provider closure before delegating registration to `DomainRegistry`.

Current examples:

```text
physics.quantum
  -> linear_algebra
  -> probability

probability.continuous
  -> mathematics
  -> calculus

physics.waves
  -> mathematics

electromagnetism
  -> mathematics

mechanics / physics.particles
  -> differential_equations
```

## Architectural responsibilities

`DomainCatalog`:

- knows discoverable domain factories;
- maps capability names to provider domains;
- computes required-domain closure;
- does not own scientific runtime state;
- does not bypass capability versions;
- does not register partial dependency graphs itself.

`DomainRegistry`:

- owns registered semantic types;
- owns actual capability objects and versions;
- validates dependency contract versions;
- performs atomic batch registration/rollback;
- owns visualization dispatch.

This separation is deliberate. Catalog metadata may later come from package entry points, downloaded plugins, organization-specific modules, or an application bundle without changing the runtime registry contract.

## Adding a built-in domain

For a new bundled domain:

1. implement the normal `DomainModule` contract;
2. depend on stable capabilities with `DomainDependency`;
3. register scientific semantics/capabilities/visualizers normally;
4. add one `DomainDescriptor` to `builtin_domain_catalog()` listing the capabilities the domain provides;
5. add a dependency-loading test.

Do not put subject-specific knowledge into `DomainCatalog` or `DomainRegistry`.

## Current limitation

The catalog currently allows one built-in provider per capability name. Multiple competing providers, provider priority, remote plugin discovery, and semantic-version ranges are future concerns. They should be added only when real use cases require them.
