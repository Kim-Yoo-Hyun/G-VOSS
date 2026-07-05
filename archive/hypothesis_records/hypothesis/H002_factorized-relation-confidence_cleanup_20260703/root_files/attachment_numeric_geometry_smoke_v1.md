# H002 Attachment Numeric Geometry Smoke V1

Date: 2026-06-25 KST

## Purpose

이 문서는 `attachment_numeric_geometry_materialization_v1`에서 만든 numeric attachment
`G_e`가 실제로 compatibility/reliability target에 signal을 갖는지 확인한 train-only
smoke를 기록한다.

핵심 질문:

```text
For attachment_deferred relations, does T_e + G_e compatibility explain
geometry-support labels better than source-only and shortcut probes?
```

## Runner

```text
tools/attachment_numeric_geometry_smoke_v1.py
```

Default command:

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/attachment_numeric_geometry_smoke_v1.py
```

Input:

```text
artifacts/attachment_numeric_geometry_v1/
```

Output:

```text
artifacts/attachment_numeric_geometry_smoke_v1/
```

## Tasks

### Task A: Attachment Compatibility

Target:

```text
geometry-support positive vs contradiction
```

Rows:

```text
114 = 33 positive + 81 negative
```

Scope:

```text
attached to + hanging on
```

`connected to` is excluded from binary compatibility and kept as diagnostic.

### Task B: Observability

Target:

```text
observable vs limited
```

Rows:

```text
240
```

### Task C: Reliability

Target:

```text
accept vs reject
```

Rows:

```text
114 = 33 accept + 81 reject
```

### Task D: Connected Diagnostic

Target:

```text
diagnostic_connected_possible vs diagnostic_connected_ambiguous
```

Rows:

```text
62 = 37 possible + 25 ambiguous
```

## Model Views

| Name | Input |
| --- | --- |
| `M1_source_only_Z` | source score/rank only |
| `M2_semantic_source_TZ` | semantic content plus source confidence |
| `M3_geometry_only_G` | numeric attachment geometry only |
| `M4_compatibility_TG` | semantic content plus numeric geometry |
| `M5_factorized_TZGQ` | semantic, source, geometry, and observability |
| `S1_predicate_family_shortcut` | predicate/family only |
| `S2_source_rank_shortcut` | source score/rank scalar only |
| `H1_hidden_construction_probe` | hidden construction fields, audit only |
| `H2_hidden_witness_score_probe` | hidden witness scores, audit only |

Hidden probes are not deployable model inputs. They are included only to measure whether the target
can be explained by construction artifacts.

## Current Result

Result artifact:

```text
artifacts/attachment_numeric_geometry_smoke_v1/summary.json
```

Task A compatibility:

```text
source-only Z AUROC = 0.4635
semantic+source T+Z AUROC = 0.8148
geometry-only G AUROC = 0.8949
compatibility T+G AUROC = 0.9282
factorized T+Z+G+Q AUROC = 0.9364
predicate/family shortcut AUROC = 0.5305
source/rank shortcut AUROC = 0.4848
hidden construction probe AUROC = 0.8767
hidden witness score probe AUROC = 0.8010
```

Predicate-specific `T+G` compatibility:

```text
attached to AUROC = 0.9378, n = 49
hanging on AUROC = 0.9228, n = 65
```

Connected diagnostic:

```text
geometry-only G AUROC = 0.9081
compatibility T+G AUROC = 0.9265
factorized T+Z+G+Q AUROC = 0.9243
```

Gate result:

```text
dataset sanity = pass
compatibility signal = pass
geometry signal = pass
hidden shortcut audit = pass
overall = attachment_smoke_promising_but_requires_hidden_shortcut_review
validation_errors = 0
```

## Interpretation

This is the first attachment-specific evidence that numeric `G_e` is not merely decorative.
For `attached to` and `hanging on`, geometry-only `G_e` already beats source-only and
predicate/family shortcut probes, and `T_e + G_e` improves further.

However, the result is still not paper-ready:

- Task A is imbalanced: `33/81`.
- `M2 semantic+source T+Z` is already strong.
- hidden construction probes remain high, especially `H1_hidden_construction_probe = 0.8767`.
- v18 labels were created from a controlled packet process, so target construction must still be
  reviewed before promoting this route.

## Boundary

This runner:

- uses train-internal grouped folds only;
- does not use validation/test data;
- does not train a paper model;
- does not modify upstream artifacts;
- does not produce paper-level evidence.

## Follow-Up

```text
attachment_smoke_path_decision_v1 = completed
next = attachment_shortcut_controlled_smoke_v1
```

The path decision selected a stricter shortcut-controlled smoke before any combined prototype
promotion. The next step should:

- run stricter shortcut controls first;
- repair/rebalance the attachment target;
- decide after that whether attachment remains diagnostic or joins the combined H002 prototype.
