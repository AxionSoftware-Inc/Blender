import pytest

from spectra.core.types import Vec3
from spectra.domains import DomainRegistry
from spectra.domains.calculus import CalculusDomain
from spectra.domains.mathematics import MathematicsDomain, ScalarField3D, VectorField3D


def test_gradient_divergence_and_curl_are_domain_capabilities() -> None:
    registry = DomainRegistry()
    registry.add_domains([CalculusDomain(), MathematicsDomain()])

    gradient_at = registry.require("calculus.gradient_at", min_version=1)
    divergence_at = registry.require("calculus.divergence_at", min_version=1)
    curl_at = registry.require("calculus.curl_at", min_version=1)

    scalar = ScalarField3D(
        lambda p: p.x * p.x + p.y * p.y + p.z * p.z,
        name="quadratic",
    )
    radial = VectorField3D(lambda p: Vec3(p.x, p.y, p.z), name="radial")
    rotation = VectorField3D(lambda p: Vec3(-p.y, p.x, 0.0), name="rotation")

    point = Vec3(1.5, -2.0, 0.5)
    gradient = gradient_at(scalar, point)
    assert gradient.x == pytest.approx(3.0, rel=1e-5)
    assert gradient.y == pytest.approx(-4.0, rel=1e-5)
    assert gradient.z == pytest.approx(1.0, rel=1e-5)

    assert divergence_at(radial, point) == pytest.approx(3.0, rel=1e-5)

    curl = curl_at(rotation, point)
    assert curl.x == pytest.approx(0.0, abs=1e-8)
    assert curl.y == pytest.approx(0.0, abs=1e-8)
    assert curl.z == pytest.approx(2.0, rel=1e-5)


def test_vector_calculus_validates_finite_difference_step() -> None:
    field = ScalarField3D(lambda p: p.x)
    registry = DomainRegistry()
    registry.add_domains([MathematicsDomain(), CalculusDomain()])
    gradient_at = registry.require("calculus.gradient_at")

    with pytest.raises(ValueError, match="finite and positive"):
        gradient_at(field, Vec3(0.0, 0.0, 0.0), step=0.0)
