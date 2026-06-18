# H002 Full-Train Independent Support/Vertical Audit Packet

## Purpose

이 문서는 83번 claim boundary에서 선택한 H002 revised-factor scope,
`support_contact + relative_vertical`,에 대해 independent audit packet을 만든다.

핵심 질문:

```text
현재 claim을 직접 검증할 selected support/vertical rows를 hidden target-construction
metadata 없이 labeler에게 제공할 수 있는가?
```

## Boundary

- Split: Open3DSG train-only.
- 새 paper-level experiment는 아니다.
- validation/test는 사용하지 않는다.
- selected scope는 `support_contact + relative_vertical`이다.
- `proximity`는 main audit packet에서 제외하고 risk slice로 보존한다.
- multi-view/mesh/pointcloud packet은 audit evidence only다.
- multi-view/mesh/pointcloud는 posterior input이 아니다.
- labeler sheet에는 source score/rank, `p_geom_valid`, `geometry_status`, target label,
  `label_match_status`, `proposed_audit_role`, `queue_kind` 등을 노출하지 않는다.
- hidden metadata는 `internal_reference_post_label_only.jsonl`에만 보존한다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_audit_packet.py
```

Observed:

```text
status=full_train_independent_support_vertical_audit_packet_ready
validation_used=False
selected_rows=127
support=72
vertical=55
leakage_hits=0
next=full_train_independent_support_vertical_label_readiness
```

## Input

이 packet은 다음 artifact를 사용한다.

```text
independent_revised_factor_dataset_codex_ver/revised_factor_rows.jsonl
independent_revised_factor_claim_boundary_codex_ver/summary.json
asset_packet_gap_audit/label_ready_support_contact_sheet_with_packets.tsv
asset_packet_gap_audit/label_ready_relative_vertical_sheet_with_packets.tsv
```

선택 기준:

```text
predicate_family in {support_contact, relative_vertical}
```

이 기준은 revised-factor posterior evidence를 만든 158-row controlled set에서
`support_contact` 72 rows와 `relative_vertical` 55 rows만 선택한다.

## Output Summary

| Item | Count |
| --- | ---: |
| selected rows | 127 |
| support_contact rows | 72 |
| relative_vertical rows | 55 |
| ready packet rows | 124 |
| ready with packet caveat rows | 3 |
| missing packet rows | 0 |
| proximity risk rows | 31 |
| labeler leakage hits | 0 |
| packet text leakage hits | 0 |

## Labeler Surface

Labeler에게 보이는 sheet는 다음 파일이다.

```text
support_vertical_audit_sheet.tsv
support_contact_audit_sheet.tsv
relative_vertical_audit_sheet.tsv
```

Sheet에는 다음 종류의 정보만 들어간다.

- blind review id
- scan/context id
- subject/object id와 label
- predicate label/family
- family-specific audit question/cues
- evidence packet path
- raw witness values:
  - distance XY/3D
  - center delta Z
  - vertical gap
  - projected IoU/overlap
  - support-contact gap/overlap witness
  - relative-vertical signed margin/sign agreement witness
- reviewer fill-in fields

Sheet에는 다음 정보가 없다.

- source model score/rank
- `p_geom_valid`
- `geometry_status`
- posterior target `y`
- relation validity bootstrap label
- label source
- `label_match_status`
- `proposed_audit_role`
- `queue_kind`
- `rank_band`
- prediction id

## Internal Reference

Post-label join용 hidden reference는 따로 저장했다.

```text
internal_reference_post_label_only.jsonl
```

이 파일에는 hidden target/audit metadata가 들어가므로 labeler에게 제공하면 안 된다.
용도는 label lock 이후 다음 항목을 분석하는 것이다.

- bootstrap target과 human label의 일치/불일치
- `geometry_status_hidden`별 label 변화
- `label_match_status_hidden`별 label 변화
- `proposed_audit_role_hidden`별 shortcut risk
- semantic rank/p_geom/disagreement와 human label의 post-hoc 관계

## Proximity Risk Slice

`proximity`는 main audit packet에서 제외했다.

이유:

```text
proximity_only D4 dAUPRC = -0.0917
proximity_only D4 dBrier = +0.0290
```

다만 failure/risk 분석을 위해 다음 파일에 보존했다.

```text
proximity_risk_slice_post_label_only.jsonl
```

이 파일도 labeler용 main sheet가 아니라 post-label/risk analysis용이다.

## Leakage Audit

Leakage audit 결과:

```text
labeler_surface_hit_count = 0
packet_text_hit_count = 0
```

검사 대상:

- labeler sheet headers
- labeler sheet values
- sampled linked packet text

금지된 정보 범주:

- source score/rank
- `p_geom`
- `geometry_status`
- H001 verification status
- queue/proposed role/candidate axis
- prediction id
- target label
- label source
- matched GT/predicate
- machine hint/reason code
- disagreement/uncertainty-derived shortcut terms

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_audit_packet_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_audit_packet_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_audit_packet_codex_ver/support_vertical_audit_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_audit_packet_codex_ver/support_contact_audit_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_audit_packet_codex_ver/relative_vertical_audit_sheet.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_audit_packet_codex_ver/internal_reference_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_audit_packet_codex_ver/proximity_risk_slice_post_label_only.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_audit_packet_codex_ver/manifest.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_audit_packet_codex_ver/leakage_hits.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_audit_packet.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_audit_packet.py
```

Observed:

```text
validation_used=False
selected_rows=127
support=72
vertical=55
leakage_hits=0
```

## Next TODO

Completed next action:

```text
full_train_independent_support_vertical_label_readiness
```

Result:

```text
status=full_train_independent_support_vertical_label_readiness_ready_for_label_fill
rows=127
errors=0
leakage=0
next=full_train_independent_support_vertical_label_fill
```

Next action:

```text
full_train_independent_support_vertical_label_fill
```

Goal:

- `support_vertical_label_fill_sheet.tsv`의 127 rows를 schema에 맞춰 채운다.
- hidden internal reference는 label lock 전까지 사용하지 않는다.
- label fill 후 ingestion을 통해 independent labels와 hidden reference를 post-label로만 join한다.
