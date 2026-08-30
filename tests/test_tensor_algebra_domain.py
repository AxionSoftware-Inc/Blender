import pytest

from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.tensor_algebra import Tensor


def test_tensor_domain_loads_from_catalog() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["tensor_algebra"])

    assert "tensor_algebra" in registry.domains
    assert registry.require("tensor.tensor") is Tensor


def test_tensor_outer_product_and_trace() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["tensor_algebra"])
    outer = registry.require("tensor.outer_product")
    trace = registry.require("tensor.trace")

    left = Tensor.vector((1.0, 2.0), name="left")
    right = Tensor.vector((3.0, 4.0, 5.0), name="right")
    product = outer(left, right)

    assert product.shape == (2, 3)
    assert product.values == pytest.approx((3.0, 4.0, 5.0, 6.0, 8.0, 10.0))

    matrix = Tensor.matrix(((1.0, 2.0), (3.0, 4.0)))
    traced = trace(matrix)
    assert traced.shape == ()
    assert traced.values == pytest.approx((5.0,))


def test_tensor_axis_permutation_and_contraction() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["tensor_algebra"])
    permute = registry.require("tensor.permute_axes")
    contract = registry.require("tensor.contract")

    tensor = Tensor(
        shape=(2, 2, 2),
        values=tuple(float(value) for value in range(8)),
        name="rank3",
    )
    permuted = permute(tensor, (2, 0, 1))
    assert permuted.shape == (2, 2, 2)
    assert permuted.at(1, 0, 1) == pytest.approx(tensor.at(0, 1, 1))

    identity_stack = Tensor(
        shape=(2, 2, 2),
        values=(1.0, 0.0, 0.0, 1.0, 2.0, 0.0, 0.0, 2.0),
    )
    contracted = contract(identity_stack, 1, 2)
    assert contracted.shape == (2,)
    assert contracted.values == pytest.approx((2.0, 4.0))
