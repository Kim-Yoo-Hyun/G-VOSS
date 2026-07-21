# RelCompat3D Paper Progress

Last updated: 2026-07-20 KST

이 문서는 현재 paper-facing work의 완료 상태와 남은 작업만 기록한다. Smoke
test, historical split, checkpoint recovery, method-selection chronology는
`archive/`, `experiments/`, `TODO.md`가 소유하며 여기서 반복하지 않는다.

## Current Phase

Status: `submission_package_scientifically_complete_author_metadata_pending`

현재 scientific claim에 필요한 method, main comparisons, controls, statistics,
figures, supplement, Docker source package가 준비되었다. 추가 실험은 새로운
claim을 열거나 특정 reviewer risk를 닫을 때만 수행한다.

## Completed Scientific Components

| component | status | paper role |
| --- | --- | --- |
| fixed-candidate reliability problem | complete | Introduction / Method |
| source relation score and compatibility separation | complete | Method |
| linked positive--counterfactual training | complete | Method / supplement |
| proximity symmetry and joint endpoint-swap/inverse-predicate consistency | complete | Method / proof |
| constrained family-aware re-ranking | complete | family-sequence preservation and prefix-utility optimality |
| strict train/development/evaluation split | complete | Experimental Setup |
| VL-SAT/Open3DSG/SGFN evaluation | complete | Table 1 / Figure 2 |
| RelCompat3D-MLP capacity, RankAvg, RRF | complete | second proposed capacity and matched fusion baselines |
| wrong predicate/pair/shuffle/swap controls | complete | main K=50 / supplemental K=100 tables |
| distance-only and compatibility-only controls | complete | main K=50 / supplemental K=100 tables |
| uncertainty and family decomposition | complete | supplement / limitations |
| scan-cluster confidence intervals at every reported K | complete | Results / supplement |
| bounded CPU runtime and parameter count | complete | supplement |
| threshold sensitivity | complete | supplement |
| feature-removal refits | complete | supplement |
| point/mesh surface-based geometry audit | complete | exact main prose / full supplement |
| relative-size secondary extension | complete | artifact only; excluded from submission |
| cross-dataset stress test | complete | supplement limitation evidence |

## Completed Manuscript Components

- Six-section AAAI structure.
- Exact-number-free Abstract.
- Percentage-scale Table 1 and Table 2.
- Figure 1 method overview and Figure 2 Source/Linear/MLP all-K trajectory use
  Helvetica-compatible source typography, high-resolution PNG
  manuscript assets, white backgrounds, thin neutral rules, and restrained
  colorblind-safe accents.
- Separate first-page-teaser manuscript variant sharing the transcript, adding
  a pair-level Top-50 demotion, and retaining the later full-width framework
  figure. The qualitative grid is supplemental in both main variants to
  preserve the seven-page technical limit.
- One-column K=50 matched-control table in the main paper; complete K=100
  controls and full point/mesh/consensus audit in the supplement.
- Counterfactual rules and relation-transformation proofs in supplement.
- GEODE, RelWitness, RelGraphOV, TAD, and PUF boundaries in Related Work.
- Discussion that consolidates shared-target, construct-overlap, and
  support/contact limits.
- Separate reported-evaluation and re-ranking family scopes, exact preservation
  of the support/contact source subsequence, and explicit disclosure of the
  OBB-measurement overlap between counterfactual construction and the primary
  verifier.
- Standalone reproducibility checklist.
- Anonymous code/data supplement with outer/inner checksum validation.

## Current Canonical Build

- main: `paper/aaai/main_aaai27.pdf`, 9 pages.
- teaser comparison: `paper/aaai/main_teaser_aaai27.pdf`, 9 pages.
- supplement: `paper/aaai/supplement_aaai27.pdf`, 10 pages.
- checklist: `paper/aaai/reproducibility_checklist_aaai27.pdf`, 2 pages.
- release: `release/h001_aaai27_openreview_20260720_084307/` is the verified
  active-method bundle and selects the teaser main PDF.

## Decisions Already Made

- The strict train-only `no_family_indicator_v1` refit is the active method;
  family selects the head/procedure but is not a constant feature. The former
  69-parameter model is historical provenance.
- Main claim은 shared-target cross-predictor reliability다.
- 모든 K=`{5,10,20,50,100}`를 공개한다.
- K=50은 intermediate reported budget이며 별도 표시하지 않는다.
- Primary rule은 proximity/vertical family-aware product re-ranking이다.
- Support/contact는 source order를 유지한다.
- RelCompat3D-MLP는 Linear와 동등한 proposed capacity로 main에 포함한다.
- Pooled compatibility, hard filter, external transfer는 supplement 또는
  diagnostic이다.
- Relative size는 core learned-method evidence가 아니다.
- 독립 human reference가 없는 상태에서 Human V를 주장하지 않는다.

## Deferred or Non-Main Tracks

| track | 현재 상태 | main claim에 넣지 않는 이유 |
| --- | --- | --- |
| relative size | artifact only | fixed geometric rule이 learned score와 동등하게 강하고 core claim 밖임 |
| support/contact learned re-ranking | deferred | local contact/pose evidence와 valid transform 부족 |
| attachment subtype | development only | multiple-source joint gate 미충족 |
| relative horizontal | blocked | global reference-frame semantics 불명확 |
| Qwen-VL | extension only | main three-source contract 밖의 별도 inference pipeline |
| ReplicaSSG/FROSS | stress test | target-dependent transfer와 K=100 saturation |

## Remaining Work

### Required before submission

- current canonical source/PDF를 사용한 anonymous release bundle 재생성.
- default main과 first-page teaser main 중 upload layout 선택.
- OpenReview author metadata.
- reciprocal-reviewer declaration.
- live form의 title, abstract, TL;DR, topics 확인.
- public license와 post-acceptance artifact URL 결정.
- Optional only: verify source locks if Figure 1--3 are later redrawn manually
  in an external vector editor.

### Optional scientific strengthening

- independent human physical-validity reference.
- untouched external dataset with adequate candidate coverage.
- richer contact/pose observation for support/contact.

이 optional work는 현재 scoped submission을 빌드하는 데 필요한 blocking task가
아니다. 수행한다면 `paper/risk.md`의 해당 risk와 claim boundary를 먼저 갱신한다.
