# H002: Factorized Relation Confidence

Last updated: 2026-07-11 KST

이 폴더는 H002의 hypothesis-stage 근거와 현재 paper claim의 경계를 관리한다.
실행 코드는 `experiments/H002_compatibility_routing/`, manuscript는
`paper/h002_compatibility_routing/aaai2027/`가 소유한다.

## Current Claim

3D Scene Graph relation의 source confidence는 predicate와 object-pair geometry의
compatibility를 직접 보장하지 않는다. H002는 다음 factor를 분리한다.

- `T_e`: predicate와 subject/object semantic content
- `G_e`: predicate와 source confidence를 보지 않는 geometry evidence
- `Z_e`: source score와 rank
- `C_e = compatibility(T_e, G_e)`

현재 main reranking score는 다음과 같다.

\[
S_2(e)=\widetilde Z_e\,\widetilde C_e.
\]

Raw \(C_e\)는 \(Z_e\)를 입력으로 받지 않는다. 구현에서는 source score를 source별,
compatibility를 source-family별 label-free candidate-pool min-max로 정규화한 뒤
최종 ranking 단계에서만 곱한다.

## Validated Scope

| Route | Relations | Status |
| --- | --- | --- |
| comparison compatibility | higher/lower, bigger/smaller | main validated |
| frame-aware lateral | left/right | caveated validated |
| geometry-only control | close by | diagnostic control |
| frame/depth ambiguity | front/behind | failure analysis |
| hard contact/pose | standing on, lying on, supported by | diagnostic only |

다음은 현재 claim이 아니다.

- all-relation 또는 SOTA 3DSSG predictor
- support/contact solved
- calibrated `p_obs/p_rel`
- learned `G_e`의 final-score 개선
- official hidden-test result

## Canonical Documents

- `paper_claim_core.md`: 현재 claim, score, 실험 경계
- `method_contract_v1.md`: factor separation, 실제 score와 leakage contract
- `geometry_evidence_schema_v1.md`: `G_e` schema
- `RGA_framework.md`: Relation-Geometry Agreement와 Violation 정의
- `report/report_0706.md`: 현재 결과와 폐기된 확장 시도 요약

과거 stage별 report와 transition 문서는 현재 claim을 중복하거나 폐기된 branch를
기록하므로 제거했다.

## Reproduction Inputs

`artifacts/`에는 현재 Docker pipeline이 직접 읽는 protocol과 route input만
남긴다.

- four route materialization/schema pairs
- grouped-evaluation protocol
- Docker preflight protocol and skeleton
- source-reranking materialization protocol, source inventory, metric protocol

Row-level runtime outputs는 이 폴더가 아니라
`experiments/H002_compatibility_routing/`에 둔다.

## Current Status

Scoped H002 experiment, compact table/CI/qualitative package, AAAI manuscript,
supplement와 checklist build가 완료됐다. 자동으로 열려 있는 추가 experiment는 없다.
각 runtime artifact의 `next_todo`는 생성 당시 stage provenance이며 현재 task board가
아니다. 현재 작업 우선순위는 `TODO.md`가 소유한다.

## H001 Boundary

H002는 H001 파일을 수정하지 않는다. H001에서 재사용 가능한 H002 산출물은 factor
separation \((T_e,G_e,Z_e,C_e)\), wrong-predicate, shuffled-geometry,
wrong-pair-geometry control 설계뿐이다. H001의 score, experiment, manuscript
파일은 각각의 H001 owner가 관리한다.
