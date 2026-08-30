import pytest

from spectra.core.primitives import Polyline
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.physics import DiffusionProblem1D
from spectra.domains.partial_differential_equations import UniformGrid1D


def test_diffusion_domain_auto_loads_pde_and_ode_dependencies() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.diffusion"])

    assert "physics.diffusion" in registry.domains
    assert "partial_differential_equations" in registry.domains
    assert "differential_equations" in registry.domains


def test_diffusion_solution_reuses_generic_pde_visualization() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.diffusion"])
    solve = registry.require("physics.diffusion.solve1d")

    problem = DiffusionProblem1D(
        grid=UniformGrid1D(0.0, 1.0, 7),
        initial_values=(0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0),
        diffusivity=0.05,
        boundary="fixed",
        name="thermal-pulse",
    )
    solution = solve(problem, end_time=0.1, steps=20)

    assert solution.states[-1][3] < 1.0
    assert solution.states[-1][2] > 0.0
    assert solution.states[-1][4] > 0.0
    assert solution.states[-1][0] == pytest.approx(0.0)
    assert solution.states[-1][-1] == pytest.approx(0.0)

    scene = registry.compile_scene(solution)
    profile = scene.get("thermal-pulse.profile")
    assert isinstance(profile, Polyline)
    assert scene.timeline.duration == pytest.approx(0.1)
