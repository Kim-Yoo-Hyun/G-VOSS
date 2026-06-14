# H002 Human Label Readiness

Last updated: 2026-06-13

## Purpose

`31_human_confirmation_protocol.md`에서 만든 strict primary review sheet에 대해
사용자 지시에 따라 Codex bootstrap label을 실제로 채웠다.

Reviewer id:

```text
(codex_ver)
```

Important boundary:

```text
codex_ver label != human-confirmed label
```

따라서 이 단계의 결과는 train-only posterior plumbing smoke를 재개하기 위한 임시
라벨이다. 논문 evidence, posterior advantage claim, reviewer agreement evidence로는
사용하지 않는다.

## Tools

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/codex_fill_strict_labels.py
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/human_label_readiness.py
```

Commands:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/codex_fill_strict_labels.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/human_label_readiness.py
```

The original blank human template is preserved:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/strict_review_sheet.tsv
```

Codex-filled sheet:

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/strict_review_sheet_codex_ver.tsv
```

## Codex Label Mapping

The mapping is controlled and explicit:

| Working label | Codex final label | Posterior target |
| --- | --- | ---: |
| `true_underconfidence` | `reliable_promote` | 1 |
| `dense_relation_noise` | `unreliable_dense_noise` | 0 |

Interpretation:

- `reliable_promote`: geometry-satisfied relation that the semantic source
  under-ranked; suitable positive candidate for relation reliability plumbing.
- `unreliable_dense_noise`: geometry-satisfied but trivial/dense relation that
  should not be promoted as an informative relation; suitable negative candidate.

Filled fields:

| Field | `true_underconfidence` | `dense_relation_noise` |
| --- | --- | --- |
| `reviewer_id` | `(codex_ver)` | `(codex_ver)` |
| `object_pair_valid` | `yes` | `yes` |
| `predicate_visually_plausible` | `yes` | `yes` |
| `geometry_witness_correct` | `yes` | `yes` |
| `relation_informative` | `yes` | `no` |
| `relation_trivial_or_dense` | `no` | `yes` |
| `annotation_missing_or_sparse` | `yes` | `no` |
| `ontology_or_granularity_issue` | `no` | `no` |
| `segmentation_or_instance_issue` | `uncertain` | `uncertain` |
| `confidence` | `medium` | `medium` |

The segmentation field is deliberately `uncertain` because Codex did not perform
a full independent instance-level mesh inspection for all rows.

## Output Artifacts

```text
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/strict_review_sheet_codex_ver.tsv
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/strict_codex_ver_labels.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/strict_codex_ver_binary_targets.jsonl
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/codex_ver_summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/codex_ver_report.md
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/codex_ver_readiness_summary.json
artifacts/train_rga_seed/open3dsg_train_pilot/rga/human_confirmation_protocol/codex_ver_readiness_report.md
```

## Readiness Result

Status:

```text
ready_for_train_only_codex_plumbing_smoke
```

Counts:

| Item | Count |
| --- | ---: |
| strict rows | 27 |
| completed rows | 27 |
| usable binary rows | 27 |
| `reliable_promote` | 16 |
| `unreliable_dense_noise` | 11 |
| positive posterior target | 16 |
| negative posterior target | 11 |
| per-class minimum | 11 |
| missing required fields | 0 |
| invalid values | 0 |
| reviewers | 1 |
| reviewer id | `(codex_ver)` |

The hypothesis-stage minimum from the protocol is structurally satisfied:

| Criterion | Required | Result |
| --- | ---: | ---: |
| strict rows completed | 27 | 27 |
| usable binary rows | >=20 | 27 |
| per-class minimum | >=8 | 11 |
| required fields complete | yes | yes |
| allowed values valid | yes | yes |

## Boundary

Allowed:

- train-set only posterior plumbing smoke.
- feature pipeline sanity check with temporary `(codex_ver)` labels.
- checking whether factorized reliability posterior can consume the strict target.

Not allowed:

- claiming human-confirmed target quality.
- claiming posterior model advantage.
- reporting paper-level metric evidence.
- using validation/test rows.
- treating `(codex_ver)` as independent reviewer agreement.

## Decision

H002 can proceed to a Codex-label-only plumbing smoke:

```text
33_codex_label_smoke.md
```

The goal of the next smoke is narrow:

```text
Can the factorized reliability posterior consume the codex_ver strict labels
without relying on validation/test data or shortcut target leakage?
```

It should still report all results as hypothesis-stage, train-only, and
not-human-confirmed.
