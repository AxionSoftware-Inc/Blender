from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any

from spectra.core.units import Dimension, Quantity, Unit
from spectra.domains.experiments.domain import MetricValue, TrackedExperimentResult
from spectra.domains.registry import DomainDependency, DomainRegistry
from spectra.reproducibility import ScientificEnvironmentSnapshot


EXPERIMENT_ARTIFACT_SCHEMA = "spectra.experiment"
EXPERIMENT_ARTIFACT_VERSION = 1


def _encode_unit(unit: Unit) -> dict[str, Any]:
    dimension = unit.dimension
    return {
        "name": unit.name,
        "symbol": unit.symbol,
        "scale_to_si": unit.scale_to_si,
        "offset_to_si": unit.offset_to_si,
        "dimension": {
            "length": dimension.length,
            "mass": dimension.mass,
            "time": dimension.time,
            "current": dimension.current,
            "temperature": dimension.temperature,
            "amount": dimension.amount,
            "luminous_intensity": dimension.luminous_intensity,
        },
    }


def _decode_unit(payload: dict[str, Any]) -> Unit:
    dimension_raw = payload.get("dimension")
    if not isinstance(dimension_raw, dict):
        raise ValueError("serialized unit dimension must be an object")
    dimension = Dimension(
        length=int(dimension_raw.get("length", 0)),
        mass=int(dimension_raw.get("mass", 0)),
        time=int(dimension_raw.get("time", 0)),
        current=int(dimension_raw.get("current", 0)),
        temperature=int(dimension_raw.get("temperature", 0)),
        amount=int(dimension_raw.get("amount", 0)),
        luminous_intensity=int(dimension_raw.get("luminous_intensity", 0)),
    )
    return Unit(
        name=str(payload["name"]),
        symbol=str(payload["symbol"]),
        dimension=dimension,
        scale_to_si=float(payload.get("scale_to_si", 1.0)),
        offset_to_si=float(payload.get("offset_to_si", 0.0)),
    )


def _encode_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("experiment artifact cannot serialize non-finite floats")
        return value
    if isinstance(value, Quantity):
        return {
            "__spectra_type__": "quantity",
            "value": value.value,
            "unit": _encode_unit(value.unit),
        }
    if isinstance(value, tuple):
        return {
            "__spectra_type__": "tuple",
            "items": [_encode_value(item) for item in value],
        }
    if isinstance(value, list):
        return [_encode_value(item) for item in value]
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("experiment artifact dictionaries require string keys")
        return {key: _encode_value(item) for key, item in sorted(value.items())}
    raise TypeError(f"unsupported experiment artifact value type: {type(value).__name__}")


def _decode_value(value: Any) -> Any:
    if isinstance(value, list):
        return [_decode_value(item) for item in value]
    if not isinstance(value, dict):
        return value
    marker = value.get("__spectra_type__")
    if marker == "quantity":
        unit_raw = value.get("unit")
        if not isinstance(unit_raw, dict):
            raise ValueError("serialized quantity requires unit metadata")
        return Quantity(float(value["value"]), _decode_unit(unit_raw))
    if marker == "tuple":
        items = value.get("items")
        if not isinstance(items, list):
            raise ValueError("serialized tuple requires items list")
        return tuple(_decode_value(item) for item in items)
    if marker is not None:
        raise ValueError(f"unknown serialized experiment value marker: {marker}")
    return {str(key): _decode_value(item) for key, item in value.items()}


