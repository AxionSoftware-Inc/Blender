# Spectra Science — Initial Structured Diagnostic Code Matrix

Status: **design code vocabulary; runtime diagnostic classes are not implemented yet**.

This document turns `DIAGNOSTICS_AND_ERRORS.md` into a concrete first set of stable machine-readable diagnostic codes for UI, CLI, project validation, plugins, numerical providers, presentation, and renderer backends.

Codes describe failure class. Human messages may evolve/localize independently.

## Code format

Recommended:

```text
<category>.<specific_code>
```

Examples:

```text
validation.unit_mismatch
capability.missing_provider
numerical.unsupported_problem
presentation.required_feature_unavailable
backend.resource_update_failed
```

Do not encode Python class/module names into durable diagnostic identity.

## Common fields

Conceptual diagnostic record:

```python
Diagnostic(
    code: str,
    severity: str,
    message: str,
    subject_id: str | None = None,
    details: tuple[tuple[str, str], ...] = (),
    cause_code: str | None = None,
)
```

Optional structured extensions may carry typed values later.

## Validation

### `validation.non_finite_value`

Use when input/state contains NaN/inf where finite values are required.

### `validation.unit_mismatch`

Expected dimension differs from supplied quantity/unit.

Include:

```text
parameter
expected dimension
actual dimension/unit
```

### `validation.shape_mismatch`

Array/vector/grid/state dimensions incompatible.

### `validation.empty_required_value`

Required state/list/name/value is empty.

### `validation.invalid_interval`

Examples:

```text
end_time <= start_time
minimum >= maximum
invalid ordered range
```

### `validation.invalid_choice`

Enum/boundary/mode outside supported vocabulary.

### `validation.duplicate_id`

Persistent/project/Scene/plugin/resource identity collision.

### `validation.broken_reference`

A stable ID references a missing model/result/view/resource/primitive/material/etc.

## Capability/domain catalog

### `capability.missing_provider`

No provider is discoverable for required capability.

### `capability.version_mismatch`

Provider exists but version < required minimum.

### `capability.provider_conflict`

More than one provider claims a capability that must be unique.

### `capability.dependency_cycle`

Domain/provider closure contains a cycle.

### `capability.registration_failed`

Domain registration threw before completing.

### `capability.registration_rolled_back`

Informational/error detail indicating transactional rollback restored registry state.

### `capability.unknown_domain`

Requested domain name absent from catalog.

### `capability.unknown_capability`

Requested capability not loaded/discoverable in the relevant operation.

## Solver selection

### `numerical.no_solver_match`

No implementation satisfies policy/requirements/problem compatibility.

Attach candidate rejection records.

### `numerical.unsupported_problem`

Explicit implementation selected but compatibility predicate rejects the semantic problem.

### `numerical.execution_kind_unavailable`

Requested `cpu/gpu/external/...` kind absent.

### `numerical.precision_unavailable`

Requested precision not provided.

### `numerical.order_requirement_unsatisfied`

No solver meets minimum formal order.

### `numerical.adaptive_requirement_unsatisfied`

Adaptive/fixed requirement cannot be met.

### `numerical.required_tag_missing`

Provider missing required feature/tag.

### `numerical.provider_unavailable`

Provider package/native library/device is known but unavailable at runtime.

## Numerical execution

### `numerical.invalid_step_count`

Requested fixed steps/hint invalid.

### `numerical.derivative_dimension_mismatch`

ODE derivative output size differs from state.

### `numerical.non_finite_result`

Solver produced non-finite state/result.

### `numerical.convergence_failed`

Iterative/adaptive operation could not meet declared convergence/tolerance contract.

### `numerical.iteration_limit`

Maximum iterations reached.

### `numerical.linear_solve_failed`

Internal linear system solve failed/singular outside allowed handling.

### `numerical.out_of_memory`

Execution provider cannot allocate required memory.

### `numerical.device_lost`

GPU/external execution device became unavailable.

### `numerical.native_execution_failed`

Native provider returned failure not represented by a more specific code.

### `numerical.cancelled`

Cooperative operation cancelled.

## Stability/conservation

These are usually warning/info rather than hard errors.

### `stability.cfl_exceeded`

### `stability.diffusion_limit_exceeded`

### `stability.divergence_residual_high`

### `stability.energy_drift_high`

### `stability.continuity_residual_high`

Details should state whether threshold is mathematical, heuristic, project policy, or user configured.

## Convergence experiments

### `convergence.invalid_refinement_sequence`

### `convergence.reference_unavailable`

### `convergence.observed_order_unavailable`

Examples: zero errors or insufficient valid samples.

### `convergence.order_below_expectation`

### `convergence.adaptive_solver_not_supported`

Fixed-step refinement study given adaptive implementation.

## Experiment execution

### `experiment.case_failed`

Case failure in record mode.

### `experiment.metric_missing`

Requested metric absent for a successful case/output.

### `experiment.metric_unit_mismatch`

Metric aggregation/comparison incompatible by dimension.

### `experiment.batch_output_count_mismatch`

Batched evaluator returned different count from requested cases.

### `experiment.no_valid_cases`

Analysis/calibration/Pareto has no usable cases.

### `experiment.calibration_no_candidate`

No valid candidate can be ranked/fitted.

### `experiment.invalid_weights`

