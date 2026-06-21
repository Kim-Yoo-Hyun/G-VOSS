# H002 Full-Train Independent Support/Vertical V2 Reviewer Provenance Decision

## Purpose

`112_full_train_independent_support_vertical_v2_user_submitted_review_target_independence_audit.md`의
next TODO인 `confirm_reviewer_independence_or_collect_external_labels`를 진행했다.
이번 단계는 user-submitted sheet를 독립 reviewer label로 확정할 수 있는지 artifact
수준에서 확인하고, target audit blocker까지 함께 고려해 다음 경로를 고정한다.

핵심 질문:

```text
Can H002 treat the submitted 70-row sheet as independent labels and open
posterior smoke, or should it collect a fresh external full-127 label pass?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- H001 artifact를 사용하거나 수정하지 않는다.
- multi-view는 audit/label evidence로만 유지하며 posterior input으로 승격하지 않는다.
- 이 단계는 label provenance와 target-readiness decision이며 성능 실험이 아니다.

## Execution

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_reviewer_provenance_decision.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_reviewer_provenance_decision.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_reviewer_provenance_decision_collect_external_labels
user_rows=70
codex_like_rows=70
independence_confirmed=False
relation_strict=none
relation_construction=none
external_rows=127
validation_used=False
test_used=False
next=collect_external_full127_labels_with_fixed_reviewer_provenance
```

## Decision

선택:

```text
collect_fresh_full127_external_labels_with_fixed_reviewer_provenance
```

이유:

- 제출된 70-row sheet의 `external_reviewer_id`가 모두 `codex_packet_only_diagnostic`이다.
- 따라서 artifact 수준에서는 독립 reviewer provenance가 확인되지 않는다.
- provenance를 별도로 확인하더라도, 112 audit에서 strict slice와 construction-only slice가
  모두 `none`이었다.
- 즉, reviewer provenance 문제와 target-independence 문제 둘 다 posterior smoke를 막는다.
- 기존 full-127 external protocol은 127 rows, ready packets 124, ready-with-caveat 3,
  packet path errors 0, header leakage hits 0이므로 다음 label surface로 가장 적절하다.

## Reviewer Provenance Result

| Item | Value |
| --- | --- |
| submitted rows | 70 |
| reviewer id counts | `{'codex_packet_only_diagnostic': 70}` |
| review round counts | `{'r1_20260619_packet_only': 70}` |
| codex-like reviewer rows | 70 |
| artifact-level independence confirmed | `False` |

해석:

- 이 결과는 사용자가 실제로 sheet를 보지 않았다는 뜻이 아니다.
- 다만 현재 파일 안에 남은 provenance 정보만으로는 독립 reviewer label이라고 주장할 수 없다.
- paper-level 또는 posterior method-validation label로 쓰려면 non-Codex reviewer id와
  packet-only confirmation이 필요하다.

## Target Audit Carryover

| Target | Rows | Pos | Neg | Status | Strict Slice | Construction Slice |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `geometry_validity_user_submitted_review_target` | 68 | 57 | 11 | `blocked_no_controlled_slice` | `none` | `none` |
| `relation_reliability_user_submitted_review_target` | 68 | 35 | 33 | `blocked_no_controlled_slice` | `none` | `none` |

해석:

- relation target의 class balance는 나쁘지 않지만 hidden prior carryover를 제거한
  controlled slice가 없다.
- geometry target은 57/11로 개선됐지만 negative class가 작다.
- 따라서 provenance만 수정해서 같은 labels를 다시 쓰는 것은 충분하지 않다.

## External Label Path

다음 label pass는 full-127 external sheet로 진행한다.

| Item | Count |
| --- | ---: |
| full external review rows | 127 |
| `support_contact` rows | 72 |
| `relative_vertical` rows | 55 |
| ready packets | 124 |
| ready with packet caveat | 3 |
| packet path errors | 0 |
| header leakage hits | 0 |

Labeler-visible constraints:

- `external_reviewer_id`는 실제 non-Codex reviewer id로 채운다.
- `external_review_round`는 실제 review pass id로 채운다.
- multi-view packet, mesh/point-cloud packet, contact/context sheet만 사용한다.
- source score/rank, `p_geom_valid`, hidden metadata, previous proxy labels, posterior target
  fields는 사용하지 않는다.
- multi-view는 audit evidence일 뿐 아직 posterior input이 아니다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/113_full_train_independent_support_vertical_v2_reviewer_provenance_decision.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_reviewer_provenance_decision.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_reviewer_provenance_decision/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_reviewer_provenance_decision/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_reviewer_provenance_decision/provenance_confirmation_request.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_reviewer_provenance_decision/external_label_collection_request.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_reviewer_provenance_decision/external_evidence_review_sheet_full127_fixed_provenance.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_reviewer_provenance_decision/external_manifest_full127_post_label_only.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_reviewer_provenance_decision.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_reviewer_provenance_decision.py
wc -l hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_reviewer_provenance_decision/external_evidence_review_sheet_full127_fixed_provenance.tsv hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_reviewer_provenance_decision/external_manifest_full127_post_label_only.jsonl
```

Observed:

```text
external_evidence_review_sheet_full127_fixed_provenance.tsv = 128 lines
external_manifest_full127_post_label_only.jsonl = 127 lines
validation_used=False
test_used=False
```

## Next TODO

Current next action:

```text
collect_external_full127_labels_with_fixed_reviewer_provenance
```

Goal:

- fill the full-127 external sheet using a real non-Codex reviewer id.
- keep the reviewer-provenance confirmation with the label artifacts.
- ingest the completed full-127 labels only after label lock.
- rerun target-independence audit before any posterior smoke.
- keep posterior combiner upgrade blocked until target/evidence independence is defensible.
