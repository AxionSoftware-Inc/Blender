from spectra.domains.base import DomainModule
from spectra.domains.builtin_catalog import builtin_domain_catalog
from spectra.domains.catalog import DomainCatalog, DomainDescriptor
from spectra.domains.registry import DomainDependency, DomainRegistry, DomainResolutionError

__all__ = [
    "DomainCatalog",
    "DomainDependency",
    "DomainDescriptor",
    "DomainModule",
    "DomainRegistry",
    "DomainResolutionError",
    "builtin_domain_catalog",
]
