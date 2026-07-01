# Stage 05 Hanging And RGA Reframing V67-V81

## Scope

이 문서는 기존 `v67`부터 `v81`까지의 `hanging on` strict / positive-anchor route와 RGA benchmark
reframing을 병합한 요약이다.

## 진행한 내용

- `v67-v76`: `hanging on` strict packet plan, candidate mining, source inventory, audit packet plan/materialization/leakage review, label fill, ingestion, target-independence audit, path decision을 진행했다.
- `v77-v80`: positive-anchor repair plan, capacity scan, blocker synthesis, path decision을 진행했다.
- `v81`: RGA benchmark reframing plan과 target-identifiability contract를 고정했다.

## 핵심 결과

`hanging on` strict route는 hidden proxy balance를 만들 수 있었지만, visual/mesh audit 후
`accept/reject/abstain = 9/193/38`로 severe positive-sparse target이 됐다. 즉 proxy-balanced
construction이 reliability-balanced target으로 이어지지 않았다.

Positive-anchor route는 `curtain/blinds/bag/towel` subject와 `door/window/stand` anchor에 집중된
accept seed를 기반으로 설계했다. Full train에는 positive-anchor proxy 455개와 hard-negative proxy
377개가 있었지만, `same_affordance_rank_coverage` control spec에서 mixed cell은 5개뿐이었다.
따라서 row count가 아니라 matched-cell diversity가 blocker였다.

## 방향성 검토

`v80`에서 H002의 conceptual direction은 유지하되, 현재 Open3DSG train-side posterior-target
mining route는 method claim으로 준비되지 않았다고 판단했다.

```text
conceptual_direction = valid_and_worth_preserving
current_operational_route = not_ready_for_posterior_method_claim
```

문제는 combiner가 약한 것이 아니라 target-identifiability다. 현재 target은 object/endpoint,
predicate/rank, geometry_status, positive-sparse distribution, too-few matched cells로 설명될 수
있다.

## V81 Reframing

H002는 immediate posterior method claim이 아니라 RGA benchmark / target-identifiability
framework로 재정리됐다. 고정한 benchmark task는 다음과 같다.

- RGA state assignment
- relation-family witness audit
- target-identifiability audit
- failure taxonomy
- posterior gate

Posterior smoke는 class mass, controlled mixed-cell, shortcut-probe, hidden-field leakage,
train-only provenance, audit-label independence gate가 모두 통과될 때만 허용한다.

## 다음 단계

다음 TODO는 `reliability_target_v24_rga_failure_taxonomy_materialization`이다. 기존 artifact에서
relation-family별 blocker를 benchmark-facing table로 materialize한다.

## Boundary

- Train-only H002 hypothesis evidence.
- Validation/test 사용 없음.
- H001 artifact 수정 없음.
- 새 label 없음.
- Posterior smoke 없음.
