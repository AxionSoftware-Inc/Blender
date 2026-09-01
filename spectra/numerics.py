from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import math
from typing import Any, Generic, Literal, TypeVar


T = TypeVar("T")
ExecutionKind = Literal["python", "cpu", "gpu", "external"]


@dataclass(frozen=True, slots=True)
class NumericalMethodDescriptor:
    """Renderer/domain-neutral description of a numerical method implementation."""

    method_id: str
    family: str
    implementation: str
    order: int | None = None
    adaptive: bool = False
    reference_implementation: bool = True
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.method_id:
            raise ValueError("numerical method_id cannot be empty")
        if not self.family:
            raise ValueError("numerical method family cannot be empty")
        if not self.implementation:
            raise ValueError("numerical method implementation cannot be empty")
        if self.order is not None and self.order < 1:
            raise ValueError("numerical method order must be >= 1")
        if any(not note for note in self.notes):
            raise ValueError("numerical method notes cannot contain empty strings")


@dataclass(frozen=True, slots=True)
class NumericalPipelineDescriptor:
    """Ordered composition of numerical method stages used by a solver capability."""

    pipeline_id: str
    stages: tuple[NumericalMethodDescriptor, ...]
    reference_implementation: bool = True
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.pipeline_id:
            raise ValueError("numerical pipeline_id cannot be empty")
        if not self.stages:
            raise ValueError("numerical pipeline requires at least one stage")
        if any(not note for note in self.notes):
            raise ValueError("numerical pipeline notes cannot contain empty strings")


@dataclass(frozen=True, slots=True)
class NumericalRunRecord:
    method: NumericalMethodDescriptor | NumericalPipelineDescriptor
    start_time: float
    end_time: float
    steps: int
    state_size: int | None = None
    tags: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not math.isfinite(self.start_time) or not math.isfinite(self.end_time):
            raise ValueError("numerical run times must be finite")
        if self.end_time <= self.start_time:
            raise ValueError("numerical run end_time must be greater than start_time")
        if self.steps < 1:
            raise ValueError("numerical run steps must be >= 1")
        if self.state_size is not None and self.state_size < 1:
            raise ValueError("numerical run state_size must be >= 1")
        if any(not key or not value for key, value in self.tags):
            raise ValueError("numerical run tags require non-empty keys and values")

    @property
    def fixed_step_size(self) -> float:
        return (self.end_time - self.start_time) / self.steps


@dataclass(frozen=True, slots=True)
class TrackedNumericalResult(Generic[T]):
    result: T
    run: NumericalRunRecord


@dataclass(frozen=True, slots=True)
class NumericalExecutionDescriptor:
    """Execution characteristics independent of a specific device API."""

    kind: ExecutionKind = "python"
    backend: str = "python"
    precision: str = "float64"
    device: str | None = None
    supports_in_place: bool = False
    batched: bool = False

    def __post_init__(self) -> None:
        if self.kind not in {"python", "cpu", "gpu", "external"}:
            raise ValueError(f"unknown numerical execution kind: {self.kind}")
        if not self.backend:
            raise ValueError("numerical execution backend cannot be empty")
        if not self.precision:
            raise ValueError("numerical execution precision cannot be empty")
        if self.device is not None and not self.device:
            raise ValueError("numerical execution device cannot be empty")


@dataclass(frozen=True, slots=True)
class NumericalSolverRequirements:
    """Hard constraints used to choose among interchangeable solver implementations."""

    execution_kinds: tuple[ExecutionKind, ...] = ()
    precisions: tuple[str, ...] = ()
    minimum_order: int | None = None
    adaptive: bool | None = None
    allow_reference: bool = True
    required_tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.minimum_order is not None and self.minimum_order < 1:
            raise ValueError("solver minimum_order must be >= 1")
        if any(kind not in {"python", "cpu", "gpu", "external"} for kind in self.execution_kinds):
            raise ValueError("solver requirements contain unknown execution kind")
        if any(not precision for precision in self.precisions):
            raise ValueError("solver requirement precisions cannot be empty")
        if any(not tag for tag in self.required_tags):
            raise ValueError("solver required_tags cannot contain empty strings")


@dataclass(frozen=True, slots=True)
class NumericalSolverImplementation:
    """One interchangeable implementation of a stable numerical solver role."""

    role: str
    implementation_id: str
    solver: Callable[..., Any]
    method: NumericalMethodDescriptor | NumericalPipelineDescriptor
    provider_domain: str | None = None
    priority: int = 0
    tags: tuple[str, ...] = ()
    execution: NumericalExecutionDescriptor = NumericalExecutionDescriptor()

    def __post_init__(self) -> None:
        if not self.role:
            raise ValueError("numerical solver role cannot be empty")
        if not self.implementation_id:
            raise ValueError("numerical solver implementation_id cannot be empty")
        if not callable(self.solver):
            raise TypeError("numerical solver implementation must be callable")
        if self.provider_domain is not None and not self.provider_domain:
            raise ValueError("numerical solver provider_domain cannot be empty")
        if any(not tag for tag in self.tags):
            raise ValueError("numerical solver tags cannot contain empty strings")

    @property
    def effective_order(self) -> int | None:
        if isinstance(self.method, NumericalMethodDescriptor):
            return self.method.order
        orders = tuple(stage.order for stage in self.method.stages if stage.order is not None)
        return min(orders) if orders else None

    @property
    def adaptive(self) -> bool:
        if isinstance(self.method, NumericalMethodDescriptor):
            return self.method.adaptive
        return any(stage.adaptive for stage in self.method.stages)

    @property
    def reference_implementation(self) -> bool:
        return self.method.reference_implementation

    def satisfies(self, requirements: NumericalSolverRequirements) -> bool:
        if requirements.execution_kinds and self.execution.kind not in requirements.execution_kinds:
            return False
        if requirements.precisions and self.execution.precision not in requirements.precisions:
            return False
        if requirements.minimum_order is not None:
            if self.effective_order is None or self.effective_order < requirements.minimum_order:
                return False
        if requirements.adaptive is not None and self.adaptive != requirements.adaptive:
            return False
        if not requirements.allow_reference and self.reference_implementation:
            return False
        if not set(requirements.required_tags).issubset(self.tags):
            return False
        return True


