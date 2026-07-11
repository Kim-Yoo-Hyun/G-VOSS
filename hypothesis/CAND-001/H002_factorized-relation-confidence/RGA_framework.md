# Relation-Geometry Agreement Framework

Last updated: 2026-07-11 KST

## Purpose

Relation-Geometry Agreement (RGA)는 relation label correctness와 geometric
satisfiability를 분리해 관찰한다. Source confidence가 높더라도 relation-specific
geometry evidence와 충돌할 수 있고, source confidence가 낮더라도 geometry가
predicate를 지지할 수 있다.

## Edge Record

각 edge \(e=(s,p,o)\)는 다음 evidence를 분리해 보존한다.

- semantic content \(T_e\)
- source confidence \(Z_e\)
- predicate-independent geometry evidence \(G_e\)
- compatibility \(C_e=f_C(T_e,G_e)\)
- geometry coverage/status for metric computation

Observability quality \(Q_e\)와 \(p_{\rm obs}/p_{\rm rel}\)은 현재 scoped claim의
main path가 아니며 calibrated reliability로 검증됐다고 주장하지 않는다.

## Agreement States

Continuous score를 먼저 계산하고, 상태는 audit와 metric 집계를 위해서만 사용한다.

| State | Meaning |
| --- | --- |
| supported | available geometry supports the predicate |
| violated | available geometry contradicts the predicate |
| uncertain | evidence is present but inconclusive |
| missing | required geometry is unavailable |
| unsupported | current geometry schema cannot evaluate the relation |

이 상태는 universal frozen rule이 아니다. Relation family별 evidence contract와
coverage 조건이 상태를 결정한다.

## Relation Evidence

| Family | Main geometry evidence | Current role |
| --- | --- | --- |
| relative vertical | signed vertical offset | validated compatibility |
| relative size | size/extent ratio | validated compatibility |
| left/right | frame-aware lateral offset | caveated compatibility |
| front/behind | depth/reference frame | failure analysis |
| proximity | normalized pair distance | geometry-only control |
| support/contact | gap, overlap, contact, pose | diagnostic only |

## Metrics

### Violation@K

\[
\operatorname{Violation@K}
=\frac{\#\{\text{top-K selected edges marked violated}\}}
{\#\{\text{top-K selected edges evaluable by RGA}\}}.
\]

The denominator excludes missing and unsupported rows. Violation@K is a custom
reliability diagnostic, not an official 3DSSG leaderboard metric.

### Recall@K

Recall@K is computed against the mapped 3DSSG validation relation labels. H002
uses Recall and Violation jointly: a reranker is useful only when it lowers
geometric risk without unacceptable semantic-utility loss.

## Counterfactual Checks

- wrong predicate within a controlled route
- shuffled geometry
- wrong object-pair geometry
- subject/object swap
- axis or frame flip where defined

The checks establish that the score responds to matched predicate-geometry
evidence. They are mechanism tests, not additional benchmark systems.

## Boundary

RGA does not assert that all 3DSSG relations are geometry-decidable. Semantic,
structural, identity, attachment, and containment relations may need different
evidence or abstention. Current quantitative claims are restricted to the
validated routes in `paper_claim_core.md`.
