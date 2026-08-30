from spectra.domains import DomainRegistry, builtin_domain_catalog


def test_geodesics_catalog_loads_geometry_tensor_linear_algebra_and_ode() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(registry, ["differential_geometry.geodesics"])

    assert "tensor_algebra" in loaded
    assert "linear_algebra" in loaded
    assert "differential_geometry" in loaded
    assert "differential_equations" in loaded
    assert "differential_geometry.geodesics" in loaded
    assert registry.has_capability("geometry.solve_geodesic")


def test_general_relativity_catalog_loads_curvature_providers() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(registry, ["physics.relativity.general"])

    assert "tensor_algebra" in loaded
    assert "linear_algebra" in loaded
    assert "differential_geometry" in loaded
    assert "physics.relativity.general" in loaded
    assert registry.has_capability("geometry.ricci_tensor", min_version=2)
    assert registry.has_capability("physics.relativity.einstein_tensor")


def test_2d_diffusion_catalog_resolves_pde_stack() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(registry, ["physics.diffusion.2d"])

    assert "differential_equations" in loaded
    assert "partial_differential_equations" in loaded
    assert "partial_differential_equations.2d" in loaded
    assert "physics.diffusion.2d" in loaded
    assert registry.has_capability("pde.laplacian_2d")
    assert registry.has_capability("physics.diffusion.solve2d")
