# H002 Attachment Independent Audit Label Fill V1

Date: 2026-06-25 KST

## Purpose

`attachment_independent_audit_subset_plan_v1`에서 만든 `200` row blank review template에
Codex visible-packet proxy label을 채운다.

목표는 proxy construction label이 아니라 reviewer-visible evidence 기준의 독립 label 후보를
만드는 것이다.

```text
old label source = construction proxy
new label source = codex_visible_packet_label_v1
```

## Runner

Command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/attachment_independent_audit_label_fill_v1.py
```

Output:

```text
artifacts/attachment_independent_audit_label_fill_v1/
```

## Boundary

```text
hidden_manifest_used_for_label_decisions = false
prior_v20_labels_used = false
source_score_or_rank_used = false
proxy_construction_label_used = false
validation_usage = false
test_usage = false
paper_evidence_allowed = false
```

The fill uses reviewer-visible fields from `visible_review_template.tsv`: relation text,
subject/object labels, evidence tier, visual context summary, mesh context summary, and audit
question. It does not use the hidden manifest or prior v20 labels for label decisions.

## Result

```text
status = h002_attachment_independent_audit_label_fill_v1_completed
rows = 200
validation_errors = 0
```

Reliability label distribution:

```text
accept_reliable = 17
reject_unreliable = 91
abstain_uncertain = 92
```

Predicate-level distribution:

```text
attached to:
  accept_reliable = 2
  reject_unreliable = 53
  abstain_uncertain = 25

hanging on:
  accept_reliable = 15
  reject_unreliable = 38
  abstain_uncertain = 27

connected to:
  abstain_uncertain = 40
```

Primary binary preview:

```text
accept_reliable = 17
reject_unreliable = 91
binary_preview_rows = 108
```

Auxiliary labels:

```text
geometry_support:
  supported = 17
  unsupported = 63
  uncertain = 120

endpoint_identity:
  clear_endpoint_identity = 170
  uncertain_endpoint_identity = 30

coverage:
  sufficient = 72
  limited = 128
```

## Interpretation

The independent audit fill is positive-sparse. This is not tuned away.

The result says:

```text
attachment-like relation reliability is hard under visible packet evidence,
especially for attached to.
```

This matters for new H002 because the next question is no longer whether a proxy label can be
predicted. The next question is whether the factorized evidence representation can still explain
the independent hard-label structure.

Expected next audit:

```text
Can C_e / Q_e / p_obs / p_rel explain accept/reject/abstain better than source score,
predicate prior, endpoint identity, or construction metadata?
```

## Next TODO

```text
attachment_independent_audit_label_ingestion_v1
```

The next step should ingest the filled sheet with the hidden manifest, create target artifacts, and
run the first viability checks:

- multiclass target: accept / reject / abstain;
- primary binary target: accept / reject only;
- geometry-support target;
- endpoint-identity target;
- coverage/uncertainty target;
- mismatch table against existing GT match;
- source/proxy/endpoint shortcut probes.

## Boundary

- train-only H002 artifact;
- no validation/test data;
- no model training;
- no H001 modification;
- not paper evidence until ingestion and target-independence audit pass.
