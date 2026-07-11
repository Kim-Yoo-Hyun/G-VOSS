# H002 Current Evidence Report

Last updated: 2026-07-11 KST

## 목적

H002의 현재 scoped claim, Docker experiment 결과, 실패한 확장 branch와 paper
boundary를 한 파일에 유지한다. Stage별 긴 실행 로그는 제거하고 compact runtime
artifact를 authoritative source로 사용한다.

## 현재 Claim

Source confidence \(Z_e\)와 predicate-geometry compatibility
\(C_e=f_C(T_e,G_e)\)를 분리하고, validation candidate를 다음 score로 rerank한다.

\[
S_2(e)=\widetilde Z_e\widetilde C_e.
\]

Raw \(C_e=f_C(T_e,G_e)\)에는 source score/rank가 들어가지 않는다. 구현은
\(Z_e\)를 source별, raw \(C_e\)를 source-family별 label-free min-max로 정규화한
뒤 결합한다. 이 분리는 H001에서도 재사용할 수
있는 핵심 설계이지만, H001 파일과 결과는 변경하지 않는다.

## 검증 설정

- official 3DSSG validation split
- VL-SAT and Open3DSG source predictions
- internal train rows: 4,868
- source rows scored: 762,888
- primary families: relative vertical and relative size
- metrics: Recall@K and custom Violation@K
- grouped bootstrap: 1,000 replicates
- main normalization: frozen label-free per-source `Z_e` and per-source-family
  raw `C_e` min-max

## Main Comparison Result

| K | Delta Recall, 95% CI | Delta Violation, 95% CI | Interpretation |
| ---: | --- | --- | --- |
| 5 | +0.0079 [-0.0060, 0.0226] | -0.2407 [-0.2544, -0.2277] | Recall claim weak |
| 10 | +0.0420 [0.0232, 0.0621] | -0.2299 [-0.2397, -0.2202] | joint improvement |
| 20 | +0.0816 [0.0481, 0.1180] | -0.2431 [-0.2519, -0.2351] | joint improvement |
| 50 | +0.1032 [0.0689, 0.1407] | -0.2592 [-0.2662, -0.2524] | joint improvement |

Geometry-only and plain concatenation do not explain the main score result.
Wrong-predicate and shuffled-geometry controls degrade, supporting matched
\(T_e\)-\(G_e\) compatibility rather than source-score copying.

## Route Decisions

### Main validated

- higher than / lower than
- bigger than / smaller than

### Caveated

- left/right: 15/20 metric cells win and no Violation regression occurs.
- Open3DSG improves Recall and Violation.
- VL-SAT lowers Violation but loses at most 0.0453 Recall; therefore this is not
  a universal lateral success claim.

### Diagnostic

- close by: normalized distance reaches AUROC/accuracy 1.0 on the route target.
  It is a geometry-only control, not evidence that interaction is always needed.
- front/behind: 11/20 cells win, but Recall loss exceeds 0.05 in 8 cells.
  Reference-frame/depth ambiguity remains.
- support/contact: repaired proxy has 35 positives and 347 negatives, majority
  accuracy 0.908, and `geometry_rule_state` reconstructs the target at
  accuracy/macro recall 1.0. The target is not independent and no solved-route
  or training claim is allowed.

## Rejected Extensions

### p_obs / p_rel

Observability labels and repaired \(Q_e\) were construction-coupled. The branch
did not establish independently calibrated selective reliability and is removed
from the current claim.

### Learned G_e

Point/learned geometry variants increased Recall in some slices but also
increased Violation. They did not dominate the frozen \(S_2\) score and remain
outside the paper claim.

### General all-relation framework

Relation-aware routing remains the design framework, but observability-heavy,
attachment, containment, and semantic/structural routes are not quantitatively
solved. The paper validates one mechanism across scoped relation families rather
than claiming an all-relation system.

## Cleanup Decision, 2026-07-10

- Removed the 48GB legacy H002 cleanup snapshot after promoting only the route
  inputs required by the current Docker pipeline.
- Removed repeated stage reports, hypothesis tools duplicated by Docker scripts,
  learned-G_e and p_obs/p_rel branches, transition scaffolds, and row-level
  outputs that can be regenerated.
- Preserved compact metrics, CI, qualitative examples, failure diagnostics,
  canonical AAAI source, and H001-reusable controls.

## Authoritative Paths

- current claim: `paper_claim_core.md`
- experiment commands: `experiments/H002_compatibility_routing/commands.md`
- main table: `experiments/H002_compatibility_routing/main_validation_table_refresh/latest/`
- paper source: `paper/h002_compatibility_routing/aaai2027/`

## Remaining Boundary

The manuscript may report validation-level, scoped compatibility reranking.
It must not claim official hidden-test, SOTA, normalization invariance,
support/contact solved, learned geometry improvement, or calibrated
\(p_{\rm obs}/p_{\rm rel}\).

## Current Package Status, 2026-07-11

- compact main/appendix tables, 1,000-replicate CI, sensitivity, qualitative
  cases와 support/contact diagnostic freeze를 보존했다.
- canonical AAAI build는 main 7 pages, supplement 3 pages, checklist 2 pages다.
- US Letter, Type 3 font 0, missing citation/reference 0, LaTeX error 0,
  overfull box 0 검사를 통과했다.
- scoped H002에 자동으로 열린 추가 experiment는 없다. External release URL,
  submission portal policy 또는 broad-route 재개는 사용자 결정 후 별도 protocol로 연다.