@dataclass(frozen=True, slots=True)
class ExperimentAxisArtifact:
    name: str
    values: tuple[Any, ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("experiment artifact axis name cannot be empty")
        if not self.values:
            raise ValueError("experiment artifact axis requires values")


@dataclass(frozen=True, slots=True)
class ExperimentMetricArtifact:
    name: str
    unit: Unit | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("experiment artifact metric name cannot be empty")


@dataclass(frozen=True, slots=True)
class ExperimentCaseArtifact:
    case_id: str
    parameters: tuple[tuple[str, Any], ...]
    metrics: tuple[MetricValue, ...]
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.case_id:
            raise ValueError("experiment artifact case_id cannot be empty")
        names = tuple(name for name, _value in self.parameters)
        if len(names) != len(set(names)):
            raise ValueError("experiment artifact case parameters must be unique")


@dataclass(frozen=True, slots=True)
class ExperimentArtifact:
    name: str
    axes: tuple[ExperimentAxisArtifact, ...]
    metric_definitions: tuple[ExperimentMetricArtifact, ...]
    cases: tuple[ExperimentCaseArtifact, ...]
    environment: ScientificEnvironmentSnapshot
    metadata: tuple[tuple[str, str], ...] = ()
    schema: str = EXPERIMENT_ARTIFACT_SCHEMA
    version: int = EXPERIMENT_ARTIFACT_VERSION

    def __post_init__(self) -> None:
        if self.schema != EXPERIMENT_ARTIFACT_SCHEMA:
            raise ValueError("unknown experiment artifact schema")
        if self.version != EXPERIMENT_ARTIFACT_VERSION:
            raise ValueError("unsupported experiment artifact version")
        if not self.name:
            raise ValueError("experiment artifact name cannot be empty")
        if not self.axes:
            raise ValueError("experiment artifact requires at least one parameter axis")
        if not self.cases:
            raise ValueError("experiment artifact requires at least one case")
        metadata_keys = tuple(key for key, _value in self.metadata)
        if len(metadata_keys) != len(set(metadata_keys)) or any(not key for key in metadata_keys):
            raise ValueError("experiment artifact metadata keys must be non-empty and unique")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "version": self.version,
            "name": self.name,
            "axes": [
                {
                    "name": axis.name,
                    "values": [_encode_value(value) for value in axis.values],
                }
                for axis in self.axes
            ],
            "metrics": [
                {
                    "name": metric.name,
                    "unit": None if metric.unit is None else _encode_unit(metric.unit),
                }
                for metric in self.metric_definitions
            ],
            "cases": [
                {
                    "case_id": case.case_id,
                    "parameters": [
                        [name, _encode_value(value)]
                        for name, value in case.parameters
                    ],
                    "metrics": [
                        {
                            "name": metric.name,
                            "value": metric.value,
                            "unit": None if metric.unit is None else _encode_unit(metric.unit),
                        }
                        for metric in case.metrics
                    ],
                    "error": case.error,
                }
                for case in self.cases
            ],
            "environment": self.environment.to_dict(),
            "environment_fingerprint": self.environment.fingerprint,
            "metadata": {key: value for key, value in self.metadata},
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ExperimentArtifact":
        if not isinstance(payload, dict):
            raise TypeError("experiment artifact payload must be an object")
        if payload.get("schema") != EXPERIMENT_ARTIFACT_SCHEMA:
            raise ValueError("unknown experiment artifact schema")
        if int(payload.get("version", -1)) != EXPERIMENT_ARTIFACT_VERSION:
            raise ValueError("unsupported experiment artifact version")

        axes_raw = payload.get("axes")
        metrics_raw = payload.get("metrics")
        cases_raw = payload.get("cases")
        environment_raw = payload.get("environment")
        metadata_raw = payload.get("metadata", {})
        if not isinstance(axes_raw, list) or not isinstance(metrics_raw, list) or not isinstance(cases_raw, list):
            raise ValueError("experiment artifact axes/metrics/cases must be lists")
        if not isinstance(environment_raw, dict):
            raise ValueError("experiment artifact environment must be an object")
        if not isinstance(metadata_raw, dict):
            raise ValueError("experiment artifact metadata must be an object")

        axes = tuple(
            ExperimentAxisArtifact(
                name=str(item["name"]),
                values=tuple(_decode_value(value) for value in item["values"]),
            )
            for item in axes_raw
        )
        metric_definitions = tuple(
            ExperimentMetricArtifact(
                name=str(item["name"]),
                unit=(None if item.get("unit") is None else _decode_unit(item["unit"])),
            )
            for item in metrics_raw
        )
        cases = []
        for item in cases_raw:
            parameters_raw = item.get("parameters", [])
            metrics_values_raw = item.get("metrics", [])
            cases.append(
                ExperimentCaseArtifact(
                    case_id=str(item["case_id"]),
                    parameters=tuple(
                        (str(pair[0]), _decode_value(pair[1]))
                        for pair in parameters_raw
                    ),
                    metrics=tuple(
                        MetricValue(
                            name=str(metric["name"]),
                            value=float(metric["value"]),
                            unit=(
                                None
                                if metric.get("unit") is None
                                else _decode_unit(metric["unit"])
                            ),
                        )
                        for metric in metrics_values_raw
                    ),
                    error=(None if item.get("error") is None else str(item["error"])),
                )
            )
        environment = ScientificEnvironmentSnapshot.from_dict(environment_raw)
        expected_fingerprint = payload.get("environment_fingerprint")
        if expected_fingerprint is not None and str(expected_fingerprint) != environment.fingerprint:
            raise ValueError("experiment artifact environment fingerprint mismatch")
        return cls(
            name=str(payload["name"]),
            axes=axes,
            metric_definitions=metric_definitions,
            cases=tuple(cases),
            environment=environment,
            metadata=tuple(sorted((str(key), str(value)) for key, value in metadata_raw.items())),
        )

    @property
    def fingerprint(self) -> str:
        encoded = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


def artifact_from_tracked_experiment(
    tracked: TrackedExperimentResult,
    *,
    metadata: tuple[tuple[str, str], ...] = (),
) -> ExperimentArtifact:
    experiment = tracked.experiment
    metric_definitions_by_name: dict[str, ExperimentMetricArtifact] = {}
    for case in experiment.cases:
        for metric in case.metrics:
            existing = metric_definitions_by_name.get(metric.name)
            definition = ExperimentMetricArtifact(metric.name, metric.unit)
            if existing is not None and existing != definition:
                raise ValueError(f"experiment metric unit changed across cases: {metric.name}")
            metric_definitions_by_name[metric.name] = definition
    return ExperimentArtifact(
        name=experiment.name,
        axes=tuple(
            ExperimentAxisArtifact(axis.name, axis.values)
            for axis in experiment.sweep.axes
        ),
        metric_definitions=tuple(
            metric_definitions_by_name[name]
            for name in sorted(metric_definitions_by_name)
        ),
        cases=tuple(
            ExperimentCaseArtifact(
                case_id=case.case.case_id,
                parameters=case.case.parameters,
                metrics=case.metrics,
                error=case.error,
            )
            for case in experiment.cases
        ),
        environment=tracked.environment,
        metadata=metadata,
    )


def artifact_to_json(artifact: ExperimentArtifact, *, indent: int | None = None) -> str:
    return json.dumps(
        artifact.to_dict(),
        sort_keys=True,
        separators=None if indent is not None else (",", ":"),
        indent=indent,
    )


def artifact_from_json(payload: str) -> ExperimentArtifact:
    decoded = json.loads(payload)
    if not isinstance(decoded, dict):
        raise ValueError("experiment artifact JSON root must be an object")
    return ExperimentArtifact.from_dict(decoded)


class ExperimentArtifactsDomain:
    """Durable metric/parameter summaries for tracked experiments."""

    name = "experiments.artifacts"
    version = "1"
    dependencies = (
        DomainDependency("experiments.run_sweep_tracked"),
    )

    def register(self, registry: DomainRegistry) -> None:
        registry.register_semantic_type("experiments.artifact", ExperimentArtifact)
        registry.provide("experiments.artifact", ExperimentArtifact)
        registry.provide("experiments.artifact_from_tracked", artifact_from_tracked_experiment)
        registry.provide("experiments.artifact_to_json", artifact_to_json)
        registry.provide("experiments.artifact_from_json", artifact_from_json)


__all__ = [
    "EXPERIMENT_ARTIFACT_SCHEMA",
    "EXPERIMENT_ARTIFACT_VERSION",
    "ExperimentArtifact",
    "ExperimentArtifactsDomain",
    "ExperimentAxisArtifact",
    "ExperimentCaseArtifact",
    "ExperimentMetricArtifact",
    "artifact_from_json",
    "artifact_from_tracked_experiment",
    "artifact_to_json",
]
