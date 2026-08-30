import math

import pytest

from spectra.core.primitives import Polyline
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.mathematics import Interval


def test_spatial_quantum_auto_loads_math_calculus_and_continuous_probability() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.quantum.spatial"])

    assert "physics.quantum.spatial" in registry.domains
    assert "mathematics" in registry.domains
    assert "calculus" in registry.domains
    assert "probability.continuous" in registry.domains


def test_gaussian_wavefunction_normalizes_and_produces_position_probability() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.quantum.spatial"])

    make_wavefunction = registry.require("physics.quantum.spatial.make_wavefunction")
    position_distribution = registry.require(
        "physics.quantum.spatial.position_distribution"
    )
    probability_between = registry.require(
        "physics.quantum.spatial.probability_between"
    )
    integrate = registry.require("calculus.integrate", min_version=3)

    wavefunction = make_wavefunction(
        lambda x: complex(math.exp(-(x * x)), 0.0),
        Interval(-5.0, 5.0),
        name="gaussian",
        integration_steps=1024,
    )
    normalized_mass = integrate(
        wavefunction.function.magnitude_squared(),
        steps=1024,
    )
    assert normalized_mass == pytest.approx(1.0, rel=1e-6)

    distribution = position_distribution(wavefunction)
    assert distribution.normalization == pytest.approx(1.0, rel=1e-5)
    central_probability = probability_between(wavefunction, -1.0, 1.0)
    assert 0.9 < central_probability < 1.0

    scene = registry.compile_scene(wavefunction)
    assert len(scene.primitives) == 3
    assert all(isinstance(primitive, Polyline) for primitive in scene.primitives)
    assert scene.get("gaussian.probability_density").points[len(scene.get("gaussian.probability_density").points) // 2].y > 0.0
