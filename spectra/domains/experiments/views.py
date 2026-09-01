from __future__ import annotations

from dataclasses import dataclass
import math

from spectra.core.primitives import PointCloud, Polyline, TextLabel
from spectra.core.scene import Scene
from spectra.core.types import Color, Vec3
from spectra.core.units import Quantity
from spectra.domains.experiments.analysis import ParetoFront
from spectra.domains.experiments.convergence import SolverConvergenceResult
from spectra.domains.experiments.domain import ExperimentResult, MetricValue
from spectra.domains.experiments.sensitivity import LocalSensitivityResult
from spectra.domains.registry import DomainDependency, DomainRegistry


def _metric_si(metric: MetricValue) -> float:
    return metric.unit.to_si(metric.value) if metric.unit is not None else metric.value


def _parameter_si(value: object) -> float:
    if isinstance(value, Quantity):
        return value.si_value
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("experiment numeric view parameter must be numeric or Quantity")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError("experiment numeric view parameter must be finite")
    return numeric


@dataclass(frozen=True, slots=True)
class MetricSeriesView2D:
    experiment: ExperimentResult
    parameter: str
    metric: str
    name: str = "metric_series"

    def __post_init__(self) -> None:
        if not self.parameter or not self.metric or not self.name:
            raise ValueError("metric-series view identifiers cannot be empty")


@dataclass(frozen=True, slots=True)
class ParetoFrontView2D:
    front: ParetoFront
    x_metric: str
    y_metric: str
    name: str = "pareto_front"

    def __post_init__(self) -> None:
        if not self.x_metric or not self.y_metric or not self.name:
            raise ValueError("Pareto view identifiers cannot be empty")
        if self.x_metric == self.y_metric:
            raise ValueError("Pareto view requires distinct x/y metrics")


@dataclass(frozen=True, slots=True)
class ConvergenceView2D:
    convergence: SolverConvergenceResult
    log10: bool = True
    name: str = "convergence"

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("convergence view name cannot be empty")


@dataclass(frozen=True, slots=True)
class SensitivityView2D:
    sensitivity: LocalSensitivityResult
    metric: str
    normalized: bool = True
    name: str = "sensitivity"

    def __post_init__(self) -> None:
        if not self.metric or not self.name:
            raise ValueError("sensitivity view identifiers cannot be empty")


def compile_metric_series_view(view: MetricSeriesView2D) -> Scene:
    samples = []
    for case in view.experiment.cases:
        if not case.successful:
            continue
        parameters = case.case.as_dict()
        if view.parameter not in parameters:
            raise KeyError(f"metric-series parameter not present: {view.parameter}")
        samples.append(
            (
                _parameter_si(parameters[view.parameter]),
                _metric_si(case.metric(view.metric)),
            )
        )
    if not samples:
        raise ValueError("metric-series view has no successful samples")
    samples.sort(key=lambda pair: pair[0])
    points = tuple(Vec3(x, y, 0.0) for x, y in samples)
    primitives = [
        PointCloud(
            id=f"{view.name}.points",
            positions=points,
            radius=0.04,
            color=Color(0.35, 0.75, 1.0, 1.0),
        )
    ]
    if len(points) >= 2:
        primitives.append(
            Polyline(
                id=f"{view.name}.line",
                points=points,
                width=0.02,
                color=Color(0.35, 0.75, 1.0, 1.0),
            )
        )
    return Scene(primitives=tuple(primitives))


def compile_pareto_front_view(view: ParetoFrontView2D) -> Scene:
    if not view.front.cases:
        raise ValueError("Pareto view has no cases")
    points = tuple(
        Vec3(
            _metric_si(case.metric(view.x_metric)),
            _metric_si(case.metric(view.y_metric)),
            0.0,
        )
        for case in view.front.cases
    )
    return Scene(
        primitives=(
            PointCloud(
                id=f"{view.name}.points",
                positions=points,
                radius=0.06,
                color=Color(0.4, 1.0, 0.55, 1.0),
            ),
        )
    )


