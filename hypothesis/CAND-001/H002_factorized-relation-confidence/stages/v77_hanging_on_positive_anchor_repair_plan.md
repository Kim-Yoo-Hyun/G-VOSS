# V77 Hanging-On Positive-Anchor Repair Plan

## 목적

v76 path decision에서 선택한 `v23_hanging_on_positive_anchor_repair_plan`을
구체적인 capacity-scan contract로 고정했다.

이 단계는 새 label fill, candidate mining, posterior smoke가 아니다. v22에서 관측된
9개 accept가 어떤 subject-anchor affordance cell에 집중되는지 요약하고, 다음 단계에서
그 cell 안에 matched hard negative가 충분히 존재하는지 검사할 계획을 만든다.

## 입력

- Path decision:
  `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_path_decision_after_audit/`
- Label ingestion:
  `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_ingestion/`

## 결과

```text
status = h002_reliability_target_v23_hanging_on_positive_anchor_repair_plan_ready_for_capacity_scan
next_todo = reliability_target_v23_hanging_on_positive_anchor_capacity_scan
validation_errors = 0
posterior_smoke_allowed = false
```

v22 label seed:

```text
accept_rows = 9
reject_rows = 193
abstain_rows = 38
```

Accepted subject/object labels:

```text
accept_subject_counts = curtain:4, blinds:2, bag:2, towel:1
accept_object_counts = door:5, window:3, stand:1
accept_subject_object_counts =
  curtain|door:2
  curtain|window:1
  curtain|stand:1
  blinds|window:2
  bag|door:2
  towel|door:1
```

Affordance-cell summary:

```text
positive_anchor_candidate_cell = accept:9, reject:2
soft_subject_with_non_anchor_or_uncertain_object = reject:10, abstain:3
anchor_object_with_non_hanging_subject = reject:27, abstain:15
non_anchor_generic_or_confound_cell = reject:154, abstain:20
```

## 해석

v22의 문제는 `hanging on` relation 자체가 항상 무의미하다는 것이 아니다. 문제는 generic
`hanging on` 후보를 strict sampling해도 대부분이 support/proximity confound, implausible
subject, generic endpoint, wrong relation family로 reject된다는 것이다.

Accept는 `curtain`, `blinds`, `bag`, `towel` 같은 soft/hanging subject와 `door`, `window`,
`stand` 같은 anchor 후보에 집중된다. 따라서 다음 route는 이 positive-anchor cell을
capacity scan 대상으로 삼는다.

중요한 제한은 다음과 같다.

- Positive-anchor cell은 label이 아니라 sampling hypothesis다.
- 쉬운 positive만 더 뽑으면 object/anchor label shortcut이 더 강해진다.
- 반드시 같은 또는 가까운 affordance cell 내부에서 matched hard negative가 충분해야 한다.
- matched hard negative가 부족하면 attachment-deferred posterior route는 중단하고 blocker
  synthesis로 넘어가야 한다.

## Capacity Scan Contract

Next route:

```text
reliability_target_v23_hanging_on_positive_anchor_capacity_scan
```

Pre-label gates:

```text
positive_anchor_candidate_rows_min = 300
matched_positive_negative_cells_min = 30
balanced_proxy_capacity_min = 160
min_rank_band_coverage = 2
min_geometry_bucket_coverage = 2
max_single_subject_label_share = 0.20
max_single_object_label_share = 0.20
max_single_scan_share = 0.05
max_visible_endpoint_pair_share = 0.04
```

Required controls:

- predicate fixed to `hanging on`
- subject affordance family matched or capped
- anchor affordance family matched or capped
- subject/object label capped and reported
- rank band matched or balanced
- geometry bucket matched or balanced
- coverage tier matched or balanced
- evidence tier matched or balanced
- scan id capped
- visible endpoint pair capped
- GT label match status audit-only and reported after selection

## Boundary

- Train-only H002 hypothesis artifact.
- No validation/test rows were used.
- No new labels were filled.
- No candidate mining was run.
- No posterior was trained or evaluated.
- Multi-view and mesh remain audit/confirmation evidence only.
- H001 and paper artifacts were not modified.

## 산출물

- Script: `tools/reliability_target_v23_hanging_on_positive_anchor_repair_plan.py`
- Artifact root: `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v23_hanging_on_positive_anchor_repair_plan/`
- Summary: `summary.json`
- Repair plan: `repair_plan.json`
- Affordance taxonomy: `affordance_taxonomy.json`
- Seed summary: `positive_anchor_seed_summary.json`
- Capacity scan contract: `capacity_scan_contract.json`
- Report: `report.md`
- Validation errors: `validation_errors.jsonl`
