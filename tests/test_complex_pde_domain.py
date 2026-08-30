import cmath

import pytest

from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.partial_differential_equations import ComplexPDEProblem1D, UniformGrid1D


def test_complex_pde_reuses_existing_solver_stack() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["partial_differential_equations.complex"])
    solve = registry.require("pde.complex.solve_method_of_lines")

    problem = ComplexPDEProblem1D(
        grid=UniformGrid1D(0.0, 1.0, 3),
        initial_values=(1.0 + 0.0j, 1.0 + 0.0j, 1.0 + 0.0j),
        rhs=lambda _time, _grid, values: tuple(1j * value for value in values),
        name="complex-rotation",
    )
    solution = solve(problem, end_time=0.1, steps=20)

    assert "partial_differential_equations" in registry.domains
    assert "differential_equations" in registry.domains
    assert solution.states[-1][1] == pytest.approx(cmath.exp(0.1j), rel=1e-7)
    assert registry.compile_scene(solution).timeline.duration == pytest.approx(0.1)
