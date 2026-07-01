# Compatibility Dataset V3 Multi-Family Claim Synthesis After Size-Relative

Created: 2026-06-29 KST

## Purpose

`size_relative` result review를 기존 H002 relation-aware evidence-routing synthesis에
반영했다. 이 단계는 새 learned smoke를 실행하지 않고, 현재까지의 relation-family별
evidence route와 claim boundary를 갱신하는 synthesis 단계다.

## Command

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative.py
```

## Artifact

```text
artifact_root = artifacts/compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative/
status = h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative_ready
selected_path = update_relation_aware_compatibility_routing_claim_with_size_relative_select_table_plan_update
validation_errors = 0
next_todo = compatibility_dataset_v3_ablation_and_table_plan_update_after_size_relative_synthesis
```

Generated files:

```text
summary.json
claim_skeleton.json
evidence_table.csv
family_route_table.csv
reviewer_risk_table.csv
route_decision.csv
framework_skeleton.md
next_plan_contract.json
report.md
validation_errors.jsonl
```

## Updated Family Routes

| Family | Role | Claim Position |
| --- | --- | --- |
| `relative_vertical` | clean compatibility mechanism | main mechanism anchor |
| `size_relative` | clean compatibility mechanism | second main mechanism anchor with calibration caveat |
| `support_contact` | challenging compatibility route | main evidence with caveat |
| `proximity` | geometry-easy control | diagnostic / generality control |
| `attachment_like` | observability-heavy route | future / diagnostic |
| `support_contact_superordinate` | diagnostic taxonomy | deferred |
| `relative_horizontal` | reference-frame route | deferred |

## Interpretation

`size_relative` strengthens H002 because it adds a second clean route where `T_e` and
`G_e` must interact. The same object-size-ratio geometry supports either `bigger than`
or `smaller than` depending on predicate semantics. This does not make H002 a
geometry-only framework because geometry-only and no-interaction concat remain near
chance for the size-relative target.

Allowed claim:

```text
H002 supports a train-only mechanism claim: relation families require different
evidence routes, and clean size/vertical routes plus challenging support/contact
controls support explicit predicate-geometry compatibility rather than fixed
score fusion.
```

Still blocked:

- paper-level performance
- held-out/test relation reliability
- all relation-family generality
- support/contact fully solved
- `Q_e` as relation truth
- final calibrated `p_rel` / `p_obs`
- geometry-only reliability framework

## Next

```text
compatibility_dataset_v3_ablation_and_table_plan_update_after_size_relative_synthesis
```

The previous ablation/table plan predates `size_relative`, so it must be updated rather
than reused as-is.
