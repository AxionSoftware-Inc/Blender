"""Public facade for coupled multi-component PDE capabilities."""

from spectra.domains.partial_differential_equations.coupled3d import (
    CoupledScalarPDE3DDomain,
    CoupledScalarPDEProblem3D,
    CoupledScalarPDESolution3D,
)

__all__ = [
    "CoupledScalarPDE3DDomain",
    "CoupledScalarPDEProblem3D",
    "CoupledScalarPDESolution3D",
]
