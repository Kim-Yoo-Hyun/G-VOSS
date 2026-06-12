# H002 Diagnostic

Last updated: 2026-06-11

## Purpose

이 문서는 `04_projection.md` 이후 실행한 compact RGA projection validator의
초기 진단 결과를 기록한다. 목표는 H002가 H001의 이름 바꾸기인지, 아니면
`Relation-Geometric Agreement`라는 별도 문제 정의로 유지할 가치가 있는지 다음
gate를 정하는 것이다.

현재 결과는 hypothesis-stage smoke evidence다. 논문 본문용 experiment result가
아니며, Docker paper metric으로 승격하지 않는다.

## Artifacts

Validator:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/project_rga.py
```

Compact summaries:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/rga_smoke/vlsat_summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/rga_smoke/open3dsg_recovery_summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/rga_smoke/report.md
```

No row-level H002 projection JSONL was created.

## Projection Gate

| Source | Status | Projected rows | Key mismatch | Missing required fields | Posterior non-null |
| --- | --- | ---: | ---: | ---: | ---: |
| `vlsat` | `ready_for_rga_diagnostic` | 957,008 | 0 | 0 | 0 |
| `open3dsg_recovery_relaxed_views_min2` | `ready_for_rga_diagnostic_with_caveat` | 695,916 | 0 | 0 | 0 |

Interpretation:

- H001 full-validation artifacts are sufficient for a read-only H002 RGA
  projection.
- `prediction_id` identity is preserved across prediction and geometry rows.
- H002 can proceed to metric-equivalence diagnostics without touching H001
  artifacts.
- Open3DSG must keep the recovery-policy caveat.

## Dry RGA Result

Dry RGA uses semantic rank and deterministic H001 verifier status only.
`p_geom_valid` thresholds are not used to define `RGA-HL`.

| Source | K | Covered top-K denom. | Top-K rows | `RGA-HL@K` | `RGA-valid@K` | `RGA-uncertain@K` | `RGA-coverage@K` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `vlsat` | 50 | 9,099 | 27,400 | 0.0127 | 0.8187 | 0.1686 | 0.3321 |
| `vlsat` | 100 | 17,890 | 54,800 | 0.0188 | 0.7508 | 0.2304 | 0.3265 |
| `open3dsg_recovery_relaxed_views_min2` | 50 | 9,675 | 27,400 | 0.2232 | 0.4630 | 0.3138 | 0.3531 |
| `open3dsg_recovery_relaxed_views_min2` | 100 | 19,874 | 54,704 | 0.1569 | 0.4811 | 0.3620 | 0.3633 |

Initial observations:

- `RGA-coverage@K` is only about one third for both sources because unsupported
  families remain included in top-K coverage accounting.
- Open3DSG has much higher high-semantic / geometry-unsatisfied rate than
  `VL-SAT` under the current dry RGA contract.
- `RGA-uncertain@K` is nontrivial, especially for Open3DSG. Treating uncertain
  rows as valid or invalid would materially change the interpretation.

## H001 Comparison

H001 semantic-only violation reference:

| Source | K | H001 `Violation@K` | H001 violated / denom. |
| --- | ---: | ---: | ---: |
| `vlsat` | 50 | 0.0268 | 733 / 27,400 |
| `vlsat` | 100 | 0.0476 | 2,611 / 54,800 |
| `open3dsg_recovery_relaxed_views_min2` | 50 | 0.1386 | 3,763 / 27,142 |
| `open3dsg_recovery_relaxed_views_min2` | 100 | 0.1242 | 6,587 / 53,036 |

Important diagnostic:

- Dry `RGA-HL@K` is not numerically identical to H001 `Violation@K`.
- This difference is not yet a novelty claim.
- The difference may come from denominator, top-K selection, relation-family
  coverage, selected verification policy, or H001 metric condition logic.

Therefore the next gate is an equivalence audit, not factor graph design.

## What Looks Promising

The strongest H002 signal from this smoke is not the factor graph idea. It is
the measurement split:

- `RGA-HL@K` isolates high semantic rank plus deterministic geometry
  contradiction.
- `RGA-valid@K` separates strict geometry support from merely non-violated rows.
- `RGA-uncertain@K` prevents ambiguous geometry from being hidden.
- `RGA-coverage@K` exposes the unsupported-family denominator that H001's main
  violation rate does not foreground in the same way.

This supports keeping H002 alive for one more diagnostic gate.

## What Is Still Weak

H002 is not yet independent of H001.

Reasons:

- The geometry axis still reuses H001 verifier status.
- `p_geom_valid` remains an H001-derived input.
- No factorized posterior has been defined.
- No all-row label-geometry agreement table exists yet.
- The observed RGA/H001 metric difference might be a denominator artifact.

Current verdict:

```text
H002 status: continue as diagnostic branch, not yet independent hypothesis.
```

## Decision Gate

H002 can proceed toward a factor graph spec only if the next audit shows that
RGA adds one of the following:

- denominator insight not captured by H001 `Violation@K`;
- meaningful uncertain/coverage decomposition;
- label-correct but geometry-unsatisfied rows;
- source-transfer failure pattern that H001's current metric table does not
  explain cleanly.

If the next audit shows RGA is just a reparameterized H001 violation analysis,
H002 should be folded back into H001 as appendix/failure-analysis material.

## Next TODO

Next document:

```text
06_equivalence.md
```

Required next work:

- Audit why dry `RGA-HL@K` differs from H001 semantic-only `Violation@K`.
- Compare denominator definitions, selected rows, and verifier-policy fields.
- Decide whether `RGA-HL@K`, `RGA-uncertain@K`, and `RGA-coverage@K` provide
  information that H001 tables do not already report.
- Do not design the factor graph until this equivalence audit passes.
