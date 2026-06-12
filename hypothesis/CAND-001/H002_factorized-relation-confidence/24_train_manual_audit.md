# H002 Train Manual Audit

Last updated: 2026-06-12

## Purpose

`23_train_rga_audit.md`에서 만든 train audit seed를 실제 검토 가능한 review bundle로
변환한다. 이 단계는 contact sheet, mesh/instance asset link, manual sheet, and
machine-assisted working labels를 만든다.

Important boundary:

```text
working label != paper-locked human annotation
```

이번 단계에서 생성한 label은 H002 workflow를 이어가기 위한 train-side working label이다.
사람이 contact sheet/mesh를 확인해 확정한 annotation이 아니므로, final posterior 학습이나
paper-level claim에는 그대로 사용할 수 없다.

## Input

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/audit/audit_seed.jsonl
```

Input rows:

| Queue | Rows |
| --- | ---: |
| `HL` | 47 |
| `LH` | 170 |
| total | 217 |

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/train_manual_audit.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/train_manual_audit.py \
  --render-contact-sheets
```

Status:

```text
status: ready
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/manual_audit/review_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/manual_audit/working_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/manual_audit/needs_human_confirmation.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/manual_audit/manual_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/manual_audit/train_manual_audit_summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/manual_audit/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/manual_audit/contact_sheets/
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/manual_audit/spotcheck_labels.jsonl
```

Line/file counts:

| Artifact | Count |
| --- | ---: |
| `review_queue.jsonl` | 217 rows |
| `working_labels.jsonl` | 217 rows |
| `needs_human_confirmation.jsonl` | 217 rows |
| `manual_sheet.tsv` | 217 rows + header |
| contact sheets | 217 images |
| agent visual spot-check labels | 2 rows |

Asset availability:

| Asset State | Rows |
| --- | ---: |
| `subject_and_object_images` | 217 |

All 217 rows also include scan mesh and instance `.ply` links when present.

## Working Label Policy

Working labels are assigned from queue type, label-match status, relation family,
geometry status, and reason codes. They are intentionally conservative.

Allowed working labels:

```text
true_underconfidence
annotation_sparsity
ontology_mismatch
semantic_overconfidence
dense_relation_noise
object_pair_error
geometry_artifact
uncertain_needs_visual_or_mesh
```

Rules:

- `HL + unsatisfied geometry` -> `semantic_overconfidence`, unless endpoint labels
  are too ambiguous.
- `LH + exact_match` -> `true_underconfidence`.
- `LH + family_match` -> `ontology_mismatch`.
- `LH + pair_has_other_predicate` -> `ontology_mismatch`.
- `LH + no_gt + proximity` -> `dense_relation_noise`.
- `LH + no_gt + relative_vertical` -> `annotation_sparsity`.
- `LH + no_gt + support_contact` -> `annotation_sparsity` or
  `uncertain_needs_visual_or_mesh`.

This policy does not claim that no-GT geometry-satisfied rows are valid missing
positives. It only creates a review prior.

## Working Label Result

| Working Label | Rows |
| --- | ---: |
| `ontology_mismatch` | 63 |
| `true_underconfidence` | 48 |
| `semantic_overconfidence` | 45 |
| `annotation_sparsity` | 28 |
| `uncertain_needs_visual_or_mesh` | 22 |
| `dense_relation_noise` | 11 |

Confidence:

| Confidence | Rows |
| --- | ---: |
| `medium` | 119 |
| `low` | 98 |

Queue split:

| Queue / Working Label | Rows |
| --- | ---: |
| `LH / ontology_mismatch` | 63 |
| `LH / true_underconfidence` | 48 |
| `HL / semantic_overconfidence` | 45 |
| `LH / annotation_sparsity` | 28 |
| `LH / uncertain_needs_visual_or_mesh` | 20 |
| `LH / dense_relation_noise` | 11 |
| `HL / uncertain_needs_visual_or_mesh` | 2 |

Family split:

| Family / Working Label | Rows |
| --- | ---: |
| `support_contact / ontology_mismatch` | 34 |
| `support_contact / semantic_overconfidence` | 27 |
| `relative_vertical / ontology_mismatch` | 24 |
| `relative_vertical / annotation_sparsity` | 23 |
| `support_contact / true_underconfidence` | 21 |
| `relative_vertical / semantic_overconfidence` | 18 |
| `proximity / true_underconfidence` | 16 |
| `proximity / dense_relation_noise` | 11 |
| `relative_vertical / true_underconfidence` | 11 |
| `relative_vertical / uncertain_needs_visual_or_mesh` | 9 |
| `support_contact / uncertain_needs_visual_or_mesh` | 7 |
| `proximity / uncertain_needs_visual_or_mesh` | 6 |
| `proximity / ontology_mismatch` | 5 |
| `support_contact / annotation_sparsity` | 5 |

## Spot Check

Two contact sheets were opened for sanity checking:

| Audit ID | Queue | Predicate | Working Label | Spot-check Label | Note |
| --- | --- | --- | --- | --- | --- |
| `train_audit_0001` | `HL` | `wall lower than floor` | `semantic_overconfidence` | `semantic_overconfidence` | wall/floor relation is not visually plausible as a reliable lower-than edge |
| `train_audit_0048` | `LH` | `couch table close by couch` | `true_underconfidence` | `true_underconfidence` | exact GT close-by, geometry satisfied, semantic rank 275 |

Spot-check boundary:

```text
spotcheck_labels.jsonl = agent visual spot-check, not paper-locked human annotation
```

The purpose is only to verify that generated contact sheets are usable and that
the working-label policy is not obviously inverted on two representative rows.

## Interpretation

The train audit bundle strengthens the need for H002's factorized formulation,
but it does not yet prove the final claim.

Evidence from working labels:

- `true_underconfidence = 48` rows in the seed. These are the cleanest LH signal:
  exact GT relation exists, geometry is satisfied, but the semantic source ranks
  the edge outside top100.
- `ontology_mismatch = 63` rows. These show that label granularity and multiple
  relation labels on the same pair are central to relation reliability.
- `semantic_overconfidence = 45` rows. These keep the original high-semantic /
  low-geometry failure case alive.
- `dense_relation_noise = 11` rows, all from the proximity branch. This confirms
  that LH cannot be used as automatic graph promotion.

Therefore H002 should not model reliability as:

```text
semantic_score * p_geom_valid
```

alone. A useful posterior needs separate semantic, label/audit, geometry,
coverage, and uncertainty factors.

## Current Boundary

Established:

- Train audit rows are reviewable with contact sheets and mesh/instance links.
- All 217 audit seed rows have subject/object visual assets.
- Machine-assisted working labels separate `true_underconfidence`,
  `annotation_sparsity`, `ontology_mismatch`, `semantic_overconfidence`,
  `dense_relation_noise`, and uncertain cases.
- Two agent visual spot-checks confirm that contact sheets are usable.

Not established:

- Human-confirmed manual labels.
- Paper-locked annotation quality.
- Final train labels for posterior fitting.
- Factorized reliability model weights.
- Held-out validation/test performance.

## Next TODO

Next document:

```text
25_factor_contract.md
```

Required next work:

- define the train-only factorized reliability target without using validation.
- decide whether `working_labels.jsonl` is used only for weak supervision or
  whether a human-confirmed subset is required first.
- specify feature blocks for semantic-only, geometry-only, semantic+geometry,
  and factorized posterior baselines.
- define leakage rules for label evidence: GT/audit labels are allowed for
  training/evaluation supervision, not as deployment-time input.
