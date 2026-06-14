# Audit

Last updated: 2026-05-07

## Role

This document records the compact G4 audit evidence: structured audit,
GT-supported audit-burden reduction, and reduced visual sanity check.

Merged former file:

- `13_human_audit.md`

## Structured Audit

Boundary:

```text
codex_structured_audit_v1 is a structured audit from exported
prediction/geometry fields, not an independent 3D visual rendering review.
```

Sample buckets:

| Bucket | Rows |
| --- | ---: |
| `semantic_topk_violated` | 50 |
| `probabilistic_reranked_away` | 50 |
| `rule_verified_removed` | 50 |
| `uncertain_support_contact` | 50 |
| `family_balanced_random_in_scope` | 50 |

Structured label distribution:

| Label | Count |
| --- | ---: |
| `invalid_relation` | 108 |
| `semantic_label_too_coarse` | 33 |
| `valid_relation` | 84 |
| `ambiguous` | 14 |
| `scan_geometry_missing` | 9 |
| `annotation_noise` | 2 |
| `verifier_error` | 0 |

Structured audit metrics:

| Metric | Value |
| --- | ---: |
| label rows | 250 / 250 |
| strict invalid-only precision | 0.7133 |
| quality-issue precision | 0.8933 |
| invalid-or-noise precision | 0.7200 |

Interpretation:

- Quality-issue precision is the better H001 signal because many
  support/contact cases are valid relation ideas expressed with over-specific
  or coarse predicates.
- This supports the hypothesis-stage reading that verifier violations often
  correspond to real relation-quality issues.

## Reduced Visual Sanity Check

Boundary:

```text
This is a reduced 50-row qualitative sanity check. Do not describe it as a
large-scale or strictly blinded human audit.
```

Facts:

| Item | Value |
| --- | ---: |
| selected rows | 50 |
| unique prediction ids | 50 |
| unique scans | 35 |
| labels filled | 50 / 50 |
| reviewer id | `yhkim` |
| summary status | `ready_sanity_pass` |
| exact private-reference match | 50 / 50 |

Visual label distribution:

| Label | Count |
| --- | ---: |
| `invalid_relation` | 24 |
| `semantic_label_too_coarse` | 8 |
| `scan_geometry_missing` | 3 |
| `valid_relation` | 13 |
| `ambiguous` | 2 |

Target-bucket summary:

| Metric | Value |
| --- | ---: |
| target rows | 30 |
| quality-issue support | 28 / 30 |
| quality-issue rate | 0.9333 |
| contradiction rate | 0.0333 |

Provenance caveat:

```text
yhkim reported that the 50 visual labels were consistent with the private
reference labels, with wording-level differences. Codex transcribed those
confirmed finite-schema labels into labels.jsonl.
```

If a venue or reviewer requires strictly blinded audit wording, repeat the
50-row review with a reviewer who does not inspect `reference.jsonl` before
labeling.

## Audit Interpretation

Facts:

- Structured audit supports violation/quality-issue credibility.
- GT-based verifier evaluation provides the stronger quantitative validity
  signal.
- Reduced visual sanity check supports qualitative paper wording, with the
  provenance caveat above.

Inference:

- The audit evidence is adequate for scoped `VL-SAT`-centered experiment entry.
- It is not enough for broad human-study claims.
- It should not be used to claim a large independent audit.

## Canonical Artifacts

| Artifact | Path |
| --- | --- |
| structured audit root | `artifacts/evaluation/vlsat_closed_set/hardened/human_audit/` |
| structured labels | `artifacts/evaluation/vlsat_closed_set/hardened/human_audit/labels.jsonl` |
| structured label summary | `artifacts/evaluation/vlsat_closed_set/hardened/human_audit/label_summary.json` |
| visual spot-check root | `artifacts/evaluation/vlsat_closed_set/hardened/human_audit/visual_spotcheck/` |
| visual labels | `artifacts/evaluation/vlsat_closed_set/hardened/human_audit/visual_spotcheck/labels.jsonl` |
| visual summary | `artifacts/evaluation/vlsat_closed_set/hardened/human_audit/visual_spotcheck/summary.json` |
