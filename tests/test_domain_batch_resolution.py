import pytest

from spectra.domains import DomainRegistry, DomainResolutionError
from spectra.domains.linear_algebra import LinearAlgebraDomain
from spectra.domains.mathematics import MathematicsDomain
from spectra.domains.physics.electromagnetism import ElectromagnetismDomain
from spectra.domains.physics.quantum import QuantumDomain
from spectra.domains.probability import ProbabilityDomain


def test_domains_can_be_added_in_arbitrary_dependency_order() -> None:
    registry = DomainRegistry()
    registry.add_domains(
        [
            QuantumDomain(),
            ElectromagnetismDomain(),
            ProbabilityDomain(),
            MathematicsDomain(),
            LinearAlgebraDomain(),
        ]
    )

    assert registry.has_capability("physics.quantum.make_state")
    assert registry.has_capability("physics.electromagnetism.electric_field_from_point_charges")


def test_unresolved_domain_dependencies_report_missing_capabilities() -> None:
    registry = DomainRegistry()

    with pytest.raises(DomainResolutionError, match="probability.discrete_distribution"):
        registry.add_domains([QuantumDomain(), LinearAlgebraDomain()])
