# Reliability Target V4 Matched Contrast Path Decision

2026-06-21 KST에 `reliability_target_v4_matched_contrast_path_decision` TODO를
진행했다. 이 단계는 `163_reliability_target_v4_matched_contrast_target_independence_audit.md`에서
v4 target이 blocked 된 이후, posterior smoke를 강행할지, 같은 v4 sampling을 확장할지,
target construction을 다시 바꿀지 결정하는 단계다.

## Boundary

- Split: Open3DSG train-only.
- Validation/test rows: not used.
- Posterior model: not trained.
- New labels: not filled.
- H001 artifacts: not modified.
- Multi-view remains audit/label evidence, not posterior input.
- This is a hypothesis-stage target-construction decision, not paper evidence.

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_path_decision.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_path_decision.py
```

Observed:

```text
status=h002_reliability_target_v4_matched_contrast_path_decision_select_v5_cell_contrast_feasibility
selected=v5_cell_contrast_feasibility_scan
rel=47/23/24
posterior_allowed=False
validation_used=False
test_used=False
next=reliability_target_v5_cell_contrast_feasibility_scan
```

## Decision

Selected path:

```text
v5_cell_contrast_feasibility_scan
```

Decision:

```text
Do not run posterior smoke or expand the same v4 sampling. v4 fixed role
balance but failed subject/object-family target independence, so the next step
is a train-only v5 cell-contrast feasibility scan. If that scan cannot find
enough mixed-capacity cells, freeze H002 as an RGA diagnostic framework rather
than forcing a posterior claim.
```

## Why Not Posterior

v4의 좋은 점은 분명하다. `matched_contrast_role_hidden` 자체는 original target에서
strong shortcut으로 잡히지 않았고, relation reliability target도 `23/24`로 균형을 맞췄다.
하지만 target independence는 통과하지 못했다.

핵심 blocker:

| Observation | Meaning |
| --- | --- |
| relation reliability `47` rows, `23/24` | class balance는 확보했다. |
| strict/diagnostic controlled slice 없음 | posterior-ready target은 아니다. |
| `subject_object_family_cell_hidden` NMI `1.0000`, majority acc `1.0000` | subject/object/family cell만으로 label을 완전히 맞춘다. |
| visible `subject_label` NMI `0.7764`, majority acc `0.9149` | visible object identity도 강한 shortcut이다. |
| `subject_object_family_cell_balanced_v4` rows `0` | 현재 v4는 exact subject-object-family cell 안에서 mixed label을 만들지 못했다. |
| direct reliable/unreliable pair `1/79` | pairwise contrast target도 현재는 너무 sparse하다. |

따라서 지금 posterior smoke를 실행하면 factorized relation reliability를 배웠다는 주장을
방어할 수 없다. 성능이 좋아져도 모델이 object/family cell을 외운 것인지, semantic/geometry/
coverage/uncertainty factor를 결합한 것인지 분리되지 않는다.

## Option Matrix

| Option | Verdict | Reason |
| --- | --- | --- |
| `run_posterior_smoke_now` | reject | balanced target이지만 endpoint/object와 visible-object shortcut을 통과하지 못했다. |
| `expand_same_v4_matched_contrast_sampling` | reject as primary | 같은 construction을 늘리면 같은 shortcut이 scale될 가능성이 크다. |
| `use_object_label_or_family_as_model_factor` | reject for main claim | audit에서 드러난 shortcut을 model factor로 쓰면 factorized reliability claim을 방어하기 어렵다. |
| `use_geometry_support_as_main_target` | reject for reliability claim | geometry support는 evidence axis이지 relation reliability target이 아니다. |
| `use_relation_usefulness_as_main_target` | reject | usefulness는 balanced이지만 reliability와 같은 endpoint/object shortcut을 가진다. |
| `use_pairwise_v4_contrast_target` | reject for now | direct reliable/unreliable contrast가 `1/79` pairs뿐이다. |
| `use_subject_object_family_balanced_slice` | reject in current v4 | exact subject-object-family balanced slice가 `0` rows다. |
| `v5_cell_contrast_feasibility_scan` | select | full train pool에 within-cell positive/negative capacity가 있는지 먼저 확인해야 한다. |
| `freeze_h002_as_rga_diagnostic_framework` | fallback | v5 capacity가 없으면 posterior claim을 강제하지 않는다. |

## V5 Direction

v5는 label을 바로 더 채우는 단계가 아니다. 먼저 full train pool에서 다음 조건을 만족하는
cell이 충분한지 확인한다.

```text
same subject/object/family cell 안에서
reliable-like candidate와 unreliable-like candidate를 둘 다 뽑을 수 있는가?
```

Cell axes:

- `predicate_family`
- `predicate_label` when feasible
- `subject_label`
- `object_label`
- `endpoint_flag_pattern_hidden`
- `subject_object_family_cell_hidden`

Secondary controls:

- `rank_band_hidden`
- `source_queue_hidden`
- `geometry_status_hidden`
- `label_match_status_hidden`
- `asset_packet_source_hidden`
- scan cap

Feasibility gates:

- label fill 전 candidate rows가 최소 `80`개 이상이어야 한다.
- contrast pair 또는 equivalent balanced rows가 최소 `40`개 이상이어야 한다.
- both-role capacity를 가진 distinct subject-object-family cell이 최소 `10`개 이상이어야 한다.
- single cell이 selected rows의 `20%`를 넘기면 안 된다.
- capacity가 불가능하다고 확인되지 않는 한 `support_contact`와 `relative_vertical`을 둘 다 포함한다.
- label fill 전에 asset packet coverage 또는 asset generation path가 명시되어야 한다.

Posterior reopen gate after v5 labels:

- relation reliability binary target이 최소 `20` positive / `20` negative를 가진다.
- `subject_object_family_cell` balanced slice가 nonempty이고 diagnostic-ready여야 한다.
- endpoint/object 및 visible object-label risk만으로 target을 설명할 수 없어야 한다.
- rank band, source queue, geometry status, packet source가 control 또는 audit되어야 한다.
- validation/test usage는 계속 `False`여야 한다.

## Stop Rule

v5 feasibility scan에서도 enough mixed-capacity cells를 찾지 못하면 H002를 posterior-learning
claim으로 더 밀지 않는다. 그 경우 H002는 다음처럼 정리한다.

```text
RGA diagnostic/decomposition framework:
semantic score, geometry support, relation usefulness, uncertainty, and
relation reliability are separable, but the current relation-source/label
construction does not provide a clean posterior-learning target.
```

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/164_reliability_target_v4_matched_contrast_path_decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v4_matched_contrast_path_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_path_decision_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_path_decision_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_path_decision_codex_proxy_user_requested/option_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_path_decision_codex_proxy_user_requested/failure_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v4_matched_contrast_path_decision_codex_proxy_user_requested/next_plan.json
```

## Next TODO

```text
reliability_target_v5_cell_contrast_feasibility_scan
```

Goal:

- full train-only support/vertical pool에서 subject-object/family cell 내부 contrast capacity를 확인한다.
- label fill 전에 exact object identity shortcut을 줄일 수 있는지 판단한다.
- feasibility가 없으면 H002 posterior track을 멈추고 RGA diagnostic framework로 정리한다.
