# V76 Hanging-On Strict Audit Packet Path Decision

## 목적

v75 target-independence audit 이후, v22 `hanging on` strict target을 posterior smoke로
넘길지, diagnostic-only로 고정하고 새로운 repair route로 넘어갈지 결정했다.

## 입력

- Input artifact:
  `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_target_independence_audit/`
- Primary relation binary target: `202` rows, `9/193`
- Strict/diagnostic clear slices: `0/0`
- Full quick-probe risk flags: `107`
- Slice-level blocking risk flags: `1,666`

## 결과

```text
status = h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_path_decision_select_v23_positive_anchor_repair_plan
selected_path = freeze_v22_hanging_on_strict_diagnostic_select_v23_positive_anchor_repair_plan
next_todo = reliability_target_v23_hanging_on_positive_anchor_repair_plan
validation_errors = 0
posterior_smoke_allowed = false
```

## 결정

v22 `hanging on` strict target은 posterior target으로 승격하지 않는다.
Diagnostic-only negative target-construction evidence로 고정한다.

다음 route는 `v23_hanging_on_positive_anchor_repair_plan`으로 선택한다.

## 왜 이 결정인가

v22는 full-train strict capacity와 audit packet generation까지는 성공했지만, 실제 visible/mesh
evidence 기반 reliability label에서는 accept가 9개뿐이었다.

```text
primary_binary_rows = 202
accept = 9
reject = 193
min_class_count = 9
required_min_class_count = 60
strict_clear_slice = 0
diagnostic_clear_slice = 0
```

Balanced full slice도 `9/9`에 불과하고, 같은 visible endpoint pair 내부 mixed slice는
0 rows다. 따라서 현재 target으로 posterior smoke를 실행하면 factorized reliability를
검증하는 것이 아니라 reject-heavy construction artifact를 학습할 위험이 크다.

하지만 accept 9개는 실제 `hanging on` relation이 완전히 없는 것은 아니라는 신호다.
Accept는 generic object pair가 아니라 curtain/towel/bag/clothes류 subject와
window/door/rack/hook/stand류 anchor가 결합된 hanging-anchor case에 집중된다. 따라서
다음 route는 generic `hanging on` 후보를 더 많이 라벨링하는 것이 아니라,
positive-anchor cell 안에서 matched hard negative가 충분히 존재하는지를 먼저 검증하는 것이다.

## Rejected Options

- `run_posterior_smoke_now`: reject
- `train_on_balanced_9_9_slice`: reject
- `try_stronger_posterior_combiner_now`: reject
- `use_geometry_support_as_primary_target`: reject
- `label_more_rows_with_same_v22_recipe`: reject for now
- `promote_attached_to_or_connected_to_primary_now`: reject
- `multi_view_or_mesh_as_model_input_now`: reject for now
- `conclude_h002_is_invalid`: reject

## Selected Next Contract

Next route:

```text
reliability_target_v23_hanging_on_positive_anchor_repair_plan
```

Purpose:

```text
Repair the positive-sparse hanging-on target by testing whether accept-rich but shortcut-controlled
positive-anchor strata exist in the full train pool.
```

Required controls:

- fixed predicate: `hanging on`
- matched/capped subject affordance family
- matched/capped anchor affordance family
- capped subject/object label
- matched or balanced rank band
- matched or balanced geometry bucket
- matched or balanced coverage tier
- capped scan id
- capped visible endpoint pair

Pre-label gates:

```text
positive_anchor_candidate_rows_min = 300
matched_positive_negative_cells_min = 30
balanced_proxy_capacity_min = 160
max_single_subject_label_share = 0.20
max_single_object_label_share = 0.20
max_single_scan_share = 0.05
max_visible_endpoint_pair_share = 0.04
```

If these capacity gates fail, the path decision records that attachment-deferred target construction
should stop as a posterior route and move to blocker synthesis rather than weakening controls.

## Boundary

- Train-only H002 hypothesis artifact.
- No validation/test rows were used.
- No new labels were filled.
- No posterior was trained or evaluated.
- Multi-view and mesh remain audit/confirmation evidence only.
- H001 and paper artifacts were not modified.

## 산출물

- Script: `tools/reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_path_decision_after_audit.py`
- Artifact root: `artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_path_decision_after_audit/`
- Summary: `summary.json`
- Path decision: `path_decision.json`
- Report: `report.md`
- Validation errors: `validation_errors.jsonl`
