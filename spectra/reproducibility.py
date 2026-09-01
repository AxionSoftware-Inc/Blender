from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, TYPE_CHECKING

from spectra.numerics import (
    NumericalMethodDescriptor,
    NumericalPipelineDescriptor,
    NumericalSolverRequirements,
)

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
class SolverRequirementRecord:
    execution_kinds: tuple[str, ...] = ()
    precisions: tuple[str, ...] = ()
    minimum_order: int | None = None
    adaptive: bool | None = None
    allow_reference: bool = True
    required_tags: tuple[str, ...] = ()

    @classmethod
    def from_requirements(cls, requirements: NumericalSolverRequirements) -> "SolverRequirementRecord":
        return cls(
            execution_kinds=tuple(requirements.execution_kinds),
            precisions=tuple(requirements.precisions),
            minimum_order=requirements.minimum_order,
            adaptive=requirements.adaptive,
            allow_reference=requirements.allow_reference,
            required_tags=tuple(requirements.required_tags),
        )


@dataclass(frozen=True, slots=True)
class SolverPolicyRecord:
    role: str
    name: str
    rules: tuple[SolverRequirementRecord, ...]
    fallback_to_default: bool

    def __post_init__(self) -> None:
        if not self.role or not self.name:
            raise ValueError("solver policy record identifiers cannot be empty")


@dataclass(frozen=True, slots=True)
class ScientificEnvironmentSnapshot:
    domains: tuple[DomainVersionRecord, ...]
    capabilities: tuple[CapabilityVersionRecord, ...]
    solvers: tuple[SolverImplementationRecord, ...]
    policies: tuple[SolverPolicyRecord, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
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
            "policies": [
                {
                    "role": record.role,
                    "name": record.name,
                    "fallback_to_default": record.fallback_to_default,
                    "rules": [
                        {
                            "execution_kinds": list(rule.execution_kinds),
                            "precisions": list(rule.precisions),
                            "minimum_order": rule.minimum_order,
                            "adaptive": rule.adaptive,
                            "allow_reference": rule.allow_reference,
                            "required_tags": list(rule.required_tags),
                        }
                        for rule in record.rules
                    ],
                }
                for record in self.policies
            ],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ScientificEnvironmentSnapshot":
        if not isinstance(payload, dict):
            raise TypeError("scientific environment payload must be a dictionary")
        try:
            domains_raw = payload["domains"]
            capabilities_raw = payload["capabilities"]
            solvers_raw = payload["solvers"]
        except KeyError as exc:
            raise ValueError(f"scientific environment payload missing key: {exc.args[0]}") from exc
        policies_raw = payload.get("policies", [])
        if not isinstance(domains_raw, list) or not isinstance(capabilities_raw, list) or not isinstance(solvers_raw, list):
            raise ValueError("scientific environment collections must be lists")
        if not isinstance(policies_raw, list):
            raise ValueError("scientific environment policies must be a list")
        domains = tuple(
            DomainVersionRecord(name=str(item["name"]), version=str(item["version"]))
            for item in domains_raw
        )
        capabilities = tuple(
            CapabilityVersionRecord(
                key=str(item["key"]),
                version=int(item["version"]),
                provider_domain=(
                    None if item.get("provider_domain") is None else str(item["provider_domain"])
                ),
            )
            for item in capabilities_raw
        )
        solvers = tuple(
            SolverImplementationRecord(
                role=str(item["role"]),
                implementation_id=str(item["implementation_id"]),
                provider_domain=(
                    None if item.get("provider_domain") is None else str(item["provider_domain"])
                ),
                method_id=str(item["method_id"]),
                execution_kind=str(item["execution_kind"]),
                backend=str(item["backend"]),
                precision=str(item["precision"]),
                is_default=bool(item["is_default"]),
                priority=int(item["priority"]),
                tags=tuple(str(tag) for tag in item.get("tags", ())),
            )
            for item in solvers_raw
        )
        policies = tuple(
            SolverPolicyRecord(
                role=str(item["role"]),
                name=str(item["name"]),
                fallback_to_default=bool(item.get("fallback_to_default", True)),
                rules=tuple(
                    SolverRequirementRecord(
                        execution_kinds=tuple(str(value) for value in rule.get("execution_kinds", ())),
                        precisions=tuple(str(value) for value in rule.get("precisions", ())),
                        minimum_order=(
                            None if rule.get("minimum_order") is None else int(rule["minimum_order"])
                        ),
                        adaptive=(None if rule.get("adaptive") is None else bool(rule["adaptive"])),
                        allow_reference=bool(rule.get("allow_reference", True)),
                        required_tags=tuple(str(value) for value in rule.get("required_tags", ())),
                    )
                    for rule in item.get("rules", ())
                ),
            )
            for item in policies_raw
        )
        return cls(
            domains=domains,
            capabilities=capabilities,
            solvers=solvers,
            policies=policies,
        )

    @property
    def fingerprint(self) -> str:
        encoded = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")
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
    policy_records = []
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
        policy = registry.numerical_solvers.policy_for(role)
        if policy is not None:
            policy_records.append(
                SolverPolicyRecord(
                    role=role,
                    name=policy.name,
                    rules=tuple(
                        SolverRequirementRecord.from_requirements(rule)
                        for rule in policy.rules
                    ),
                    fallback_to_default=policy.fallback_to_default,
                )
            )
    return ScientificEnvironmentSnapshot(
        domains=domains,
        capabilities=capabilities,
        solvers=tuple(solver_records),
        policies=tuple(policy_records),
    )


__all__ = [
    "CapabilityVersionRecord",
    "DomainVersionRecord",
    "ScientificEnvironmentSnapshot",
    "SolverImplementationRecord",
    "SolverPolicyRecord",
    "SolverRequirementRecord",
    "capture_environment",
]
