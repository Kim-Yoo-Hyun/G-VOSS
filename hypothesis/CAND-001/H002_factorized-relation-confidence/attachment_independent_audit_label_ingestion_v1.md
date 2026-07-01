# H002 Attachment Independent Audit Label Ingestion V1

Created: 2026-06-25

## Purpose

`attachment_independent_audit_label_fill_v1`에서 잠근 200-row visible-packet label을 hidden
audit manifest와 조인해, 새 H002 framework의 train-only diagnostic target을 만든다.

이 단계의 목적은 posterior 학습이 아니라 다음 target이 실제로 성립하는지 확인하는 것이다.

```text
C_e = compatibility(T_e, G_e)
Q_e = observability / evidence quality
p_obs = whether the relation is judgeable
p_rel = whether the relation is reliable given observable evidence
```

Hidden construction proxy, source rank/status, prior v20 label은 label fill에 사용되지 않았고,
ingestion 이후에도 diagnostic-only field로만 유지한다.

## Runner

```bash
python hypothesis/CAND-001/H002_factorized-relation-confidence/tools/attachment_independent_audit_label_ingestion_v1.py
```

Default output:

```text
artifacts/attachment_independent_audit_label_ingestion_v1/
```

## Boundary

```text
split = train_only
validation_usage = false
test_usage = false
reads_hidden_manifest_after_label_lock = true
hidden_manifest_used_for_label_fill = false
hidden_fields_as_model_input = false
source_score_or_rank_as_model_input = false
construction_proxy_as_model_input = false
uses_p_geom_valid = false
trains_new_posterior = false
posterior_smoke_allowed = false
paper_evidence_allowed = false
h001_artifacts_modified = false
```

## Outputs

```text
ingested_rows.jsonl
factor_views.jsonl
multiclass_reliability_target.jsonl
primary_binary_target.jsonl
compatibility_binary_target.jsonl
p_obs_target.jsonl
p_obs_primary_target.jsonl
p_rel_target.jsonl
geometry_support_target.jsonl
evidence_quality_target.jsonl
connected_diagnostic_target.jsonl
abstain_rows.jsonl
shortcut_probe_risks.json
shortcut_flag_summary.csv
proxy_vs_label_table.csv
cell_vs_label_table.csv
rank_vs_label_table.csv
source_geometry_status_vs_label_table.csv
predicate_vs_label_table.csv
visible_pair_vs_label_table.csv
evidence_tier_vs_label_table.csv
gt_reliability_mismatch_table.csv
summary.json
report.md
validation_errors.jsonl
```

## Result

```text
status = h002_attachment_independent_audit_label_ingested_positive_sparse_with_shortcut_risk
rows = 200
validation_errors = 0

multiclass_rows = 200
primary_binary_rows = 108
compatibility_binary_rows = 108
p_rel_rows = 108
p_obs_rows = 200
p_obs_primary_rows = 160
geometry_support_rows = 80
evidence_quality_rows = 200

review_relation_reliability = accept 17 / reject 91 / abstain 92
primary_binary_target = positive 17 / negative 91
p_obs_target = observable 108 / abstain-or-unobservable 92
review_geometry_support = supported 17 / unsupported 63 / uncertain 120
```

## Shortcut / Viability

```text
minimum_positive_for_posterior_smoke = 30
minimum_negative_for_posterior_smoke = 30
primary_positive_rows = 17
primary_negative_rows = 91
class_mass_pass = false

quick_probe_risk_flags = 81
model_shortcut_probe_risk_flags = 60
construction_proxy_probe_risk_flags = 19
label_derived_probe_risk_flags = 21
```

`label_derived_probe_risk_flags`는 `review_geometry_support`, `review_uncertainty`처럼 같은
review label bundle 안의 auxiliary target 상관을 포함한다. 따라서 source/proxy leakage로
해석하지 않는다. 실제 target-independence 판단은 `model_shortcut_probe_risk_flags`와
`construction_proxy_probe_risk_flags`를 분리해 봐야 한다.

Important mixed-group evidence:

```text
same_proxy_role_mixed_primary_binary_groups = 2
same_cell_mixed_primary_binary_groups = 4
same_rank_band_mixed_primary_binary_groups = 3
same_source_geometry_status_mixed_primary_binary_groups = 2
same_predicate_mixed_primary_binary_groups = 2
same_visible_pair_mixed_primary_binary_groups = 0
```

Construction proxy가 label을 완전히 결정하지는 않지만, primary positive가 17개뿐이고
visible endpoint pair 단위 mixed binary가 없어서 learned posterior smoke로 바로 가기에는
target이 아직 약하다.

## Interpretation

이 단계는 새 H002 방향에 맞다. 기존 H002처럼 proxy target을 잘 맞추는 posterior를 확인하는
것이 아니라, independent audit label을 조인해 `C_e`, `Q_e`, `p_obs`, `p_rel`을 만들 수
있는지와 그 target이 source/proxy shortcut에서 충분히 독립적인지를 먼저 확인한다.

현재 결론은 다음과 같다.

- target schema와 factor-view materialization은 성공했다.
- `p_obs`는 200 rows에서 만들 수 있고, primary 기준으로도 160 rows가 있다.
- `p_rel`/`C_e` binary는 108 rows만 usable하며 positive가 17개뿐이다.
- hidden construction proxy와 visible semantic/id field에 대한 shortcut probe가 남아 있다.
- 따라서 posterior smoke는 아직 금지하고, 다음 단계는 target-independence audit이다.

## Next

```text
attachment_independent_target_independence_audit_v1
```
