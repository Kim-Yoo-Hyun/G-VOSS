# H002 Full-Train Independent Support/Vertical Target Independence Audit

## Purpose

`87_full_train_independent_support_vertical_label_ingestion.md`에서 ingestion은
성공했지만, hidden metadata correlation risk가 남아 있었다. 이번 단계는
selected `support_contact + relative_vertical` 114-row binary target이 posterior
smoke에 들어갈 만큼 독립적인지 확인하고, controlled slice가 남는지 검사한다.

핵심 질문:

```text
Can we construct a support/vertical train-only target slice where the binary
target is not explained by hidden label carryover, rank, queue, geometry status,
or visible policy shortcuts?
```

## Boundary

- Split: Open3DSG train-only.
- validation/test는 사용하지 않는다.
- posterior를 학습하지 않는다.
- label은 Codex bootstrap label이며 human-confirmed가 아니다.
- hidden metadata는 label-lock 이후 audit와 controlled-slice construction에만 사용한다.
- multi-view는 audit evidence pointer일 뿐 posterior input이 아니다.
- paper-level posterior claim은 허용하지 않는다.

## Audit Modes

이번 audit은 두 mode를 분리한다.

### Strict Hidden Mode

이 mode는 이전 bootstrap label carryover까지 포함한다.

```text
relation_validity_label_hidden
label_use_hidden
rank_band_hidden
proposed_audit_role_hidden
queue_kind_hidden
geometry_status_hidden
label_match_status_hidden
```

Strict mode를 통과해야만 posterior method validation target으로 볼 수 있다.

### Construction-Only Mode

이 mode는 이전 bootstrap label carryover를 제외하고, target-construction shortcut만 본다.

```text
rank_band_hidden
proposed_audit_role_hidden
queue_kind_hidden
geometry_status_hidden
label_match_status_hidden
```

Construction-only mode를 통과한 slice는 plumbing/error diagnostic에는 쓸 수 있지만,
strict independence를 통과한 것은 아니다.

