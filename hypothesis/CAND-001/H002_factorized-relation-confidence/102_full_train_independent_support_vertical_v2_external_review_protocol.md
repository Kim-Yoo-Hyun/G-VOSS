# H002 Full-Train Independent Support/Vertical V2 External Review Protocol

## Purpose

`101_full_train_independent_support_vertical_v2_human_target_independence_audit.md`에서
Codex-proxy human target도 strict relation-reliability slice를 만들지 못했다.
이번 단계는 그 원인을 반영해, 다음 label pass를 위한 external evidence review protocol을
만든다.

핵심 질문:

```text
Can we create a label protocol whose target is not a re-reading of the same
numeric geometry witness and prior target-construction labels?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- combiner upgrade를 진행하지 않는다.
- multi-view, mesh, contact/context packet은 audit/label evidence로만 사용한다.
- multi-view는 아직 posterior input이 아니다.
- source score/rank, `p_geom_valid`, deterministic geometry status, numeric witness,
  previous proxy labels, hidden prior labels, v2 reference axes는 labeler-visible field에서
  제거한다.

## Motivation

101 audit의 실패 원인은 단순히 Codex가 human을 대신했기 때문만은 아니다. 더 직접적인
문제는 이전 sheet가 다음 정보를 labeler-visible surface에 포함했다는 점이다.

- numeric geometry witness values
- positive/negative cue text
- predicate-family-specific rule prompt

이 정보는 posterior에서 사용하려는 deployable geometry evidence와 너무 가깝다. 따라서
labeler가 독립적으로 판단했다기보다 기존 target construction을 다시 읽는 형태가 될 수
있다. 실제 audit에서도 `relation_validity_label_hidden`, `label_use_hidden`,
`posterior_target_y_hidden` carryover가 계속 남았다.

## Revised Protocol

새 protocol은 labeler-visible sheet를 다음 정보로 제한한다.

- relation identity: subject, predicate, object
- predicate family question
- evidence packet paths
- external review completion fields

숨기는 정보:

- source semantic score/rank
- `p_geom_valid`
- deterministic geometry status
- raw numeric witness values
- old positive/negative cue text
- previous Codex proxy labels
- hidden prior labels
- v2 reference axes
- posterior target fields

Labeler는 `multiview_packet`, `pointcloud_or_mesh_packet`, `contact_or_context_sheet`만 보고
visual evidence와 mesh evidence를 분리해 판단한다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_protocol.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_external_review_protocol_ready
rows=127
ready_packets=124
packet_path_errors=0
header_leakage_hits=0
validation_used=False
test_used=False
next=fill_external_evidence_review_sheet_or_user_review
```

## Counts

| Item | Count |
| --- | ---: |
| review rows | 127 |
| `support_contact` rows | 72 |
| `relative_vertical` rows | 55 |
| ready packets | 124 |
| ready with packet caveat | 3 |
| packet path errors | 0 |
| labeler header leakage hits | 0 |

## Labeler-Visible Fields

Visible sheet fields:

```text
blind_review_id
review_scope
scan_id
scene_context_id
subject_id
subject_label
predicate_label
predicate_family
object_id
object_label
family_question
evidence_packet_status
multiview_packet
pointcloud_or_mesh_packet
contact_or_context_sheet
external_reviewer_id
external_review_round
endpoint_identity_external
visual_pair_evaluability_external
mesh_pair_evaluability_external
visual_geometry_answer_external
mesh_geometry_answer_external
relation_informativeness_external
final_relation_reliability_external
uncertainty_reason_external
external_label_notes
```

Leakage check:

```text
score/rank/p_geom/geometry_status/target_y/label_use/relation_validity_label/
posterior/v2/witness/positive_cues/negative_cues/human/proxy header hits = 0
```

## Target Derivation Contract

After label lock:

```text
geometry_validity_external_target
```

- positive: visual or mesh answer supports the predicate and neither available
  modality clearly contradicts it.
- negative: visual or mesh answer contradicts the predicate with evaluable evidence
  and no supporting modality.
- exclude: endpoint unclear/wrong, visual and mesh uncertain, missing evidence, or
  reviewer uncertainty.

```text
relation_reliability_external_target
```

- positive: endpoint identity is valid, geometry supports the predicate, relation is
  informative, and final reliability is `reliable`.
- negative: final reliability is `unreliable`, endpoint is wrong, geometry contradicts
  the predicate, ontology mismatch, or trivial dense/room-structure relation.
- exclude: final reliability is `uncertain` or evidence is insufficient.

## Interpretation

이번 단계의 결론:

```text
The next defensible path is not a stronger posterior combiner. It is an external
evidence label pass that avoids reusing numeric witness fields and prior
target-construction labels as the label surface.
```

좋아진 점:

- Full 127-row external evidence review sheet가 생성됐다.
- labeler-visible header leakage가 0이다.
- packet path error가 0이다.
- numeric witness와 previous proxy labels는 post-label manifest로만 보존된다.

남은 caveat:

- 127 rows 중 3 rows는 `ready_with_packet_caveat`다.
- 아직 external review label이 채워진 것은 아니다.
- posterior smoke는 여전히 blocked다.

가능한 사용:

- next human/user/external review input.
- target-independence blocker를 해결하기 위한 protocol revision evidence.
- multi-view/mesh/contact evidence를 audit axis로 편입하는 H002 근거.

불가능한 사용:

- factorized posterior performance claim.
- multi-view input method claim.
- paper-level external annotation completion claim.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/102_full_train_independent_support_vertical_v2_external_review_protocol.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_protocol.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_protocol/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_protocol/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_protocol/external_evidence_review_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_protocol/external_manifest_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_protocol/external_review_schema.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_protocol/reviewer_instructions.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_protocol/labeler_header_leakage_hits.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_protocol/packet_path_errors.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_protocol.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_protocol.py
```

Line counts:

```text
external_evidence_review_sheet.tsv = 127 rows + header
external_manifest_post_label_only.jsonl = 127
labeler_header_leakage_hits.jsonl = 0
packet_path_errors.jsonl = 0
```

## Next TODO

Completed by:

```text
103_full_train_independent_support_vertical_v2_external_review_fill
```

Goal:

- The requested user-proxy fill was completed in
  `103_full_train_independent_support_vertical_v2_external_review_fill.md`.
- Current active next action is `external_evidence_review_label_ingestion`.
