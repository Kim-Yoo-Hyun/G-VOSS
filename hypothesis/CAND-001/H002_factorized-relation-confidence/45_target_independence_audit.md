# H002 Target Independence Audit

Last updated: 2026-06-14

## Purpose

`44_rank_matched_target.md`에서 stricter rank-matched target을 만들었지만,
grouped metric에서는 여전히 `negative_rank_only`가
`factorized_reliability_posterior`보다 강했다.

이번 gate의 질문은 다음이다.

```text
rank matching 이후에도 rank proxy가 강한 이유가 무엇인가?
```

구체적으로는 다음을 분리한다.

- target construction effect
- deployable evidence effect
- label/audit metadata alignment
- geometry-only evidence weakness
- remaining semantic-rank direction

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/target_independence_audit.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/target_independence_audit.py
```

Result:

```text
status=target_independence_not_established feature_rows=16 metadata_rows=16 validation_used=False
```

## Boundary

- Train-only hypothesis-stage audit.
- `(codex_ver)` labels are treated as real labels by user-directed assumption.
- No validation/test rows are used.
- This audit does not train a new posterior.
- `V_mv_e` is not used as model input.
- This is not a paper-level metric.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_independence_audit_codex_real_assumption/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_independence_audit_codex_real_assumption/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_independence_audit_codex_real_assumption/feature_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_independence_audit_codex_real_assumption/metadata_summaries.csv
```

## Main Verdict

Current verdict:

```text
target_independence_not_established
```

Meaning:

```text
Current codex-controlled rank-matched labels are still not independent enough
from semantic-rank / underconfidence construction to support a posterior method
claim.
```

This does not invalidate RGA. It means the current target cannot prove that a
factorized posterior is better than a strong rank proxy.

## Pair Rank Direction

Even after `rank_gap_abs <= 50`, positive rows usually have worse source rank
than matched negative rows.

| Target | Pairs | Mean rank gap | Max rank gap | Positive has worse rank share |
| --- | ---: | ---: | ---: | ---: |
| `mined_rank_matched_gap50_codex_ver` | 43 | 14.56 | 47.00 | 0.8140 |
| `combined_rank_matched_gap50_codex_ver` | 43 | 14.56 | 47.00 | 0.8140 |

Interpretation:

- Rank matching reduced absolute gap.
- But pair direction still strongly favors the underconfidence proxy.
- The label distinction is not independent from source under-ranking.

## Raw Feature Separability

Primary rows are identical for `mined` and `combined`, so the metrics are the
same.

| Feature | Meaning | Mean y1-y0 | AUROC | AUPRC | Pairwise accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| `negative_rank_only_raw` | `1 - semantic_score_norm` | +0.0148 | 0.9459 | 0.9547 | 0.8372 |
| `p_geom_valid_raw` | geometry-only validity | +0.0046 | 0.5041 | 0.6401 | 0.5349 |
| `negative_geometry_residual_raw` | geometry residual inverse | +0.0138 | 0.6092 | 0.6014 | 0.6279 |
| `underconfidence_raw` | underconfidence score | +0.0164 | 0.5251 | 0.6674 | 0.5581 |
| `absolute_disagreement_raw` | semantic-geometry disagreement | +0.0135 | 0.5246 | 0.6672 | 0.5581 |

Key observation:

```text
negative_rank_only_raw is much more separable than raw geometry evidence.
```

Therefore the current positive/negative distinction is closer to:

```text
source underconfidence vs dense relation noise
```

than to:

```text
deployable geometry/coverage/uncertainty evidence explains reliability
```

## Metadata Purity

Two target metadata fields are perfectly aligned with the binary label.

| Field | Unique values | Row-majority purity | Meaning |
| --- | ---: | ---: | --- |
| `final_controlled_label` | 2 | 1.0000 | `reliable_promote` vs `unreliable_dense_noise` maps exactly to y |
| `proposed_review_stratum` | 2 | 1.0000 | sampling stratum maps exactly to y |

Balanced fields:

| Field | Row-majority purity |
| --- | ---: |
| `rank_band` | 0.5000 |
| `predicate_family` | 0.5000 |
| `predicate_label` | 0.5000 |
| `geometry_status` | 0.5000 |

Interpretation:

- Rank band, family, predicate label, and geometry status are controlled.
- But final label and proposed stratum are still tautologically aligned with y.
- This is acceptable for bookkeeping, but not sufficient as independent evidence.

## Target Overlap

The evaluated `mined` and `combined` primary targets are the same row set.

| Left | Right | Intersection | Jaccard |
| --- | --- | ---: | ---: |
| `combined_rank_matched_gap50_codex_ver` | `mined_rank_matched_gap50_codex_ver` | 86 | 1.0000 |

Therefore `combined` does not currently provide independent confirmation for the
rank-matched primary target. Its extra rows are in the tail exploratory set and
are not used in smoke metrics.

## Diagnosis

The current failure is not mainly:

```text
model architecture too weak
```

It is:

```text
label target not independent enough from semantic-rank construction
```

Why:

- positive rows are `reliable_promote`.
- negative rows are `unreliable_dense_noise`.
- these labels are conceptually tied to underconfidence / dense-noise semantics.
- even after close rank matching, positives still more often have worse rank.
- raw geometry validity barely separates the labels.

## Implication For Factorized Combination

Do not use this target to choose a more complex posterior model.

Allowed next modeling checks:

- residual reliability model as an audit, not as a paper claim.
- gated evidence model as a design prototype.
- pairwise rank-matched ranking loss as a diagnostic.
- debiased/orthogonalized factor audit.

Blocked as claim:

```text
factorized posterior improves relation reliability prediction.
```

Reason:

```text
The target is still rank/label-construction confounded.
```

## Minimum Evidence Needed

Before H002 can support a posterior method claim, it needs an independent target.

Required next label/audit properties:

- semantic rank hidden from annotator.
- proposed review stratum hidden from annotator.
- candidate order randomized within matched pairs.
- pair-level labels collected without exposing positive/negative seed identity.
- visual/mesh evidence may be used for audit, but audit rationale must remain
  separated from deployable input features.
- at least one non-proximity family, preferably `support_contact`, should be
  included before method-level claim.

## Decision

Current H002 route:

```text
continue RGA framework and target construction,
pause posterior method claim,
collect independent rank-hidden audit labels.
```

This keeps H002 alive but changes the next blocker:

```text
from model combination -> independent supervision
```

## Next TODO

Next document:

```text
46_independent_label_protocol.md
```

Goal:

- define a rank-hidden independent audit protocol.
- include multi-view as audit evidence, not model input.
- prioritize `support_contact` first, then `attachment_deferred`, then
  `relative_vertical`.
- specify how new labels will support residual/gated factorized combiner tests.
