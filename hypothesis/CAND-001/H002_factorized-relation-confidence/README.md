# H002 Factorized Relation Confidence

H002는 3D Scene Graph relation edge의 `semantic score`, `geometry validity`,
`coverage`, `uncertainty`, `relation reliability`를 분리해 보는 hypothesis branch다.

현재 핵심 명제:

```text
semantic score != geometry validity != relation reliability
```

## Current Status

```text
current_gate = v13 proximity LH scene/geometry label fill completed
current_status = visible-only scene/geometry proxy labels filled; positive-mass risk noted
posterior_smoke_allowed = false
validation_or_test_used = false
next_todo = reliability_target_v13_proximity_lh_scene_geometry_label_ingestion
```

현재 결론은 H002 가설이 틀렸다는 것이 아니다. 현재까지의 반복은 relation reliability를
검증할 target이 shortcut 없이 독립적이어야 한다는 점을 확인한 과정이다. v9에서는
exact endpoint-pair 후보 수는 충분했지만, `rank_band`가 predicate를 너무 잘 설명해서
primary posterior target으로 쓰기 어렵다는 결론에 도달했다. v9 path decision에서는 이
exact-pair route를 diagnostic-only로 고정하고, 다음 target repair route로 `close by` /
`proximity` feasibility scan을 선택했다. v10 proximity feasibility scan 결과, proximity는
전체 train 수량과 LH 후보 수량은 충분하지만 현재 RGA queue에서는 `RGA-HL = 0`,
`RGA-LH = 171324`로 양방향 mismatch target이 아니라 LH-only target-repair branch로만
가능하다는 결론이다. 이후 path decision에서 RGA framework는 양방향 HL/LH mismatch로
유지하고, 다음 empirical branch만 proximity LH-only로 좁히기로 결정했다.
v12 label-readiness 결과, 240개 reviewer-visible row와 hidden audit manifest가 준비됐고
visible leakage hit와 validation error는 모두 0이다.
v12 label-fill 결과, hidden metadata를 읽지 않고 visible-only proxy label을 채웠으며
`accept/reject/abstain = 36/71/133`, binary usable row는 107개다.
v12 label-ingestion 결과, multiclass 240개와 binary 107개 target을 만들었지만 quick probe에서
object-pair shortcut risk가 강하게 나타나 posterior smoke는 계속 금지된다.
v12 target-independence audit 결과, strict/diagnostic controlled slice가 0개이며
object-pair mixed contrast도 0개라 posterior target으로 사용할 수 없다는 결론이다.
이후 path decision에서 visible-only proximity branch는 diagnostic-only negative evidence로
고정하고, 다음 단계는 scene/geometry-aware target repair plan으로 선택했다.
v13 repair plan 결과, train-only repair pool은 50,966개이며 visible object-pair block 후보는
1,510개, strong block 후보는 778개로 candidate mining capacity가 충분하다. 다음 단계는
object-pair text가 아니라 local scene/geometry evidence를 reviewer-visible surface로 제공하는
candidate sheet를 만드는 것이다. v13 candidate mining 결과, 30개 visible object-pair block에서
각 8개씩 총 240개 row를 선택했고, 182개 scan / 196개 subgraph를 포함하며 visible leakage는
0개다. v13 label-fill 결과, hidden audit manifest를 읽지 않고 reviewer-visible scene/geometry
evidence만 사용해 `accept/reject/abstain = 39/137/64`, binary usable row `176`개를 만들었다.
다만 positive row가 `39`개로 이전 post-label gate의 minimum-per-class `50` 기준에는 못
미치므로 posterior smoke는 계속 금지된다. 다음 단계는 hidden audit manifest join과
target-independence audit을 위한 label ingestion이다.

## Canonical Files

| File | Role |
| --- | --- |
| `README.md` | 현재 H002 폴더의 파일 역할과 최신 상태 |
| `summary_branch_v2.md` | H002의 긴 누적 research log와 근거/claim boundary |
| `RGA_framework.md` | RGA framework 정의, axis, bucket, metric, gate 원칙 |
| `feasibility_check.md` | multi-view와 posterior 결합 방식 관련 feasibility 판단 |
| `stages/` | v1~v20 stage별 진행 내용, 문제점, 다음 단계로 넘어간 이유 |

## Consolidation

2026-06-22 KST에 루트의 numbered markdown stage logs `01_*.md`부터 `217_*.md`까지는
v1~v10 stage별 문서(`stages/`)와 전체 흐름 요약(`summary_branch_v2.md`)으로 정리했다.
이후 새 stage는 루트 numbered markdown을 만들지 않고 `stages/` 아래에 v11부터 이어간다.
개별 단계의 raw result는 `artifacts/` 아래의 `summary.json`, `report.md`, `csv/jsonl`
산출물이 소유한다.

따라서 새 H002 TODO를 진행할 때는 루트에 새 numbered markdown을 계속 늘리지 않는다.
새로운 큰 decision이나 stage 요약은 다음 중 하나에 기록한다.

- 현재 상태와 전체 단계 흐름: `summary_branch_v2.md`
- stage별 상세 진행: `stages/`
- framework 정의 변경: `RGA_framework.md`
- 연구 framing과 claim boundary: `summary_branch_v2.md`
- posterior/multi-view feasibility 판단: `feasibility_check.md`

## Current Relation Scope

Core target construction은 현재 `support_contact`와 `relative_vertical` 중심이다.

포함 또는 예정:

- `standing on`, `lying on`
- `higher than`, `lower than`
- `close by`는 v10/v11 feasibility, v12 path decision, v13 label readiness, v14 visible-only label fill, v15 label ingestion, v16 target-independence audit, v17 path decision, v18 repair plan, v19 candidate mining, v20 scene/geometry-aware label fill을 거쳐 label ingestion 대기 상태다.
- `attached to`, `hanging on`, `connected to`는 multi-view/contact evidence 확장 후보로 유지한다.
- `front`, `behind`, `left`, `right`는 현재 H002 primary posterior target이 아니라 future relation-family expansion이다.

## Guardrails

- H002 hypothesis 단계에서는 train-only evidence만 사용한다.
- validation/test는 hypothesis target construction이나 posterior smoke에 쓰지 않는다.
- posterior smoke는 target-independence gate가 통과할 때까지 실행하지 않는다.
- `rank_band_hidden`, `machine_hint_hidden`, target construction key는 model input이 아니라 audit/control axis다.
- multi-view는 현재 deployable input이 아니라 audit/label confirmation evidence다.
- H001 관련 파일과 paper experiment output은 수정하지 않는다.
