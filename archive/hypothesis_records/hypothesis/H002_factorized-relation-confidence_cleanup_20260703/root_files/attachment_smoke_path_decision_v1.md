# H002 Attachment Smoke Path Decision V1

Date: 2026-06-25 KST

## Purpose

이 문서는 `attachment_numeric_geometry_smoke_v1` 이후의 path decision을 기록한다.
결정해야 할 질문은 다음이다.

```text
Should attachment_deferred numeric G_e be promoted into the combined H002 prototype now,
or should it remain diagnostic until stricter shortcut controls pass?
```

## Input Evidence

Input artifact:

```text
artifacts/attachment_numeric_geometry_smoke_v1/
```

Task A attachment compatibility:

```text
rows = 114
positive / negative = 33 / 81
source-only Z AUROC = 0.4635
semantic+source T+Z AUROC = 0.8148
geometry-only G AUROC = 0.8949
compatibility T+G AUROC = 0.9282
factorized T+Z+G+Q AUROC = 0.9364
predicate/family shortcut AUROC = 0.5305
hidden construction probe AUROC = 0.8767
hidden witness score probe AUROC = 0.8010
```

Predicate-specific `T+G`:

```text
attached to AUROC = 0.9378, n = 49
hanging on AUROC = 0.9228, n = 65
```

Connected diagnostic:

```text
connected diagnostic T+G AUROC = 0.9265, n = 62
```

## What Is Good

Attachment numeric `G_e` is useful.

Evidence:

```text
geometry-only G AUROC = 0.8949
source-only Z AUROC = 0.4635
predicate/family shortcut AUROC = 0.5305
```

This means the materialized numeric geometry evidence is not merely copying source confidence or
predicate frequency.

`T_e + G_e` also improves over geometry-only:

```text
T+G AUROC = 0.9282
G-only AUROC = 0.8949
```

This supports the H002 compatibility-learning direction:

```text
predicate semantics should condition how geometry evidence is interpreted.
```

## What Blocks Immediate Promotion

The attachment target is still construction-sensitive.

Hidden construction probe:

```text
H1_hidden_construction_probe AUROC = 0.8767
```

Hidden witness score probe:

```text
H2_hidden_witness_score_probe AUROC = 0.8010
```

These fields are not model inputs, but they reveal that the current v18 target can be partly
explained by how candidates were constructed.

The strongest visible issue is cell imbalance:

```text
A1_attached_near_anchor_supported_candidate: positive 8 / negative 10
A2_attached_far_or_floor_confound_candidate: positive 3 / negative 27
H1_hanging_anchor_supported_candidate: positive 21 / negative 5
H2_hanging_no_anchor_or_floor_supported_candidate: positive 1 / negative 26
U1_attachment_missing_or_uncertain_coverage_audit: positive 0 / negative 13
```

This means a reviewer could reasonably ask whether the model learns attachment compatibility or
simply recovers the candidate construction bucket.

The primary target is also imbalanced:

```text
positive / negative = 33 / 81
```

The class mass is enough for hypothesis smoke, but not enough for a main method claim.

## Decision

Do not promote attachment numeric `G_e` directly into the main combined H002 prototype yet.

Selected path:

```text
attachment_shortcut_controlled_smoke_v1
```

Attachment is upgraded from `blocked/no numeric G_e` to:

```text
promising diagnostic extension requiring shortcut-controlled confirmation
```

## Decision Matrix

| Option | Decision | Reason |
| --- | --- | --- |
| Promote attachment into combined H002 prototype now | Reject for main claim | Signal is strong, but hidden construction probe remains high. |
| Keep attachment permanently diagnostic-only | Reject | Numeric `G_e` and `T+G` compatibility are strong enough to justify one stricter control pass. |
| Run stricter shortcut controls first | Select | Best balance between preserving the promising signal and avoiding shortcut-driven novelty risk. |
| Rebuild labels from scratch immediately | Defer | Current rows already support a smaller within-cell control smoke; use that before expensive relabeling. |

## Next Control

Next TODO:

```text
attachment_shortcut_controlled_smoke_v1
```

Minimum control design:

1. Build a strict within-cell balanced slice from Task A rows.
2. Use only rows where the hidden construction cell has both positive and negative examples.
3. Downsample each hidden cell to matched positive/negative counts.
4. Re-run source-only, geometry-only, `T+G`, `T+Z`, `T+Z+G+Q`, predicate/family shortcut, and hidden probes.
5. Report whether `T+G` remains above hidden probes on the controlled slice.

Expected strict slice from current counts:

```text
A1: 8 positive + 8 negative
A2: 3 positive + 3 negative
H1: 5 positive + 5 negative
H2: 1 positive + 1 negative
total = 34 rows
```

This slice is small, so it should not be used as paper evidence. Its purpose is to decide whether
attachment deserves a larger controlled mining/labeling pass.

## Promotion Rule

Attachment can be merged into the combined H002 prototype only if one of the following is true:

```text
strict controlled smoke passes
```

or

```text
new controlled mining increases within-cell balanced compatibility rows
and T+G remains stronger than source-only, predicate/family shortcut, and hidden construction probes.
```

If the strict control fails:

```text
attachment remains diagnostic/future-work evidence,
while support_contact and relative_vertical remain the safer main compatibility-learning scope.
```

## Boundary

This path decision:

- uses train-only hypothesis artifacts;
- does not use validation/test data;
- does not train a paper model;
- does not promote attachment results to paper-level evidence;
- does not modify H001 artifacts.

## Follow-Up Result

`attachment_shortcut_controlled_smoke_v1` was completed on 2026-06-25.

Controlled slice:

```text
rows = 34
positive / negative = 17 / 17
pair groups = 17
hidden cells = 4
validation_errors = 0
```

Key metrics:

```text
source-only Z AUROC = 0.5467
geometry-only G AUROC = 0.7232
compatibility T+G AUROC = 0.9550
factorized T+Z+G+Q AUROC = 0.9689
predicate/family shortcut AUROC = 0.5000
hidden construction probe AUROC = 0.5000
hidden witness score probe AUROC = 0.5000
```

Decision update:

```text
strict_control_passed = true
direct_paper_promotion = false
next = attachment_controlled_expansion_plan_v1
```

Interpretation:

- the previous hidden construction shortcut does not survive strict within-cell balancing;
- attachment numeric `G_e` remains promising;
- the controlled slice is too small for paper evidence, so the next step is larger controlled
  attachment mining rather than direct combined-prototype promotion.
