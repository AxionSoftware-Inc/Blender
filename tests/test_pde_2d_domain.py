import pytest

from spectra.core.primitives import Surface
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import UniformGrid1D, UniformGrid2D
from spectra.domains.physics import DiffusionProblem2D


def test_laplacian_2d_matches_quadratic_interior() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["partial_differential_equations.2d"])
    grid = UniformGrid2D(
        UniformGrid1D(-1.0, 1.0, 5),
        UniformGrid1D(-1.0, 1.0, 5),
    )
    values = tuple(x * x + y * y for x, y in grid.coordinates)
    laplacian = registry.require("pde.laplacian_2d")
    result = laplacian(values, grid, boundary="fixed")

    center = grid.flat_index(2, 2)
    assert result[center] == pytest.approx(4.0, abs=1e-10)
    assert result[grid.flat_index(0, 2)] == 0.0


def test_2d_diffusion_reuses_pde_and_compiles_to_animated_surface() -> None:
    registry = DomainRegistry()
    loaded = builtin_domain_catalog().load(registry, ["physics.diffusion.2d"])
    assert "partial_differential_equations.2d" in loaded
    assert "partial_differential_equations" in loaded
    assert "differential_equations" in loaded

    grid = UniformGrid2D(
        UniformGrid1D(-1.0, 1.0, 7),
        UniformGrid1D(-1.0, 1.0, 7),
    )
    initial = [0.0] * grid.count
    center_index = grid.flat_index(3, 3)
    neighbour_index = grid.flat_index(4, 3)
    initial[center_index] = 1.0
    problem = DiffusionProblem2D(
        grid=grid,
        initial_values=tuple(initial),
        diffusivity=0.1,
        boundary="fixed",
        name="heat2d",
    )

    solve = registry.require("physics.diffusion.solve2d")
    solution = solve(problem, end_time=0.05, steps=20)
    assert solution.states[-1][center_index] < 1.0
    assert solution.states[-1][neighbour_index] > 0.0

    scene = registry.compile_scene(solution)
    assert len(scene.primitives) == 1
    surface = scene.primitives[0]
    assert isinstance(surface, Surface)
    assert len(surface.vertices) == grid.count
    assert len(surface.triangles) == 2 * (grid.x.count - 1) * (grid.y.count - 1)
    assert scene.timeline.duration == pytest.approx(0.05)

    final_scene = scene.sample(scene.timeline.duration)
    final_surface = final_scene.primitives[0]
    assert isinstance(final_surface, Surface)
    assert final_surface.vertices[center_index].z < surface.vertices[center_index].z
