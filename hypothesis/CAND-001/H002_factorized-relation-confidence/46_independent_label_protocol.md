# H002 Independent Label Protocol

Last updated: 2026-06-14

## Purpose

`45_target_independence_audit.md`의 결론은 다음이었다.

```text
target_independence_not_established
```

현재 codex-controlled label은 rank-matched 이후에도 semantic-rank /
underconfidence construction과 충분히 독립적이지 않다. 따라서 H002가 posterior
method claim으로 계속 가려면 rank-hidden independent audit label이 필요하다.

이번 gate의 목적은 새 모델을 학습하는 것이 아니라, independent label collection
protocol을 고정하고 실제 blind review sheet를 생성하는 것이다.

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/independent_label_protocol.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/independent_label_protocol.py
```

Result:

```text
status=independent_label_protocol_ready rows=87 families={'support_contact': 26, 'proximity': 27, 'relative_vertical': 34} validation_used=False
```

## Boundary

- Train-only hypothesis-stage protocol.
- No validation/test rows are used.
- No posterior is trained in this stage.
- `V_mv_e` is not used as model input.
- Multi-view and mesh assets are audit evidence only.
- Semantic rank, semantic score, `p_geom_valid`, working label, queue identity,
  and proposed stratum are hidden from annotators.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/protocol.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_all_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_support_contact_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_proximity_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/blind_relative_vertical_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/independent_label_protocol/internal_key.jsonl
```

## Candidate Counts

| Family | Rows | Role |
| --- | ---: | --- |
| `support_contact` | 26 | first multi-view reliability family |
| `proximity` | 27 | current debugging family |
| `relative_vertical` | 34 | control / robustness family |
| `attachment_deferred` | 0 | future high-novelty family; separate candidate generator needed |

Asset coverage:

| Asset | Count |
| --- | ---: |
| contact sheet | 87 / 87 |
| mesh obj | 87 / 87 |
| subject image count | 2-10 |
| object image count | 2-10 |

## Hidden Fields

The following fields are stored only in `internal_key.jsonl` and must not be
shown to annotators before labels are locked.

```text
prediction_id
queue_name
priority_rank
working_label
geometry_status
rank_bucket
semantic_score_raw
semantic_score_norm
p_geom_valid
consistency_score
geometry_residual_proxy
proposed_review_stratum
final_controlled_label
```

This directly addresses the failure in `45_target_independence_audit.md`.

## Shown Fields

Annotators see only identity and evidence assets:

```text
blind_review_id
scan_id
subject_id / subject_label
predicate_label / predicate_family
object_id / object_label
contact_sheet
subject/object crop paths
mesh_obj
instance_ply
family-specific question
```

The blind sheet check found no exposed columns containing:

```text
score
rank
working_label
p_geom
geometry_status
queue
prediction_id
```

## Audit Labels

Primary audit field:

```text
relation_validity_label
```

Allowed values:

```text
reliable_informative
valid_but_trivial_dense
annotation_sparsity_candidate
ontology_mismatch
invalid_relation
invalid_pair
visibility_or_geometry_artifact
abstain_uncertain
```

Binary mapping for later posterior diagnostics:

| Use | Labels |
| --- | --- |
| positive | `reliable_informative`, `annotation_sparsity_candidate` |
| negative | `valid_but_trivial_dense`, `invalid_relation`, `invalid_pair`, `visibility_or_geometry_artifact` |
| exclude or multiclass only | `ontology_mismatch`, `abstain_uncertain` |

Supporting audit fields:

```text
subject_visibility
object_visibility
pair_covisible
pair_context_sufficient
visual_3d_support
relation_informativeness
family_specific_check
confidence
notes
```

## Family-Specific Protocol

### `support_contact`

Priority:

```text
1
```

Question:

```text
Is there visual/3D evidence that the subject is physically supported by or
standing on the object?
```

Use this as the first multi-view family because support/contact has concrete
3D witness and visually inspectable contact/support evidence.

### `attachment_deferred`

Priority:

```text
2
```

Current rows:

```text
0
```

This is the strongest novelty extension but requires a separate candidate
generator and relation-specific witness schema. It should not be mixed into the
current blind sheets until candidates exist.

### `relative_vertical`

Priority:

```text
3
```

Use as a control family. Multi-view helps visibility/identity checks, but the
main relation evidence is mostly 3D vertical geometry.

### `proximity`

Priority:

```text
4
```

Keep as current debugging family. It is useful for dense-noise analysis but is
not the best final multi-view payoff family.

## How This Supports Better Factor Combination

Once completed labels are available, H002 should run combiner diagnostics in this
order:

1. Residual reliability model:

```text
logit P(R=1) = logit P_sem(R=1 | S) + Delta(G,C,U)
```

Purpose:

```text
Does non-semantic evidence explain reliability beyond semantic rank?
```

2. Gated evidence model:

```text
P(R=1) = sigmoid(f_sem(S) + gate(C,U) * f_geom(G) + f_uncertainty(U))
```

Purpose:

```text
Does coverage/uncertainty control when geometry evidence should matter?
```

3. Pairwise rank-matched ranking diagnostic:

```text
score(e_pos) > score(e_neg)
```

Purpose:

```text
Does factorized evidence rank independently audited positives above negatives
inside controlled pairs?
```

4. Debiased factor audit:

```text
G_res = G - E[G | rank_band, semantic_score]
U_res = U - E[U | rank_band, semantic_score]
```

Purpose:

```text
Does geometry/uncertainty evidence survive rank residualization?
```

## Decision

Current status:

```text
independent_label_protocol_ready
```

Meaning:

```text
H002 should collect or fill rank-hidden independent labels before any stronger
posterior method claim.
```

Do not use the current codex labels to choose a larger model. Use this protocol
to create a less confounded supervision source first.

## Next TODO

Next document:

```text
47_independent_label_ingestion.md
```

Goal:

- define how completed blind sheets are validated and joined back to
  `internal_key.jsonl`.
- prevent hidden fields from leaking into deployable features.
- materialize independent binary/multiclass targets.
- prepare residual/gated combiner diagnostics without validation/test rows.
