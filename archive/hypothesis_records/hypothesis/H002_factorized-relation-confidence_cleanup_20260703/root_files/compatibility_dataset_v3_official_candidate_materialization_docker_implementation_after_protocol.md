# Compatibility Dataset V3 Official Candidate Materialization Docker Implementation After Protocol

## Status

```text
artifact_root = artifacts/compatibility_dataset_v3_official_candidate_materialization_docker_implementation_after_protocol/
runtime_root = experiments/H002_compatibility_routing/official_materialization/latest/
status = h002_compatibility_dataset_v3_official_candidate_materialization_docker_implementation_after_protocol_ready
selected_path = official_materialization_ready_select_schema_shortcut_audit
validation_errors = 0
next_todo = compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation
```

## Command

```bash
HOST_UID=$(id -u) HOST_GID=$(id -g) docker compose -f configs/h002/compose.yaml run --rm h002-official-materialize-candidates
```

## Output

| File | Rows |
| --- | ---: |
| `candidate_rows.jsonl` | 23062 |
| `model_safe_view.jsonl` | 23062 |
| `hidden_manifest.jsonl` | 23062 |
| `validation_errors.jsonl` | 0 |

Family counts:

| Family | Rows | Label 0 | Label 1 |
| --- | ---: | ---: | ---: |
| `relative_horizontal` | 18764 | 13290 | 5474 |
| `relative_vertical` | 780 | 390 | 390 |
| `size_relative` | 340 | 170 | 170 |
| `support_contact` | 3178 | 1589 | 1589 |

Candidate origin counts:

| Origin | Rows |
| --- | ---: |
| `official_gt_positive` | 7623 |
| `official_same_pair_predicate_counterfactual` | 15439 |

## Boundary

- Docker official validation candidate materialization completed.
- Official validation metric 생성 없음.
- Official test 사용 없음.
- Paper-level result 생성 없음.
- `p_rel` / `p_obs` claim 생성 없음.
- H001 artifacts 수정 없음.
- Main `C_e` allowed blocks remain `T_e` and `G_e`; `Q_e` and `Z_e` are diagnostic-only.

다음 단계는 materialized official rows의 schema/shortcut audit이다.

