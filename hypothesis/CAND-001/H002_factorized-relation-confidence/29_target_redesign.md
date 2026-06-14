# H002 Target Redesign

Last updated: 2026-06-13

## Purpose

`28_shortcut_control.md`에서 기존 strict/weak target이 독립적인 relation reliability
target이 아니라는 점이 확인됐다. 특히 strict target은 `HL vs LH`,
`satisfied vs unsatisfied` 구조와 거의 동치였고, shortcut feature를 제거해도 continuous
geometry evidence만으로 완전히 분리됐다.

이 문서는 H002 posterior branch를 계속 검증하기 위한 target v2 contract를 정의한다.

핵심 원칙:

```text
posterior target must not be equivalent to RGA bucket identity
```

따라서 target v2는 geometry status와 RGA bucket을 직접 맞히는 문제가 아니라, 같은
geometry-supported 후보 안에서 relation이 실제로 promote/use 가능한지 구분하는 문제로
재설계한다.

## Input Artifact

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/factor_dataset/target_joined.jsonl
```

Input count:

```text
217 train audit target rows
```

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/target_redesign.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/target_redesign.py
```

Status:

```text
ready_target_v2_contract
```

Boundary:

```text
split = train_only
validation usage = false
paper result = false
human confirmed labels = false
```

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/target_contract.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/target_assignments.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/strict_proximity_informativeness.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/weak_satisfied_actionability.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/target_redesign/report.md
```

## Why Previous Targets Are Blocked

Previous strict target:

```text
positive = true_underconfidence
negative = semantic_overconfidence
```

Problem:

- positives were `geometry_status=satisfied` and semantic tail rows.
- negatives were `geometry_status=unsatisfied` and top100 rows.
- the target became close to `LH vs HL` or `satisfied vs unsatisfied`.

Previous weak target:

```text
positive = true_underconfidence + annotation_sparsity
negative = semantic_overconfidence + dense_relation_noise
```

Problem:

- less trivial than strict because `dense_relation_noise` is also
  geometry-satisfied.
- still strongly explained by geometry/rank construction signals.
- not enough to claim posterior novelty.

## Label Policy

The working labels are reinterpreted as follows.

| Working label | Target v2 role | Rationale |
| --- | --- | --- |
| `true_underconfidence` | positive candidate | geometry-supported relation under-ranked by semantic source |
| `annotation_sparsity` | weak positive candidate | geometry-supported relation likely missing from sparse annotation |
| `dense_relation_noise` | negative candidate | geometry-supported but uninformative/dense relation should not be promoted |
| `ontology_mismatch` | relabel-only | may be useful after predicate canonicalization, not binary keep/reject |
| `semantic_overconfidence` | RGA overconfidence diagnostic | geometry-unsatisfied HL row; excluded from target v2 |
| `uncertain_needs_visual_or_mesh` | abstain | needs human/mesh confirmation before target assignment |

Important decision:

```text
semantic_overconfidence is not a target-v2 negative.
```

It remains central to RGA-HL analysis, but using it as posterior negative repeats
the shortcut that `28_shortcut_control.md` already exposed.

## Target V2 Modes

### 1. Strict Proximity Informativeness

Definition:

```text
eligible if geometry_status = satisfied
eligible if predicate_family = proximity
positive if working_label = true_underconfidence
negative if working_label = dense_relation_noise
```

Counts:

| Class | Rows |
| --- | ---: |
| positive | 16 |
| negative | 11 |
| total | 27 |

Controls:

- all rows are `geometry_status=satisfied`.
- all rows are `predicate_family=proximity`.
- all rows are semantic tail rows.
- the target no longer asks whether geometry is satisfied.
- the target asks whether a satisfied proximity relation is informative enough to
  promote/use.

Boundary:

```text
least-confounded but very small
machine-label only
plumbing smoke allowed
posterior claim blocked
```

### 2. Weak Satisfied Actionability

Definition:

```text
eligible if geometry_status = satisfied
positive if working_label in {true_underconfidence, annotation_sparsity}
negative if working_label = dense_relation_noise
```

Counts:

| Class | Rows |
| --- | ---: |
| positive | 76 |
| negative | 11 |
| total | 87 |

Family distribution:

| Target | Family | Rows |
| --- | --- | ---: |
| negative | `proximity` | 11 |
| positive | `proximity` | 16 |
| positive | `relative_vertical` | 34 |
| positive | `support_contact` | 26 |

Boundary:

```text
larger but family-confounded
sensitivity-only
not a main posterior target
```

The weak target is useful because every eligible row is geometry-satisfied, so it
no longer collapses to `satisfied vs unsatisfied`. However, negatives exist only
in `proximity`, so family confounding remains.

## Excluded Roles

### Ontology Mismatch

`ontology_mismatch` rows are not binary negatives. These rows usually mean the
edge may need predicate canonicalization or relabeling, not rejection.

Use:

```text
relation-to-ontology compiler / relabel action
```

Do not use:

```text
main binary reliability target
```

### Semantic Overconfidence

`semantic_overconfidence` remains important for RGA-HL:

```text
high semantic + geometry unsatisfied
```

But it is excluded from target v2 because including it as negative makes the
posterior target recoverable from geometry status.

Use:

```text
RGA-HL diagnostic, graph suppression/repair audit
```

Do not use:

```text
target-v2 binary negative
```

### Uncertain

`uncertain_needs_visual_or_mesh` is abstain until visual/mesh confirmation.

Use:

```text
human confirmation queue
```

Do not use:

```text
positive or negative target
```

## Decision

Current decision:

```text
Use strict_proximity_informativeness as the next train-only plumbing smoke target.
Use weak_satisfied_actionability only as sensitivity.
Do not claim posterior advantage until labels are human-confirmed.
```

This keeps H002 honest:

- RGA remains the main benchmark/diagnostic contribution.
- Factorized posterior remains a method candidate.
- Target v2 avoids the strongest shortcut, but row count and label quality are
  still insufficient for paper-level claims.

## Human Confirmation Rule

Human confirmation is required before any of the following claims:

- `factorized_reliability_posterior` improves relation reliability.
- target-v2 labels are ground truth reliability labels.
- posterior performance should appear in a paper main table.
- relation promotion/rejection performance generalizes beyond the train pilot.

Machine-assisted labels are allowed only for:

- pipeline debugging.
- target-design sanity checks.
- train-only hypothesis-stage smoke.
- deciding whether a human audit protocol is worth running.

## Current Boundary

Established:

- previous strict/weak targets are blocked for method claims.
- target v2 contract exists.
- `strict_proximity_informativeness.jsonl` has 27 rows.
- `weak_satisfied_actionability.jsonl` has 87 rows.
- no validation rows were used.

Not established:

- human-confirmed target labels.
- posterior advantage over `semantic_plus_geometry`.
- cross-family target balance.
- validation/test performance.
- paper-level main table result.

## Next TODO

Next document:

```text
30_redesigned_target_smoke.md
```

Required next work:

- run train-only smoke on `strict_proximity_informativeness.jsonl`.
- run `weak_satisfied_actionability.jsonl` only as sensitivity.
- remove direct target identity features such as `geometry_status`,
  `predicate_family=proximity`, `tail_gt100_and_satisfied`, and RGA bucket flags
  from the tested view.
- report whether the redesigned target is still trivially predictable.
- keep the result as plumbing diagnostic, not posterior evidence.
