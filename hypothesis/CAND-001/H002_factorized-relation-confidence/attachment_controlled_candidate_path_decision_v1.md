# H002 Attachment Controlled Candidate Path Decision V1

Date: 2026-06-25 KST

## Purpose

이 문서는 `attachment_controlled_candidate_smoke_v1` 이후의 path decision을 기록한다.
결정해야 할 질문은 다음이다.

```text
Should the 400-row attachment controlled candidate set be promoted into the combined H002
prototype, used only as compatibility-proxy/pretraining evidence, or repaired through
independent visual/mesh/human audit labels?
```

## Input Evidence

Input artifact:

```text
artifacts/attachment_controlled_candidate_smoke_v1/
```

Primary compatibility task:

```text
rows = 320
positive / negative = 160 / 160
attached to = 80 positive + 80 counterfactual negative
hanging on = 80 positive + 80 counterfactual negative
connected to = 80 diagnostic rows, not primary binary
validation_errors = 0
```

Main smoke metrics:

```text
source-only Z AUROC = 0.4585
semantic+source T+Z AUROC = 0.4798
geometry-only G AUROC = 1.0000
compatibility T+G AUROC = 1.0000
factorized T+Z+G+Q AUROC = 1.0000
predicate/family shortcut AUROC = 0.4876
source-rank shortcut AUROC = 0.4908
endpoint-label-pair shortcut AUROC = 0.5074
hidden cell/construction probe AUROC = 1.0000
```

## What Is Good

The 400-row attachment candidate set is useful as a geometry evidence stress test.

The visible shortcut probes are weak:

```text
source-only Z AUROC = 0.4585
predicate/family shortcut AUROC = 0.4876
source-rank shortcut AUROC = 0.4908
endpoint-label-pair shortcut AUROC = 0.5074
```

This means the proxy target is not explained by source confidence, source rank, predicate label,
or endpoint label-pair identity.

The numeric `G_e` features are also strong:

```text
geometry-only G AUROC = 1.0000
compatibility T+G AUROC = 1.0000
```

So the materialized pair-geometry feature schema is functioning. The current result supports this
limited claim:

```text
predicate-independent pair geometry can recover the constructed attachment compatibility proxy.
```

## What Blocks Promotion

The current target is still construction-defined.

The hidden probes are perfect:

```text
hidden cell probe AUROC = 1.0000
hidden construction probe AUROC = 1.0000
```

These hidden fields are not model inputs, but they reveal that the binary target is recoverable from
how the 400 rows were constructed. Therefore, a reviewer could reasonably say:

```text
The model is solving the construction proxy, not independent relation reliability.
```

This is not a failure of the H002 factorization itself. It means the current attachment target is
not the right evaluation target for `p_rel` or final relation reliability.

## Decision

Do not promote the 400-row attachment proxy labels into the combined H002 reliability prototype.

Selected status:

```text
attachment_400_proxy_status = compatibility_proxy_pretraining_only
attachment_feature_schema_status = keep
attachment_proxy_label_status = do_not_use_as_paper_reliability_target
attachment_paper_evidence_status = not_promoted
```

Selected next step:

```text
attachment_independent_audit_subset_plan_v1
```

The next step should create an audit plan that converts a subset of attachment rows into
independent labels using visual/mesh evidence and human-visible review fields.

## Decision Matrix

| Option | Decision | Reason |
| --- | --- | --- |
| Promote 400-row proxy labels into main H002 reliability prototype | Reject | Hidden construction probes are perfect, so the target is not independent. |
| Discard attachment entirely | Reject | Numeric `G_e` is strong and visible shortcuts are weak; the family is still valuable. |
| Use 400-row rows for compatibility pretraining or representation smoke only | Select with boundary | The label is a valid constructed proxy if it is named as such, not as reliability GT. |
| Merge only the feature schema into the combined prototype | Select | The `T_e/Z_e/G_e/Q_e` schema and pair-geometry join are valid engineering outputs. |
| Add visual/mesh/human audit confirmation | Select as next | Independent labels are needed before any reliability claim. |
| Mine another proxy-only target immediately | Reject for now | More proxy rows will not solve hidden construction dominance. |
| Train a stronger combiner now | Reject | The bottleneck is target independence, not model capacity. |

## Next Audit Plan Contract

Next TODO:

```text
attachment_independent_audit_subset_plan_v1
```

Minimum design:

```text
candidate_source = artifacts/attachment_controlled_candidates_v1/candidate_rows.jsonl
audit_split = train_only
primary_predicates = attached to, hanging on
diagnostic_predicate = connected to
model_input_fields_hidden_from_reviewer = source score/rank, proxy role, hidden cell,
                                          construction status, machine hints, proxy label
audit_evidence = point/mesh geometry summary + available visual/multi-view packet if present
audit_labels = accept / reject / abstain
```

Recommended subset target:

```text
primary audit rows = 160
attached to = 80
hanging on = 80
diagnostic connected rows = 40 optional
```

The audit should sample across the existing positive and negative proxy cells, but the final label
must be assigned from visual/mesh/geometry evidence, not copied from proxy construction.

## Promotion Gates After Audit

Attachment can move beyond diagnostic/pretraining evidence only if the independent audit subset
passes these gates:

```text
binary usable audit rows >= 80
per primary predicate binary usable rows >= 30
minority class count >= 20
validation_errors = 0
source-only Z does not dominate
predicate/family shortcut does not dominate
endpoint-label-pair shortcut AUROC <= 0.70
hidden construction probe AUROC < T+G AUROC - 0.05
T+G or factorized model beats source-only and visible shortcuts
```

If these gates fail, attachment remains:

```text
geometry evidence schema / proxy-pretraining / qualitative diagnostic evidence
```

and the safer main H002 scope remains `support_contact` and `relative_vertical`.

## Boundary

This path decision:

- uses train-only hypothesis artifacts;
- does not use validation/test data;
- does not train a paper model;
- does not modify H001 artifacts;
- does not promote attachment proxy labels to paper-level reliability evidence;
- keeps multi-view/mesh evidence as audit confirmation first, not deployable model input.
