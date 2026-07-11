# H002 Method Contract V1

Last updated: 2026-07-11 KST

## Purpose

이 문서는 현재 scoped H002 구현의 factor boundary, score, training/evaluation
firewall과 route claim을 고정한다. 확장 아이디어인 learned geometry encoder,
observability head, all-relation routing은 현재 구현 계약에 포함하지 않는다.

## Factor Boundary

각 relation candidate $e=(s,p,o)$를 다음처럼 분리한다.

\[
T_e=f_T(p,c_s,c_o),\qquad
G_e=f_G(x_s,x_o),\qquad
Z_e=(s_{\rm src},r_{\rm src}).
\]

- $T_e$: predicate와 subject/object class semantics
- $G_e$: 같은 ordered object pair의 predicate-independent geometry evidence
- $Z_e$: source score와 rank
- $C_e=f_C(T_e,G_e)$: predicate-geometry compatibility

핵심 leakage boundary는 다음과 같다.

\[
Z_e\notin f_C.
\]

따라서 $C_e$는 기존 source confidence를 복사할 수 없고, source confidence는
compatibility 계산이 끝난 뒤 final reranking에서만 사용한다.

## Implemented Compatibility Model

현재 $f_C$는 internal train split의 4,868개 row로 학습한 logistic model이다.
입력은 $T_e$, $G_e$, 명시적 $T_e\times G_e$ interaction feature이며 source
score/rank, validation GT, Violation label과 construction-only hidden field는 제외한다.

비교 조건은 동일 train split에서 학습한다.

| Condition | Input | Role |
| --- | --- | --- |
| semantic-only | $T_e$ | semantic shortcut probe |
| geometry-only | $G_e$ | geometry sufficiency ablation |
| plain concat | $T_e+G_e$ | generic fusion ablation |
| compatibility | $T_e,G_e,T_e\times G_e$ | main $C_e$ model |
| wrong predicate | mismatched $T_e$, same $G_e$ | predicate dependence control |
| shuffled/wrong-pair geometry | same $T_e$, mismatched $G_e$ | pair geometry dependence control |

Official 3DSSG validation rows are evaluation-only and do not fit the model or tune
the score weight.

## Score Definition

Raw source score is min-max normalized per source. Raw compatibility probability is
min-max normalized per source and relation family over the label-free candidate pool:

\[
\widetilde Z_e=\operatorname{MinMax}_{\rm source}(Z_e),\qquad
\widetilde C_e=\operatorname{MinMax}_{\rm source,family}(f_C(T_e,G_e)).
\]

The implemented primary score is

\[
S_2(e)=\operatorname{clip}(\widetilde Z_e,\epsilon,1)
       \operatorname{clip}(\widetilde C_e,\epsilon,1),
\qquad \epsilon=10^{-6}.
\]

Its log-space interpretation is

\[
\log S_2(e)=\log\widetilde Z_e-\lambda[-\log\widetilde C_e],
\qquad \lambda=1.
\]

$\lambda=1$ is the parameter-free product form; it is not selected using
validation labels. H002 reports normalization sensitivity and does not claim
normalization invariance.

## Route Assignment Protocol

Route assignment follows the evidence needed to decide a relation, not a post-hoc
success table.

| Decision question | Route | Current evidence status |
| --- | --- | --- |
| Is metric geometry sufficient? | geometry-only | close by control |
| Does predicate meaning change geometry interpretation? | compatibility | higher/lower, bigger/smaller validated |
| Is a directional reference frame required? | frame-aware | left/right caveated; front/behind failure |
| Are local contact and pose cues required? | hard physical | support/contact diagnostic only |
| Is evidence availability itself uncertain? | observability-aware | defined extension, not solved |
| Is the relation primarily ontological/structural? | semantic/structural | scope boundary, not evaluated |

This protocol is a framework map. It does not establish that every route is solved.

## Metric Contract

- Dataset: official 3DSSG validation split
- Sources: VL-SAT and Open3DSG validation predictions
- Metrics: Recall@K and custom Violation@K
- K grid: 5, 10, 20, 50, 100
- Uncertainty: 1,000 grouped bootstrap replicates
- Main interpretation: improve or preserve semantic utility while reducing geometric
  violation risk

Violation@K is a custom diagnostic over geometrically evaluable rows, not an official
3DSSG leaderboard metric.

## Current Claim Boundary

Validated:

- relative vertical: higher than, lower than
- relative size: bigger than, smaller than

Caveated:

- left/right as a frame-aware lateral route with source-dependent Recall tradeoff

Control or failure analysis:

- close by: geometry-only control
- front/behind: depth/reference-frame failure
- standing on, lying on, supported by: target-dependent support/contact diagnostic

Not claimed:

- official hidden-test or SOTA result
- all-relation reliability solved
- support/contact solved
- learned $G_e$ final-score improvement
- calibrated $p_{\rm obs}/p_{\rm rel}$
- normalization-invariant improvement

## Authoritative Runtime

- implementation: `experiments/H002_compatibility_routing/scripts/`
- commands: `experiments/H002_compatibility_routing/commands.md`
- score manifest: `experiments/H002_compatibility_routing/source_reranking_evaluation/latest/score_manifest.json`
- compact table: `experiments/H002_compatibility_routing/main_validation_table_refresh/latest/`
