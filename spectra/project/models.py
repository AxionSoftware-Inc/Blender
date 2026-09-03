from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from spectra.numerics import NumericalSolverRequirements

@dataclass(frozen=True, slots=True)
class ProjectMetadata:
    project_id: str
    title: str
    description: str = ""
    created_with: str | None = None
    tags: tuple[str, ...] = ()

@dataclass(frozen=True, slots=True)
class ModelRecord:
    model_id: str
    semantic_type: str
    payload_schema: str
    payload: dict[str, Any]
    resource_ids: tuple[str, ...] = ()

@dataclass(frozen=True, slots=True)
class ProjectSolverSelection:
    role: str
    policy_name: str | None = None
    implementation_id: str | None = None
    requirements: NumericalSolverRequirements | None = None

@dataclass(frozen=True, slots=True)
class ResultRecord:
    result_id: str
    model_id: str
    artifact_uri: str
    artifact_schema: str
    environment_fingerprint: str | None = None
    model_fingerprint: str | None = None
    status: str = "ready"

@dataclass(frozen=True, slots=True)
class ExperimentRecord:
    experiment_id: str
    artifact_uri: str
    artifact_schema: str = "spectra.experiment"
    environment_fingerprint: str | None = None

@dataclass(frozen=True, slots=True)
class ViewRecord:
    view_id: str
    source_result_id: str
    view_type: str
    parameters: dict[str, Any]

@dataclass(frozen=True, slots=True)
class PresentationVariantRecord:
    presentation_id: str
    view_id: str
    preset: str
    intent_payload: dict[str, Any]

@dataclass(frozen=True, slots=True)
class EnvironmentRequirement:
    capability: str | None = None
    min_version: int | None = None
    plugin_id: str | None = None
    plugin_version: str | None = None