Uncertainty/calibration weights invalid/non-positive/not normalizable according to contract.

## Reproducibility/artifacts

### `reproducibility.environment_mismatch`

Current environment fingerprint differs from artifact expectation where equality is required.

### `reproducibility.fingerprint_mismatch`

Serialized payload/environment fingerprint does not match canonical recomputation.

### `serialization.unknown_schema`

Unknown schema ID.

### `serialization.unsupported_version`

Known schema but unsupported version.

### `serialization.malformed_payload`

Required structural fields/types invalid.

### `serialization.non_finite_value`

Persistent artifact contains disallowed NaN/inf.

### `serialization.checksum_mismatch`

External resource/artifact checksum fails.

## Project runtime

### `project.missing_model`

### `project.missing_result`

### `project.missing_view`

### `project.missing_presentation`

Use specific stable ID in details.

### `project.result_stale`

Result fingerprint/revision no longer matches current model/solver selection.

### `project.view_stale`

View depends on stale/missing result.

### `project.presentation_stale`

Presentation depends on stale/missing view.

### `project.remote_result_revision_mismatch`

Late remote artifact belongs to an older model revision/fingerprint.

### `project.environment_requirement_unsatisfied`

Project requires capability/plugin not currently satisfied.

## Plugin runtime

### `plugin.duplicate_id`

### `plugin.version_incompatible`

### `plugin.missing_required_plugin`

### `plugin.dependency_cycle`

### `plugin.domain_name_conflict`

### `plugin.capability_provider_conflict`

### `plugin.activation_failed`

### `plugin.disabled`

Requested capability belongs to known but disabled plugin.

### `plugin.trust_not_granted`

Application/user has not allowed executable plugin/native provider activation.

Important: project parse never emits “auto-install failed” because project parsing must not auto-install code.

## Presentation

### `presentation.empty_bounds`

Auto-fit requested but no scientific bounds available.

This may be info/warning if empty Scene is valid.

### `presentation.invalid_camera_policy`

### `presentation.invalid_color_range`

### `presentation.color_semantics_missing`

Quantitative legend/color requested without enough semantic metadata to choose faithful scale/range.

### `presentation.required_feature_unavailable`

Backend cannot express a REQUIRED presentation/scientific display feature.

### `presentation.preferred_feature_fallback`

Informational/warning: requested preferred feature degraded deterministically.

### `presentation.animation_track_conflict`

Presentation wants `(target_id, property_path)` already owned by scientific timeline.

Default action: scientific track wins; presentation effect skipped.

### `presentation.quantitative_surface_attributes_unavailable`

Current Scene/backend cannot faithfully represent requested continuous Surface values.

### `presentation.display_decimation_active`

Info/warning with explicit display sample counts; numerical resolution unchanged.

## Backend generic

### `backend.unsupported_primitive`

Scene primitive kind unsupported by backend capabilities.

### `backend.required_capability_missing`

Backend feature profile cannot meet required representation.

### `backend.create_failed`

### `backend.update_failed`

### `backend.destroy_failed`

### `backend.session_closed`

Operation attempted after session close.

### `backend.resource_update_failed`

Specific native resource could not update/rebuild.

### `backend.resource_leak_detected`

Validation/stress tooling observed growing owned native resources.

## Blender-specific developer details

Durable top-level code should remain generic where possible:

```text
backend.update_failed
```

Details may include backend=`blender` and native context.

Avoid making generic UI depend on codes such as:

```text
blender.geometry_nodes_socket_missing
```

unless a backend-private diagnostic inspector needs them. Such subcodes can live in details/internal diagnostic namespace.

## Native provider details

Likewise public/durable code:

```text
numerical.provider_unavailable
numerical.native_execution_failed
numerical.device_lost
```

Provider-private native status/error number can be attached in details.

## Severity defaults

Suggested default mapping:

```text
validation.*                         error
capability.missing_provider          error
capability.registration_rolled_back  info/error-context
numerical.no_solver_match            error
stability.*                          warning by default
convergence.order_below_expectation  warning/error depending test policy
experiment.case_failed               warning in record mode, error in raise mode
serialization.*                      error
plugin.missing_required_plugin       error for solve, warning for metadata-only open
presentation.preferred_feature_fallback warning/info
presentation.required_feature_unavailable error
backend.resource_leak_detected       error/fatal in validation suite
```

Application surface may escalate/de-escalate where contract explicitly allows, but should not turn scientific invalidity into success.

## Candidate rejection detail

For `numerical.no_solver_match`, retain structured candidate reasons:

```json
{
  "role": "ode.first_order",
  "candidates": [
    {
      "implementation": "rk4.reference",
      "reasons": ["adaptive_required"]
    },
    {
      "implementation": "rk45.reference",
      "reasons": ["reference_disallowed"]
    }
  ]
}
```

Do not make users guess why fallback/selection failed.

## Stability of codes

Once exposed through project/CLI/plugin APIs:

- adding a new code is backward compatible;
- changing human wording is compatible;
- renaming/removing a code requires deprecation/mapping;
- changing semantic meaning of an existing code is breaking.

## Success criterion

The same failure should be classifiable consistently whether surfaced in Blender UI, standalone app, CLI, Python, remote worker, or AI orchestration, while preserving detailed technical causes for developers.