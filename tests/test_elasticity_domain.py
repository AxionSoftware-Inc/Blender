import pytest

from spectra.core.types import Vec3
from spectra.core.units import METER, PASCAL, Quantity
from spectra.domains.calculus.jacobian3d import Jacobian3DDomain
from spectra.domains.linear_algebra import LinearAlgebraDomain
from spectra.domains.mathematics import MathematicsDomain
from spectra.domains.mathematics.fields import VectorField3D
from spectra.domains.physics.elasticity import (
    ElasticityDomain,
    IsotropicElasticMaterial,
    StressTensor3D,
    von_mises_stress,
)
from spectra.domains.registry import DomainRegistry
from spectra.domains.tensor_algebra import Tensor, TensorAlgebraDomain


def test_small_strain_from_linear_displacement_field() -> None:
    registry = DomainRegistry()
    registry.add_domains(
        (
            ElasticityDomain(),
            Jacobian3DDomain(),
            TensorAlgebraDomain(),
            LinearAlgebraDomain(),
            MathematicsDomain(),
        )
    )
    displacement = VectorField3D(
        lambda point: Vec3(0.01 * point.x, 0.0, 0.0),
        output_unit=METER,
    )
    strain = registry.require("physics.elasticity.small_strain_at")(
        displacement,
        Vec3(1.0, 2.0, 3.0),
    )
    assert strain.tensor.at(0, 0) == pytest.approx(0.01, rel=1e-5)
    assert strain.tensor.at(1, 1) == pytest.approx(0.0, abs=1e-10)
    assert strain.tensor.at(0, 1) == pytest.approx(0.0, abs=1e-10)

    material = IsotropicElasticMaterial(Quantity(200e9, PASCAL), 0.3)
    stress = registry.require("physics.elasticity.stress_from_strain")(material, strain)
    assert stress.tensor.at(0, 0) > 0.0


def test_von_mises_uniaxial_stress_equals_axial_stress() -> None:
    stress = StressTensor3D(
        Tensor.matrix(
            (
                (100.0, 0.0, 0.0),
                (0.0, 0.0, 0.0),
                (0.0, 0.0, 0.0),
            ),
            name="uniaxial",
        ),
        PASCAL,
    )
    assert von_mises_stress(stress).to(PASCAL).value == pytest.approx(100.0)
