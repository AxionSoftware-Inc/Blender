from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.numerics import NumericalSolverPolicy, NumericalSolverRequirements
from spectra.reproducibility import ScientificEnvironmentSnapshot, capture_environment


def test_environment_fingerprint_changes_when_active_solver_policy_changes() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["differential_equations"])
    baseline = capture_environment(registry)

    registry.set_numerical_solver_policy(
        "ode.first_order",
        NumericalSolverPolicy(
            rules=(
                NumericalSolverRequirements(
                    execution_kinds=("gpu",),
                    allow_reference=False,
                ),
            ),
            fallback_to_default=True,
            name="gpu_first",
        ),
    )
    with_policy = capture_environment(registry)

    assert baseline.policies == ()
    assert len(with_policy.policies) == 1
    assert with_policy.policies[0].name == "gpu_first"
    assert with_policy.fingerprint != baseline.fingerprint


def test_environment_snapshot_policy_round_trip_preserves_fingerprint() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["differential_equations"])
    registry.set_numerical_solver_policy(
        "ode.first_order",
        NumericalSolverPolicy(
            rules=(
                NumericalSolverRequirements(
                    minimum_order=4,
                    adaptive=False,
                    required_tags=("reference",),
                ),
            ),
            fallback_to_default=False,
            name="fixed_reference",
        ),
    )
    snapshot = capture_environment(registry)
    restored = ScientificEnvironmentSnapshot.from_dict(snapshot.to_dict())

    assert restored == snapshot
    assert restored.fingerprint == snapshot.fingerprint