def compile_convergence_view(view: ConvergenceView2D) -> Scene:
    points = []
    for sample in view.convergence.samples:
        x = sample.step_size
        y = sample.error
        if view.log10:
            if x <= 0.0 or y <= 0.0:
                raise ValueError("log convergence view requires positive step sizes and errors")
            x = math.log10(x)
            y = math.log10(y)
        points.append(Vec3(x, y, 0.0))
    primitives = (
        Polyline(
            id=f"{view.name}.line",
            points=tuple(points),
            width=0.025,
            color=Color(1.0, 0.7, 0.3, 1.0),
        ),
        PointCloud(
            id=f"{view.name}.points",
            positions=tuple(points),
            radius=0.045,
            color=Color(1.0, 0.7, 0.3, 1.0),
        ),
    )
    return Scene(primitives=primitives)


def compile_sensitivity_view(view: SensitivityView2D) -> Scene:
    estimates = tuple(
        estimate
        for estimate in view.sensitivity.estimates
        if estimate.metric == view.metric
    )
    if not estimates:
        raise ValueError(f"sensitivity view has no estimates for metric: {view.metric}")
    primitives = []
    tip_positions = []
    for index, estimate in enumerate(estimates):
        value = (
            estimate.normalized_sensitivity
            if view.normalized
            else estimate.derivative_si
        )
        if value is None:
            raise ValueError(
                f"normalized sensitivity is undefined for parameter: {estimate.parameter}"
            )
        x = float(index)
        origin = Vec3(x, 0.0, 0.0)
        tip = Vec3(x, float(value), 0.0)
        primitives.append(
            Polyline(
                id=f"{view.name}.stem.{index}",
                points=(origin, tip),
                width=0.04,
                color=Color(0.75, 0.55, 1.0, 1.0),
            )
        )
        primitives.append(
            TextLabel(
                id=f"{view.name}.label.{index}",
                text=estimate.parameter,
                position=Vec3(x, 0.0, 0.0),
                size=0.25,
                color=Color(0.9, 0.9, 0.9, 1.0),
            )
        )
        tip_positions.append(tip)
    primitives.append(
        PointCloud(
            id=f"{view.name}.tips",
            positions=tuple(tip_positions),
            radius=0.05,
            color=Color(0.75, 0.55, 1.0, 1.0),
        )
    )
    return Scene(primitives=tuple(primitives))


class ExperimentViewsDomain:
    """Explicit renderer-independent views for generic experiment results."""

    name = "experiments.views"
    version = "1"
    dependencies = (
        DomainDependency("experiments.result"),
        DomainDependency("experiments.pareto_front"),
        DomainDependency("experiments.solver_convergence"),
        DomainDependency("experiments.local_sensitivity_result"),
    )

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type("experiments.metric_series_view2d", MetricSeriesView2D)
        registry.register_semantic_type("experiments.pareto_view2d", ParetoFrontView2D)
        registry.register_semantic_type("experiments.convergence_view2d", ConvergenceView2D)
        registry.register_semantic_type("experiments.sensitivity_view2d", SensitivityView2D)
        registry.provide("experiments.metric_series_view2d", MetricSeriesView2D)
        registry.provide("experiments.pareto_view2d", ParetoFrontView2D)
        registry.provide("experiments.convergence_view2d", ConvergenceView2D)
        registry.provide("experiments.sensitivity_view2d", SensitivityView2D)
        registry.register_visualization(MetricSeriesView2D, compile_metric_series_view)
        registry.register_visualization(ParetoFrontView2D, compile_pareto_front_view)
        registry.register_visualization(ConvergenceView2D, compile_convergence_view)
        registry.register_visualization(SensitivityView2D, compile_sensitivity_view)


__all__ = [
    "ConvergenceView2D",
    "ExperimentViewsDomain",
    "MetricSeriesView2D",
    "ParetoFrontView2D",
    "SensitivityView2D",
]
