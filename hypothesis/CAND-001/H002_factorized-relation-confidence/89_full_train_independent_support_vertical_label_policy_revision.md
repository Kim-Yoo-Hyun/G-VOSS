# H002 Full-Train Independent Support/Vertical Label Policy Revision

## Purpose

`88_full_train_independent_support_vertical_target_independence_audit.md`에서 strict
controlled target이 실패했다. 원인은 model capacity가 아니라 label policy 자체가
이전 bootstrap label/use와 강하게 겹친다는 점이다.

이번 단계의 목적은 direct reliability label을 제거하고, support/vertical second-pass
review를 factual axes로 재설계하는 것이다.

핵심 질문:

```text
Can we revise the label policy so relation reliability is derived after label
lock from independent factual axes rather than directly filled as a target?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- v2 policy는 label protocol revision이지 paper experiment가 아니다.
- hidden metadata는 policy failure audit에만 사용한다.
- multi-view는 audit evidence pointer일 뿐 posterior input이 아니다.
- paper-level posterior claim은 계속 막혀 있다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_policy_revision.py
```

Observed:

```text
status=full_train_independent_support_vertical_label_policy_revision_ready_for_v2_readiness
validation_used=False
rows=127
support=72
vertical=55
same_label=72
same_use=95
next=full_train_independent_support_vertical_v2_label_readiness
```

## Current Policy Failure

현재 v1 label은 prior bootstrap label/use와 너무 많이 겹친다.

| Carryover Item | Rows |
| --- | ---: |
| same prior relation label | 72 / 127 |
| same prior binary use | 95 / 127 |

Association summary:

| Source Key | Target | Majority Acc | NMI |
| --- | --- | ---: | ---: |
| `hidden.relation_validity_label_hidden` | `independent_relation_label` | 0.6142 | 0.4583 |
| `hidden.label_use_hidden` | `label_use` | 0.7480 | 0.3595 |
| `relation_informativeness` | `independent_relation_label` | 0.8268 | 0.7937 |
| `visual_3d_support` | `independent_relation_label` | 0.6457 | 0.5585 |
| `confidence` | `independent_relation_label` | 0.5118 | 0.3160 |

해석:

```text
The v1 label surface is not independent enough because it asks the reviewer to
directly produce a reliability label.
```

특히 `relation_informativeness`와 `visual_3d_support`가 direct label과 거의 같은
역할을 하므로, 이 field들을 posterior input으로 쓰면 target leakage가 된다.

## V2 Policy

V2에서는 labeler-visible direct target field를 제거한다.

Removed from labeler target surface:

```text
independent_relation_label
confidence
subject_identity_valid
object_identity_valid
object_pair_visible
relation_visible_or_inferable
visual_3d_support
relation_informativeness
evidence_notes
```

New factual-axis fields:

```text
endpoint_validity_v2
pair_visibility_v2
relation_geometry_answer_v2
geometry_evidence_strength_v2
relation_informativeness_v2
ontology_fit_v2
uncertainty_reason_v2
audit_notes_v2
```

Labeler가 binary reliability를 직접 찍지 않는다. Binary targets는 label-lock 이후에만
derive한다.

## Target Derivation

V2는 target을 두 개로 분리한다.

### Geometry Validity Target

Positive:

```text
relation_geometry_answer_v2 = supports_predicate
geometry_evidence_strength_v2 in {strong, moderate}
```

Negative:

```text
relation_geometry_answer_v2 = contradicts_predicate
```

Exclude:

```text
ambiguous, not_evaluable, weak, none
```

### Relation Reliability Target

Positive:

```text
endpoint_validity_v2 = both_valid
pair_visibility_v2 in {visible, partially_visible}
relation_geometry_answer_v2 = supports_predicate
geometry_evidence_strength_v2 in {strong, moderate}
relation_informativeness_v2 = informative
ontology_fit_v2 = fits_predicate
```

Negative:

```text
endpoint invalid
or relation_geometry_answer_v2 = contradicts_predicate
or relation_informativeness_v2 in {dense_trivial, redundant_room_structure}
or ontology_fit_v2 in {better_alternative_predicate, ontology_mismatch}
```

Exclude:

```text
uncertain / weak / not_visible / not_evaluable cases
```

## Feature Contract Change

Allowed posterior input candidates after label lock:

- source semantic score/rank normalized within source context.
- continuous geometry evidence from raw witness values.
- automatic geometry coverage/missingness indicators.
- family/predicate identity only as explicit ablation or stratified calibration.

Audit-only, not model input:

- all v2 review fields.
- reviewer id/round.
- audit notes.
- hidden prior labels/use.
- hidden proposed role, label match, geometry status.
- human/Codex reviewer confidence.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_policy_revision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_policy_revision_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_policy_revision_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_policy_revision_codex_ver/v2_completion_schema.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_policy_revision_codex_ver/v2_feature_contract.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_policy_revision_codex_ver/support_vertical_v2_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_policy_revision_codex_ver/support_contact_v2_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_policy_revision_codex_ver/relative_vertical_v2_label_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_policy_revision_codex_ver/carryover_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_label_policy_revision_codex_ver/carryover_matrix.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_policy_revision.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_label_policy_revision.py
```

Observed:

```text
validation_used=False
rows=127
support=72
vertical=55
same_label=72
same_use=95
```

Line counts:

```text
support_vertical_v2_label_sheet.tsv = 128 including header
support_contact_v2_label_sheet.tsv = 73 including header
relative_vertical_v2_label_sheet.tsv = 56 including header
carryover_matrix.jsonl = 127
```

## Next TODO

Next action:

```text
full_train_independent_support_vertical_v2_label_fill
```

Goal:

- v2 readiness는 `90_full_train_independent_support_vertical_v2_label_readiness.md`에서 완료됐다.
- direct reliability label 없이 factual axes만 채운다.
- hidden prior label/use와 target-construction metadata는 fill 중 읽지 않는다.
- geometry validity / relation reliability target은 label lock 이후에만 derive한다.
