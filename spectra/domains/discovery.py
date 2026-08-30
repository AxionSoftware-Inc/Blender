from __future__ import annotations

from functools import lru_cache
import importlib
import inspect
import pkgutil
from types import ModuleType

from spectra.domains.base import DomainModule


_INFRASTRUCTURE_MODULES = {
    "spectra.domains.base",
    "spectra.domains.registry",
    "spectra.domains.catalog",
    "spectra.domains.discovery",
    "spectra.domains.builtin_catalog",
}


def _candidate_domain_classes(module: ModuleType):
    for _name, candidate in inspect.getmembers(module, inspect.isclass):
        if candidate.__module__ != module.__name__:
            continue
        if not candidate.__name__.endswith("Domain"):
            continue
        yield candidate


def _module_names(package_name: str) -> tuple[str, ...]:
    package = importlib.import_module(package_name)
    package_path = getattr(package, "__path__", None)
    if package_path is None:
        raise ValueError(f"domain discovery root is not a package: {package_name}")
    return tuple(
        info.name
        for info in pkgutil.walk_packages(package_path, prefix=f"{package_name}.")
        if info.name not in _INFRASTRUCTURE_MODULES
    )


@lru_cache(maxsize=None)
def discover_domain_factories(
    package_name: str = "spectra.domains",
) -> tuple[type[DomainModule], ...]:
    """Discover zero-argument DomainModule classes under a package.

    Discovery is deliberately convention-based but narrow: a class must be
    defined by the module being inspected, end in ``Domain``, instantiate with
    no arguments, and satisfy the runtime DomainModule protocol. Re-exported
    classes are ignored, so package ``__init__`` modules do not create duplicate
    providers. Results are sorted by the instantiated stable domain name.
    """

    discovered: list[tuple[str, type[DomainModule]]] = []
    for module_name in _module_names(package_name):
        module = importlib.import_module(module_name)
        for candidate in _candidate_domain_classes(module):
            try:
                instance = candidate()
            except TypeError as exc:
                raise TypeError(
                    f"discovered domain class must support zero-argument construction: "
                    f"{module_name}.{candidate.__name__}"
                ) from exc
            if not isinstance(instance, DomainModule):
                raise TypeError(
                    f"discovered class does not satisfy DomainModule: "
                    f"{module_name}.{candidate.__name__}"
                )
            if not instance.name:
                raise ValueError(
                    f"discovered domain has empty stable name: "
                    f"{module_name}.{candidate.__name__}"
                )
            discovered.append((instance.name, candidate))

    names = [name for name, _factory in discovered]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(
            "domain auto-discovery found duplicate stable names: "
            + ", ".join(duplicates)
        )

    discovered.sort(key=lambda item: item[0])
    return tuple(factory for _name, factory in discovered)


def inferred_domain_tags(
    factories: tuple[type[DomainModule], ...],
) -> dict[str, tuple[str, ...]]:
    """Infer lightweight discovery tags from stable dotted domain names."""

    result: dict[str, tuple[str, ...]] = {}
    for factory in factories:
        name = factory().name
        parts = tuple(part.replace("_", "-") for part in name.split(".") if part)
        result[name] = tuple(dict.fromkeys(parts))
    return result
