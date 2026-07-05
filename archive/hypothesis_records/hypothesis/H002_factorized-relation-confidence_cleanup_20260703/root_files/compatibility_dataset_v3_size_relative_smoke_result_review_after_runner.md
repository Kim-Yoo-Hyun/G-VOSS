# Compatibility Dataset V3 Size-Relative Smoke Result Review After Runner

Created: 2026-06-29 KST

## Purpose

`size_relative` learned smoke runner가 통과한 뒤, 이 결과를 H002 claim 안에서
어떤 역할로 사용할 수 있는지 고정했다. 이 단계는 새 모델 학습이나 추가 target
materialization이 아니라 result review와 claim boundary 결정이다.

## Command

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_size_relative_smoke_result_review_after_runner.py
```

## Artifact

```text
artifact_root = artifacts/compatibility_dataset_v3_size_relative_smoke_result_review_after_runner/
status = h002_compatibility_dataset_v3_size_relative_smoke_result_review_after_runner_ready_for_multi_family_synthesis_update
selected_path = promote_size_relative_as_main_compatibility_route_evidence_keep_calibration_caveat
validation_errors = 0
next_todo = compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative
```

Generated files:

```text
summary.json
review_decision.json
route_position.csv
claim_boundary.csv
reviewer_risks.csv
next_steps.csv
report.md
validation_errors.jsonl
```

## Decision

`size_relative`는 H002의 `main compatibility-route mechanism evidence`로 둔다.
이 family에서 중요한 결과는 size geometry 자체가 강하다는 것이 아니라, 같은
`G_e_size`가 `bigger than`과 `smaller than` predicate에 따라 반대로 해석되어야
한다는 점이다.

```text
T_e only AUROC = 0.4707
G_e_size only AUROC = 0.5000
T_e + G_e no-interaction AUROC = 0.4707
T_e x G_e_size interaction AUROC = 0.9999
wrong-T AUROC = 0.00009
shuffled-G AUROC = 0.4931 / 0.4767
sign-flipped-G AUROC = 0.00008
```

## Claim Boundary

Allowed:

- `size_relative` is strong train-only mechanism evidence for `C_e = compatibility(T_e, G_e)`.
- Same geometry evidence must be interpreted through predicate semantics.
- It can be added to the multi-family relation-aware evidence-routing synthesis.

Not allowed:

- calibrated `p_rel` or `p_obs` probability claim
- paper-level performance claim
- geometry-only reliability claim
- universal all-relation-family generalization claim

The primary model has high AUROC but high ECE, so this result supports ranking/decision
mechanism evidence, not calibrated reliability probability.
