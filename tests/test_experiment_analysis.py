from spectra.domains import DomainRegistry, builtin_domain_catalog
from spectra.domains.experiments import MetricObjective, MetricSpec, ParameterAxis, ParameterSweep


def _design_experiment(registry: DomainRegistry):
    run = registry.require("experiments.run_sweep")
    sweep = ParameterSweep(
        axes=(ParameterAxis("design", ("A", "B", "C", "D")),),
        name="designs",
    )
    data = {
        "A": {"cost": 1.0, "error": 4.0, "throughput": 10.0},
        "B": {"cost": 2.0, "error": 2.0, "throughput": 20.0},
        "C": {"cost": 4.0, "error": 1.0, "throughput": 30.0},
        "D": {"cost": 5.0, "error": 3.0, "throughput": 15.0},
    }
    return run(
        sweep,
        lambda parameters: data[parameters["design"]],
        metrics=(
            MetricSpec("cost", lambda output, _parameters: output["cost"]),
            MetricSpec("error", lambda output, _parameters: output["error"]),
            MetricSpec("throughput", lambda output, _parameters: output["throughput"]),
        ),
    )


def test_experiment_ranking_respects_objective_direction() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["experiments.analysis"])
    experiment = _design_experiment(registry)
    rank = registry.require("experiments.rank_cases")
    best = registry.require("experiments.best_case")

    error_ranking = rank(experiment, MetricObjective("error", "minimize"))
    throughput_ranking = rank(experiment, MetricObjective("throughput", "maximize"))

    assert tuple(item.case.case.as_dict()["design"] for item in error_ranking) == (
        "C",
        "B",
        "D",
        "A",
    )
    assert throughput_ranking[0].case.case.as_dict()["design"] == "C"
    assert best(experiment, MetricObjective("cost", "minimize")).case.as_dict()["design"] == "A"


def test_pareto_front_removes_dominated_designs() -> None:
    registry = DomainRegistry()
    builtin_domain_catalog().load(registry, ["experiments.analysis"])
    experiment = _design_experiment(registry)
    pareto = registry.require("experiments.pareto_front")

    front = pareto(
        experiment,
        (
            MetricObjective("cost", "minimize"),
            MetricObjective("error", "minimize"),
        ),
    )

    assert tuple(case.case.as_dict()["design"] for case in front.cases) == (
        "A",
        "B",
        "C",
    )
