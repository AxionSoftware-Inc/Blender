from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, TYPE_CHECKING, runtime_checkable

if TYPE_CHECKING:
    from spectra.domains.registry import DomainDependency, DomainRegistry


@runtime_checkable
class DomainModule(Protocol):
    """Contract for a pluggable scientific domain.

    A domain owns scientific semantics and compilers specific to one field
    (for example calculus, linear algebra, probability, statistics, or physics),
    while depending only on stable Spectra core/domain contracts.
    """

    @property
    def name(self) -> str:
        """Stable machine-readable domain name."""
        ...

    @property
    def version(self) -> str:
        """Domain contract/version identifier."""
        ...

    @property
    def dependencies(self) -> Iterable["DomainDependency"]:
        """Capabilities that must already exist before registration."""
        ...

    def register(self, registry: "DomainRegistry") -> None:
        """Register domain-owned semantic types, compilers, or capabilities."""
        ...
