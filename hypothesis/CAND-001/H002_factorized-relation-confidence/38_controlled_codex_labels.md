# H002 Controlled Codex Labels

Last updated: 2026-06-13

## Purpose

`37_controlled_label_readiness.md`에서 비어 있던 controlled review sheets를
사용자 지시에 따라 Codex bootstrap label로 먼저 채운다.

중요한 경계:

```text
codex_ver label != human-confirmed label
```

이 단계의 목적은 train-only posterior plumbing을 진행하기 위한 임시 라벨 생성이다.
논문 근거, reviewer agreement, posterior advantage claim에는 사용할 수 없다.

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/fill_controlled_codex_labels.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/fill_controlled_codex_labels.py
```

Result:

```text
status=controlled_codex_ver_labels_filled_not_human_confirmed mined=96 pos=48 neg=48 combined=123 pos=64 neg=59 validation_used=False
```

## Label Mapping

Codex bootstrap mapping:

| Proposed stratum | Final label | Target |
| --- | --- | ---: |
| `candidate_reliable_promote_seed` | `reliable_promote` | 1 |
| `existing_strict_reliable_seed` | `reliable_promote` | 1 |
| `candidate_unreliable_dense_noise_seed` | `unreliable_dense_noise` | 0 |
| `existing_strict_dense_seed` | `unreliable_dense_noise` | 0 |

This mapping is intentionally marked as a bootstrap label because it uses the
controlled sampling prior. It is not independent human evidence.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/mined_controlled_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/combined_review_sheet_codex_ver.tsv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_codex_labels/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_codex_labels/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_codex_labels/mined_codex_ver_labels.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_codex_labels/combined_codex_ver_labels.jsonl
```

The original blank review sheets were preserved:

```text
mined_controlled_sheet.tsv
combined_review_sheet.tsv
```

## Counts

| Sheet | Rows | Positive | Negative |
| --- | ---: | ---: | ---: |
| `mined_controlled` | 96 | 48 | 48 |
| `combined_review` | 123 | 64 | 59 |

## Readiness Recheck

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/controlled_label_readiness.py \
  --mined-sheet hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/mined_controlled_sheet_codex_ver.tsv \
  --combined-sheet hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_target/combined_review_sheet_codex_ver.tsv \
  --output-dir hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness_codex_ver
```

Result:

```text
status=ready_for_train_only_controlled_posterior_smoke mined_completed=96/96 combined_completed=123/123 mined_binary=96 combined_binary=123 validation_used=False
```

Readiness output:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness_codex_ver/mined_binary_targets.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/controlled_label_readiness_codex_ver/combined_binary_targets.jsonl
```

## Decision

Codex-filled controlled labels are ready for train-only posterior plumbing smoke.

Allowed:

- run `controlled_posterior_smoke` as an implementation check.
- compare whether the four baseline views consume the controlled target.

Not allowed:

- claim that H002 posterior is validated.
- report these numbers as paper evidence.
- treat `codex_ver` labels as human-confirmed labels.
- add `V_mv_e` as model input.

## Next TODO

Next document:

```text
39_controlled_posterior_smoke.md
```
