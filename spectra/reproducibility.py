from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import TYPE_CHECKING

from spectra.numerics import NumericalMethodDescriptor, NumericalPipelineDescriptor

if TYPE_CHECKING:
    from spectra.domains.registry import DomainRegistry


@dataclass(frozen=True, slots=True)
class DomainVersionRecord:
    name: str
    version: str

    def __post_init__(self) -> None:
        if not self.name or not self.version:
            raise ValueError("domain version record requires name and version")


@dataclass(frozen=True, slots=True)
class CapabilityVersionRecord:
    key: str
    version: int
    provider_domain: str | None

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("capability version record key cannot be empty")
        if self.version < 1:
            raise ValueError("capability version must be >= 1")


@dataclass(frozen=True, slots=True)
class SolverImplementationRecord:
    role: str
    implementation_id: str
    provider_domain: str | None
    method_id: str
    execution_kind: str
    backend: str
    precision: str
    is_default: bool
    priority: int
    tags: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.role or not self.implementation_id or not self.method_id:
            raise ValueError("solver implementation record identifiers cannot be empty")
        if not self.execution_kind or not self.backend or not self.precision:
            raise ValueError("solver implementation execution metadata cannot be empty")


@dataclass(frozen=True, slots=True)
class ScientificEnvironmentSnapshot:
    domains: tuple[DomainVersionRecord, ...]
    capabilities: tuple[CapabilityVersionRecord, ...]
    solvers: tuple[SolverImplementationRecord, ...]

    @property
    def fingerprint(self) -> str:
        payload = {
            "domains": [
                {"name": record.name, "version": record.version}
                for record in self.domains
            ],
            "capabilities": [
                {
                    "key": record.key,
                    "version": record.version,
                    "provider_domain": record.provider_domain,
                }
                for record in self.capabilities
            ],
            "solvers": [
                {
                    "role": record.role,
                    "implementation_id": record.implementation_id,
                    "provider_domain": record.provider_domain,
                    "method_id": record.method_id,
                    "execution_kind": record.execution_kind,
                    "backend": record.backend,
                    "precision": record.precision,
                    "is_default": record.is_default,
                    "priority": record.priority,
                    "tags": list(record.tags),
                }
                for record in self.solvers
            ],
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


def _method_id(method: NumericalMethodDescriptor | NumericalPipelineDescriptor) -> str:
    if isinstance(method, NumericalMethodDescriptor):
        return method.method_id
    return method.pipeline_id


def capture_environment(registry: "DomainRegistry") -> ScientificEnvironmentSnapshot:
    domains = tuple(
        DomainVersionRecord(name=name, version=str(registry.domains[name].version))
        for name in sorted(registry.domains)
    )
    capabilities = tuple(
        CapabilityVersionRecord(
            key=key,
            version=registry.capability_versions.get(key, 1),
            provider_domain=registry.capability_providers.get(key),
        )
        for key in sorted(registry.capabilities)
    )
    solver_records = []
    for role in registry.numerical_solvers.roles():
        default_id = registry.numerical_solvers.default_implementation_id(role)
        for implementation in registry.numerical_solver_implementations(role):
            solver_records.append(
                SolverImplementationRecord(
                    role=role,
                    implementation_id=implementation.implementation_id,
                    provider_domain=implementation.provider_domain,
                    method_id=_method_id(implementation.method),
                    execution_kind=implementation.execution.kind,
                    backend=implementation.execution.backend,
                    precision=implementation.execution.precision,
                    is_default=implementation.implementation_id == default_id,
                    priority=implementation.priority,
                    tags=tuple(sorted(implementation.tags)),
                )
            )
    return ScientificEnvironmentSnapshot(
        domains=domains,
        capabilities=capabilities,
        solvers=tuple(solver_records),
    )


__all__ = [
    "CapabilityVersionRecord",
    "DomainVersionRecord",
    "ScientificEnvironmentSnapshot",
    "SolverImplementationRecord",
    "capture_environment",
]
