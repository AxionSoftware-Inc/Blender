import pytest

from spectra.core.primitives import PointCloud, Polyline, TextLabel
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.experiments import (
    ConvergenceEstimate,
    ConvergenceSample,
    ConvergenceView2D,
    MetricObjective,
    MetricSeriesView2D,
    MetricSpec,
    ParameterAxis,
    ParameterSweep,
    ParetoFrontView2D,
    SensitivityParameter,
    SensitivityView2D,
    SolverConvergenceResult,
)


def test_metric_series_view_compiles_experiment_to_pointcloud_and_polyline() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["experiments.views"])
    experiment = registry.require("experiments.run_sweep")(
        ParameterSweep((ParameterAxis("x", (1.0, 2.0, 3.0)),), name="response"),
        lambda parameters: parameters["x"] ** 2,
        metrics=(MetricSpec("y", lambda output, _parameters: output),),
    )
    scene = registry.compile_scene(MetricSeriesView2D(experiment, "x", "y"))

    assert isinstance(scene.get("metric_series.points"), PointCloud)
    assert isinstance(scene.get("metric_series.line"), Polyline)
    assert scene.get("metric_series.points").positions[-1].y == pytest.approx(9.0)


def test_pareto_front_view_compiles_two_metrics_to_pointcloud() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["experiments.views"])
    experiment = registry.require("experiments.run_sweep")(
        ParameterSweep((ParameterAxis("design", (1.0, 2.0, 3.0)),), name="designs"),
        lambda parameters: parameters["design"],
        metrics=(
            MetricSpec("cost", lambda output, _parameters: output),
            MetricSpec("quality", lambda output, _parameters: output),
        ),
    )
    front = registry.require("experiments.pareto_front")(
        experiment,
        (
            MetricObjective("cost", "minimize"),
            MetricObjective("quality", "maximize"),
        ),
    )
    scene = registry.compile_scene(ParetoFrontView2D(front, "cost", "quality"))

    cloud = scene.get("pareto_front.points")
    assert isinstance(cloud, PointCloud)
    assert cloud.instance_count == 3


def test_convergence_view_uses_log_coordinates_when_requested() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["experiments.views"])
    result = SolverConvergenceResult(
        role="ode.first_order",
        implementation_id="test",
        samples=(
            ConvergenceSample(8, 0.125, 1e-2),
            ConvergenceSample(16, 0.0625, 2.5e-3),
        ),
        estimates=(ConvergenceEstimate(8, 16, 2.0),),
        method_order=2,
    )
    scene = registry.compile_scene(ConvergenceView2D(result, log10=True))

    line = scene.get("convergence.line")
    assert isinstance(line, Polyline)
    assert line.points[0].x == pytest.approx(-0.90308998699)
    assert line.points[0].y == pytest.approx(-2.0)


def test_sensitivity_view_compiles_stems_labels_and_tip_batch() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["experiments.views"])
    sensitivity = registry.require("experiments.local_sensitivity")(
        (
            SensitivityParameter("a", 2.0, 0.1),
            SensitivityParameter("b", 3.0, 0.1),
        ),
        lambda parameters: parameters["a"] * parameters["b"],
        metrics=(MetricSpec("product", lambda output, _parameters: output),),
    )
    scene = registry.compile_scene(SensitivityView2D(sensitivity, "product"))

    assert isinstance(scene.get("sensitivity.stem.0"), Polyline)
    assert isinstance(scene.get("sensitivity.label.0"), TextLabel)
    tips = scene.get("sensitivity.tips")
    assert isinstance(tips, PointCloud)
    assert tips.instance_count == 2
