from __future__ import annotations

import pytest

from spectra.domains import DomainRegistry
from spectra.domains.probability import ProbabilityDomain
from spectra.domains.statistics import Dataset1D, StatisticsDomain


def test_statistics_reuses_probability_for_empirical_distribution() -> None:
    registry = DomainRegistry()
    registry.add_domains([StatisticsDomain(), ProbabilityDomain()])

    dataset = Dataset1D.of([1.0, 1.0, 2.0, 4.0], name="sample")
    summarize = registry.require("statistics.summarize")
    summary = summarize(dataset)

    assert summary.count == 4
    assert summary.mean == pytest.approx(2.0)
    assert summary.minimum == 1.0
    assert summary.maximum == 4.0

    empirical = registry.require("statistics.empirical_distribution")(dataset)
    expectation = registry.require("probability.expectation")
    assert expectation(empirical) == pytest.approx(summary.mean)


def test_histogram_is_a_visualizable_statistics_semantic_object() -> None:
    registry = DomainRegistry()
    registry.add_domains([StatisticsDomain(), ProbabilityDomain()])

    dataset = Dataset1D.of([0.0, 0.1, 0.8, 1.0])
    histogram = registry.require("statistics.histogram")(dataset, bins=2)

    assert registry.can_visualize(histogram)
    scene = registry.compile_scene(histogram)
    assert len(scene.primitives) == 4
    assert scene.get("statistics.histogram.bin.0") is not None
