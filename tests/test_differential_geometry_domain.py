import math

from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.differential_geometry import MetricTensorField
from spectra.domains.tensor_algebra import Tensor


def test_differential_geometry_loads_through_builtin_catalog() -> None:
    registry = DomainRegistry()

    loaded = builtin_domain_catalog().load(registry, ["differential_geometry"])

    assert loaded == ("tensor_algebra", "linear_algebra", "differential_geometry")
    assert registry.has_capability("geometry.christoffel_symbols")


def test_euclidean_metric_has_zero_christoffel_symbols() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["differential_geometry"])
    metric = MetricTensorField.constant(((1.0, 0.0), (0.0, 1.0)))

    symbols = registry.require("geometry.christoffel_symbols")(metric, (0.0, 0.0))

    assert max(abs(value) for value in symbols.values) < 1e-9


def test_polar_metric_has_expected_non_zero_christoffel_symbols() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["differential_geometry"])
    metric = MetricTensorField(
        2,
        lambda point: Tensor.matrix(
            ((1.0, 0.0), (0.0, point[0] ** 2)),
            name="polar",
        ),
    )

    symbols = registry.require("geometry.christoffel_symbols")(metric, (2.0, 0.0))

    assert math.isclose(symbols.values[3], -2.0, rel_tol=1e-5)
    assert math.isclose(symbols.values[5], 0.5, rel_tol=1e-5)
    assert math.isclose(symbols.values[6], 0.5, rel_tol=1e-5)
