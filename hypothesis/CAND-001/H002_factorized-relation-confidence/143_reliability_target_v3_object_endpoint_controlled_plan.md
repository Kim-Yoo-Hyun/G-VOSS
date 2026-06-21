# H002 Reliability Target V3 Object/Endpoint-Controlled Plan

Date: 2026-06-20 KST

## Purpose

`142_reliability_target_v3_path_decision.md`에서 현재 v3 relation reliability target이
object label과 endpoint pattern shortcut에 막힌 것을 확인했다. 이 단계는 posterior를
다시 열기 전에, 다음 label pool을 어떤 object/endpoint control cell에서 뽑아야 하는지
계획한다.

핵심 질문:

```text
Can we construct train-only sampling cells where positive/negative candidates
co-exist inside matched or near-matched object and endpoint strata?
```

## Boundary

- Split: Open3DSG train-only.
- Validation/test rows: not used.
- Label fill: not run.
- Posterior training: not run.
- H001 artifacts: not modified.
- Multi-view remains audit/label evidence only, not model input.
- Candidate-positive / candidate-negative proxy는 sampling stratum일 뿐 target label이 아니다.

## Command

```bash
python3 -m py_compile hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_controlled_plan.py
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_controlled_plan.py
```

Observed:

```text
status=h002_reliability_target_v3_object_endpoint_controlled_plan_ready_broader_mining_required
candidates=302
strict_eligible_rows=73
posterior_allowed=False
validation_used=False
test_used=False
next=reliability_target_v3_object_endpoint_candidate_mining
```

## Result

Status:

```text
h002_reliability_target_v3_object_endpoint_controlled_plan_ready_broader_mining_required
```

Decision:

```text
Use a multi-tier object/endpoint-controlled sampling contract.
Strict subject/object/family cells are preferred but insufficient alone, so the
next candidate mining step must combine strict matched cells, object-family
fallback cells, and endpoint-family balancing cells.
```

## Candidate Inventory

| Item | Count |
| --- | ---: |
| ready packets | 347 |
| packet-ready support/vertical candidate rows | 302 |
| candidate-positive proxy rows | 222 |
| candidate-negative proxy rows | 80 |
| support_contact rows | 196 |
| relative_vertical rows | 106 |

## Cell Feasibility

| Cell Type | Cells | Eligible Cells | Strong Cells | Eligible Rows | Pos Proxy | Neg Proxy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `subject_object_family` | 139 | 12 | 3 | 73 | 36 | 37 |
| `subject_object` | 119 | 13 | 3 | 89 | 46 | 43 |
| `object_family` | 54 | 10 | 4 | 163 | 91 | 72 |
| `object_predicate` | 89 | 5 | 2 | 73 | 22 | 51 |
| `endpoint_family` | 12 | 10 | 6 | 274 | 194 | 80 |
| `predicate_label` | 5 | 4 | 3 | 242 | 162 | 80 |

Interpretation:

- Strict `subject_label/object_label/predicate_family` cell만으로는 충분하지 않다.
- Strict cell에는 `73` eligible rows만 있고, strong cell은 `3`개뿐이다.
- 따라서 strict matched cell을 우선 쓰되, `object_family`와 `endpoint_family` fallback이
  필요하다.
- `endpoint_family`는 coverage가 크지만 shortcut 위험도 크므로 balancing/control stratum으로만
  써야 한다.

## Recommended Sampling Tiers

| Tier | Cells | Suggested Pos Proxy | Suggested Neg Proxy | Suggested Total |
| --- | ---: | ---: | ---: | ---: |
| `T1_strict_subject_object_family` | 12 | 26 | 25 | 51 |
| `T2_object_family_fallback` | 4 | 23 | 19 | 42 |
| `T3_endpoint_family_balance` | 6 | 34 | 31 | 65 |

Suggested total:

```text
158 rows = 83 candidate-positive proxy + 75 candidate-negative proxy
```

Important caveat:

```text
candidate-positive proxy and candidate-negative proxy are not labels.
They only define the sampling balance before v3 label fill.
```

## Sampling Contract

Primary tier:

```text
T1_strict_subject_object_family
```

Fallback tiers:

```text
T2_object_family_fallback
T3_endpoint_family_balance
```

Labeler-visible forbidden fields:

- candidate proxy class
- queue kind
- rank band
- sampling category
- expected role
- geometry status
- `p_geom_valid`
- semantic score/rank
- label match status
- endpoint flag pattern

Post-label audit required:

- hidden provenance risk
- endpoint pattern risk
- construction risk
- visible object identity risk
- visible relation surface risk
- geometry alignment risk
- scan/group leakage risk

## Interpretation

이 결과는 H002가 여전히 posterior-ready가 아니라는 뜻이다. 하지만 이전과 다르게 다음
실험 조건이 더 구체적이다. 문제는 positive가 부족한 것이 아니라, target을 설명하는
object/endpoint shortcut을 끊을 control cell이 부족했던 것이다.

따라서 다음 단계는 label fill이 아니라 candidate mining이다. 실제 label sheet를 만들기
전에, 위 tier별 recommended cell에서 중복을 제거하고, labeler-visible field가 깨끗한지
검사하고, post-label-only manifest를 따로 만들어야 한다.

## Main Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/143_reliability_target_v3_object_endpoint_controlled_plan.md
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/reliability_target_v3_object_endpoint_controlled_plan.py
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_controlled_plan/summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_controlled_plan/report.md
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_controlled_plan/candidate_pool_internal_preview.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_controlled_plan/cell_inventory.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_controlled_plan/recommended_sampling_cells.csv
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_full/open3dsg_train_full/rga/reliability_target_v3_object_endpoint_controlled_plan/recommended_sampling_cells.json
```

## Next TODO

```text
reliability_target_v3_object_endpoint_candidate_mining
```

Goal:

- recommended cell에서 실제 label sheet 후보를 mine한다.
- candidate-positive/negative proxy를 labeler-visible field에 노출하지 않는다.
- duplicate physical pair와 scan over-concentration을 줄인다.
- post-label-only hidden manifest를 만든다.
- posterior smoke는 계속 block한다.
