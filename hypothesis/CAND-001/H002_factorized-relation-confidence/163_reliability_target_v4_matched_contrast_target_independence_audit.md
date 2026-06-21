# Reliability Target V4 Matched Contrast Target Independence Audit

2026-06-21 KST에 `reliability_target_v4_matched_contrast_target_independence_audit` TODO를
진행했다. 이 단계는 v4 matched-contrast label ingestion 결과가 posterior smoke로
넘어갈 수 있는지 확인하는 train-only target audit이다. Posterior는 학습하지 않았다.

## Boundary

- Split: train only.
- Validation/test usage: none.
- Posterior training: none.
- Multi-view: audit/label evidence로만 유지하고 posterior input으로 사용하지 않는다.
- Hidden matched-contrast role, source queue, geometry status, rank band, packet source,
  endpoint flags, object/family cells, audit packet paths는 label lock 이후 audit에만 사용한다.
- V4 review fields는 posterior input이 아니다.
- 이 결과는 paper evidence가 아니라 H002 hypothesis-stage gate다.

## Result

```text
status = h002_reliability_target_v4_matched_contrast_target_independence_audit_blocked
validation errors = 0
relation reliability = 47 rows, 23 positive, 24 negative
geometry support = 47 rows, 30 positive, 17 negative
relation usefulness = 50 rows, 25 positive, 25 negative
posterior_allowed = False
validation_used = False
test_used = False
next = reliability_target_v4_matched_contrast_path_decision
```

Per-target decision:

| Target | Status | Rows | Positive | Negative | Strict Slice | Diagnostic Slice |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `relation_reliability_v4_binary_target` | `blocked_no_controlled_slice` | 47 | 23 | 24 | none | none |
| `geometry_support_v4_binary_target` | `blocked_positive_sparse` | 47 | 30 | 17 | none | none |
| `relation_usefulness_v4_binary_target` | `blocked_no_controlled_slice` | 50 | 25 | 25 | none | none |

## Main Finding

V4 matched-contrast target은 class balance 자체는 개선했다. Relation reliability target은
`23/24`로 거의 균형이고, matched role 자체도 original target에서 strong risk로 잡히지 않았다.
하지만 posterior-ready target은 아니다.

가장 큰 문제는 target label이 relation reliability의 일반 원리보다 endpoint/object identity에
강하게 묶여 있다는 점이다. Original relation reliability target에서:

| Risk Key | NMI | Majority Rule Acc | Excess over Baseline | Positive Rate Range |
| --- | ---: | ---: | ---: | ---: |
| `subject_object_family_cell_hidden` | 1.0000 | 1.0000 | 0.4894 | 1.0000 |
| `subject_label` | 0.7764 | 0.9149 | 0.4043 | 1.0000 |
| `endpoint_flag_pattern_hidden` | 0.5774 | 0.8085 | 0.2979 | 1.0000 |
| `endpoint_family_cell_hidden` | 0.5774 | 0.8085 | 0.2979 | 1.0000 |
| `object_family_cell_hidden` | 0.3937 | 0.7447 | 0.2340 | 1.0000 |
| `object_label` | 0.3914 | 0.7447 | 0.2340 | 1.0000 |

해석은 명확하다. 현재 label set에서 model이 factorized posterior를 학습한다고 해도,
semantic evidence, geometry evidence, coverage, uncertainty의 결합을 배운다기보다
특정 subject/object/family cell을 외우는 shortcut을 배울 위험이 크다.

## Controlled Slice Audit

총 `54`개 slice를 생성했다: 3개 target 각각에 대해 18개 slice다.

Relation reliability 주요 slice:

| Slice | Rows | Positive | Negative | Endpoint/Object Risks | Construction Risks | Object Risks | Strict | Diagnostic |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `matched_role_balanced_v4` | 42 | 21 | 21 | 4 | 1 | 2 | false | false |
| `source_queue_balanced_v4` | 42 | 21 | 21 | 4 | 1 | 2 | false | false |
| `geometry_status_balanced_v4` | 42 | 21 | 21 | 4 | 1 | 2 | false | false |
| `rank_band_balanced_v4` | 38 | 19 | 19 | 4 | 1 | 2 | false | false |
| `family_balanced_v4` | 32 | 16 | 16 | 4 | 2 | 2 | false | false |
| `object_label_balanced_v4` | 24 | 12 | 12 | 3 | 2 | 1 | false | false |
| `endpoint_flag_pattern_balanced_v4` | 18 | 9 | 9 | 2 | 4 | 2 | false | false |
| `subject_object_family_cell_balanced_v4` | 0 | 0 | 0 | 0 | 0 | 0 | false | false |

Strict criterion은 최소 `50` rows와 class별 최소 `20` rows, 그리고 matched-role /
endpoint-object / construction / visible-object shortcut risk 제거를 요구한다. Relation reliability
target은 original부터 `47` rows라 strict size 기준을 만족하지 못하고, balanced slice에서도
shortcut risk가 남는다.

Diagnostic criterion은 최소 `30` rows와 class별 최소 `10` rows를 만족하더라도 hidden
endpoint/object, construction, visible object shortcut을 제거해야 한다. 현재는 이 조건을
만족하는 diagnostic slice도 없다.

## Interpretation

이번 결과는 H002 방향 자체의 실패라기보다 target construction의 실패에 가깝다.
즉, `semantic score != geometry validity != relation reliability`라는 문제 정의는 유지된다.
다만 현재 v4 label set은 factorized posterior를 검증하기에 충분히 독립적이지 않다.

구체적으로:

- matched role balance만으로는 충분하지 않다.
- relation reliability label이 subject/object family cell에 거의 종속되어 있다.
- `support_contact` / `relative_vertical` 안에서도 object identity가 target을 강하게 설명한다.
- geometry support target은 `30/17`이라 geometry axis 분석에는 참고 가능하지만,
  main relation reliability target으로 쓰기에는 negative class mass가 부족하다.
- relation usefulness target도 balanced이지만 endpoint/object shortcut이 reliability target과
  같은 방식으로 남아 있다.

따라서 posterior combiner나 SOTA-style 결합 방식을 바꾸기 전에 target path decision이 먼저다.
현재 target으로 posterior를 돌리면 성능이 좋아져도 relation reliability를 배운 것인지,
object/family shortcut을 배운 것인지 방어할 수 없다.

## Next Decision

다음 TODO는 `reliability_target_v4_matched_contrast_path_decision`이다.

결정해야 할 선택지는 다음과 같다.

1. 더 강한 endpoint/object-controlled resampling으로 target을 다시 만든다.
2. Relation reliability를 바로 binary target으로 두지 않고, object/family-stratified target 또는
   pair-level contrast target으로 재정의한다.
3. Geometry support / relation usefulness를 main target이 아니라 auxiliary evidence axis로 유지한다.
4. Posterior smoke는 target-independence gate가 통과할 때까지 계속 막는다.

## Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/163_reliability_target_v4_matched_contrast_target_independence_audit.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_target_independence_audit_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_target_independence_audit_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_target_independence_audit_codex_proxy_user_requested/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_target_independence_audit_codex_proxy_user_requested/group_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_target_independence_audit_codex_proxy_user_requested/group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_target_independence_audit_codex_proxy_user_requested/validation_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_target_independence_audit_codex_proxy_user_requested/target_slices/
```
