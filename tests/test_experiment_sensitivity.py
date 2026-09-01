import pytest

from spectra.core.units import METER, Quantity
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.experiments import MetricSpec, SensitivityParameter


def test_local_sensitivity_matches_quadratic_analytical_derivative_and_normalized_value() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["experiments.sensitivity"])
    local_sensitivity = registry.require("experiments.local_sensitivity")

    result = local_sensitivity(
        (SensitivityParameter("length", baseline=2.0, step=0.1, unit=METER),),
        lambda parameters: parameters["length"],
        metrics=(
            MetricSpec(
                "area",
                lambda output, _parameters: output.value ** 2,
                unit=METER ** 2,
            ),
        ),
    )

    estimate = result.estimate("length", "area")
    assert estimate.baseline_parameter_si == pytest.approx(2.0)
    assert estimate.baseline_response_si == pytest.approx(4.0)
    assert estimate.derivative_si == pytest.approx(4.0)
    assert estimate.normalized_sensitivity == pytest.approx(2.0)


def test_local_sensitivity_passes_quantity_parameters_to_evaluator() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["experiments.sensitivity"])
    local_sensitivity = registry.require("experiments.local_sensitivity")
    observed: list[type] = []

    def evaluator(parameters):
        value = parameters["length"]
        observed.append(type(value))
        return value.si_value

    result = local_sensitivity(
        (SensitivityParameter("length", baseline=1.0, step=0.05, unit=METER),),
        evaluator,
        metrics=(MetricSpec("length_si", lambda output, _parameters: output, unit=METER),),
    )

    assert all(value_type is Quantity for value_type in observed)
    assert result.estimate("length", "length_si").derivative_si == pytest.approx(1.0)


def test_local_sensitivity_rejects_fixed_parameter_overlap() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["experiments.sensitivity"])
    local_sensitivity = registry.require("experiments.local_sensitivity")

    with pytest.raises(ValueError, match="overlap"):
        local_sensitivity(
            (SensitivityParameter("x", baseline=1.0, step=0.1),),
            lambda parameters: parameters["x"],
            metrics=(MetricSpec("value", lambda output, _parameters: output),),
            fixed_parameters={"x": 2.0},
        )
