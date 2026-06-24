# V65 Attachment Conditional Contrast Capacity Scan

## 목적

v20의 320-row audit packet이 reject-heavy였던 것이 sampling artifact인지 확인하기 위해,
packet이 아니라 full-train attachment pool 전체에서 conditional contrast capacity를 확인했다.

검증 질문은 다음이다.

```text
same predicate / rank / geometry / object-family 조건 안에서도
supported proxy와 contradicted proxy가 함께 존재하는가?
```

이 단계는 새 human label을 만들거나 posterior smoke를 실행하는 단계가 아니다.

## 입력

- Input rows: `artifacts/train_rga_full/open3dsg_train_full/rga/match_rows.jsonl`
- Previous gate: `reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_audit_packet_path_decision_after_audit`
- Primary predicates: `attached to`, `hanging on`
- Diagnostic predicate: `connected to`

## 결과

```text
status = h002_reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan_blocked_predicate_imbalanced_strict_capacity
next_todo = reliability_target_v21_attachment_deferred_conditional_contrast_path_decision_after_capacity_scan
validation_errors = 0
posterior_smoke_allowed = false
```

Full-train attachment scope:

```text
primary_rows = 370692
diagnostic_connected_rows = 185346
joined_rows = 556038
unique_scans = 1157
unique_subgraphs = 3738
unique_visible_pairs = 7995
```

Primary proxy role counts:

```text
accept_proxy_supported_candidate = 79491
reject_proxy_contradicted_candidate = 257849
uncertain_proxy = 33352
```

Strict condition:

```text
spec = same_predicate_rank_geometry_family
mixed_groups = 258
balanced_pair_capacity = 4507
by_predicate = hanging on only
capacity_pass = false
```

Diagnostic relaxed condition:

```text
spec = same_predicate_rank_family
mixed_groups = 591
balanced_pair_capacity = 53539
by_predicate = attached to and hanging on
```

## 해석

Full-train에는 factorization을 요구할 만한 conditional contrast capacity가 전혀 없는 것은 아니다.
특히 `same predicate + rank + object-family` 수준에서는 `attached to`와 `hanging on` 모두
mixed proxy strata가 존재한다.

하지만 strict 조건인 `same predicate + rank + geometry bucket + object-family`까지 고정하면
mixed stratum이 `hanging on`에만 남고 `attached to`에서는 사라진다. 따라서 바로 새 packet을
만들면 H002의 primary predicate 두 개가 동일한 독립성 조건을 만족한다고 주장하기 어렵다.

## Relation Scope 확인

다른 relation들도 train-only/full-train artifact에서 확인했다. 다만 모두 active primary target은 아니다.

| Relation | Full-Train Checked | Current Status | Reason |
| --- | --- | --- | --- |
| `close by` | true | diagnostic/generality evidence | current RGA queue는 `RGA-HL = 0`, `RGA-LH = 171324`인 LH-only branch |
| `standing on` | true | diagnostic support/contact branch | hard room-surface filter와 side/geometry shortcut issue |
| `lying on` | true | diagnostic support/contact branch | row mass는 충분하지만 HL/LH가 geometry status와 너무 강하게 정렬 |
| `supported by` | true | excluded from current primary | LH-only 또는 current core 밖 |
| `higher than` | true | relative-vertical control examined | HL capacity가 너무 작음 |
| `lower than` | true | relative-vertical control used | geometry-easy control family |
| `attached to` | true | active but strict-v21 blocked | strict condition에서 mixed proxy stratum 부족 |
| `hanging on` | true | active v21-supported | strict condition에서도 mixed proxy stratum 존재 |
| `connected to` | true | diagnostic-only | OBB/point geometry만으로 functional connection 판단이 애매함 |

## 다음 단계

다음 TODO는 path decision이다.

```text
reliability_target_v21_attachment_deferred_conditional_contrast_path_decision_after_capacity_scan
```

판단해야 할 선택지는 다음이다.

1. `hanging on` strict target으로 primary를 좁힌다.
2. `attached to`는 diagnostic relaxed condition으로 낮추고 `hanging on`을 primary로 둔다.
3. strict condition을 한 단계 완화해 `same predicate + rank + object-family`를 primary packet condition으로 쓴다.
4. attachment branch를 diagnostic-only로 고정하고 다른 relation-family로 이동한다.

현재 판단으로는 3번은 shortcut 위험이 커서 바로 posterior로 가기 어렵고, 1번 또는 2번을
path decision에서 검토하는 것이 합리적이다.

## 산출물

- Script: `tools/reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan.py`
- Artifact root: `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan/`
- Summary: `summary.json`
- Report: `report.md`
- Strata table: `conditional_strata_capacity.csv`
- Top strata: `top_conditional_strata.jsonl`
- Relation scope status: `relation_scope_full_train_status.json`
