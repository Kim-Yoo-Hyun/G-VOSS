# H002 Reliability Target V3 Informative Anchor Path Decision

Date: 2026-06-20 KST

## Purpose

`154_reliability_target_v3_informative_anchor_target_independence_audit.md`에서
informative-anchor v3 target이 posterior-ready가 아님을 확인했다. 이번 단계는
posterior smoke를 강행할지, geometry-support target으로 바꿀지, 같은 방식으로 label을
더 모을지, 아니면 target construction 자체를 바꿀지 결정한다.

핵심 질문:

```text
Is the next principled step more data, better posterior capacity, or a different target construction?
```

## Boundary

- Split: Open3DSG train-only.
- Validation/test rows: not used.
- Posterior model: not trained.
- Combiner upgrade: not run.
- H001 artifacts: not modified.
- Multi-view remains audit/label evidence, not posterior input.
- Current labels are user-requested Codex proxy labels, not independent human evidence.

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_path_decision.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_path_decision.py
```

Observed:

```text
status=h002_reliability_target_v3_informative_anchor_path_decision_matched_contrast_v4
selected=revise_to_matched_contrast_reliability_target_v4
rel=82/35/47
rel_status=blocked_no_controlled_slice
posterior_allowed=False
validation_used=False
test_used=False
next=reliability_target_v4_matched_contrast_plan
```

## Decision

Selected path:

```text
revise_to_matched_contrast_reliability_target_v4
```

Decision:

```text
Do not run posterior smoke, accept the full informative-anchor target, or use
geometry-support as the main target. v3 fixed positive sparsity but failed
target independence, so the next step is a v4 matched-contrast target
construction that compares positives and negatives inside matched
endpoint/object/rank strata.
```

## Why This Path

이번 failure는 “데이터가 부족하다”보다 더 구체적이다.

| Observation | Meaning |
| --- | --- |
| reliability target `82` rows, `35/47` | positive mass는 이제 충분하다. |
| strict/diagnostic slice 없음 | target independence는 아직 실패했다. |
| `anchor_category_hidden` majority acc `0.9634` | sampling anchor가 hidden label proxy처럼 작동한다. |
| endpoint/object structure majority acc up to `1.0000` | endpoint/object cell만으로 target을 거의 맞출 수 있다. |
| object label majority acc `0.9512` | visible object identity도 shortcut이다. |
| geometry-support `72/13` | geometry validity는 evidence axis이지 reliability target이 아니다. |

따라서 지금 posterior를 돌리면 factorized relation reliability를 검증하는 것이 아니라,
anchor/object/endpoint construction을 맞추는 실험이 될 가능성이 높다.

## Option Matrix

| Option | Verdict | Reason |
| --- | --- | --- |
| `run_posterior_smoke_now` | `reject` | target mass는 있지만 controlled slice가 없다. |
| `use_full_informative_anchor_target` | `reject` | anchor/object/endpoint/rank shortcut이 너무 강하다. |
| `use_family_or_predicate_balanced_slice` | `reject_for_posterior_keep_for_diagnostic` | row 수는 남지만 shortcut이 그대로 남는다. |
| `use_anchor_or_endpoint_balanced_slice` | `reject` | shortcut은 줄지만 `6` rows 또는 `4` rows 수준으로 붕괴한다. |
| `use_geometry_support_as_main_target` | `reject_for_reliability_claim` | relation reliability를 geometry validity로 다시 합친다. |
| `collect_more_same_informative_anchor_rows` | `reject_as_primary` | 같은 construction shortcut을 반복할 가능성이 높다. |
| `matched_contrast_reliability_target_v4` | `select` | 같은 endpoint/object/rank stratum 안에서 positive/negative를 비교해야 한다. |
| `freeze_h002_as_rga_diagnostic_only` | `fallback` | v4도 실패하면 posterior claim을 강제하지 않는다. |
| `add_multi_view_as_model_input_now` | `reject_now` | target independence 없이 feature를 늘리면 shortcut과 feature gain이 섞인다. |

## V4 Direction

v4는 sample 수만 늘리는 것이 아니라 construction principle을 바꾼다.

기존 v3:

```text
positive-like anchor bucket vs negative-like anchor bucket
```

v4:

```text
same predicate / endpoint-object / rank stratum 안에서
reliable edge와 unreliable edge를 contrast
```

Matching axes:

- `predicate_family`
- `predicate_label` when enough rows exist
- `endpoint_flag_pattern_hidden`
- `object_family_cell_hidden` or `endpoint_family_cell_hidden`
- `rank_band_hidden`

Sampling constraints:

- `anchor_category`를 positive/negative construction axis로 쓰지 않는다.
- `floor`, `wall`, `ceiling`, room-surface endpoint를 stratum별로 cap한다.
- `support_contact`와 `relative_vertical`을 모두 포함하되, family 자체가 label이 되지 않게 한다.
- repeated object-family cell에서 reliable/unreliable 후보가 같이 있는 경우를 우선한다.
- semantic score, rank, `p_geom_valid`, geometry status, label-match status, queue 정보는 labeler에게 숨긴다.
- hidden construction metadata는 label lock 이후에만 audit에 사용한다.
- multi-view는 계속 audit evidence이고 posterior input이 아니다.

## Posterior Reopen Gate

Posterior smoke는 다음 조건 전까지 계속 막는다.

- relation reliability binary target이 최소 `20` positive / `20` negative를 가진다.
- strict 또는 명시적으로 방어 가능한 diagnostic controlled slice가 존재한다.
- selected slice에서 anchor/category shortcut risk가 `0`이어야 한다.
- endpoint/object 및 visible object-label shortcut만으로 target을 설명할 수 없어야 한다.
- rank-band와 geometry-status control이 selected slice를 지배하지 않아야 한다.
- validation/test usage는 계속 `False`다.

## Fallback Stop Rule

v4 matched contrast에서도 independent target을 만들지 못하면 H002를 posterior method
claim으로 더 밀지 않는다. 그 경우 H002는 다음 형태로 정리하는 것이 더 방어 가능하다.

```text
RGA diagnostic/decomposition framework:
semantic score, geometry support, usefulness, uncertainty, and relation
reliability can be separated, but current source/label construction does not
provide a clean posterior-learning target.
```

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/155_reliability_target_v3_informative_anchor_path_decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_informative_anchor_path_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_path_decision_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_path_decision_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_path_decision_codex_proxy_user_requested/option_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_path_decision_codex_proxy_user_requested/failure_matrix.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_informative_anchor_path_decision_codex_proxy_user_requested/next_plan.json
```

## Next TODO

```text
reliability_target_v4_matched_contrast_plan
```

Goal:

- train-only full RGA rows에서 matched contrast v4 후보 stratum을 찾는다.
- positive/negative anchor bucket이 아니라 같은 endpoint/object/rank stratum 내부 contrast를 만든다.
- posterior smoke는 계속 block한다.
