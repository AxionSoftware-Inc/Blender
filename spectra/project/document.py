from __future__ import annotations
from dataclasses import asdict, dataclass
import json
from typing import Any
from .models import *

@dataclass(frozen=True, slots=True)
class ProjectDocument:
    schema: str
    metadata: ProjectMetadata
    models: tuple[ModelRecord, ...] = ()
    solver_selections: tuple[ProjectSolverSelection, ...] = ()
    results: tuple[ResultRecord, ...] = ()
    experiments: tuple[ExperimentRecord, ...] = ()
    views: tuple[ViewRecord, ...] = ()
    presentations: tuple[PresentationVariantRecord, ...] = ()
    requirements: tuple[EnvironmentRequirement, ...] = ()

    def __post_init__(self) -> None:
        if self.schema != "spectra.project.v1":
            raise ValueError("unsupported project schema")
        for records in (self.models, self.results, self.views, self.presentations):
            ids = [getattr(record, next(name for name in ("model_id", "result_id", "view_id", "presentation_id") if hasattr(record, name))) for record in records]
            if len(ids) != len(set(ids)):
                raise ValueError("project record identifiers must be unique")

def _plain(value: Any) -> Any:
    if isinstance(value, tuple): return [_plain(v) for v in value]
    if isinstance(value, dict): return {k: _plain(v) for k, v in value.items()}
    if hasattr(value, "__dataclass_fields__"):
        return {k: _plain(v) for k, v in asdict(value).items()}
    return value

def project_to_dict(project: ProjectDocument) -> dict[str, object]: return _plain(project)
def project_to_json(project: ProjectDocument) -> str: return json.dumps(project_to_dict(project), sort_keys=True, indent=2)

def project_from_dict(payload: dict[str, object]) -> ProjectDocument:
    if payload.get("schema") != "spectra.project.v1": raise ValueError("unsupported project schema")
    def records(key: str, cls: Any) -> tuple[Any, ...]: return tuple(cls(**item) for item in payload.get(key, []))
    return ProjectDocument(str(payload["schema"]), ProjectMetadata(**payload["metadata"]),
        records("models", ModelRecord), records("solver_selections", ProjectSolverSelection),
        records("results", ResultRecord), records("experiments", ExperimentRecord), records("views", ViewRecord),
        records("presentations", PresentationVariantRecord), records("requirements", EnvironmentRequirement))
def project_from_json(text: str) -> ProjectDocument: return project_from_dict(json.loads(text))
