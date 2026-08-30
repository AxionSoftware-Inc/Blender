"""Public facade for time-domain Maxwell capabilities."""

from spectra.domains.physics.maxwell3d import (
    Maxwell3DDomain,
    MaxwellProblem3D,
    MaxwellSolution3D,
)
from spectra.domains.physics.maxwell_diagnostics3d import (
    MaxwellDiagnosticSnapshot3D,
    MaxwellDiagnostics3D,
    MaxwellDiagnostics3DDomain,
)
from spectra.domains.physics.maxwell_particles3d import MaxwellParticleDynamics3DDomain
from spectra.domains.physics.maxwell_sources3d import (
    MaxwellGaussSnapshot3D,
    MaxwellSourceDiagnostics3D,
    MaxwellSourceFields3D,
    MaxwellSourceHistory3D,
    MaxwellSources3DDomain,
)
from spectra.domains.physics.maxwell_views3d import (
    MaxwellFields3D,
    MaxwellViews3DDomain,
)

__all__ = [
    "Maxwell3DDomain",
    "MaxwellDiagnosticSnapshot3D",
    "MaxwellDiagnostics3D",
    "MaxwellDiagnostics3DDomain",
    "MaxwellFields3D",
    "MaxwellGaussSnapshot3D",
    "MaxwellParticleDynamics3DDomain",
    "MaxwellProblem3D",
    "MaxwellSolution3D",
    "MaxwellSourceDiagnostics3D",
    "MaxwellSourceFields3D",
    "MaxwellSourceHistory3D",
    "MaxwellSources3DDomain",
    "MaxwellViews3DDomain",
]
