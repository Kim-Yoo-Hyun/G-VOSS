# H002 Reliability Target V3 Object/Endpoint Target Independence Audit

Date: 2026-06-20 KST

## Purpose

`146_reliability_target_v3_object_endpoint_label_ingestion.md`에서 만든
object/endpoint-controlled v3 target이 posterior smoke로 넘어갈 수 있는지 감사했다.

핵심 질문:

```text
Is the current object/endpoint v3 target failure a true shortcut problem,
or mostly a positive-sparse target artifact?
```

## Boundary

- Split: Open3DSG train-only.
- Validation/test rows: not used.
- Posterior training/smoke: not run.
- Labels are user-requested Codex proxy labels, not independent human annotation.
- Hidden provenance/sampling fields are used only after label lock for audit and slice construction.
- V3 review fields, hidden sampling buckets, audit packet paths, and multi-view evidence are not posterior inputs.
- Majority-baseline excess is reported so positive-sparse targets are not mistaken for true shortcut signal.
- H001 artifacts: not modified.

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_target_independence_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_target_independence_audit.py
```

Observed:

```text
status=h002_reliability_target_v3_object_endpoint_target_independence_audit_reliability_blocked_geometry_support_available
rel=107/8/99
rel_status=blocked_positive_sparse
geom=111/85/26
geom_status=blocked_no_controlled_slice
use=111/10/101
use_status=blocked_positive_sparse
errors=0
posterior_allowed=False
validation_used=False
test_used=False
next=reliability_target_v3_object_endpoint_path_decision
```

## Result

Status:

```text
h002_reliability_target_v3_object_endpoint_target_independence_audit_reliability_blocked_geometry_support_available
```

Decision:

```text
The main reliability target is blocked by positive sparsity, while
geometry-support has usable mass. Do not switch the main claim to geometry
support without a path decision.
```

## Per-Target Decisions

| Target | Rows | Positive | Negative | Status | Strict Slice | Diagnostic Slice |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `relation_reliability_v3_binary_target` | 107 | 8 | 99 | `blocked_positive_sparse` | none | none |
| `geometry_support_v3_binary_target` | 111 | 85 | 26 | `blocked_no_controlled_slice` | none | none |
| `relation_usefulness_v3_binary_target` | 111 | 10 | 101 | `blocked_positive_sparse` | none | none |

## Interpretation

이번 결과는 H002의 핵심 분리 주장을 다시 확인하지만, posterior 실험을 열 수 있는
상태는 아니다.

```text
geometry support has mass, but relation reliability does not.
```

구체적으로:

- `relation_reliability_v3_binary_target`은 positive가 `8/107`개뿐이다.
  이 target으로 posterior smoke를 돌리면 모델이 reliability를 배운 것이 아니라
  대부분 negative인 target을 맞춘 결과가 될 위험이 크다.
- `relation_usefulness_v3_binary_target`도 positive가 `10/111`개라 같은 문제가 있다.
- `geometry_support_v3_binary_target`은 `85/26`으로 mass는 있지만, endpoint pattern,
  predicate label, object label, construction axis를 통제한 strict/diagnostic slice가
  없다.

따라서 `geometry_support`를 바로 main reliability target으로 바꾸면 H002가 원래
주장한 `semantic score != geometry validity != relation reliability` 구분을 잃고,
geometry-only verifier 문제로 축소될 수 있다.

## What This Means

이 단계에서 실패한 것은 posterior 결합 방식이 아니다. 더 근본적인 문제는 target이다.

현재 target은 다음 두 성질을 동시에 갖는다.

- geometry predicate를 지지하는 row는 많다.
- 그러나 scene graph relation으로 신뢰할 만한 row는 매우 적다.

즉, 우리가 찾은 문제는 "semantic과 geometry를 합치면 된다"가 아니라, relation
reliability target을 어떻게 정의하고 샘플링해야 하는지의 문제다. 이 점은 H002가
단순 geometry rule 후처리가 아니라 relation-level reliability 문제라는 주장과도 맞다.

## Next Path Options

다음 TODO는 posterior smoke가 아니라 path decision이다.

검토해야 할 선택지는 다음과 같다.

| Option | Verdict | Reason |
| --- | --- | --- |
| posterior smoke now | reject | main reliability target positive-sparse |
| geometry-support as main target | reject by default | relation reliability와 geometry validity를 다시 합쳐버림 |
| mine more informative positives | plausible | trivial room/surface relation을 줄이고 reliable positives를 늘릴 수 있음 |
| relax reliability definition | plausible but risky | positive mass는 늘 수 있지만 target 의미가 흐려질 수 있음 |
| keep geometry-support diagnostic only | safe | H002 decomposition evidence로는 유효하지만 main posterior target은 아님 |

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/147_reliability_target_v3_object_endpoint_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_target_independence_audit_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_target_independence_audit_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_target_independence_audit_codex_proxy_user_requested/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_target_independence_audit_codex_proxy_user_requested/group_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_target_independence_audit_codex_proxy_user_requested/group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_target_independence_audit_codex_proxy_user_requested/validation_errors.jsonl
```

## Next TODO

```text
reliability_target_v3_object_endpoint_path_decision
```

Goal:

- Decide whether to revise sampling, revise the reliability definition, keep geometry-support diagnostic only, or stop the current posterior path.
- Do not use validation/test.
- Do not add multi-view as a posterior input yet.
- Do not run posterior smoke until a posterior-ready reliability target exists.
