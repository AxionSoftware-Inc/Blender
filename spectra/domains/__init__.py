from spectra.domains.base import DomainModule
from spectra.domains.catalog import DomainCatalog, DomainDescriptor
from spectra.domains.registry import DomainDependency, DomainRegistry, DomainResolutionError


def builtin_domain_catalog() -> DomainCatalog:
    """Build the bundled domain catalog only when explicitly requested."""
    from spectra.domains.builtin_catalog import builtin_domain_catalog as build_catalog

    return build_catalog()


__all__ = [
    "DomainCatalog",
    "DomainDependency",
    "DomainDescriptor",
    "DomainModule",
    "DomainRegistry",
    "DomainResolutionError",
    "builtin_domain_catalog",
]
