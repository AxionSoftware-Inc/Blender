from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from spectra.domains.base import DomainModule


Compiler = Callable[[Any], Any]


@dataclass
class DomainRegistry:
    """Registry shared by independently-developed scientific domains.

    The registry intentionally knows nothing about calculus, probability,
    statistics, physics, or any other particular field. Domains publish
    capabilities under stable string keys and can evolve independently.
    """

    domains: dict[str, "DomainModule"] = field(default_factory=dict)
    semantic_types: dict[str, type[Any]] = field(default_factory=dict)
    compilers: dict[str, Compiler] = field(default_factory=dict)

    def add_domain(self, domain: "DomainModule") -> None:
        if domain.name in self.domains:
            raise ValueError(f"domain already registered: {domain.name}")
        self.domains[domain.name] = domain
        domain.register(self)

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
