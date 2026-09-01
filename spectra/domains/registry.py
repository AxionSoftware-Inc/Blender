from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

from spectra.core.scene import Scene
from spectra.numerics import (
    NumericalExecutionDescriptor,
    NumericalMethodDescriptor,
    NumericalPipelineDescriptor,
    NumericalSolverImplementation,
    NumericalSolverRegistry,
    NumericalSolverRequirements,
    ProblemPredicate,
)
from spectra.visualization import SceneCompiler, VisualizationRegistry

if TYPE_CHECKING:
    from spectra.domains.base import DomainModule


Compiler = Callable[[Any], Any]
Capability = Any


@dataclass(frozen=True)
class DomainDependency:
    """A stable, versioned capability dependency declared by a scientific domain."""

    capability: str
    optional: bool = False
    min_version: int = 1

    def __post_init__(self) -> None:
        if not self.capability:
            raise ValueError("dependency capability cannot be empty")
        if self.min_version < 1:
            raise ValueError("dependency min_version must be >= 1")


class DomainResolutionError(RuntimeError):
    pass


@dataclass
class _RegistrySnapshot:
    domains: dict[str, "DomainModule"]
    semantic_types: dict[str, type[Any]]
    compilers: dict[str, Compiler]
    capabilities: dict[str, Capability]
    capability_versions: dict[str, int]
    capability_providers: dict[str, str | None]
    numerical_solvers: NumericalSolverRegistry
    visualizations: VisualizationRegistry


