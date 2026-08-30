from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import sqrt
from typing import Iterable

from spectra.domains.registry import DomainDependency, DomainRegistry


@dataclass(frozen=True, slots=True)
class Dataset1D:
    values: tuple[float, ...]
    name: str = "dataset"

    def __post_init__(self) -> None:
        if not self.values:
            raise ValueError("dataset must contain at least one value")

    @classmethod
    def of(cls, values: Iterable[float], *, name: str = "dataset") -> "Dataset1D":
        return cls(tuple(float(value) for value in values), name=name)

    @property
    def size(self) -> int:
        return len(self.values)


@dataclass(frozen=True, slots=True)
class SummaryStatistics:
    count: int
    mean: float
    variance: float
    standard_deviation: float
    minimum: float
    maximum: float


@dataclass(frozen=True, slots=True)
class HistogramBin:
    left: float
    right: float
    count: int

    def __post_init__(self) -> None:
        if self.right <= self.left:
            raise ValueError("histogram bin right edge must be greater than left edge")
        if self.count < 0:
            raise ValueError("histogram bin count cannot be negative")


@dataclass(frozen=True, slots=True)
class Histogram:
    bins: tuple[HistogramBin, ...]
    total_count: int
    name: str = "histogram"

    def __post_init__(self) -> None:
        if not self.bins:
            raise ValueError("histogram must contain at least one bin")
        if self.total_count <= 0:
            raise ValueError("histogram total_count must be positive")
        if sum(bin_.count for bin_ in self.bins) != self.total_count:
            raise ValueError("histogram bin counts must sum to total_count")


def mean(dataset: Dataset1D) -> float:
    return sum(dataset.values) / dataset.size


def sample_variance(dataset: Dataset1D) -> float:
    if dataset.size < 2:
        raise ValueError("sample variance requires at least two observations")
    center = mean(dataset)
    return sum((value - center) ** 2 for value in dataset.values) / (dataset.size - 1)


def summarize(dataset: Dataset1D) -> SummaryStatistics:
    center = mean(dataset)
    variance = 0.0 if dataset.size == 1 else sample_variance(dataset)
    return SummaryStatistics(
        count=dataset.size,
        mean=center,
        variance=variance,
        standard_deviation=sqrt(variance),
        minimum=min(dataset.values),
        maximum=max(dataset.values),
    )


def histogram(dataset: Dataset1D, *, bins: int = 10) -> Histogram:
    if bins < 1:
        raise ValueError("bins must be >= 1")

    minimum = min(dataset.values)
    maximum = max(dataset.values)
    if minimum == maximum:
        half_width = 0.5
        return Histogram(
            bins=(HistogramBin(minimum - half_width, maximum + half_width, dataset.size),),
            total_count=dataset.size,
            name=f"{dataset.name}.histogram",
        )

    width = (maximum - minimum) / bins
    counts = [0 for _ in range(bins)]
    for value in dataset.values:
        index = int((value - minimum) / width)
        if index == bins:
            index -= 1
        counts[index] += 1

    histogram_bins = tuple(
        HistogramBin(
            minimum + width * index,
            minimum + width * (index + 1),
            count,
        )
        for index, count in enumerate(counts)
    )
    return Histogram(
        bins=histogram_bins,
        total_count=dataset.size,
        name=f"{dataset.name}.histogram",
    )


class StatisticsDomain:
    name = "statistics"
    version = "1"
    dependencies = (
        DomainDependency("probability.discrete_distribution"),
    )

    def register(self, registry: DomainRegistry) -> None:
        from spectra.domains.statistics.visualization import compile_histogram_scene

        distribution_type = registry.require("probability.discrete_distribution")

        def empirical_distribution(dataset: Dataset1D):
            counts = Counter(dataset.values)
            total = float(dataset.size)
            pairs = tuple(
                (value, count / total)
                for value, count in sorted(counts.items())
            )
            return distribution_type.from_pairs(pairs)

        registry.register_semantic_type("statistics.dataset1d", Dataset1D)
        registry.register_semantic_type("statistics.summary", SummaryStatistics)
        registry.register_semantic_type("statistics.histogram", Histogram)

        registry.provide("statistics.dataset1d", Dataset1D)
        registry.provide("statistics.mean", mean)
        registry.provide("statistics.sample_variance", sample_variance)
        registry.provide("statistics.summarize", summarize)
        registry.provide("statistics.histogram", histogram)
        registry.provide("statistics.empirical_distribution", empirical_distribution)

        registry.register_visualization(Histogram, compile_histogram_scene)
