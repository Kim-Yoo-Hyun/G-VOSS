# H002 Equivalence

Last updated: 2026-06-11

## Purpose

이 문서는 dry H002 `RGA-HL@K`와 H001 semantic-only `Violation@K`가 왜 다르게
나왔는지 audit한 결과를 기록한다. 핵심 질문은 다음이다.

```text
H002 RGA가 H001 Violation@K의 이름 바꾸기인가?
```

현재 답은 조건부다.

```text
H001과 같은 scope/selection을 쓰면 RGA-HL은 H001 Violation@K로 붕괴한다.
하지만 global source-rank 관점에서는 RGA가 unsupported coverage와 uncertainty를
명시적으로 드러낸다.
```

따라서 H002는 아직 독립 hypothesis가 아니다. 다만 source-level diagnostic branch로
한 단계 더 확인할 가치는 있다.

## Artifacts

Auditor:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/audit_equivalence.py
```

Outputs:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/equivalence/vlsat_equivalence.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/equivalence/open3dsg_recovery_equivalence.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/equivalence/report.md
```

No H001 artifact was modified.

## Definitions Compared

### H002 Dry Global-Rank RGA

Selection:

```text
semantic_rank_in_subgraph <= K
```

Characteristics:

- uses the source's global semantic rank;
- includes all relation families;
- keeps unsupported families as `RGA-HM` or `RGA-LM`;
- computes `RGA-HL@K` over covered top-K rows only;
- does not use `p_geom_valid` thresholds.

### H001 Semantic-Only `Violation@K`

Selection:

```text
filter to H001 families
  -> sort by source ranking_score within each subgraph
  -> take top-K scoped predictions
```

H001 families:

- `support_contact`
- `proximity`
- `relative_vertical`

Violation denominator:

```text
verification_status in {satisfied, uncertain, violated}
```

Violation numerator:

```text
verification_status == violated
```

## Equivalence Result

When H002 uses H001-equivalent scoped-score selection, it exactly reproduces
H001 semantic-only `Violation@K`.

| Source | K | H001-equivalent violated / denom. | H001 metric violated / denom. | Match |
| --- | ---: | ---: | ---: | --- |
| `vlsat` | 50 | 733 / 27,400 | 733 / 27,400 | yes |
| `vlsat` | 100 | 2,611 / 54,800 | 2,611 / 54,800 | yes |
| `open3dsg_recovery_relaxed_views_min2` | 50 | 3,763 / 27,142 | 3,763 / 27,142 | yes |
| `open3dsg_recovery_relaxed_views_min2` | 100 | 6,587 / 53,036 | 6,587 / 53,036 | yes |

This means:

- `RGA-HL@K` is not independently novel if evaluated on the exact H001 scoped
  selection.
- The earlier mismatch was caused by selection-scope differences, not by a new
  geometry-validity target.

## Why The Earlier Values Differed

The selected row sets are mostly different.

| Source | K | Global-rank selected | H001-scoped selected | Intersection | Jaccard |
| --- | ---: | ---: | ---: | ---: | ---: |
| `vlsat` | 50 | 27,400 | 27,400 | 9,099 | 0.1991 |
| `vlsat` | 100 | 54,800 | 54,800 | 17,890 | 0.1951 |
| `open3dsg_recovery_relaxed_views_min2` | 50 | 27,400 | 27,142 | 9,675 | 0.2156 |
| `open3dsg_recovery_relaxed_views_min2` | 100 | 54,704 | 53,036 | 19,874 | 0.2262 |

Interpretation:

- H002 dry global-rank RGA answers: "what does the source rank highly overall,
  and how much of that is geometrically covered, uncertain, or contradicted?"
- H001 `Violation@K` answers: "among H001-covered families only, after scoped
  score sorting, how often are selected rows geometrically violated?"

These are different diagnostics. The difference is useful only if H002 claims a
source-level coverage/agreement benchmark, not if it claims a better H001
violation metric.

## Implication For H002

This audit weakens the original H002 method claim.

Weak claim:

```text
RGA-HL@K improves on H001 Violation@K.
```

This is not defensible, because the H001-equivalent version matches H001 exactly.

More defensible claim:

```text
RGA decomposes source-level relation confidence into supported, contradicted,
uncertain, and unsupported coverage states before relation-family scoping hides
the denominator.
```

This claim is more benchmark/diagnostic oriented than method oriented.

## Current Verdict

```text
H002 status: continue only as source-level diagnostic / benchmark branch.
Do not proceed to factor graph method yet.
```

Reason:

- The factor graph would currently be built on top of H001 geometry signals.
- Without a new label-geometry disagreement result, factor graph rescoring is
  likely to look like H001 recalibration with extra notation.
- RGA's current added value is coverage/uncertainty decomposition, not a new
  posterior method.

## Next Decision Gate

H002 needs one more diagnostic before deciding whether to continue independently.

The next gate should test:

```text
Do exact-label-correct or high-confidence relation rows exist where geometry is
unsatisfied or uncertain in a way that H001's current tables do not isolate?
```

Required next document:

```text
07_label_geometry.md
```

Required next work:

- Build a label-geometry agreement diagnostic from failure rows first.
- Count `exact_match + violated`, `exact_match + uncertain`, `family_match +
  violated`, and `no_gt_for_pair + satisfied`.
- Separate top-50/top-100 membership from all failure rows.
- Decide whether label correctness and geometric satisfiability actually
  disagree in a nontrivial, source-transferable way.

Stop condition:

- If label-geometry disagreement is rare or already fully explained by H001
  failure rows, H002 should be folded into H001 appendix/failure analysis.

Continue condition:

- If label-correct but geometry-unsatisfied/uncertain rows are frequent enough,
  and appear in both `VL-SAT` and Open3DSG, H002 can continue as an RGA benchmark
  branch. Only then should factor graph posterior design be reopened.