## Execution

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_target_independence_audit.py
```

Observed:

```text
status=full_train_independent_support_vertical_target_independence_audit_strict_blocked_construction_slice_available
validation_used=False
rows=114
positive=40
negative=74
errors=0
strict=none
construction=rank_band_balanced_codex_ver
next=full_train_independent_support_vertical_label_policy_revision
```

## Original Target Risk

Original target:

```text
original_support_vertical_codex_ver
```

Rows:

```text
114
positive = 40
negative = 74
```

Original strict hidden risks:

| Hidden Key | NMI | Majority Acc | Pos Rate Range |
| --- | ---: | ---: | ---: |
| `relation_validity_label_hidden` | 0.5710 | 0.8421 | 0.9583 |
| `label_use_hidden` | 0.4506 | 0.8333 | 0.6667 |
| `rank_band_hidden` | 0.2128 | 0.6930 | 0.7778 |
| `proposed_audit_role_hidden` | 0.1672 | 0.6491 | 0.5000 |
| `queue_kind_hidden` | 0.1634 | 0.6491 | 0.4376 |
| `geometry_status_hidden` | 0.1634 | 0.6491 | 0.4376 |

해석:

```text
Original support/vertical target is not independent enough for posterior
method validation.
```

가장 큰 blocker는 이전 bootstrap label carryover다. `relation_validity_label_hidden`과
`label_use_hidden`은 현재 binary target과 너무 강하게 연결되어 있다.

## Controlled Slice Results

Candidate criteria:

```text
rows >= 60
min(positive, negative) >= 25
strict hidden risk count == 0      for strict candidate
construction hidden risk count == 0 for construction-only candidate
```

Slice summary:

| Target Slice | Rows | Pos | Neg | Strict Risks | Construction Risks | Strict | Construction |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `rank_band_balanced_codex_ver` | 70 | 35 | 35 | 2 | 0 | no | yes |
| `rank_family_balanced_codex_ver` | 66 | 33 | 33 | 2 | 0 | no | yes |
| `proposed_role_balanced_codex_ver` | 80 | 40 | 40 | 3 | 1 | no | no |
| `queue_balanced_codex_ver` | 80 | 40 | 40 | 3 | 1 | no | no |
| `geometry_status_balanced_codex_ver` | 80 | 40 | 40 | 3 | 1 | no | no |
| `label_match_balanced_codex_ver` | 80 | 40 | 40 | 4 | 2 | no | no |
| `family_balanced_codex_ver` | 80 | 40 | 40 | 7 | 5 | no | no |
| `predicate_balanced_codex_ver` | 80 | 40 | 40 | 6 | 4 | no | no |
| `queue_family_balanced_codex_ver` | 72 | 36 | 36 | 3 | 1 | no | no |
| `role_family_balanced_codex_ver` | 70 | 35 | 35 | 3 | 1 | no | no |
| `label_use_balanced_codex_ver` | 38 | 19 | 19 | 5 | 5 | no | no |
| `relation_validity_balanced_codex_ver` | 36 | 18 | 18 | 5 | 5 | no | no |
| `original_support_vertical_codex_ver` | 114 | 40 | 74 | 6 | 4 | no | no |

## Recommendation

Strict controlled slice:

```text
none
```

Construction-only diagnostic slice:

```text
rank_band_balanced_codex_ver
```

Rows:

```text
70 rows = 35 positive + 35 negative
```

이 slice는 rank/queue/role/geometry-status construction shortcut을 줄인
plumbing diagnostic에는 쓸 수 있다. 그러나 strict mode에서는
`relation_validity_label_hidden`과 `label_use_hidden` carryover가 남아 있으므로
posterior method validation target으로는 부족하다.

## Interpretation

이번 audit의 결론은 명확하다.

```text
Do not run the next main posterior smoke on this target as method evidence.
```

가능한 사용:

- `rank_band_balanced_codex_ver`로 feature pipeline이 깨지지 않는지 보는 diagnostic.
- error-analysis plumbing.
- label policy revision 전후 비교용 baseline.

불가능한 사용:

- factorized posterior가 relation reliability를 잘 설명한다고 주장.
- support/vertical selected target이 independent label이라고 주장.
- paper-level posterior improvement claim.

## Output Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_target_independence_audit.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_target_independence_audit_codex_ver/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_target_independence_audit_codex_ver/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_target_independence_audit_codex_ver/slice_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_target_independence_audit_codex_ver/group_summaries.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_target_independence_audit_codex_ver/group_table.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_target_independence_audit_codex_ver/validation_errors.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_target_independence_audit_codex_ver/target_slices/
```

Construction-only diagnostic slice:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/independent_support_vertical_target_independence_audit_codex_ver/target_slices/rank_band_balanced_codex_ver.jsonl
```

## Verification

Commands:

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_target_independence_audit.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/full_train_independent_support_vertical_target_independence_audit.py
```

Observed:

```text
errors=0
validation_used=False
strict=none
construction=rank_band_balanced_codex_ver
```

Line counts:

```text
rank_band_balanced_codex_ver.jsonl = 70
rank_family_balanced_codex_ver.jsonl = 66
original_support_vertical_codex_ver.jsonl = 114
validation_errors.jsonl = 0
```

## Follow-Up Status

The next action from this document has been completed:

```text
full_train_independent_support_vertical_label_policy_revision
```

Observed follow-up:

```text
status=full_train_independent_support_vertical_label_policy_revision_ready_for_v2_readiness
validation_used=False
rows=127
support=72
vertical=55
same_label=72
same_use=95
```

## Next TODO

Next action:

```text
full_train_independent_support_vertical_v2_label_readiness
```

Goal:

- v2 sheet와 schema가 leakage/readiness gate를 통과하는지 검증한다.
- direct reliability label 제거가 실제 header에서 유지되는지 확인한다.
