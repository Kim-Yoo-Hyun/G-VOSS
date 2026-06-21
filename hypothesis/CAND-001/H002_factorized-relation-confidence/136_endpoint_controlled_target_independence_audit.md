# Endpoint-Controlled Target Independence Audit

Date: 2026-06-20 KST

## Purpose

`endpoint_controlled_target_independence_audit`은
`135_endpoint_controlled_label_ingestion.md`에서 생성한 endpoint-controlled targets가
posterior smoke로 넘어갈 수 있는지 확인하는 단계다.

핵심 질문:

```text
Does endpoint-controlled resampling produce a target that is independent enough
and balanced enough to test factorized relation reliability?
```

## Boundary

- Split: Open3DSG train-only.
- Validation/test row는 사용하지 않았다.
- Posterior model은 학습하지 않았다.
- Codex-proxy endpoint-controlled labels는 paper-level human annotation이 아니다.
- Hidden endpoint/sampling metadata는 label lock 이후 audit에만 사용했다.
- Review fields, hidden endpoint metadata, packet paths, multi-view evidence는 posterior input이 아니다.
- H001 artifact는 수정하지 않았다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_target_independence_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_target_independence_audit.py
```

Observed:

```text
status=h002_endpoint_controlled_target_independence_audit_blocked_positive_sparse
relation_rows=34
relation_pos=2
relation_neg=32
majority_baseline=0.9412
errors=0
relation_strict=none
relation_diagnostic=none
validation_used=False
test_used=False
next=endpoint_controlled_target_path_decision
```

## Per-Target Decision

| Target | Status | Rows | Pos | Neg | Positive Sparse | Strict Slice | Diagnostic Slice |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| `geometry_validity_endpoint_controlled_target` | `blocked_no_controlled_slice` | 34 | 23 | 11 | `False` | `none` | `none` |
| `relation_reliability_endpoint_controlled_target` | `blocked_positive_sparse` | 34 | 2 | 32 | `True` | `none` | `none` |

## Original Target Risks

| Target | Risk Mode | Key | Majority Acc | Baseline | NMI | Pos Rate Range | Sparse-Dominated |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| `geometry_validity_endpoint_controlled_target` | `construction` | `proposed_audit_role_hidden` | 0.9412 | 0.6765 | 0.7568 | 1.0000 | `False` |
| `geometry_validity_endpoint_controlled_target` | `endpoint_control` | `endpoint_flag_pattern_hidden` | 0.9706 | 0.6765 | 0.8831 | 1.0000 | `False` |
| `geometry_validity_endpoint_controlled_target` | `visible_non_target` | `predicate_label` | 0.8529 | 0.6765 | 0.4198 | 0.7778 | `False` |
| `relation_reliability_endpoint_controlled_target` | `construction` | `proposed_audit_role_hidden` | 0.9412 | 0.9412 | 0.6355 | 0.5000 | `True` |
| `relation_reliability_endpoint_controlled_target` | `endpoint_control` | `endpoint_flag_pattern_hidden` | 1.0000 | 0.9412 | 1.0000 | 1.0000 | `True` |
| `relation_reliability_endpoint_controlled_target` | `visible_non_target` | `predicate_label` | 0.9412 | 0.9412 | 0.4979 | 0.3333 | `True` |

## Positive-Sparsity Diagnosis

Relation reliability target:

```text
rows = 34
positive = 2
negative = 32
positive_rate = 0.0588
majority_baseline = 0.9412
```

The target is not posterior-ready for two reasons.

1. The positive class is below the minimum smoke threshold.
2. A negative-majority predictor already gets `0.9412` accuracy.

Therefore a posterior smoke test on this target would not validate factorized
relation reliability. It would mostly test whether the target construction made
nearly everything unreliable.

## Interpretation

Endpoint-controlled resampling did reduce the previous endpoint-shortcut concern
in the sampling design, but the resulting relation-reliability target collapsed
into a positive-sparse target. This is a target-construction failure, not a
posterior-combiner failure.

The audit also preserves an important H002 distinction:

```text
geometry validity != relation reliability
```

`geometry_validity_endpoint_controlled_target` has `23/11` class mass, but it is
still blocked because the full target slice is too small and construction /
endpoint-control risks remain. `relation_reliability_endpoint_controlled_target`
is more severely blocked because it has only `2` positives.

## Decision

Current status:

```text
h002_endpoint_controlled_target_independence_audit_blocked_positive_sparse
```

Decision:

```text
Posterior smoke remains blocked. Move to target path decision before changing
the posterior combiner or adding multi-view as model input.
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/136_endpoint_controlled_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/endpoint_controlled_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_independence_audit_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_independence_audit_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_independence_audit_codex_proxy_user_requested/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_independence_audit_codex_proxy_user_requested/group_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_independence_audit_codex_proxy_user_requested/group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_independence_audit_codex_proxy_user_requested/validation_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/endpoint_controlled_target_independence_audit_codex_proxy_user_requested/relation_reliability_endpoint_controlled_target_positive_rows.jsonl
```

## Next TODO

```text
endpoint_controlled_target_path_decision
```

Goal:

- decide whether to revise the relation reliability definition, revise sampling,
  expand positive label collection, or keep endpoint-controlled artifacts as
  failure diagnosis only.
- keep posterior smoke blocked until a target has enough positive mass and a
  defensible independence slice.
