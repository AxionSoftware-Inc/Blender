from __future__ import annotations

from spectra.domains.catalog import DomainCatalog
from spectra.domains.discovery import discover_domain_factories, inferred_domain_tags


# Compatibility/public introspection symbols. The source of truth is now the
# actual set of Domain classes defined under spectra.domains rather than a
# hand-maintained duplicate list in this module.
BUILTIN_DOMAIN_FACTORIES = discover_domain_factories()
BUILTIN_DOMAIN_TAGS = inferred_domain_tags(BUILTIN_DOMAIN_FACTORIES)


def builtin_domain_catalog() -> DomainCatalog:
    """Build the bundled provider catalog from discovered registration contracts.

    Domain discovery finds concrete zero-argument ``...Domain`` classes under
    ``spectra.domains``. ``DomainCatalog.from_factories`` then probe-loads those
    domains transactionally and derives capability ownership from their actual
    ``registry.provide()`` calls. Adding a built-in scientific domain therefore
    no longer requires synchronizing a central capability manifest or factory
    list.
    """

    return DomainCatalog.from_factories(
        BUILTIN_DOMAIN_FACTORIES,
        tags=BUILTIN_DOMAIN_TAGS,
    )
