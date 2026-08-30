from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class DomainModule(Protocol):
    """Contract for a pluggable scientific domain.

    A domain owns scientific semantics and compilers specific to one field
    (for example calculus, linear algebra, probability, statistics, or physics),
    while depending only on stable Spectra core contracts.
    """

    @property
    def name(self) -> str:
        """Stable machine-readable domain name."""
        ...

    @property
    def version(self) -> str:
        """Domain contract/version identifier."""
        ...

    def register(self, registry: "DomainRegistry") -> None:
        """Register domain-owned semantic types, compilers, or capabilities."""
        ...


from spectra.domains.registry import DomainRegistry  # noqa: E402  (protocol typing cycle)
