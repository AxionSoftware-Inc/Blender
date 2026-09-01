from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.experiments import ParameterAxis, ParameterSweep
from spectra.numerics import NumericalMethodDescriptor
from spectra.reproducibility import capture_environment


def test_environment_snapshot_is_deterministic_for_same_registry_state() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["differential_equations", "experiments"])

    first = capture_environment(registry)
    second = capture_environment(registry)

    assert first == second
    assert first.fingerprint == second.fingerprint
    assert len(first.fingerprint) == 64
    assert any(record.name == "experiments" for record in first.domains)
    assert any(record.role == "ode.first_order" for record in first.solvers)


def test_environment_fingerprint_changes_when_solver_inventory_changes() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["differential_equations"])
    baseline = capture_environment(registry)

    method = NumericalMethodDescriptor(
        method_id="test.solver",
        family="test",
        implementation="tests",
        order=1,
        reference_implementation=False,
    )
    registry.register_numerical_solver(
        "ode.first_order",
        "test.extra",
        lambda system, **_kwargs: system,
        method,
    )
    changed = capture_environment(registry)

    assert changed.fingerprint != baseline.fingerprint
    assert any(record.implementation_id == "test.extra" for record in changed.solvers)


def test_tracked_parameter_sweep_captures_environment() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["experiments"])
    run_tracked = registry.require("experiments.run_sweep_tracked")
    sweep = ParameterSweep(
        axes=(ParameterAxis("x", (1, 2, 3)),),
        name="tracked",
    )

    tracked = run_tracked(sweep, lambda parameters: parameters["x"] ** 2)

    assert tracked.experiment.success_count == 3
    assert tracked.environment == capture_environment(registry)
    assert tracked.environment_fingerprint == tracked.environment.fingerprint