@dataclass
class DomainRegistry:
    """Registry shared by independently-developed scientific domains."""

    domains: dict[str, "DomainModule"] = field(default_factory=dict)
    semantic_types: dict[str, type[Any]] = field(default_factory=dict)
    compilers: dict[str, Compiler] = field(default_factory=dict)
    capabilities: dict[str, Capability] = field(default_factory=dict)
    capability_versions: dict[str, int] = field(default_factory=dict)
    capability_providers: dict[str, str | None] = field(default_factory=dict)
    numerical_solvers: NumericalSolverRegistry = field(default_factory=NumericalSolverRegistry)
    visualizations: VisualizationRegistry = field(default_factory=VisualizationRegistry)
    _active_domain_name: str | None = field(default=None, init=False, repr=False)

    def _snapshot(self) -> _RegistrySnapshot:
        return _RegistrySnapshot(
            domains=dict(self.domains),
            semantic_types=dict(self.semantic_types),
            compilers=dict(self.compilers),
            capabilities=dict(self.capabilities),
            capability_versions=dict(self.capability_versions),
            capability_providers=dict(self.capability_providers),
            numerical_solvers=self.numerical_solvers.copy(),
            visualizations=self.visualizations.copy(),
        )

    def _restore(self, snapshot: _RegistrySnapshot) -> None:
        self.domains.clear()
        self.domains.update(snapshot.domains)
        self.semantic_types.clear()
        self.semantic_types.update(snapshot.semantic_types)
        self.compilers.clear()
        self.compilers.update(snapshot.compilers)
        self.capabilities.clear()
        self.capabilities.update(snapshot.capabilities)
        self.capability_versions.clear()
        self.capability_versions.update(snapshot.capability_versions)
        self.capability_providers.clear()
        self.capability_providers.update(snapshot.capability_providers)
        self.numerical_solvers = snapshot.numerical_solvers
        self.visualizations = snapshot.visualizations

    def add_domain(self, domain: "DomainModule") -> None:
        if domain.name in self.domains:
            raise ValueError(f"domain already registered: {domain.name}")

        dependencies = tuple(getattr(domain, "dependencies", ()))
        self.resolve_dependencies(dependencies)
        snapshot = self._snapshot()
        previous_active = self._active_domain_name

        try:
            self.domains[domain.name] = domain
            self._active_domain_name = domain.name
            domain.register(self)
        except Exception:
            self._restore(snapshot)
            raise
        finally:
            self._active_domain_name = previous_active

    def add_domains(self, domains: Iterable["DomainModule"]) -> None:
        """Register a set of domains in dependency-resolved, atomic order."""

        pending = list(domains)
        names = [domain.name for domain in pending]
        if len(names) != len(set(names)):
            raise ValueError("domain batch contains duplicate names")
        already_registered = set(names).intersection(self.domains)
        if already_registered:
            duplicate = sorted(already_registered)[0]
            raise ValueError(f"domain already registered: {duplicate}")

        snapshot = self._snapshot()
        try:
            while pending:
                progress = False
                next_pending: list["DomainModule"] = []

                for domain in pending:
                    required = tuple(
                        dependency
                        for dependency in getattr(domain, "dependencies", ())
                        if not dependency.optional
                    )
                    if all(
                        self.has_capability(
                            dependency.capability,
                            min_version=dependency.min_version,
                        )
                        for dependency in required
                    ):
                        self.add_domain(domain)
                        progress = True
                    else:
                        next_pending.append(domain)

                if progress:
                    pending = next_pending
                    continue

                missing_by_domain = {
                    domain.name: tuple(
                        self._dependency_label(dependency)
                        for dependency in getattr(domain, "dependencies", ())
                        if not dependency.optional
                        and not self.has_capability(
                            dependency.capability,
                            min_version=dependency.min_version,
                        )
                    )
                    for domain in next_pending
                }
                detail = "; ".join(
                    f"{name}: {', '.join(missing) if missing else 'unresolved dependency'}"
                    for name, missing in sorted(missing_by_domain.items())
                )
                raise DomainResolutionError(f"could not resolve domain dependencies: {detail}")
        except Exception:
            self._restore(snapshot)
            raise

    @staticmethod
    def _dependency_label(dependency: DomainDependency) -> str:
        if dependency.min_version <= 1:
            return dependency.capability
        return f"{dependency.capability}>={dependency.min_version}"

    def register_semantic_type(self, key: str, semantic_type: type[Any]) -> None:
        if key in self.semantic_types:
            raise ValueError(f"semantic type already registered: {key}")
        self.semantic_types[key] = semantic_type

    def register_compiler(self, key: str, compiler: Compiler) -> None:
        if key in self.compilers:
            raise ValueError(f"compiler already registered: {key}")
        self.compilers[key] = compiler

    def compiler_for(self, key: str) -> Compiler:
        try:
            return self.compilers[key]
        except KeyError as exc:
            raise KeyError(f"unknown compiler capability: {key}") from exc

    def register_visualization(
        self,
        semantic_type: type[Any],
        compiler: SceneCompiler,
    ) -> None:
        self.visualizations.register(semantic_type, compiler)

    def can_visualize(self, value_or_type: Any) -> bool:
        return self.visualizations.supports(value_or_type)

    def compile_scene(self, semantic_object: Any) -> Scene:
        return self.visualizations.compile(semantic_object)

    def provide(self, key: str, capability: Capability, *, version: int = 1) -> None:
        if not key:
            raise ValueError("capability key cannot be empty")
        if version < 1:
            raise ValueError("capability version must be >= 1")
        if key in self.capabilities:
            raise ValueError(f"capability already registered: {key}")
        self.capabilities[key] = capability
        self.capability_versions[key] = version
        self.capability_providers[key] = self._active_domain_name

    def register_numerical_solver(
        self,
        role: str,
        implementation_id: str,
        solver: Callable[..., Any],
        method: NumericalMethodDescriptor | NumericalPipelineDescriptor,
        *,
        make_default: bool = False,
        priority: int = 0,
        tags: tuple[str, ...] = (),
        execution: NumericalExecutionDescriptor | None = None,
        supports_problem: ProblemPredicate | None = None,
    ) -> None:
        """Register one selectable implementation for a stable solver role."""

        self.numerical_solvers.register(
            NumericalSolverImplementation(
                role=role,
                implementation_id=implementation_id,
                solver=solver,
                method=method,
                provider_domain=self._active_domain_name,
                priority=priority,
                tags=tags,
                execution=execution or NumericalExecutionDescriptor(),
                supports_problem=supports_problem,
            ),
            make_default=make_default,
        )

    def numerical_solver_for(
        self,
        role: str,
        implementation_id: str | None = None,
    ) -> Callable[..., Any]:
        return self.numerical_solvers.solver_for(role, implementation_id)

    def numerical_solver_method(
        self,
        role: str,
        implementation_id: str | None = None,
    ) -> NumericalMethodDescriptor | NumericalPipelineDescriptor:
        return self.numerical_solvers.method_for(role, implementation_id)

    def numerical_solver_implementations(
        self,
        role: str,
    ) -> tuple[NumericalSolverImplementation, ...]:
        return self.numerical_solvers.implementations(role)

    def select_numerical_solver(
        self,
        role: str,
        requirements: NumericalSolverRequirements,
    ) -> NumericalSolverImplementation:
        return self.numerical_solvers.select(role, requirements)

    def select_numerical_solver_for_problem(
        self,
        role: str,
        problem: Any,
        requirements: NumericalSolverRequirements,
    ) -> NumericalSolverImplementation:
        return self.numerical_solvers.select_for_problem(role, problem, requirements)

    def set_default_numerical_solver(self, role: str, implementation_id: str) -> None:
        self.numerical_solvers.set_default(role, implementation_id)

    def has_capability(self, key: str, *, min_version: int = 1) -> bool:
        return key in self.capabilities and self.capability_versions.get(key, 1) >= min_version

    def capability_version(self, key: str) -> int:
        if key not in self.capabilities:
            raise KeyError(f"capability is not registered: {key}")
        return self.capability_versions.get(key, 1)

    def capability_provider(self, key: str) -> str | None:
        if key not in self.capabilities:
            raise KeyError(f"capability is not registered: {key}")
        return self.capability_providers.get(key)

    def provided_capabilities(self, domain_name: str) -> tuple[str, ...]:
        if domain_name not in self.domains:
            raise KeyError(f"domain is not registered: {domain_name}")
        return tuple(
            key
            for key in self.capabilities
            if self.capability_providers.get(key) == domain_name
        )

    def require(self, key: str, *, min_version: int = 1) -> Capability:
        try:
            capability = self.capabilities[key]
        except KeyError as exc:
            raise KeyError(f"required capability is not registered: {key}") from exc
        version = self.capability_versions.get(key, 1)
        if version < min_version:
            raise KeyError(
                f"required capability version is not available: {key}>={min_version} "
                f"(registered v{version})"
            )
        return capability

    def resolve_dependencies(self, dependencies: Iterable[DomainDependency]) -> dict[str, Capability]:
        resolved: dict[str, Capability] = {}
        for dependency in dependencies:
            if self.has_capability(
                dependency.capability,
                min_version=dependency.min_version,
            ):
                resolved[dependency.capability] = self.capabilities[dependency.capability]
            elif not dependency.optional:
                registered_version = self.capability_versions.get(dependency.capability)
                if registered_version is None:
                    raise KeyError(
                        f"required capability is not registered: {dependency.capability}"
                    )
                raise KeyError(
                    "required capability version is not available: "
                    f"{dependency.capability}>={dependency.min_version} "
                    f"(registered v{registered_version})"
                )
        return resolved
