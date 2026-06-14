# H002 Multi-View Audit Protocol

Last updated: 2026-06-13

## Purpose

H002에서 point cloud + multi-view를 언제, 어떤 역할로 추가할지 결정한다.

Current decision:

```text
Do not add V_mv_e as model input yet.
```

Reason:

현재 H002의 병목은 feature 부족이 아니라 target independence와 label quality다. 따라서
multi-view를 지금 바로 `factorized_reliability_posterior` input으로 넣으면, 성능이
좋아져도 다음을 분리하기 어렵다.

```text
target construction shortcut
vs
true visual-geometric reliability evidence
```

따라서 현재 gate에서는 multi-view를 deployable feature가 아니라
audit/confirmation evidence로만 사용한다.

## Fixed Order

H002의 진행 순서를 다음처럼 고정한다.

### 1. Validate Current Factorized Posterior First

Current model family:

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

Inputs:

- `S_e`: semantic score/rank.
- `G_e`: 3D geometry evidence, including `p_geom_valid` and continuous residuals.
- `C_e`: geometry coverage/checkability.
- `U_e`: uncertainty and abstain evidence.

Required before adding `V_mv_e`:

- human-confirmed or more independent labels.
- `semantic_only`, `geometry_only`, `semantic_plus_geometry`, `factorized`
  comparison.
- same-family control.
- same-geometry-status control.
- same-rank-band control.
- no validation/test rows until target and feature policy are frozen.

### 2. Use Multi-View As Audit Evidence Now

Current multi-view role:

```text
label confirmation evidence
```

It should help decide whether a working label should become:

- `reliable_promote`
- `unreliable_dense_noise`
- `relabel_or_ontology`
- `invalid_pair`
- `visibility_or_geometry_artifact`
- `abstain_uncertain`

Main use cases:

- distinguish `true_underconfidence` from `dense_relation_noise`.
- judge whether a geometry-satisfied relation is visually informative.
- detect poor visibility, truncation, occlusion, or invalid object pair.
- decide whether `annotation_sparsity` is plausible or only an ontology artifact.

### 3. Add `V_mv_e` Only After Gate Pass

Future model family:

```text
P(R_e = 1 | S_e, G_3D_e, V_mv_e, C_e, U_e)
```

This is not a new relation generator. It is an RGA evidence-axis expansion from:

```text
semantic-geometry agreement
```

to:

```text
semantic-geometry-visual agreement
```

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/multiview_audit_protocol.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/multiview_audit_protocol.py
```

Status:

```text
ready_audit_only_vmv_deferred
```

Boundary:

```text
deployable_vmv_features_created = false
model_input_expansion_allowed_now = false
validation_usage = false
paper_result = false
posterior_claim_allowed = false
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/protocol.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/primary_strict_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/support_contact_extension_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/all_candidate_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/primary_strict_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/support_contact_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/all_candidate_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/multiview_audit_protocol/report.md
```

## Audit Queues

| Queue | Rows | Role |
| --- | ---: | --- |
| `primary_strict_current_target` | 27 | current target-v2 confirmation |
| `extension_support_contact_future_family` | 26 | future relation-family audit candidate |
| `extension_relative_vertical_lower_priority` | 34 | lower-priority extension context |

All-candidate sheet:

```text
rows = 87
families = proximity 27, support_contact 26, relative_vertical 34
```

Asset coverage:

| Sheet | Rows | Contact sheets | Mesh links | Subject images | Object images |
| --- | ---: | ---: | ---: | --- | --- |
| `primary_strict` | 27 | 27 | 27 | 2-10 | 10-10 |
| `support_contact_extension` | 26 | 26 | 26 | 2-10 | 2-10 |
| `all_candidates` | 87 | 87 | 87 | 2-10 | 2-10 |

## Audit Fields

The sheet fields are intentionally review fields, not deployable input features.

| Field | Values |
| --- | --- |
| `subject_visibility` | good / partial / poor / not_visible / uncertain |
| `object_visibility` | good / partial / poor / not_visible / uncertain |
| `pair_covisible` | yes / no / uncertain |
| `pair_context_sufficient` | yes / no / uncertain |
| `visual_relation_support` | supports / contradicts / uncertain / not_evaluable |
| `visual_informativeness` | informative / trivial_dense / uncertain / not_evaluable |
| `occlusion_or_truncation_issue` | yes / no / uncertain |
| `crop_quality` | good / usable / poor / uncertain |
| `final_visual_audit_decision` | controlled decision below |
| `confidence` | high / medium / low |

Final visual audit decisions:

| Decision | Meaning |
| --- | --- |
| `confirm_reliable_promote` | visually supports an informative relation |
| `confirm_dense_noise` | geometry-supported but visually trivial/dense relation |
| `relabel_or_ontology` | useful only after predicate/ontology adjustment |
| `invalid_pair` | wrong or unreliable object pair |
| `visibility_or_geometry_artifact` | view/segmentation/geometry artifact dominates |
| `abstain_uncertain` | evidence insufficient |

## Why Support Contact Is Separated

The current strict target is all `proximity/close by`. It is useful for debugging
informativeness but not ideal for multi-view payoff because dense proximity noise
is common.

`support_contact` is separated as a future-family candidate because:

- contact/support relations have clearer physical witnesses.
- multi-view can help judge contact plausibility and visual context.
- it aligns better with `G_3D_e + V_mv_e` than broad `close by`.

Current support-contact extension count:

```text
support_contact rows = 26
standing on = 15
supported by = 11
```

## Controls Before `V_mv_e` Model Input

`V_mv_e` can be promoted only after these controls are defined:

- wrong-pair view.
- shuffled-view.
- shuffled-geometry.
- no-view / low-visibility rows.
- same-family controlled split.
- same-geometry-status controlled split.
- same-rank-band controlled split.

## Current Decision

Established:

- multi-view audit protocol exists.
- strict proximity audit sheet exists.
- support-contact extension audit sheet exists.
- all rows have contact sheets and mesh links.
- no validation/test rows were used.
- no deployable `V_mv_e` model feature was created.

Not established:

- human-confirmed labels.
- factorized posterior advantage.
- visual evidence as deployable factor.
- visual-geometric reliability improvement.
- paper-level evidence.

Current rule:

```text
Validate S_e + G_e + C_e + U_e first.
Use multi-view only for audit evidence until that gate passes.
```

## Next TODO

Next document:

```text
35_factorized_validation_plan.md
```

Required next work:

- define the minimal independent label target needed to evaluate current
  `factorized_reliability_posterior`.
- define same-family, same-geometry-status, and same-rank-band controls.
- specify when `factorized` can be said to support the H002 hypothesis over
  `semantic_plus_geometry`.
- keep `V_mv_e` out of model input until this validation gate is satisfied.
