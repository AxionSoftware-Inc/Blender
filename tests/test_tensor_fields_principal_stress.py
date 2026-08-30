import pytest

from spectra.core.types import Vec3
from spectra.core.units import METER, PASCAL, Quantity
from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.linear_algebra import MatrixN, symmetric_eigendecomposition
from spectra.domains.mathematics import VectorField3D
from spectra.domains.physics import IsotropicElasticMaterial, StressTensor3D
from spectra.domains.tensor_algebra import Tensor


def test_symmetric_jacobi_eigensystem_orders_principal_values() -> None:
    result = symmetric_eigendecomposition(
        MatrixN.of(((3.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 2.0)))
    )
    assert result.converged
    assert result.eigenvalues == pytest.approx((3.0, 2.0, 1.0))
    for vector in result.eigenvectors:
        assert sum(value * value for value in vector.values) == pytest.approx(1.0)


def test_principal_stress_uses_generic_eigensystem() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.elasticity.principal"])
    stress = StressTensor3D(
        Tensor.matrix(
            ((30.0, 0.0, 0.0), (0.0, 20.0, 0.0), (0.0, 0.0, 10.0)),
            name="stress",
        ),
        PASCAL,
    )
    principal = registry.require("physics.elasticity.principal_stresses")(stress)
    assert principal.converged
    assert principal.values == pytest.approx((30.0, 20.0, 10.0))
    assert principal.maximum.value == pytest.approx(30.0)
    assert principal.maximum_shear.value == pytest.approx(10.0)


def test_elasticity_displacement_compiles_to_tensor_fields() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["physics.elasticity.fields"])
    displacement = VectorField3D(
        evaluator=lambda position: Vec3(0.01 * position.x, 0.0, 0.0),
        name="uniaxial_displacement",
        output_unit=METER,
    )
    material = IsotropicElasticMaterial(
        young_modulus=Quantity(1_000.0, PASCAL),
        poisson_ratio=0.25,
    )
    strain_field = registry.require(
        "physics.elasticity.strain_field_from_displacement"
    )(displacement)
    stress_field = registry.require(
        "physics.elasticity.stress_field_from_displacement"
    )(material, displacement)

    strain = strain_field.evaluate(Vec3(1.0, 0.0, 0.0))
    stress = stress_field.evaluate(Vec3(1.0, 0.0, 0.0))
    assert strain.at(0, 0) == pytest.approx(0.01, rel=1e-5)
    assert stress.shape == (3, 3)
    assert stress_field.output_unit == PASCAL
