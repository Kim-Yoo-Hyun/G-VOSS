# H002 Factorized Relation Confidence

H002는 3D Scene Graph relation edge의 `semantic score`, `geometry validity`,
`coverage`, `uncertainty`, `relation reliability`를 분리해 보는 hypothesis branch다.

현재 핵심 명제:

```text
semantic score != geometry validity != relation reliability
```

## Current Status

```text
current_gate = v22 hanging-on strict candidate mining completed
current_status = hanging-on strict 240-row candidate sheet is ready for source inventory
posterior_smoke_allowed = false
validation_or_test_used = false
next_todo = reliability_target_v22_hanging_on_strict_conditional_contrast_source_inventory
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
target-independence audit을 위한 label ingestion이다. v13 label-ingestion 결과, multiclass
240개, binary 176개, geometry-support 176개, usefulness 176개 target을 만들었고 validation
error는 0개다. 그러나 reliability positive는 여전히 39개이며 quick probe risk flag가 32개라
posterior smoke는 계속 금지된다. 같은 block / visible object-pair 내부 mixed accept/reject
group은 22개로 v12보다 개선됐지만, 다음 단계에서 target-independence audit이 필요하다.
v13 target-independence audit 결과, primary reliability target은 `39/137`로 positive-sparse이며
strict/diagnostic clear slice가 모두 0개다. Geometry-support target은 class mass 자체는
`121/55`로 통과하지만 auxiliary target이고 strict independent slice가 없다. 따라서 v13 proximity
scene-geometry branch는 posterior로 넘어갈 수 없고 path decision이 필요하다.
v13 path decision 결과, proximity branch는 diagnostic/generality evidence로 고정하고 primary
target repair route는 `v14_physical_relation_family_feasibility_scan`으로 이동했다. v14
feasibility scan 결과, `support_contact`는 match rows `556,038`, checkable rows `556,038`,
HL/LH queue rows `1,069/160,429`, same-predicate HL/LH capacity `2,138`로 다음 sampling
anchor가 가능하다. 다만 HL/LH imbalance와 `lying on` 중심 capacity concentration이 있어
posterior로 바로 가지 않는다. `relative_vertical`은 control family로 유지하고,
`attachment_deferred`는 current geometry policy에서 `unsupported_family`라 witness schema 전까지
posterior target으로 쓰지 않는다. v14 sampling plan 결과, target queue는 총 240개로 고정했다.
`support_contact`가 160개 primary anchor이고 `relative_vertical`이 80개 control이다. 세부 quota는
`lying on` HL/LH `68/68`, `standing on` HL/LH `12/12`, `lower than` HL/LH `40/40`이다.
`supported by`, `higher than`, `attachment_deferred`는 현재 primary target에서 제외한다. 다음 단계는
이 quota와 cap policy에 맞춰 실제 candidate rows를 mining하는 것이다. v14 candidate mining 결과,
240-row label-ready sheet를 만들었다. `support_contact` 160개, `relative_vertical` 80개,
unique scans 202개, unique subgraphs 222개, raw feature join 240/240, visible leakage 0,
validation error 0이다. 다만 `standing on` HL row 17개가 모두 hard room-surface subject를
포함해 hard filter를 통과하지 못했으므로, 계획된 12개를 `lying on` HL로 옮겼다.
v14 label-fill 결과, hidden audit manifest를 읽지 않고 reviewer-visible evidence만 사용해
`accept/reject/abstain = 48/152/40`, binary usable row `200`개를 만들었다. 그러나 positive
row가 `48`개로 이전 post-label gate의 minimum-per-class `50` 기준보다 2개 부족하므로
posterior smoke는 계속 금지된다. 다음 단계는 hidden audit manifest join과 target-independence
audit을 위한 label ingestion이다. v14 label-ingestion 결과, locked labels를 hidden audit
manifest와 join해 multiclass 240개, binary 200개, geometry-support 200개, usefulness 200개,
endpoint 240개, coverage 240개 target artifact를 만들었고 validation error는 0개다. 그러나
reliability positive는 `48`개라 class-mass gate를 통과하지 못했고, quick probe risk flag가
64개이므로 posterior smoke는 계속 금지된다. 같은 visible object-pair 내부 mixed binary group은
11개로 완전히 identity-determined target은 아니지만, target-independence audit이 필요하다.
v14 target-independence audit 결과, primary relation binary target은 `48/152`로 positive-sparse이고
strict/diagnostic clear slice가 모두 0개다. Full quick-probe risk flag는 65개, slice-level blocking
risk flag는 1,171개다. Balanced full slice는 `48/48`로 만들 수 있지만 shortcut risk가 남아
posterior smoke는 계속 금지된다. v14 path decision 결과, 현재 v14 target은 diagnostic
target-construction evidence로 고정하고, 다음 route는 `v15_witness_matched_physical_relation_repair_plan`으로
선택했다. 단순히 positive 2개를 추가하는 방식은 shortcut 문제를 해결하지 못하므로 rejected다.
v15 repair plan 결과, selected route는
`support_contact_witness_matched_repair_with_relative_vertical_control`로 고정했다.
새 plan은 `support_contact`를 primary target으로 두고 `relative_vertical`은 최대 16-row
control로 축소한다. Post-label gate는 positive/negative 각각 최소 60개, pre-label gate는
matched witness strata 8개 이상으로 고정했다. Posterior smoke는 계속 금지되며, 다음 단계는
이 contract를 만족하는 후보 capacity가 실제 train queue에 있는지 확인하는 capacity scan이다.
v15 capacity scan 결과, support/contact row 수량은 충분했다. Hard filter 이후
`support_contact` 후보는 51,491개이고, cap 적용 preview도 `lying on` 192개,
`standing on` 32개까지 채울 수 있다. 그러나 selected preview 240개가 모두 `LH` /
`satisfied`였고, support/contact mixed witness stratum은 0개였다. 따라서 v15 contract는
row capacity가 아니라 mixed-stratum independence gate에서 막혔으며, posterior smoke와 label
sheet 생성은 계속 금지된다.
v15 path decision after capacity scan 결과, same-witness HL/LH matching은 H002의
semantic-geometry mismatch 정의와 맞지 않는 과도한 조건으로 판단했다. 다음 route는
`controlled_cross_stratum_support_contact_contrast`로 선택했다. `support_contact`는 유지하되,
HL과 LH를 같은 witness bucket에 넣지 않고 서로 다른 disagreement state로 비교한다. 대신
predicate, source queue, rank band, scan/object distribution, endpoint type, coverage, reason
family, `p_geom_bin`, `geometry_status`를 control/audit axis로 강하게 고정한다.
v16 cross-stratum plan 결과, primary balanced target은 `lying on` HL 100개와 LH 100개로
고정했다. `standing on`은 hard filter 이후 eligible HL이 0개라 primary target이 아니라
24-row diversity/diagnostic으로 둔다. `relative_vertical lower than`은 16-row small control이다.
Visible label surface에는 `queue_kind`, `rank_band`, `geometry_status`, `p_geom_valid`,
`machine_hint`, `label_match_status`, quota cell, `RGA-HL`, `RGA-LH`를 노출하지 않는다.
v16 capacity scan 결과, raw quota capacity는 충분했지만 controlled selection은 막혔다.
`lying on` HL은 hard filter 이후 896개, LH는 26,882개였지만, HL은 전부 `unsatisfied`,
LH는 전부 `satisfied`였고 primary mixed block도 4개뿐이라 40-block gate를 통과하지 못했다.
따라서 label sheet와 posterior smoke는 계속 금지된다. v16 path decision에서는 이 route를
diagnostic-only로 고정하고, 다음 route로 `attachment_deferred_witness_schema_probe`를
선택했다. 다음 단계는 `attached to`, `hanging on`, `connected to`에 대해 typed witness schema를
정의하고 train-only capacity를 볼 수 있는 계획을 만드는 것이다. v17 plan 결과, attachment
row는 556,038개이지만 schema 전 checkable row는 0개임을 확인했고, `near_contact_distance`,
`projected_overlap`, `relative_vertical_anchor`, `floor_support_confound`,
`anchor_affordance_bucket`, `coverage`, `uncertainty`를 typed witness axis로 고정했다.
다음 단계는 같은 directed pair의 support/vertical raw geometry를 join해 capacity scan을
수행하는 것이다. v17 capacity scan 결과, 556,038 attachment rows가 모두 raw geometry에
join됐고, typed witness cell capacity와 240-row capped preview가 모두 통과했다. 그러나 이
결과는 label sheet나 posterior evidence가 아니며, 다음 단계는 candidate mining을 허용할지
결정하는 path decision이다.

## Canonical Files

| File | Role |
| --- | --- |
| `README.md` | 현재 H002 폴더의 파일 역할과 최신 상태 |
| `summary_branch_v2.md` | H002의 긴 누적 research log와 근거/claim boundary |
| `RGA_framework.md` | RGA framework 정의, axis, bucket, metric, gate 원칙 |
| `feasibility_check.md` | multi-view와 posterior 결합 방식 관련 feasibility 판단 |
| `stages/` | v1~v68 stage별 진행 내용, 문제점, 다음 단계로 넘어간 이유 |

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

Core target construction은 현재 `attachment_deferred`의 `hanging on` strict source inventory다.
이전 `support_contact`, `relative_vertical`, `proximity` branch는 full-train에서 확인했지만
현재는 diagnostic/generalization evidence로 둔다.

포함 또는 예정:

- `standing on`, `lying on`
- `higher than`, `lower than`
- `close by`는 v10/v11 feasibility, v12 path decision, v13 label readiness, v14 visible-only label fill, v15 label ingestion, v16 target-independence audit, v17 path decision, v18 repair plan, v19 candidate mining, v20 scene/geometry-aware label fill, v21 label ingestion, v22 target-independence audit, v23 path decision을 거쳐 diagnostic/generality evidence로 고정됐다.
- `support_contact`는 v24 physical relation-family feasibility scan에서 primary sampling anchor로 선택됐고, v25 sampling plan에서 160-row primary quota로 고정됐으며, v26에서 160-row label-ready candidates로 materialized 됐다.
- `relative_vertical`은 v24에서 control family로 유지됐고, v25 sampling plan에서 80-row control quota로 고정됐으며, v26에서 80-row label-ready candidates로 materialized 됐다.
- v27에서 `support_contact`/`relative_vertical` visible-only proxy labels를 채웠지만, positive class mass가 `48`이라 ingestion/audit 전까지 posterior target으로 쓰지 않는다.
- v28에서 target artifacts를 만들었지만, positive class mass fail과 quick-probe risk 때문에 target-independence audit 전까지 posterior target으로 쓰지 않는다.
- v29에서 target-independence audit을 완료했지만, strict/diagnostic clear slice가 0개라 posterior target으로 쓰지 않는다.
- v30에서 v14를 diagnostic evidence로 고정하고 v15 witness-matched repair plan을 다음 route로 선택했다.
- v31에서 v15 repair contract를 고정했다. `support_contact` primary target을 224-row 후보로 늘리고 `relative_vertical`은 16-row control로 축소하는 plan이며, label fill 전 capacity scan을 요구한다.
- v32에서 v15 capacity scan을 완료했다. 수량과 capped preview는 충분하지만 mixed witness stratum이 0개라 label sheet 생성 전 path decision이 필요하다.
- v33에서 same-witness HL/LH matching을 reject하고 v16 controlled cross-stratum support/contact contrast plan을 다음 route로 선택했다.
- v34에서 v16 cross-stratum quota, block construction, label-surface, target-independence audit plan을 고정했다. 다음은 capacity scan이다.
- v35에서 v16 capacity scan을 완료했다. Raw quota capacity는 충분하지만 `lying on` HL이 전부 `unsatisfied`, LH가 전부 `satisfied`라 side-level geometry/status shortcut이 남고 primary mixed block도 4개뿐이다. Label sheet 생성은 중단하고 path decision이 필요하다.
- v36에서 v16을 diagnostic-only로 고정하고 다음 route로 `attachment_deferred_witness_schema_probe`를 선택했다. 바로 label mining을 하지 않고 `attached to`, `hanging on`, `connected to`의 typed geometry/coverage witness schema를 먼저 정의한다.
- v37에서 `attachment_deferred` witness schema plan을 고정했다. 현재 attachment rows는 556,038개지만 schema 전에는 전부 unsupported이므로, 다음 단계는 directed pair raw geometry join과 typed witness capacity scan이다.
- v38에서 attachment witness capacity scan을 완료했다. Raw geometry join coverage는 1.0이고, all witness cells pass, 240-row capped preview deficits는 0이다. 다음은 candidate mining 허용 여부를 결정하는 path decision이다.
- v39에서 attachment path decision을 완료했다. `attached to`와 `hanging on`은 primary candidate mining으로 진행하고, `connected to`는 functional connection ambiguity 때문에 diagnostic-only로 유지한다. 다음은 hidden-field-safe v18 candidate mining이다.
- v40에서 v18 attachment candidate mining을 완료했다. 240-row label-ready sheet와 hidden audit manifest를 만들었고, primary `attached to`/`hanging on` 160개, diagnostic `connected to` 60개, uncertainty audit 20개이며 visible leakage와 validation error는 0이다. 다음은 visible-only label fill이다.
- v41에서 v18 visible-only label fill을 완료했다. Hidden manifest는 읽지 않았고 validation error는 0이다. Primary binary usable row는 114개, positive는 33개, negative는 81개라 posterior smoke는 계속 금지된다. 다음은 label ingestion이다.
- v42에서 v18 label ingestion을 완료했다. 240개 labels를 hidden manifest와 join했고 binary target 114개, diagnostic connected target 62개, geometry-support target 154개를 만들었다. Positive 33개로 class-mass gate를 통과하지 못하고 quick-probe risk flag가 102개라 posterior smoke는 계속 금지된다. 다음은 target-independence audit이다.
- v43에서 v18 target-independence audit을 완료했다. Primary relation binary는 `114`개(`33/81`)로 positive-sparse이고 strict/diagnostic clear slice가 모두 `0`개다. Full quick-probe risk flag는 `119`개, slice-level blocking risk flag는 `3,163`개다. `connected to` diagnostic target은 `62`개(`37/25`)지만 clear slice가 없고, geometry-support는 class mass는 통과해도 auxiliary target이라 main reliability target을 대체할 수 없다. 다음은 path decision이다.
- v44에서 v18 path decision을 완료했다. v18 attachment target은 diagnostic-only negative target-construction evidence로 고정하고, 다음 route로 `v19_attachment_deferred_independent_evidence_repair_plan`을 선택했다. Multi-view/mesh는 현재 model input이 아니라 audit/confirmation evidence로만 허용한다. Posterior smoke는 계속 금지된다.
- v45에서 v19 independent-evidence repair plan을 완료했다. Selected route는 `independent_visual_or_mesh_audit_packet_before_labels`이며, primary scope는 `attached to` / `hanging on`, diagnostic scope는 `connected to`다. Local probe에서는 3RScan `multi_view`와 `sequence` directory가 sampled scan 40개에서 확인됐지만, 이는 full inventory가 아니므로 다음 단계는 row별 source inventory다. Label fill, candidate mining, posterior smoke는 아직 금지된다.
- v46에서 v19 source inventory를 완료했다. 240개 row / 202개 scan 모두 scan, `multi_view`, `sequence`, mesh asset이 존재했고, primary 160개 row 모두 subject/object crop과 audit-ready evidence를 갖는다. 다만 strong same-frame co-visible row는 43개뿐이고 나머지 197개는 individual-view-plus-mesh evidence이므로, 다음 단계는 두 evidence tier를 분리하는 audit packet plan이다. Label fill과 posterior smoke는 계속 금지된다.
- v47에서 v19 audit packet plan을 완료했다. Reviewer-visible schema와 hidden asset manifest plan을 분리했고, visible packet에서 scan/subgraph/id, geometry status, rank, machine hint, raw feature, v18 label/reason/review note를 금지했다. Packet plan은 240개 row이며 primary 160개, connected diagnostic-only 62개, uncertainty/coverage audit-only 18개다. Primary evidence tier는 T1 strong pair visual 31개와 T2 individual visual plus mesh 129개다. 다음은 실제 packet materialization이다.
- v48에서 v19 audit packet materialization을 완료했다. 240개 reviewer-visible rows, 240개 packet dirs, 4,466개 neutral packet-local image copies, 240개 hidden manifest rows를 생성했고 visible leakage hit와 validation error는 모두 0개다. Source path, scan/subgraph/id, instance id, original filename은 hidden manifest에만 남겼다. 다음은 label fill 전 formal leakage review다.
- v49에서 formal leakage review를 완료했다. Visible sheet 240개 row, packet markdown 240개, neutral image files 4,466개를 검사했고 source path, scan/subgraph id, instance id, construction metadata, old label/reason/review note leakage는 0개다. Hidden manifest에는 source path와 scan id가 240개 row 모두에 보존됐다. 다음은 packet 기반 label fill이다.
- v50에서 v19 packet label fill을 완료했다. Hidden manifest를 읽지 않고 leakage-reviewed visible sheet, packet markdown, packet-local image availability만 사용했으며 validation error는 0개다. Label 분포는 `accept/reject/abstain = 26/99/53`, connected diagnostic `possible/ambiguous = 15/47`, primary binary preview는 `26/99`다. Positive-sparse risk가 남아 posterior smoke는 계속 금지되며, 다음 단계는 label ingestion이다.
- v51에서 v19 label ingestion을 완료했다. Hidden manifest는 label lock 이후에만 읽었고 validation error는 0개다. Multiclass 240개, primary binary 125개(`26/99`), connected diagnostic 62개, geometry-support 140개, uncertainty 240개 target을 만들었다. Class mass fail과 quick-probe risk 43개 때문에 posterior smoke는 계속 금지되며, 다음 단계는 target-independence audit이다.
- v52에서 v19 target-independence audit을 완료했다. Primary relation binary는 125개(`26/99`)로 class mass gate를 통과하지 못했고 strict/diagnostic clear slice는 모두 0개다. Full quick-probe risk flag는 56개, slice blocking risk flag는 1,185개이며 visible endpoint pair, scan/subgraph id, subject label, primary reason shortcut이 강하다. Posterior smoke는 계속 금지되고 다음 단계는 path decision이다.
- v53에서 v19 audit-packet path decision을 완료했다. v19 target은 diagnostic-only negative target-construction evidence로 고정하고, 다음 route로 `v20_attachment_deferred_endpoint_balanced_counterfactual_repair_plan`을 선택했다. Posterior smoke와 stronger combiner는 계속 금지하며, 다음 target은 full train attachment pool에서 endpoint/object/predicate/scan shortcut을 직접 통제하도록 설계해야 한다.
- v54에서 v20 endpoint-balanced counterfactual repair plan을 완료했다. Primary predicate는 `attached to` / `hanging on`, diagnostic predicate는 `connected to`로 고정했다. 다음 capacity scan은 sample size `240/320/400`, exact visible endpoint-pair mixed contrast, object-family/predicate/evidence-tier/scan-balanced fallback, post-label `60/60` accept/reject gate를 평가해야 한다. Posterior smoke는 계속 금지된다.
- v55에서 v20 capacity scan을 완료했다. Full train attachment pool은 556,038 rows이며 exact visible endpoint-pair mixed group 4,616개, balanced pair capacity 26,054개가 있어 exact endpoint-pair mixed contrast route가 통과했다. `240/320/400` preview가 모두 quota deficit 없이 feasible하며, default next candidate size는 `320`이다. 다음 단계는 hidden-field-safe candidate mining이다.
- v56에서 v20 candidate mining을 완료했다. 320-row candidate sheet와 hidden manifest를 만들었고 visible leakage hit는 0이다. Primary binary candidate는 256개(`attached to`/`hanging on`), `connected to` diagnostic은 64개다. 다음 단계는 새 candidate rows에 대해 multi-view/mesh/source inventory를 확인하는 것이다.
- v57에서 v20 source inventory를 완료했다. 320개 row 모두 audit-ready이고, primary 256개와 `connected to` diagnostic 64개 모두 subject/object crop과 mesh/sequence/multi-view source를 갖는다. 다만 strong same-frame co-visible evidence는 75개뿐이고 245개는 individual-view-plus-mesh tier이므로, 다음 audit packet plan은 이 evidence tier를 보존해야 한다.
- v58에서 v20 audit packet plan을 완료했다. 320-row visible packet template, hidden asset manifest plan, visible schema, packet contract를 만들었고 validation error는 0이다. Evidence tier는 T1 75개, T2 245개이며 primary rows는 T1 62개, T2 194개다. 다음 단계는 이 plan에 따라 packet assets를 neutral packet-local names로 materialize하는 것이다.
- v59에서 v20 audit packet materialization을 완료했다. 320개 packet directory와 5,836개 neutral packet-local image를 만들었고 visible leakage hit와 validation error는 0이다. Hidden materialized manifest에는 existing GT relation match axis도 320/320 join해 보존했다. 다음 단계는 label fill 전 formal leakage review다.
- v60에서 v20 audit packet formal leakage review를 완료했다. Visible sheet 320개 row, packet markdown 320개, neutral image files 5,836개를 검사했고 visible leakage hit와 validation error는 0이다. Hidden manifest에는 source path, scan id, existing GT-match auxiliary axis가 320/320 보존됐지만 visible packet에는 노출되지 않는다. 다음 단계는 packet 기반 label fill이다.
- v61에서 user-filled visible packet labels를 검증하고 label-fill artifact로 잠갔다. Hidden manifest, source path, scan id, GT-match axis, rank/score, geometry status, `p_geom_valid`를 보지 않았고 validation error는 0이다. 전체 `accept/reject/abstain = 25/182/113`, primary binary preview는 `25/182`, connected diagnostic rows는 전부 `abstain_uncertain`으로 유지했다. 다음 단계는 label ingestion이다.
- v62에서 locked labels를 hidden materialized manifest와 사후 join했다. Multiclass target 320개, primary binary 207개(`25/182`), geometry-support 219개, endpoint/coverage/uncertainty target 320개를 만들었고 validation error는 0이다. GT/reliability mismatch table도 생성했지만, positive-sparse와 quick-probe risk 70개 때문에 posterior smoke는 계속 금지된다. 다음 단계는 target-independence audit이다.
- v63에서 v20 target-independence audit을 완료했다. Primary relation binary는 207개(`25/182`)로 class-mass gate를 통과하지 못했고 strict/diagnostic clear slice가 모두 0개다. Full quick-probe risk flag는 82개, slice-level blocking risk flag는 1,112개이며, geometry-support/coverage/endpoint auxiliary target도 strict independent slice가 없다. Posterior smoke는 계속 금지되고 다음 단계는 path decision이다.
- v64에서 v20 path decision을 완료했다. v20 audit packet은 diagnostic negative target-construction evidence로 고정하고 posterior smoke, balanced `25/25` slice, stronger combiner, geometry-support-as-primary, connected-to-primary를 모두 reject했다. 다만 320-row packet이 우연히 reject-heavy였을 가능성은 남아 있으므로, 다음 route는 full-train `v21_attachment_deferred_conditional_contrast_capacity_scan`으로 선택했다.
- v65에서 v21 conditional contrast capacity scan을 완료했다. Full-train attachment pool은 primary `attached to`/`hanging on` 370,692 rows와 diagnostic `connected to` 185,346 rows로 확인됐고 raw geometry join validation error는 0이다. Strict spec `same_predicate_rank_geometry_family`는 mixed groups 258, balanced capacity 4,507로 수량은 있지만 `hanging on`에만 남고 `attached to`는 빠진다. Relaxed diagnostic spec `same_predicate_rank_family`는 `attached to`와 `hanging on` 모두 mixed group을 갖지만 shortcut risk가 커서 바로 posterior로 갈 수 없다. 다음 단계는 strict primary를 `hanging on`으로 좁힐지, `attached to`를 diagnostic으로 낮출지 결정하는 path decision이다.
- v66에서 v21 path decision을 완료했다. Strict condition은 GT rule이 아니라 predicate/rank/geometry bucket/object-family shortcut을 막기 위한 H002 control rule로 명시했다. 결정은 `hanging on`을 strict primary 후보로 남기고, `attached to`는 diagnostic/relaxed probe로 낮추며, `connected to`는 diagnostic-only로 유지하는 것이다. 다음 단계는 `reliability_target_v22_hanging_on_strict_conditional_contrast_packet_plan`이다.
- v67에서 v22 hanging-on strict packet plan을 완료했다. Full-train `hanging on` rows 185,346개에서 strict groups 2,222개, mixed strict groups 258개, balanced capacity 4,507개를 확인했다. Hidden-only dry-run preview는 240 rows, proxy role `120/120`, selected strict groups 95개, scan 192개, visible endpoint pair 193개로 구성되며 max scan/endpoint/group cap이 모두 통과했다. Visible label sheet나 packet asset은 아직 만들지 않았고, 다음 단계는 hidden-field-safe candidate mining이다.
- v68에서 v22 hanging-on strict candidate mining을 완료했다. 240-row visible candidate sheet, 240-row hidden manifest, 240-row candidate rows를 만들었고 visible leakage hit와 validation error는 모두 0이다. Visible sheet에는 relation text와 blank review fields만 두고, rank/geometry bucket/object-family/GT match/planned proxy role/strict group/source ids는 hidden manifest에만 보존했다. Packet assets와 labels는 아직 만들지 않았으므로 다음 단계는 source inventory다.
- `front`, `behind`, `left`, `right`는 현재 H002 primary posterior target이 아니라 future relation-family expansion이다.

## Guardrails

- H002 hypothesis 단계에서는 train-only evidence만 사용한다.
- validation/test는 hypothesis target construction이나 posterior smoke에 쓰지 않는다.
- posterior smoke는 target-independence gate가 통과할 때까지 실행하지 않는다.
- `rank_band_hidden`, `machine_hint_hidden`, target construction key는 model input이 아니라 audit/control axis다.
- multi-view는 현재 deployable input이 아니라 audit/label confirmation evidence다.
- H001 관련 파일과 paper experiment output은 수정하지 않는다.
