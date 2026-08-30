from spectra.domains import DomainRegistry, builtin_domain_catalog


def test_incompressible_flow_catalog_loads_pde_operator_stack() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(registry, ["physics.incompressible_flow.2d"])
    assert "partial_differential_equations" in loaded
    assert "partial_differential_equations.2d" in loaded
    assert "partial_differential_equations.operators2d" in loaded
    assert "partial_differential_equations.elliptic2d" in loaded
    assert "physics.incompressible_flow.2d" in loaded
    assert registry.has_capability("pde.solve_poisson_2d")
    assert registry.has_capability("physics.incompressible_flow.simulate2d")


def test_fluid_transport_catalog_loads_fields_dynamics_and_transport() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(registry, ["physics.fluid_transport.2d"])
    assert "mathematics" in loaded
    assert "calculus.vector2d" in loaded
    assert "field_dynamics.2d" in loaded
    assert "partial_differential_equations.transport2d" in loaded
    assert "physics.fluid_kinematics.2d" in loaded
    assert "physics.fluid_transport.2d" in loaded
    assert registry.has_capability("physics.fluid.solve_passive_scalar2d")


def test_elasticity_catalog_reuses_tensor_jacobian_and_linear_algebra() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(registry, ["physics.elasticity"])
    assert "mathematics" in loaded
    assert "linear_algebra" in loaded
    assert "tensor_algebra" in loaded
    assert "calculus.jacobian3d" in loaded
    assert "physics.elasticity" in loaded
    assert registry.has_capability("physics.elasticity.von_mises_stress")
