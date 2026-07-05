# Compatibility Dataset V3 Independent Validity Calibration Scope Plan

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_independent_validity_calibration_scope_plan/
status = h002_compatibility_dataset_v3_independent_validity_calibration_scope_plan_select_support_contact_balancing
selected_path = calibration_metric_audit_passed_select_support_contact_family_balancing
validation_errors = 0
next_todo = compatibility_dataset_v3_independent_validity_support_contact_balancing_plan
```

## Why This Step Was Needed

직전 repaired independent-validity smoke에서는 `M6_TG_compatibility_interaction`이
AUROC `0.995633`으로 강했지만, runner가 보고한 `ECE-10 = 0.480112` 때문에 calibrated
posterior claim은 막혀 있었다.

이번 단계의 목적은 두 가지였다.

- 이 `ECE-10`이 실제 calibration failure인지 확인한다.
- calibration repair, support/contact balancing, Docker promotion 중 다음 route를 선택한다.

## Calibration Audit

기존 runner의 `ECE-10`은 binary probability calibration metric으로 쓰기 어렵다. 해당 helper는
raw positive-class score를 threshold correctness와 비교하므로, negative row에서 낮은 positive
score를 낸 좋은 prediction도 낮은 confidence처럼 취급할 수 있다.

따라서 표준적인 bin-wise probability ECE와 confidence ECE를 다시 계산했다.

```text
M6 legacy runner ECE-10 = 0.480112
M6 probability ECE-10 = 0.046582
M6 confidence ECE-10 = 0.046582
M6 Brier = 0.020504

M7 legacy runner ECE-10 = 0.483268
M7 probability ECE-10 = 0.048281
M7 confidence ECE-10 = 0.048281
M7 Brier = 0.019685
```

결론은 calibration repair가 즉시 첫 blocker는 아니라는 것이다. 하지만 이것이 곧 calibrated
`p_rel` 또는 `p_obs` claim을 허용한다는 뜻은 아니다. 현재 target은 여전히 train-only `C_e`
compatibility discrimination target이고, held-out / Docker / reliability-target promotion은 아직 없다.

## Route Decision

선택한 다음 route:

```text
compatibility_dataset_v3_independent_validity_support_contact_balancing_plan
```

이유:

- 현재 `1600` rows 중 `1512` rows가 `relative_vertical`이다.
- `support_contact_pose_conditioned`는 `88` rows뿐이라 primary family generality를 주장하기 어렵다.
- support/contact는 physical relation reliability에서 가장 중요한 family 중 하나이며, `standing on`,
  `lying on`, `supported by` 계열은 `C_e = compatibility(T_e, G_e)` 주장을 relation-general claim으로
  확장하는 데 필요하다.

## Claim Boundary

Allowed now:

- train-only `C_e` discrimination/ranking evidence
- corrected calibration metric definition for future smoke runners
- `relative_vertical` 중심의 current mechanism evidence

Blocked:

- calibrated `p_rel` / `p_obs` posterior claim
- paper-level H002 result
- held-out validation/test claim
- broad all-family 3DSSG reliability claim
- support/contact primary generality claim

## Next Plan

다음 단계는 support/contact를 primary family로 다시 균형화하는 것이다.

Required constraints:

- train-only rows only
- target support/contact rows at least `400` if possible
- keep `Z_e` outside `C_e`
- use raw geometry / mesh / pose / contact evidence, not frozen `p_geom_valid` or hidden `geometry_status`
- compare semantic/source-only, geometry-only, concat, `C_e`, factorized, shuffled-G, and wrong-predicate controls
- report corrected probability-ECE and Brier, but do not promote calibrated posterior yet