class NumericalSolverRegistry:
    """Registry for multiple implementations of the same numerical solver role.

    Domain capabilities remain the dependency-discovery mechanism. This registry
    handles runtime implementation choice once the relevant solver domains are
    loaded, allowing reference Python, native CPU, GPU, or external implementations
    to coexist without competing for one capability key.
    """

    def __init__(self) -> None:
        self._implementations: dict[str, dict[str, NumericalSolverImplementation]] = {}
        self._defaults: dict[str, str] = {}

    def copy(self) -> "NumericalSolverRegistry":
        clone = NumericalSolverRegistry()
        clone._implementations = {
            role: dict(implementations)
            for role, implementations in self._implementations.items()
        }
        clone._defaults = dict(self._defaults)
        return clone

    def register(
        self,
        implementation: NumericalSolverImplementation,
        *,
        make_default: bool = False,
    ) -> None:
        role_implementations = self._implementations.setdefault(implementation.role, {})
        if implementation.implementation_id in role_implementations:
            raise ValueError(
                "numerical solver implementation already registered: "
                f"{implementation.role}/{implementation.implementation_id}"
            )
        role_implementations[implementation.implementation_id] = implementation
        if make_default or implementation.role not in self._defaults:
            self._defaults[implementation.role] = implementation.implementation_id

    def roles(self) -> tuple[str, ...]:
        return tuple(sorted(self._implementations))

    def implementations(self, role: str) -> tuple[NumericalSolverImplementation, ...]:
        implementations = self._implementations.get(role)
        if implementations is None:
            raise KeyError(f"unknown numerical solver role: {role}")
        return tuple(
            implementations[key]
            for key in sorted(implementations)
        )

    def default_implementation_id(self, role: str) -> str:
        try:
            return self._defaults[role]
        except KeyError as exc:
            raise KeyError(f"unknown numerical solver role: {role}") from exc

    def set_default(self, role: str, implementation_id: str) -> None:
        implementations = self._implementations.get(role)
        if implementations is None or implementation_id not in implementations:
            raise KeyError(
                "unknown numerical solver implementation: "
                f"{role}/{implementation_id}"
            )
        self._defaults[role] = implementation_id

    def implementation(
        self,
        role: str,
        implementation_id: str | None = None,
    ) -> NumericalSolverImplementation:
        implementations = self._implementations.get(role)
        if implementations is None:
            raise KeyError(f"unknown numerical solver role: {role}")
        selected = implementation_id or self.default_implementation_id(role)
        try:
            return implementations[selected]
        except KeyError as exc:
            raise KeyError(
                "unknown numerical solver implementation: "
                f"{role}/{selected}"
            ) from exc

    def select(
        self,
        role: str,
        requirements: NumericalSolverRequirements,
    ) -> NumericalSolverImplementation:
        candidates = tuple(
            implementation
            for implementation in self.implementations(role)
            if implementation.satisfies(requirements)
        )
        if not candidates:
            raise LookupError(f"no numerical solver implementation satisfies requirements for role: {role}")
        default_id = self._defaults.get(role)
        return max(
            candidates,
            key=lambda implementation: (
                implementation.priority,
                implementation.implementation_id == default_id,
                not implementation.reference_implementation,
                implementation.effective_order or 0,
                implementation.implementation_id,
            ),
        )

    def solver_for(self, role: str, implementation_id: str | None = None) -> Callable[..., Any]:
        return self.implementation(role, implementation_id).solver

    def method_for(
        self,
        role: str,
        implementation_id: str | None = None,
    ) -> NumericalMethodDescriptor | NumericalPipelineDescriptor:
        return self.implementation(role, implementation_id).method


def fixed_step_record(
    method: NumericalMethodDescriptor | NumericalPipelineDescriptor,
    *,
    start_time: float,
    end_time: float,
    steps: int,
    state_size: int | None = None,
    tags: tuple[tuple[str, str], ...] = (),
) -> NumericalRunRecord:
    return NumericalRunRecord(
        method=method,
        start_time=float(start_time),
        end_time=float(end_time),
        steps=int(steps),
        state_size=state_size,
        tags=tags,
    )


__all__ = [
    "ExecutionKind",
    "NumericalExecutionDescriptor",
    "NumericalMethodDescriptor",
    "NumericalPipelineDescriptor",
    "NumericalRunRecord",
    "NumericalSolverImplementation",
    "NumericalSolverRegistry",
    "NumericalSolverRequirements",
    "TrackedNumericalResult",
    "fixed_step_record",
]
