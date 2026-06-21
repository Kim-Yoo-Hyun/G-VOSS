# H002 Full-Train Independent Support/Vertical V2 External Review Fill

## Purpose

`102_full_train_independent_support_vertical_v2_external_review_protocol.md`에서 만든
external evidence review sheet를 사용자 요청에 따라 Codex가 대신 채웠다.

핵심 질문:

```text
Can we fill the revised external review surface without reading hidden target
metadata, numeric witness values, previous proxy labels, source score/rank, or
p_geom_valid?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- user-requested proxy review로 workflow를 진행한다.
- 실제 external human annotation 또는 paper-locked human label은 아니다.
- hidden manifest를 읽지 않는다.
- numeric witness values를 읽지 않는다.
- previous proxy labels를 읽지 않는다.
- source score/rank를 읽지 않는다.
- `p_geom_valid`를 읽지 않는다.
- multi-view는 model input이 아니다.

주의:

```text
This is a Codex proxy fill requested by the user. It is treated as user review
for the next hypothesis workflow step, but it is not paper evidence before user
confirmation.
```

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_fill.py
```

Observed:

```text
status=full_train_independent_support_vertical_v2_external_review_filled_codex_proxy_user_requested
rows=127
reliable=47
unreliable=69
uncertain=11
errors=0
validation_used=False
test_used=False
next=external_evidence_review_label_ingestion
```

## Counts

| Item | Count |
| --- | ---: |
| rows | 127 |
| `support_contact` rows | 72 |
| `relative_vertical` rows | 55 |
| reliable | 47 |
| unreliable | 69 |
| uncertain | 11 |
| validation errors | 0 |

Geometry answer distribution:

| Visual/Mesh Geometry Answer | Count |
| --- | ---: |
| `supports_predicate` | 105 |
| `contradicts_predicate` | 11 |
| `uncertain` | 11 |

## Fill Policy

이번 fill은 revised external review surface의 leakage를 유지하기 위해 다음 파일만 읽었다.

```text
external_evidence_review_sheet.tsv
external_review_schema.json
```

사용하지 않은 정보:

- `external_manifest_post_label_only.jsonl`
- previous proxy human labels
- hidden audit metadata
- relation-validity hidden labels
- `posterior_target_y_hidden`
- source semantic score/rank
- `p_geom_valid`
- deterministic geometry status
- raw numeric witness fields

Label decisions are therefore less target-leaky than the previous proxy-human fill, but
still not equivalent to independent human inspection of every packet image/mesh.

## Interpretation

좋아진 점:

- 127-row sheet가 모두 채워졌다.
- schema validation error는 0이다.
- hidden/numeric/posterior fields를 읽지 않았다.
- 다음 ingestion 단계에서 `geometry_validity_external_target`과
  `relation_reliability_external_target`을 derive할 수 있다.

남은 risk:

- Codex proxy fill이므로 paper-level external annotation이 아니다.
- 실제 packet image/mesh를 사람이 하나씩 판독한 것은 아니다.
- visible identity fields만으로도 hidden prior label과 상관이 생길 수 있다.
- 따라서 다음 단계의 target-independence audit이 여전히 필수다.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/103_full_train_independent_support_vertical_v2_external_review_fill.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_fill.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_fill_codex_proxy_user_requested/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_fill_codex_proxy_user_requested/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_fill_codex_proxy_user_requested/completed_external_evidence_review_sheet_codex_proxy_user_requested.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_fill_codex_proxy_user_requested/external_proxy_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_v2_external_review_fill_codex_proxy_user_requested/fill_validation_errors.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_fill.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_v2_external_review_fill.py
```

Line counts:

```text
completed_external_evidence_review_sheet_codex_proxy_user_requested.tsv = 127 rows + header
external_proxy_labels.jsonl = 127
fill_validation_errors.jsonl = 0
```

## Next TODO

Completed by:

```text
104_full_train_independent_support_vertical_v2_external_review_ingestion
```

Goal:

- The external review ingestion was completed in
  `104_full_train_independent_support_vertical_v2_external_review_ingestion.md`.
- Current active next action is `external_evidence_review_target_independence_audit`.
