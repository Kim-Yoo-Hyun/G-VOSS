# H002 Direction Transition Report

Date: 2026-06-25 KST

Working title:

```text
Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations
```

## 1. Existing H002

기존 H002는 relation source가 제공하는 하나의 confidence score가 relation reliability를
충분히 설명하지 못한다는 문제에서 출발했다.

초기 핵심 명제는 다음이었다.

```text
semantic score != geometry validity != relation reliability
```

이를 검증하기 위해 H002는 `RGA(Relation-Geometric Agreement)` framework를 만들고,
relation candidate를 semantic axis, geometry axis, coverage, uncertainty, audit label로
분해했다.

초기 method 후보는 다음 posterior였다.

```text
P(R_e = 1 | S_e, G_e, C_e, U_e)
```

여기서:

- `S_e`: source semantic score/rank
- `G_e`: geometry validity or geometry evidence
- `C_e`: coverage
- `U_e`: uncertainty
- `R_e`: relation reliability

기존 실험 route는 human/audit reliability target을 만들고, 그 target이 shortcut 없이
독립적이면 factorized posterior smoke를 실행하는 방식이었다.

## 2. What Was Learned

v1-v81의 target construction 과정에서 다음 사실이 반복적으로 확인됐다.

1. row count 자체는 여러 relation family에서 충분했다.
2. 그러나 accept/reject target은 positive-sparse하게 형성되는 경우가 많았다.
3. target label은 predicate, rank band, endpoint pair, object family, geometry status,
   construction metadata로 쉽게 설명되는 경우가 많았다.
4. shortcut을 막기 위해 control을 강하게 걸면 mixed positive/negative strata가 부족해졌다.
5. `attached to`, `hanging on`, `connected to`는 metric geometry만으로 신뢰 가능한
   reliability label을 만들기 어렵다.
6. RGA benchmark/failure taxonomy는 diagnostic으로는 필요하지만, 단독으로 top-tier method
   novelty를 만들기에는 약하다.

따라서 기존 route의 병목은 posterior combiner가 약해서가 아니라, **posterior가 학습할
독립 reliability target을 현재 방식으로 안정적으로 만들기 어렵다**는 데 있었다.

## 3. Why The Direction Changes

기존 H002는 relation reliability를 예측하려 했지만, 실제로 더 근본적인 문제는
`G_e`와 `C_e`가 충분히 잘 정의되지 않았다는 점이다.

즉 질문을 다음처럼 바꿔야 한다.

기존 질문:

```text
Can a factorized posterior predict human/audit relation reliability labels?
```

새 질문:

```text
Can we learn predicate-geometry compatibility by separating semantic evidence,
geometry-only evidence, and observability quality?
```

이 전환은 H002의 핵심 주장을 버리는 것이 아니다. 오히려 기존 factorized claim을 더
강하게 구현한다.

기존 H002의 약점:

```text
S_e, G_e, C_e, U_e를 나눴지만 실제 학습 route는 flat posterior target fitting에 가까웠다.
```

새 H002의 강점:

```text
T_e, Z_e, G_e, C_e, Q_e를 구조적으로 분리하고,
C_e를 source score 없이 counterfactual compatibility learning으로 학습한다.
```

## 4. New H002

새 H002는 다음 구조로 진행한다.

```text
Geometry-only evidence encoder -> G_e
Semantic-content encoder -> T_e
Source-confidence encoder -> Z_e
Contrastive compatibility head: compatibility(T_e, G_e) -> C_e
Evidence-quality head -> Q_e
Two-head decision -> p_obs, p_rel
```

### 4.1 Geometry-Only Evidence Encoder

입력:

- object-pair point/mesh feature
- distance, height, overlap, contact, containment
- visibility-independent geometry

출력:

```text
G_e
```

중요한 원칙:

- predicate와 source score는 geometry encoder에 넣지 않는다.
- `G_e`는 source confidence shortcut을 배우지 않아야 한다.
- H001 `p_geom_valid`는 rule-based geometry evidence baseline 또는 teacher signal로
  재사용할 수 있다.

### 4.2 Semantic-Content Encoder

입력:

- predicate text/label
- subject/object class
- relation family

출력:

```text
T_e
```

`T_e`는 relation의 의미 내용만 표현한다. Source score, rank, source id는 넣지 않는다.

### 4.3 Source-Confidence Encoder

입력:

- source score/rank
- source id
- source-specific calibration metadata

출력:

```text
Z_e
```

`Z_e`는 final reliability head에는 들어갈 수 있지만 compatibility head에는 넣지 않는다.
이렇게 해야 compatibility가 기존 relation score를 복사하지 않는다.

### 4.4 Contrastive Compatibility Head

입력:

```text
T_e, G_e
```

출력:

```text
C_e = semantic-geometry compatibility
```

금지:

```text
C_e must not use Z_e
```

학습:

- GT / audit-accepted / high-precision verified positive vs hard counterfactual
- true pair vs wrong-pair geometry
- shuffled geometry
- subject/object swap
- predicate flip
- same-scene hard negative
- same-family/rank matched negative

이 head의 목적은 relation label을 다시 맞추는 것이 아니라, predicate가 요구하는 geometry
evidence와 실제 object-pair geometry가 호환되는지 학습하는 것이다.

### 4.5 Evidence-Quality Head

입력:

- view availability
- same-frame visibility
- mesh completeness
- point coverage
- evidence agreement/conflict
- missing or unsupported state

출력:

```text
Q_e = evidence quality / observability
```

기존 `coverage`와 `uncertainty`는 `Q_e` 안에서 함께 다룬다.

### 4.6 Two-Head Reliability Decision

최종 decision은 reliability와 abstain을 분리한다.

```text
p_obs = P(evidence is sufficient to decide | Q_e)
p_rel = P(relation is reliable | evidence is observable, Z_e, C_e, optional T_e)
```

결정:

```text
p_obs low -> abstain
p_obs high and p_rel high -> accept
p_obs high and p_rel low -> reject
```

기본 relation energy:

```text
E_rel(e) = E_src(Z_e) + E_comp(C_e) + E_interaction(Z_e, C_e, T_e)
p_rel = sigmoid(-E_rel(e))
```

`E_geom(G_e)`는 기본 relation validity term으로 쓰지 않는다. Predicate를 모르는 geometry
자체만으로 relation 성립 여부를 판단할 수 없기 때문이다. 남긴다면 point cloud 누락,
mesh artifact, impossible overlap 같은 geometry 품질/아티팩트 penalty로만 쓴다.

## 5. Relation To Prior H002 Artifacts

기존 artifact는 폐기하지 않는다. 역할이 바뀐다.

| Existing Artifact Type | New Role |
| --- | --- |
| RGA rows | mismatch diagnosis and evaluation axis |
| human/audit labels | evaluation/calibration subset and high-precision positive source |
| `p_geom_valid` | geometry-only rule baseline or teacher |
| target-independence audits | shortcut-control design evidence |
| v1-v81 stage logs | evidence that target-first posterior route is weak |
| multi-view/mesh packets | future `Q_e` and hard-relation evidence, not immediate main input unless controlled |

## 6. Novelty Position

새 H002의 novelty는 "Transformer를 썼다" 또는 "semantic과 geometry를 결합했다"가 아니다.

주장해야 할 novelty:

```text
Existing relation confidence conflates semantic plausibility and geometric support.
We learn predicate-geometry compatibility from geometry-only evidence and semantic/source evidence,
then compute relation reliability with source confidence separated from compatibility
and observability handled as a selective decision head.
```

핵심 차별점:

1. geometry encoder에서 predicate/source score를 제외해 `G_e`를 독립 evidence로 만든다.
2. semantic content `T_e`와 source confidence `Z_e`를 분리한다.
3. `C_e = compatibility(T_e, G_e)`에서는 `Z_e`를 금지한다.
4. `Q_e`를 통해 evidence 부족과 true contradiction을 분리한다.
5. final decision은 `p_obs`와 `p_rel` 두 head로 계산한다.

## 7. Immediate TODO

다음 H002 TODO는 다음 순서로 진행한다.

1. `method_contract_v1`
   - completed on 2026-06-25.

2. `geometry_evidence_schema_v1`
   - completed on 2026-06-25.

3. `counterfactual_protocol_v1`
   - wrong-pair, shuffled geometry, predicate flip, subject/object swap,
     same-scene/family/rank/coverage hard negative 생성 규칙 정의.

4. `prototype_dataset_contract_v1`
   - completed on 2026-06-25.
   - train-only prototype candidate schema, GT/audit/counterfactual axes, model views,
     and baseline-ready labels defined.

5. `smoke_baseline_plan_v1`
   - completed on 2026-06-25.
   - source-only, geometry-only, `S*p_geom_valid`, concat MLP, compatibility-only,
     no-`Q_e`, full two-head factorized decision, shortcut controls, and promotion gates defined.

6. `prototype_dataset_materialization_v1`
   - completed on 2026-06-25.
   - materialized `artifacts/prototype_dataset_v1/` with `694` train-only rows,
     `67` counterfactual groups, compatibility `67/67/560` for positive/negative/unknown,
     reliability `101/442/151` for accept/reject/abstain, and validation errors `0`.

7. `smoke_baseline_runner_v1`
   - completed on 2026-06-25.
   - materialized `artifacts/smoke_baseline_v1/`; Task A `134` rows, source-only AUROC `0.5008`,
     `semantic_score * p_geom_valid` AUROC `0.5317`, generic geometry proxy AUROC `0.6298`,
     relation-conditioned geometry proxy AUROC `0.6681`, mean paired compatibility drop `0.1411`,
     validation errors `0`, overall `ready_for_learned_smoke`.

8. `learned_smoke_runner_v1`
   - completed on 2026-06-25.
   - added `tools/learned_smoke_runner_v1.py` and materialized
     `artifacts/learned_smoke_v1/`.
   - Task A compatibility `134` rows: source-only `Z` AUROC `0.4885`,
     `p_geom_valid` AUROC `0.5507`, geometry-only `G` AUROC `0.7634`,
     compatibility `T+G` AUROC `0.9728`, full factorized `T+Z+G+Q` AUROC `0.9748`,
     predicate/family shortcut AUROC `0.5978`.
   - Task B observability `M6` AUROC `1.0000`; Task C reliability `M6` AUROC `0.9648`;
     two-head accept/reject/abstain macro-F1 `0.5062`.
   - Overall interpretation:
     `learned_smoke_promising_but_needs_family_shortcut_review`.

9. `attachment_numeric_geometry_materialization_v1`
   - completed on 2026-06-25.
   - added `tools/attachment_numeric_geometry_materialization_v1.py`, wrote
     `attachment_numeric_geometry_materialization_v1.md`, and materialized
     `artifacts/attachment_numeric_geometry_v1/`.
   - Extracted numeric predicate-independent `G_e` from locked v18 raw geometry fields:
     normalized 3D/XY distance, projected overlap, center height difference, vertical gap,
     near-contact indicators, and derived closeness/overlap features.
   - Counts: rows `240`, numeric `G_e` rows `240`, `attached to / hanging on / connected to`
     = `82 / 96 / 62`, compatibility positive/negative/unknown `33 / 81 / 126`,
     counterfactual groups `33`, validation errors `0`.
   - `connected to` remains diagnostic-only because the current artifact has no balanced physical
     compatibility target for that predicate.

10. `attachment_numeric_geometry_smoke_v1`
    - completed on 2026-06-25.
    - added `tools/attachment_numeric_geometry_smoke_v1.py`, wrote
      `attachment_numeric_geometry_smoke_v1.md`, and materialized
      `artifacts/attachment_numeric_geometry_smoke_v1/`.
    - Task A compatibility `114` rows with positive/negative `33/81`: source-only `Z` AUROC
      `0.4635`, semantic+source `T+Z` AUROC `0.8148`, geometry-only `G` AUROC `0.8949`,
      compatibility `T+G` AUROC `0.9282`, full factorized `T+Z+G+Q` AUROC `0.9364`,
      predicate/family shortcut AUROC `0.5305`.
    - Hidden audit probes remain high: hidden construction AUROC `0.8767`, hidden witness score
      AUROC `0.8010`.
    - Overall interpretation:
      `attachment_smoke_promising_but_requires_hidden_shortcut_review`.

11. `attachment_smoke_path_decision_v1`
    - completed on 2026-06-25.
    - wrote `attachment_smoke_path_decision_v1.md`.
    - Decision: do not promote attachment numeric `G_e` into the combined H002 main prototype yet.
    - Rationale: attachment `T+G` signal is strong, but hidden construction probe AUROC `0.8767`
      and hidden-cell label imbalance mean the target can still be partly explained by construction
      artifacts.
    - Selected next step: `attachment_shortcut_controlled_smoke_v1`.

12. `attachment_shortcut_controlled_smoke_v1`
    - completed on 2026-06-25.
    - added `tools/attachment_shortcut_controlled_smoke_v1.py`, wrote
      `attachment_shortcut_controlled_smoke_v1.md`, and materialized
      `artifacts/attachment_shortcut_controlled_smoke_v1/`.
    - Built a strict within-hidden-cell balanced Task A slice: `34` rows, positive/negative
      `17/17`, pair groups `17`, hidden cells `4`, validation errors `0`.
    - Result: source-only `Z` AUROC `0.5467`, geometry-only `G` AUROC `0.7232`,
      compatibility `T+G` AUROC `0.9550`, full factorized `T+Z+G+Q` AUROC `0.9689`,
      predicate/family shortcut AUROC `0.5000`, hidden construction probe AUROC `0.5000`.
    - Overall interpretation:
      `attachment_controlled_smoke_passed_promote_to_larger_controlled_mining`.
    - Boundary: this is a small train-only diagnostic slice, not paper evidence.

13. `attachment_controlled_expansion_plan_v1`
    - completed on 2026-06-25.
    - added `tools/attachment_controlled_expansion_plan_v1.py`, wrote
      `attachment_controlled_expansion_plan_v1.md`, and materialized
      `artifacts/attachment_controlled_expansion_plan_v1/`.
    - Selected route:
      `v20_endpoint_balanced_preview_400_repackage_with_numeric_geometry_join`.
    - Target contract: `400` train-only rows, `320` primary binary rows, `80` connected diagnostic
      rows; `attached to` and `hanging on` each get `80` positive and `80` counterfactual negative
      rows; `connected to` gets `40/40` diagnostic rows.
    - Rejected v21 strict same-predicate/rank/geometry/family route because it remains blocked by
      predicate imbalance.
    - Boundary: no validation/test usage, no paper model training, no H001 artifact modification.

14. `attachment_controlled_candidate_materialization_v1`
    - completed on 2026-06-25.
    - added `tools/attachment_controlled_candidate_materialization_v1.py`, wrote
      `attachment_controlled_candidate_materialization_v1.md`, and materialized
      `artifacts/attachment_controlled_candidates_v1/`.
    - Repackaged the v20 `400`-row preview into the current H002 `T_e/Z_e/G_e/Q_e` schema.
    - Joined selected source prediction rows and same-directed-pair raw geometry:
      selected prediction matches `400/400`, pair geometry matches `400/400`, numeric `G_e`
      rows `400/400`.
    - Counts: primary binary rows `320`, connected diagnostic rows `80`, groups `131`,
      validation errors `0`.
    - Boundary: no validation/test usage, no paper model training, no H001 artifact modification;
      hidden construction fields are retained only for shortcut probes.

15. `attachment_controlled_candidate_smoke_v1`
    - completed on 2026-06-25.
    - added `tools/attachment_controlled_candidate_smoke_v1.py`, wrote
      `attachment_controlled_candidate_smoke_v1.md`, and generated
      `artifacts/attachment_controlled_candidate_smoke_v1/`.
    - Task A uses `320` primary rows from `attached to` and `hanging on`, with
      positive/negative balance `160/160`; `connected to` remains `80` diagnostic rows.
    - Main result: source-only `Z` AUROC `0.4585`, semantic+source `T+Z` AUROC `0.4798`,
      geometry-only `G` AUROC `1.0000`, compatibility `T+G` AUROC `1.0000`, and
      factorized `T+Z+G+Q` AUROC `1.0000`.
    - Shortcut controls: predicate/family AUROC `0.4876`, source-rank AUROC `0.4908`,
      endpoint-label-pair AUROC `0.5074`, but hidden cell/construction probes AUROC `1.0000`.
    - Interpretation: numeric `G_e` carries strong compatibility signal and visible shortcut probes
      are weak, but the target is still perfectly recoverable from hidden construction proxies.
      Therefore this is diagnostic geometry-proxy evidence, not paper-level independent reliability
      evidence.
    - Boundary: no validation/test usage, no paper model training, no H001 artifact modification.

16. `attachment_controlled_candidate_path_decision_v1`
    - completed on 2026-06-25.
    - wrote `attachment_controlled_candidate_path_decision_v1.md`.
    - Decision: do not promote the 400-row attachment proxy labels into the combined H002
      reliability prototype.
    - Selected status: use the 400-row set as `compatibility_proxy_pretraining_only`, keep the
      attachment `T_e/Z_e/G_e/Q_e` feature schema, and do not use the proxy labels as paper-level
      reliability GT.
    - Reason: `G_e` and `T+G` recover the proxy target while visible shortcuts stay weak, but hidden
      construction probes also reach AUROC `1.0000`, so the current label is construction-defined.
    - Selected next: `attachment_independent_audit_subset_plan_v1`, where visual/mesh/geometry
      evidence is used to create independent accept/reject/abstain labels before any attachment
      reliability claim.
    - Boundary: no validation/test usage, no paper model training, no H001 artifact modification;
      multi-view/mesh remains audit confirmation first, not deployable model input.

17. `attachment_independent_audit_subset_plan_v1`
    - completed on 2026-06-25.
    - added `tools/attachment_independent_audit_subset_plan_v1.py`, wrote
      `attachment_independent_audit_subset_plan_v1.md`, and generated
      `artifacts/attachment_independent_audit_subset_plan_v1/`.
    - Selected route: reuse existing v20 packet assets with a blank H002 independent review
      template.
    - Counts: current candidate rows `400`, v20 packet matched rows `298`, selected rows `200`,
      primary rows `160`, connected diagnostic rows `40`, attached/hanging/connected `80/80/40`,
      T1/T2 evidence `72/128`, validation errors `0`.
    - Boundary: prior v20 labels are hidden provenance only, current proxy labels are not promoted,
      and multi-view/mesh evidence remains audit evidence rather than model input.
    - Selected next: `attachment_independent_audit_label_fill_v1`.

18. `attachment_independent_audit_label_fill_v1`
    - completed on 2026-06-25.
    - added `tools/attachment_independent_audit_label_fill_v1.py`, wrote
      `attachment_independent_audit_label_fill_v1.md`, and generated
      `artifacts/attachment_independent_audit_label_fill_v1/`.
    - Label source: `codex_visible_packet_label_v1`; hidden manifest, prior v20 labels, source
      score/rank, and proxy construction labels were not used for label decisions.
    - Counts: rows `200`, accept/reject/abstain `17/91/92`, primary binary preview `17/91`,
      attached-to `2/53/25`, hanging-on `15/38/27`, connected-to `40` abstain diagnostic,
      validation errors `0`.
    - Interpretation: the independent attachment label fill is positive-sparse; this is preserved
      as a hard-relation target property rather than tuned away.
    - Selected next: `attachment_independent_audit_label_ingestion_v1`.

19. `attachment_independent_audit_label_ingestion_v1`
    - completed on 2026-06-25.
    - added `tools/attachment_independent_audit_label_ingestion_v1.py`, wrote
      `attachment_independent_audit_label_ingestion_v1.md`, and generated
      `artifacts/attachment_independent_audit_label_ingestion_v1/`.
    - Purpose: join locked visible-packet labels with the hidden audit manifest after label lock
      and materialize `C_e`, `Q_e`, `p_obs`, and `p_rel` diagnostic targets without promoting
      source/proxy fields to model input.
    - Counts: rows `200`, primary binary rows `108`, primary target `17` positive / `91`
      negative, `p_obs` target `108` observable / `92` abstain-or-unobservable, geometry-support
      target `17` supported / `63` unsupported / `120` uncertain, validation errors `0`.
    - Viability: minimum positive for posterior smoke is `30`, but primary positives are `17`;
      `class_mass_pass=false`.
    - Shortcut probe: model shortcut flags `60`, construction-proxy/source hidden flags `19`,
      label-derived auxiliary target flags `21`.
    - Interpretation: factor-view materialization succeeded, but posterior smoke remains blocked
      because the independent hard-relation target is positive-sparse and shortcut-prone.
    - Selected next: `attachment_independent_target_independence_audit_v1`.

20. `attachment_independent_target_independence_audit_v1`
    - completed on 2026-06-25.
    - added `tools/attachment_independent_target_independence_audit_v1.py`, wrote
      `attachment_independent_target_independence_audit_v1.md`, and generated
      `artifacts/attachment_independent_target_independence_audit_v1/`.
    - Purpose: formally audit whether the ingested `C_e`, `Q_e`, `p_obs`, and `p_rel` targets
      are predictable from construction proxy/source hidden fields, shallow visible fields, or
      high-cardinality provenance ids before any posterior smoke.
    - Counts: rows `200`, `p_rel_primary_binary` `91/17`, `c_e_compatibility_binary` `91/17`,
      `p_obs_primary_binary` `108/52`, validation errors `0`.
    - Risk flags: total `97`, construction-proxy/source hidden `26`, visible semantic/packet `29`,
      instance/scan id `21`, label-derived auxiliary `21`.
    - Decision: blocked. The primary `p_rel/C_e` target has only `17` positives and no strict or
      diagnostic clear controlled slice.
    - Selected next: `attachment_independent_target_repair_plan_v1`.

21. `attachment_independent_target_repair_plan_v1`
    - completed on 2026-06-25.
    - added `tools/attachment_independent_target_repair_plan_v1.py`, wrote
      `attachment_independent_target_repair_plan_v1.md`, and generated
      `artifacts/attachment_independent_target_repair_plan_v1/`.
    - Capacity check: current 200 rows yield `17/91` positive/negative; all v20-matched 298 rows
      would yield `24/116`; full 400 candidates under the visible-rule estimate would yield
      `45/174`.
    - Controlled contrast check: full 400 has only `1` mixed visible-pair group and `0`
      mixed predicate-visible-pair groups.
    - Decision: reject current rows as-is, reject using all v20-matched rows, keep full-400
      materialization as diagnostic-only, reject label relaxation, and select new positive-anchor
      mining with packet materialization.
    - Selected next: `attachment_independent_positive_anchor_mining_plan_v1`.

22. `attachment_independent_positive_anchor_mining_plan_v1`
    - completed on 2026-06-25.
    - added `tools/attachment_independent_positive_anchor_mining_plan_v1.py`, wrote
      `attachment_independent_positive_anchor_mining_plan_v1.md`, and generated
      `artifacts/attachment_independent_positive_anchor_mining_plan_v1/`.
    - Purpose: lock the next train-only mining contract after the independent attachment target
      repair plan, before any posterior smoke or paper-level claim.
    - Selected route:
      `train_only_positive_anchor_candidate_mining_then_packet_materialization`.
    - Contract: request `560` rows before audit, with `480` primary rows and `80` connected-to
      diagnostic rows; require at least `160` primary binary rows after audit, including at least
      `60` accept-positive and `60` reject-negative rows.
    - Query plan: `hanging on` positive anchors `120`, `hanging on` hard negatives `120`,
      `attached to` structural positive anchors `120`, `attached to` hard negatives `120`, and
      `connected to` diagnostic rows `80`.
    - Decision: `hanging on` remains the strongest primary anchor route; `attached to` is primary
      only if enough accepted positives survive independent audit; `connected to` remains
      diagnostic until functional connection evidence is available.
    - Validation errors: `0`.
    - Selected next: `attachment_independent_positive_anchor_candidate_mining_v1`.

23. `attachment_independent_positive_anchor_candidate_mining_v1`
    - completed on 2026-06-25.
    - added `tools/attachment_independent_positive_anchor_candidate_mining_v1.py`, wrote
      `attachment_independent_positive_anchor_candidate_mining_v1.md`, and generated
      `artifacts/attachment_independent_positive_anchor_candidate_mining_v1/`.
    - Purpose: mine actual train-only attachment candidates while avoiding the bad route of simply
      collecting high-score/high-rank/source-positive rows.
    - Result: selected `560` rows, with `467` primary binary seed rows, `13` primary uncertain
      buffer rows, `80` connected-to diagnostic rows, and validation errors `0`.
    - Query counts: `hanging on` positive anchors `116`, `hanging on` hard negatives `120`,
      `attached to` structural positive anchors `118`, `attached to` hard negatives `113`,
      connected-near diagnostics `40`, connected-far diagnostics `40`, uncertain buffer `13`.
    - Contrast structure: endpoint-family/rank/coverage has `55` mixed groups and `214` balanced
      rows; visible-pair has `58` mixed groups and `312` balanced rows; same-scene has `40` mixed
      groups and `86` balanced rows.
    - Decision: candidate mining passed as a mixed-strata packet-audit batch. It is not posterior
      smoke and not paper evidence.
    - Selected next: `attachment_independent_positive_anchor_packet_materialization_v1`.

24. `attachment_independent_positive_anchor_packet_materialization_v1`
    - completed on 2026-06-25.
    - added `tools/attachment_independent_positive_anchor_packet_materialization_v1.py`, wrote
      `attachment_independent_positive_anchor_packet_materialization_v1.md`, and generated
      `artifacts/attachment_independent_positive_anchor_packet_materialization_v1/`.
    - Purpose: materialize reviewer-facing multi-view and mesh evidence packets for the `560`
      selected train-only mixed-strata attachment candidates.
    - Result: packet rows `560`, ready packets `560`, label-ready rows `560`, non-ready rows `0`,
      visible leakage hits `0`, validation errors `0`.
    - Coverage: subject image rows `560/560`, object image rows `560/560`, contact sheets
      `560/560`, mesh packets `560/560`, total subject images `2174`, total object images `2204`.
    - Boundary: no label fill, no posterior training, no validation/test usage, no paper evidence
      promotion, and no H001 artifact modification. Multi-view/mesh remains audit evidence only.
    - Selected next: `attachment_independent_positive_anchor_label_fill_v1`.

25. `attachment_independent_positive_anchor_label_fill_v1`
    - completed on 2026-06-25.
    - added `tools/attachment_independent_positive_anchor_label_fill_v1.py`, wrote
      `attachment_independent_positive_anchor_label_fill_v1.md`, and generated
      `artifacts/attachment_independent_positive_anchor_label_fill_v1/`.
    - Purpose: fill independent accept/reject/abstain fields for the `560` positive-anchor visual
      packet rows before hidden/control provenance is joined.
    - Label source: Codex visible-packet proxy labeler, using reviewer-visible relation fields and
      packet availability only; hidden manifest, source score/rank, proxy role/cell id,
      `p_geom_valid`, validation/test data, and H001 artifacts were not used.
    - Result: rows `560`, accept/reject/abstain `60/246/254`, primary binary preview rows `306`,
      primary positive/negative `60/246`, connected diagnostic rows `80`, validation errors `0`.
    - Predicate distribution: `attached to` `30/95/113`, `hanging on` `30/151/61`,
      `connected to` `0/0/80`.
    - Interpretation: positive-anchor repair reached the pre-specified minimum positive gate
      exactly, but posterior smoke remains blocked until ingestion and target-independence audit.
    - Selected next: `attachment_independent_positive_anchor_label_ingestion_v1`.

26. `attachment_independent_positive_anchor_label_ingestion_v1`
    - completed on 2026-06-26.
    - added `tools/attachment_independent_positive_anchor_label_ingestion_v1.py`, wrote
      `attachment_independent_positive_anchor_label_ingestion_v1.md`, and generated
      `artifacts/attachment_independent_positive_anchor_label_ingestion_v1/`.
    - Purpose: join the locked `560` visible-packet labels with hidden/control provenance after
      label lock, then materialize `C_e`, `Q_e`, `p_obs`, and `p_rel` target artifacts.
    - Target counts: rows `560`, primary binary rows `306`, compatibility binary rows `306`,
      `p_rel` rows `306`, `p_obs` rows `560`, `p_obs` primary rows `480`, geometry-support rows
      `306`, evidence-quality rows `560`, connected diagnostic rows `80`, abstain rows `254`.
    - Primary target: positive/negative `60/246`; class mass passed the `60/60` gate.
    - Shortcut diagnostics: quick-probe risk flags `98`, model shortcut risk flags `75`,
      construction-proxy risk flags `42`, label-derived auxiliary flags `23`.
    - Mixed controls exist but are not sufficient by themselves: same-query mixed primary binary
      groups `5`, same-proxy-role `3`, same-cell `5`, same-rank-band `5`, same-predicate `2`,
      same-visible-pair `2`.
    - Boundary: hidden manifest is read only after label lock; hidden/source/proxy fields remain
      diagnostic-only and are not model inputs. No posterior training, no validation/test usage,
      no paper evidence promotion, and no H001 artifact modification.
    - Selected next: `attachment_independent_positive_anchor_target_independence_audit_v1`.

27. `attachment_independent_positive_anchor_target_independence_audit_v1`
    - completed on 2026-06-26.
    - added `tools/attachment_independent_positive_anchor_target_independence_audit_v1.py`, wrote
      `attachment_independent_positive_anchor_target_independence_audit_v1.md`, and generated
      `artifacts/attachment_independent_positive_anchor_target_independence_audit_v1/`.
    - Purpose: formally audit whether the class-mass-passing positive-anchor `C_e`, `Q_e`,
      `p_obs`, and `p_rel` targets are usable after controlling visible semantic, endpoint, rank,
      query/cell, construction, provenance, and label-derived shortcuts.
    - Counts: rows `560`; `p_rel_primary_binary` and `c_e_compatibility_binary` each have `306`
      rows with positive/negative `60/246`; `p_obs_primary_binary` has `480` rows with
      observable/unobservable-or-abstain `306/174`; validation errors `0`.
    - Class mass: primary `p_rel/C_e` class mass passes the `60/60` gate.
    - Target-independence result: strict clear slices `0`, diagnostic clear slices `0`, full risk
      flags `112`.
    - Risk categories: construction-proxy/source hidden `36`, instance/scan id `32`,
      label-derived auxiliary `21`, visible semantic/packet `20`, official GT axis `3`.
    - Decision: blocked. Positive-anchor mining repaired class mass, but did not repair target
      independence. Posterior smoke remains disallowed.
    - Selected next: `attachment_independent_positive_anchor_path_decision_after_audit_v1`.

28. `attachment_independent_positive_anchor_path_decision_after_audit_v1`
    - completed on 2026-06-26.
    - added `tools/attachment_independent_positive_anchor_path_decision_after_audit_v1.py`, wrote
      `attachment_independent_positive_anchor_path_decision_after_audit_v1.md`, and generated
      `artifacts/attachment_independent_positive_anchor_path_decision_after_audit_v1/`.
    - Purpose: decide whether to keep repairing the positive-anchor attachment target, run
      posterior smoke anyway, or freeze the target after the target-independence audit found no
      controlled slice.
    - Input audit: rows `560`; primary `p_rel/C_e` binary rows `306` with positive/negative
      `60/246`; class mass passed; strict/diagnostic clear slices `0/0`; full risk flags `112`;
      validation errors `0`.
    - Controlled-slice capacity: same-visible-pair rows `8`, same-visible-pair min class `4`,
      same-predicate-visible-pair rows `0`, construction-endpoint-strict rows `0`.
    - Decision: freeze the attachment positive-anchor target as diagnostic-only and do not run
      posterior smoke.
    - Rejected routes: posterior smoke now, same-policy positive-anchor mining, label relaxation,
      paper-level reliability GT promotion, and current-slice repair.
    - Kept route: attachment packets remain useful for `Q_e`, observability, hard-family failure
      taxonomy, and future verified positives.
    - Selected next: `compatibility_learning_scope_plan_v1`.

29. `compatibility_learning_scope_plan_v1`
    - completed on 2026-06-26.
    - added `tools/compatibility_learning_scope_plan_v1.py`, wrote
      `compatibility_learning_scope_plan_v1.md`, and generated
      `artifacts/compatibility_learning_scope_plan_v1/`.
    - Purpose: define the method-level H002 compatibility-learning scope after the attachment
      positive-anchor target was frozen as diagnostic-only.
    - Selected scope: primary `support_contact` and `relative_vertical`; diagnostic hard family
      `attachment_like`; future generality `proximity`; deferred `relative_horizontal` and
      `containment`.
    - Current prototype counts: `support_contact` `99` rows with compatibility `50/49`;
      `relative_vertical` `35` rows with compatibility `17/18`; `attachment_deferred` `560` rows
      diagnostic-only.
    - Decision: do not run a posterior smoke from attachment labels; next dataset should focus on
      `C_e = compatibility(T_e, G_e)` with support/contact and relative-vertical controls.
    - Required controls: source-only, `T_e + Z_e`, geometry-only, `T_e + G_e`, full factorized,
      predicate/family shortcut, rank shortcut, endpoint shortcut, hidden construction probe,
      wrong-pair/shuffled geometry, and directional flip/swap where applicable.
    - Selected next: `compatibility_dataset_v2_contract`.

30. `compatibility_dataset_v2_contract`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v2_contract.py`, wrote
      `compatibility_dataset_v2_contract.md`, and generated
      `artifacts/compatibility_dataset_v2_contract/`.
    - Purpose: turn the selected compatibility-learning scope into a concrete v2 dataset contract.
    - Dataset name: `h002_compatibility_dataset_v2`.
    - Primary families: `support_contact` and `relative_vertical`.
    - Diagnostic family: `attachment_like`.
    - Future/deferred families: `proximity` as future generality; `relative_horizontal` and
      `containment` deferred.
    - Requested family quotas: `support_contact` `120/120`, `relative_vertical` `80/80`;
      minimum reportable per primary family `60/60`, overall primary Task A minimum `120/120`.
    - Required controls: schema leakage, train-only split, class mass, group integrity, source-only,
      `T_e + Z_e`, geometry-only, `T_e + G_e`, predicate/family, rank, endpoint, hidden
      construction, wrong-pair/shuffled geometry, and relative-vertical flip/swap.
    - Blocking conditions: `G_e` contains predicate/source/label fields, `C_e` uses `Z_e`,
      hidden construction enters model input, no-GT is used as negative, attachment is used as
      primary `p_rel/C_e`, or relative vertical lacks directional controls.
    - Selected next: `compatibility_dataset_v2_materialization_plan`.

31. `compatibility_dataset_v2_materialization_plan`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v2_materialization_plan.py`, wrote
      `compatibility_dataset_v2_materialization_plan.md`, and generated
      `artifacts/compatibility_dataset_v2_materialization_plan/`.
    - Decision: do not directly materialize `h002_compatibility_dataset_v2` from the current
      prototype or all-label-ready files.
    - Selected route: `v2_capacity_scan_before_materialization`.
    - Current class-mass check: prototype `support_contact` `50/49`, prototype
      `relative_vertical` `17/18`, all-label-ready reliability `support_contact` `50/121`, and
      all-label-ready reliability `relative_vertical` `20/40`; v2 minimum reportable per primary
      family is `60/60`.
    - Reusable seed: raw-witness feature join v2 is kept as the train-only geometry feature
      adapter seed, but it must be repackaged from posterior-ready `baseline_inputs` into
      `T_e/Z_e/G_e/Q_e` rows.
    - Attachment policy: `attachment_like` remains diagnostic-only for `Q_e`, observability, and
      failure taxonomy.
    - Validation errors: `0`.
    - Selected next: `compatibility_dataset_v2_capacity_scan`.

32. `compatibility_dataset_v2_capacity_scan`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v2_capacity_scan.py`, wrote
      `compatibility_dataset_v2_capacity_scan.md`, and generated
      `artifacts/compatibility_dataset_v2_capacity_scan/`.
    - Full-train scan size: HL queue `1,828` rows and LH queue `455,598` rows.
    - Family capacity: `support_contact` `74,364/896` positive/negative and
      `relative_vertical` `111,032/592` positive/negative.
    - Requested class mass passes for both primary families:
      `support_contact` requested `120/120`; `relative_vertical` requested `80/80`.
    - Direct HL/LH target remains blocked. `queue_kind`, `geometry_status`, rank/source axes, and
      predicate direction can shortcut the label.
    - Predicate imbalance: support/contact negative is only `lying on` (`896`) with `standing on`
      and `supported by` both `0`; relative-vertical negative is `higher than` `1` and `lower than`
      `591`.
    - Decision: allow row materialization only with generated counterfactual controls and raw
      numeric `G_e` repackaging into `T_e/Z_e/G_e/Q_e`; do not run learned smoke yet.
    - Validation errors: `0`.
    - Selected next: `compatibility_dataset_v2_candidate_materialization`.

33. `compatibility_dataset_v2_candidate_materialization`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v2_candidate_materialization.py`, wrote
      `compatibility_dataset_v2_candidate_materialization.md`, and generated
      `artifacts/compatibility_dataset_v2_candidate_materialization/`.
    - Materialized `400` train-only candidate rows in `200` anchor/counterfactual groups.
    - Raw-witness join matched `400/400` requested prediction ids after scanning
      `4,812,438` `match_rows.jsonl` rows.
    - Compatibility target mass: `200/200` positive/negative.
    - Family mass: `support_contact` `120/120`, `relative_vertical` `80/80`.
    - Predicate balance: support/contact `lying on`, `standing on`, `supported by` each
      `40/40`; relative vertical `higher than`, `lower than` each `40/40`.
    - Generated counterfactuals: support/contact `wrong_pair_geometry` `40`,
      `shuffled_geometry` `40`, `contact_gap_or_overlap_perturbation` `40`; relative vertical
      `predicate_flip` `40`, `subject_object_swap` `40`.
    - Direct HL/LH labels are not used as the primary target; construction fields remain hidden
      controls and `C_e` remains restricted to `T_e + G_e`.
    - Validation errors: `0`.
    - Learned smoke remains blocked until schema/hidden-shortcut audit passes.
    - Selected next: `compatibility_dataset_v2_schema_shortcut_audit`.

34. `compatibility_dataset_v2_schema_shortcut_audit`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v2_schema_shortcut_audit.py`, wrote
      `compatibility_dataset_v2_schema_shortcut_audit.md`, and generated
      `artifacts/compatibility_dataset_v2_schema_shortcut_audit/`.
    - Purpose: audit whether the 400-row v2 candidate dataset can be used for learned
      compatibility smoke without leaking generated-counterfactual construction metadata.
    - Counts: rows `400`, groups `200`, compatibility positive/negative `200/200`,
      support/contact `120/120`, relative vertical `80/80`; schema errors `0`.
    - Controlled visible axes: predicate-only, family-only, source-rank-band, and source-score-bin
      probes all have accuracy `0.500`.
    - Blocking raw metadata shortcuts: `row_role`, `counterfactual_type`, `G_e.geometry_source`,
      `Q_e.generated_counterfactual`, `Q_e.evidence_conflict_flag`, `geometry_status_baseline`,
      and `relation_source` each have shortcut accuracy `1.000`.
    - Decision: raw `full_factorized`, raw `obs_head`, `baseline_view`, and `audit_view` are not
      safe model inputs. The audit wrote `sanitized_model_view.jsonl` with `T_e`, `Z_e`, numeric
      `G_e`, and sanitized `Q_e` for the next smoke plan.
    - Validation errors: `0`.
    - Learned smoke remains blocked until the sanitized-view smoke protocol is fixed.
    - Selected next: `compatibility_dataset_v2_sanitized_view_smoke_plan`.

35. `compatibility_dataset_v2_sanitized_view_smoke_plan`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v2_sanitized_view_smoke_plan.py`, wrote
      `compatibility_dataset_v2_sanitized_view_smoke_plan.md`, and generated
      `artifacts/compatibility_dataset_v2_sanitized_view_smoke_plan/`.
    - Purpose: fix the learned-smoke input contract after the schema audit blocked raw
      construction metadata.
    - Additional shortcut found: `Z_e.source_score_inherited_for_counterfactual` in the
      intermediate sanitized view has accuracy `1.000`, because generated counterfactual rows
      inherit source scores.
    - Decision: write stricter `smoke_ready_view.jsonl` and use that as the only allowed input for
      the next runner.
    - Counts: rows `400`, compatibility positive/negative `200/200`, paired groups `200`,
      validation errors `0`.
    - Planned comparisons: source-only `Z_e_safe`, semantic-only `T_e`, semantic+source,
      geometry-only `G_e`, primary compatibility `T_e + G_e`, sanitized factorized
      `T_e + Z_e_safe + G_e + Q_e_safe`, shortcut probes, shuffled-geometry control, and
      wrong-predicate control.
    - Boundary: no learned smoke was run, no paper evidence was produced, no validation/test data
      used, and no H001 artifacts were modified.
    - Selected next: `compatibility_dataset_v2_sanitized_view_smoke_runner`.

36. `compatibility_dataset_v2_sanitized_view_smoke_runner`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v2_sanitized_view_smoke_runner.py`, wrote
      `compatibility_dataset_v2_sanitized_view_smoke_runner.md`, and generated
      `artifacts/compatibility_dataset_v2_sanitized_view_smoke_runner/`.
    - Purpose: run train-only grouped-CV learned smoke on the strict `smoke_ready_view.jsonl`
      with source-only, semantic-only, geometry-only, compatibility, sanitized factorized,
      shortcut, shuffled-geometry, and wrong-predicate controls.
    - Counts: rows `400`, compatibility positive/negative `200/200`, paired groups `200`,
      validation errors `0`.
    - Key AUROC: source-only `0.5000`, semantic-only `0.4846`, semantic+source `0.4797`,
      object-pair shortcut `0.4885`, geometry-only `0.6731`, compatibility `T_e + G_e`
      `0.6250`, sanitized factorized `0.6230`, shuffled-G control `0.6085`, wrong-T same-G
      control `0.6250`.
    - Gates: dataset sanity passed and source/semantic shortcut controls passed, but
      predicate-conditioning-over-geometry-only failed and corruption controls failed.
    - Interpretation: current v2 target is not source/semantic shortcut dominated, but it is
      geometry-only-dominant. It does not yet prove predicate-conditioned compatibility because
      wrong predicate does not degrade the score and geometry-only is stronger than `T_e + G_e`.
    - Boundary: train-only hypothesis smoke, no paper evidence, no validation/test usage, and no
      H001 artifact modification.
    - Selected next: `compatibility_dataset_v2_failure_analysis`.

37. `compatibility_dataset_v2_failure_analysis`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v2_failure_analysis.py`, wrote
      `compatibility_dataset_v2_failure_analysis.md`, and generated
      `artifacts/compatibility_dataset_v2_failure_analysis/`.
    - Purpose: diagnose why the sanitized v2 smoke failed predicate-conditioning and corruption
      controls.
    - Main cause:
      `target_is_geometry_perturbation_detection_not_predicate_conditioned_compatibility`.
    - Evidence: geometry-only `M4` AUROC `0.6731`, compatibility `M5` AUROC `0.6250`,
      wrong-T same-G AUROC `0.6250`, and mean `|M5 - wrongT| = 0.0`.
    - Geometry shifts are dominated by support/contact distance and overlap fields:
      `normalized_distance_xy`, `vertical_gap_subject_on_object`, `distance_xy`,
      `projected_overlap_max`, and `projected_iou_xy`.
    - Counterfactual-type diagnosis: support/contact `shuffled_geometry` has `0.800` false
      positive rate, `wrong_pair_geometry` `0.425`, and `contact_gap_or_overlap_perturbation`
      `0.025`; relative-vertical `predicate_flip` `0.650` and `subject_object_swap` `0.375`.
    - Interpretation: source/semantic leakage is fixed, but the target is still solvable by generic
      geometry distribution shifts. The next target must create same-geometry or near-identical
      geometry multi-predicate contrasts.
    - Validation errors: `0`.
    - Selected next: `compatibility_dataset_v2_target_redesign_plan`.

38. `compatibility_dataset_v2_target_redesign_plan`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v2_target_redesign_plan.py`, wrote
      `compatibility_dataset_v2_target_redesign_plan.md`, and generated
      `artifacts/compatibility_dataset_v2_target_redesign_plan/`.
    - Purpose: decide how to redesign the compatibility target after v2 failed because the target
      was geometry-perturbation detection rather than predicate-conditioned compatibility.
    - Decision: do not repair v2 by adding more generated negatives and do not move to a stronger
      combiner before fixing target identifiability.
    - Selected route: `h002_compatibility_dataset_v3_predicate_conditioned` with
      same-geometry multi-predicate contrasts.
    - Primary initial family: `relative_vertical` with `higher than` / `lower than` same-geometry
      contrast, because the same `G_e` can be assigned one positive and one negative predicate
      label under a fixed signed-vertical margin.
    - Support/contact is kept secondary until role/orientation or visual/mesh evidence probing
      passes, because current support/contact signal is dominated by distance/overlap geometry.
    - Required v3 gates: same-geometry group integrity, geometry-only near chance,
      `T_e + G_e` gain over `G_e`, wrong-predicate degradation, and source/semantic shortcut
      control.
    - Validation errors: `0`.
    - Selected next: `compatibility_dataset_v3_contract`.

39. `compatibility_dataset_v3_contract`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v3_contract.py`, wrote
      `compatibility_dataset_v3_contract.md`, and generated
      `artifacts/compatibility_dataset_v3_contract/`.
    - Purpose: freeze the v3 predicate-conditioned target contract before any new row
      materialization or learned smoke.
    - Dataset: `h002_compatibility_dataset_v3_predicate_conditioned`.
    - Selected route: same-geometry multi-predicate contrast.
    - Primary family: `relative_vertical` with `higher than` / `lower than`.
    - Primary row rule: same directed object pair and identical numeric `G_e` are paired with two
      predicate alternatives; exactly one predicate is compatible under a frozen signed-vertical
      margin.
    - Frozen initial margin contract: `abs(center_delta_z) >= 0.10m` and
      `abs(normalized_center_delta_z) >= 0.20`.
    - Required gates: same-geometry group integrity, balanced same-group labels, blocked-field
      absence, geometry-only near-chance, `T_e + G_e` gain, wrong-predicate degradation,
      shuffled-geometry degradation, and source shortcut control.
    - Support/contact remains secondary until role/orientation or visual/mesh evidence probing
      passes.
    - Validation errors: `0`.
    - Selected next: `compatibility_dataset_v3_capacity_scan`.

40. `compatibility_dataset_v3_capacity_scan`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v3_capacity_scan.py`, wrote
      `compatibility_dataset_v3_capacity_scan.md`, and generated
      `artifacts/compatibility_dataset_v3_capacity_scan/`.
    - Purpose: verify whether the full train-side Open3DSG candidate artifact contains enough
      same-geometry `relative_vertical` groups before materializing v3 rows.
    - Input: `match_rows.jsonl` under the full train-side RGA artifact.
    - Rows scanned: `4,818,996`.
    - Relative-vertical rows: `370,692`, all with raw geometry.
    - Directed-pair groups with any vertical predicate: `185,346`.
    - Clear same-geometry groups under the frozen `0.10m / 0.20 normalized` margin: `122,570`.
    - Direction balance: `higher_positive = 61,285`, `lower_positive = 61,285`.
    - Candidate materialization is allowed, with axis controls.
    - High-risk axis: `visible_pair`; medium-risk axes: `object_label`, `subject_label`.
    - Materialization policy: sample equal higher/lower-positive groups, prioritize
      mixed-direction visible-pair cells, cap single-direction visible-pair cells, avoid
      floor/wall/ceiling-only dominance, and audit predicate-only / visible-pair-only /
      predicate+visible-pair shortcuts before learned smoke.
    - Support/contact remains secondary because current artifacts expose raw OBB/numeric features
      but not role/orientation, contact direction, surface normal, or visual/mesh evidence.
    - Validation errors: `0`.
    - Selected next: `compatibility_dataset_v3_candidate_materialization`.

41. `compatibility_dataset_v3_candidate_materialization`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v3_candidate_materialization.py`, wrote
      `compatibility_dataset_v3_candidate_materialization.md`, and generated
      `artifacts/compatibility_dataset_v3_candidate_materialization/`.
    - Purpose: materialize the first v3 predicate-conditioned compatibility candidate dataset
      after the capacity scan passed.
    - Selection policy: choose 100 mixed visible-pair cells, and from each cell select one
      `higher_positive` group and one `lower_positive` group.
    - Output: 200 geometry groups and 400 candidate rows.
    - Direction balance: `higher_positive = 100`, `lower_positive = 100`.
    - Predicate counts: `higher than = 200`, `lower than = 200`.
    - Compatibility labels: positive `200`, negative `200`.
    - Group integrity: each geometry group has two rows, one `higher than` and one `lower than`,
      identical `G_e` hash, and exactly one positive label.
    - Axis shortcut audit preview: predicate-only, visible-pair-only, predicate+visible-pair,
      endpoint-state, subject-label, and object-label majority accuracies are all `0.500`;
      source-rank-band majority accuracy is `0.5375`.
    - No high-risk or medium-risk row-level axis remained after selection.
    - Boundary: train-only materialization, no learned smoke, no validation/test usage, no paper
      evidence, and no H001 modification.
    - Validation errors: `0`.
    - Selected next: `compatibility_dataset_v3_schema_shortcut_audit`.

42. `compatibility_dataset_v3_schema_shortcut_audit`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v3_schema_shortcut_audit.py`, wrote
      `compatibility_dataset_v3_schema_shortcut_audit.md`, and generated
      `artifacts/compatibility_dataset_v3_schema_shortcut_audit/`.
    - Purpose: formally audit the v3 candidate rows and model-view artifact for label leakage,
      construction-route leakage, group-id leakage, source-predicate provenance leakage, and
      residual shortcut probes before learned smoke.
    - Decision: `candidate_rows.jsonl` is a full audit/provenance artifact, not model input.
      The audit emits `smoke_ready_view.jsonl` as the only allowed input source for the next
      learned-smoke plan.
    - Important fix: intermediate `sanitized_model_view.jsonl` still contained
      `G_e_numeric.geometry_feature_hash`; the smoke-ready view removes it from model features.
    - Allowed feature probe risk: `0` high/medium probes.
    - Allowed probe examples: predicate label `0.500`, subject/object label `0.500`,
      subject-object text `0.500`, source rank band `0.5375`, source score threshold `0.5175`,
      source rank threshold `0.5375`, and all single numeric `G_e` threshold probes `0.500`.
    - Blocked raw high-risk probes: `raw_row_id = 1.000` and
      `hidden_source_prediction_id = 1.000`; both are expected identifier shortcuts and remain
      blocked from model features.
    - Group integrity: 200 groups, 2 rows per group, one `higher than` and one `lower than`, one
      positive and one negative label, one shared geometry hash.
    - Boundary: train-only schema/shortcut audit, no learned smoke, no validation/test usage, no
      paper evidence, and no H001 modification.
    - Validation errors: `0`.
    - Selected next: `compatibility_dataset_v3_sanitized_view_smoke_plan`.

43. `compatibility_dataset_v3_sanitized_view_smoke_plan`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v3_sanitized_view_smoke_plan.py`, wrote
      `compatibility_dataset_v3_sanitized_view_smoke_plan.md`, and generated
      `artifacts/compatibility_dataset_v3_sanitized_view_smoke_plan/`.
    - Purpose: freeze the learned-smoke input contract, model views, controls, metrics, and
      promotion gates before running any learned model on v3 rows.
    - Input decision: the next runner must use
      `artifacts/compatibility_dataset_v3_schema_shortcut_audit/smoke_ready_view.jsonl` as the
      only model-input source. Raw `candidate_rows.jsonl` and intermediate
      `sanitized_model_view.jsonl` remain audit/provenance artifacts.
    - Counts: rows `400`, compatibility positive/negative `200/200`, paired groups `200`, schema
      version `h002_compatibility_dataset_v3_smoke_ready_view_v1`, validation errors `0`.
    - Primary view: `M5b_compatibility_TG_interaction`, using predicate-conditioned vertical
      features such as `expected_z_sign(predicate) * center_delta_z_m` and
      `expected_z_sign(predicate) * normalized_center_delta_z`.
    - Planned comparisons: source-only `Z_e_safe`, semantic-only `T_e`, semantic+source,
      geometry-only `G_e`, plain `T_e + G_e` concat, predicate-conditioned compatibility,
      sanitized factorized `T_e + Z_e_safe + G_e + Q_e_safe`, shortcut probes,
      wrong-T same-G, and shuffled-G controls.
    - Promotion gates: shortcut/source/semantic/geometry-only probes should stay near chance,
      primary `M5b` should reach at least `0.90` AUROC and beat the best non-compatibility
      baseline by at least `0.30` AUROC, wrong-T/shuffled-G controls must degrade, and paired
      compatible-minus-incompatible scores should be positive.
    - Boundary: train-only plan, no learned smoke executed, no validation/test usage, no paper
      evidence, and no H001 artifact modification.
    - Selected next: `compatibility_dataset_v3_sanitized_view_smoke_runner`.

44. `compatibility_dataset_v3_sanitized_view_smoke_runner`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v3_sanitized_view_smoke_runner.py`, wrote
      `compatibility_dataset_v3_sanitized_view_smoke_runner.md`, and generated
      `artifacts/compatibility_dataset_v3_sanitized_view_smoke_runner/`.
    - Purpose: run train-only grouped-CV learned smoke over the frozen v3
      `smoke_ready_view.jsonl` contract.
    - Counts: rows `400`, compatibility positive/negative `200/200`, paired groups `200`,
      validation errors `0`, epochs `120`.
    - Main result: `M5b_compatibility_TG_interaction` AUROC `1.000000`.
    - Key controls: source-only `0.525975`, semantic-only `0.445225`, semantic+source
      `0.515800`, geometry-only `0.500000`, plain concat `0.446300`, predicate label shortcut
      `0.446000`, object-pair shortcut `0.500000`, source scalar shortcut `0.445725`.
    - Corruption controls: wrong-T same-G `0.000000`, shuffled-G global `0.477713`, shuffled-G
      within-predicate `0.515400`.
    - Paired score: mean compatible-minus-incompatible score `0.812703`, positive direction
      fraction `1.0`.
    - Gates: data integrity, shortcut near-chance, primary compatibility success, interaction over
      plain concat, wrong-T degradation, shuffled-G degradation, and paired score drop all passed.
    - Interpretation: v3 fixes the v2 failure mode for `relative_vertical`; `G_e` alone is chance
      and the useful signal comes from explicit predicate-conditioned compatibility interaction.
    - Boundary: this is a train-only `relative_vertical` C_e mechanism proof, not broad relation
      reliability or paper-level evidence.
    - Selected next: `compatibility_dataset_v3_result_review_and_family_extension_decision`.

45. `compatibility_dataset_v3_result_review_and_family_extension_decision`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v3_result_review_and_family_extension_decision.py`, wrote
      `compatibility_dataset_v3_result_review_and_family_extension_decision.md`, and generated
      `artifacts/compatibility_dataset_v3_result_review_and_family_extension_decision/`.
    - Purpose: decide how to interpret the passed v3 smoke and which relation family should be
      probed next.
    - Decision: accept the v3 result as a scoped `relative_vertical` `C_e` mechanism proof.
    - Allowed claim: scoped predicate-geometry compatibility mechanism for `relative_vertical`.
    - Blocked claims: broad relation reliability, final `p_rel` / `p_obs` quality, all-family
      generality, and paper-level Docker-reproduced evidence.
    - Family decision: retain `relative_vertical` as core mechanism proof; select
      `support_contact` as the best next extension candidate, but only through an evidence probe
      before any learned smoke; keep `attachment_like` diagnostic, `proximity` future-generality,
      and `relative_horizontal` deferred.
    - Rationale: directly running support/contact from v2 generated counterfactual rows would
      likely repeat the geometry-perturbation failure. The next step must first check role,
      orientation, contact direction, surface normal, mesh, or visual evidence availability.
    - Boundary: train-only decision artifact, no learned model trained in this step, no
      validation/test usage, no paper evidence, and no H001 modification.
    - Validation errors: `0`.
    - Selected next: `compatibility_dataset_v3_support_contact_evidence_probe_plan`.

46. `compatibility_dataset_v3_support_contact_evidence_probe_plan`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v3_support_contact_evidence_probe_plan.py`, wrote
      `compatibility_dataset_v3_support_contact_evidence_probe_plan.md`, and generated
      `artifacts/compatibility_dataset_v3_support_contact_evidence_probe_plan/`.
    - Purpose: freeze the support/contact evidence inventory probe before any support/contact
      materialization or learned smoke.
    - Prior evidence: support/contact has full-train capacity (`74,364/896` eligible
      positive/negative rows), but direct HL/LH predicate balance fails and v2 required
      wrong-pair, shuffled-geometry, and contact gap/overlap generated counterfactuals.
    - v2 warning: support/contact v2 failed because the target was
      geometry-perturbation detection, not predicate-conditioned compatibility.
    - Current evidence availability: distance, 3D/XY separation, projected overlap/IoU, vertical
      gap, and object top/bottom z are available; role/orientation/pose, explicit contact
      direction, surface normal, mesh, visual, and multi-view evidence are absent in the current
      numeric view.
    - Blocked actions: do not run support/contact learned smoke now; do not use contact
      gap/overlap perturbation as primary negative; do not claim support/contact generality from
      v2; do not promote the relative-vertical result to broad reliability.
    - Next runner contract: produce source inventory, evidence-axis inventory, same/near-geometry
      capacity, negative-policy audit, shortcut precheck, and path decision.
    - Boundary: train-only plan, no learned smoke, no validation/test usage, no paper evidence,
      and no H001 modification.
    - Validation errors: `0`.
    - Selected next: `compatibility_dataset_v3_support_contact_evidence_probe_runner`.

47. `compatibility_dataset_v3_support_contact_evidence_probe_runner`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v3_support_contact_evidence_probe_runner.py`, wrote
      `compatibility_dataset_v3_support_contact_evidence_probe_runner.md`, and generated
      `artifacts/compatibility_dataset_v3_support_contact_evidence_probe_runner/`.
    - Purpose: test whether current train-side numeric support/contact artifacts are sufficient
      for a clean predicate-conditioned `C_e` materialization before learned smoke.
    - Source inventory: `161,498` support/contact queue rows, `75,763` distinct directed pairs,
      `4,109` distinct visible pairs, and `1,157` scans.
    - Capacity diagnosis: exact directed-pair multi-predicate mixed-geometry groups exist
      (`75`), but only `4` non-hard-surface exact candidate groups remain after avoiding
      hard-surface dominance.
    - Evidence-axis diagnosis: distance, overlap, vertical gap, and OBB top/bottom z are available
      or partial; role/orientation/pose, contact direction, surface normal, mesh, visual, and
      multi-view evidence are missing from the current numeric view.
    - Shortcut diagnosis: hidden construction/provenance probes remain high risk
      (`hidden_counterfactual_type`, `hidden_row_role`, and `hidden_geometry_status_baseline`
      each `1.000`), so v2 support/contact rows must stay diagnostic-only.
    - Decision: numeric-only support/contact materialization is blocked. The branch should route
      to a visual/mesh or role/orientation evidence plan instead of another numeric learned smoke.
    - Boundary: train-only evidence probe, no learned smoke, no validation/test usage, no paper
      evidence, and no H001 modification.
    - Validation errors: `0`.
    - Selected next: `compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan`.

48. `compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan.py`, wrote
      `compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan.md`, and generated
      `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_evidence_plan/`.
    - Purpose: define the evidence extension route after numeric-only support/contact smoke was
      blocked by missing role/orientation/contact-direction/surface-normal/mesh/visual axes.
    - Source snapshot: 3RScan has `1,335` scan dirs with `mesh.refined.v2.obj`, aligned instance
      PLY, and `sequence.zip`; existing visual audit contact sheets are `192`, including `64`
      support/contact sheets; attachment packet materialization provides `560` packet dirs as a
      renderer/template reference.
    - Selected route: `mesh_pose_contact_first_multiview_audit_first`.
    - Evidence plan: derive mesh instance point, mesh contact surface, and role/orientation/pose
      features as primary `G_e` candidates; keep multi-view co-visibility/crop quality as
      audit/`Q_e` first; retain numeric OBB features as baselines and shortcut controls.
    - Boundary decision: do not use multi-view as immediate model input, do not reuse attachment
      labels as support/contact labels, and do not run support/contact learned smoke before source
      inventory and join feasibility pass.
    - Boundary: train-only plan, no candidate materialization, no learned smoke, no
      validation/test usage, no paper evidence, and no H001 modification.
    - Validation errors: `0`.
    - Selected next: `compatibility_dataset_v3_support_contact_visual_mesh_source_inventory`.

49. `compatibility_dataset_v3_support_contact_visual_mesh_source_inventory`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v3_support_contact_visual_mesh_source_inventory.py`,
      wrote `compatibility_dataset_v3_support_contact_visual_mesh_source_inventory.md`, and
      generated `artifacts/compatibility_dataset_v3_support_contact_visual_mesh_source_inventory/`.
    - Purpose: inventory whether support/contact train candidates can be joined to 3RScan mesh,
      semseg OBB/normal metadata, aligned PLY object IDs, sequence frames, and packet-rendering
      assets before any materialization or learned smoke.
    - Join coverage: `161,498` support/contact rows across `1,157` scans and `75,763` directed
      pairs; scan asset complete rate `1.0`; semseg subject/object presence `1.0`; mesh contact
      source availability `1.0`; sequence availability `1.0`.
    - Predicate distribution: `lying on = 60,652`, `standing on = 50,245`, and
      `supported by = 50,601`.
    - Risk diagnosis: materialization/smoke remains blocked by hard-surface dominance
      (`0.7023`), HL/LH imbalance (`1,069/160,429`), and same exact-pair clean capacity (`4`).
    - Decision: source inventory is ready for a mesh/pose/contact feature probe, but candidate
      materialization, learned smoke, numeric-only smoke, and immediate multi-view model input are
      still disallowed.
    - Boundary: train-only source inventory, no full `match_rows.jsonl` scan, no candidate
      materialization, no learned smoke, no validation/test usage, no paper evidence, and no H001
      modification.
    - Validation errors: `0`.
    - Selected next: `compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan`.

50. `compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan.py`,
      wrote `compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan.md`,
      and generated `artifacts/compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan/`.
    - Purpose: turn the source-join success into a concrete train-only feature-probe contract for
      support/contact `G_e` candidates before materialization or learned smoke.
    - Selected route: `semseg_obb_normal_full_probe_ply_contact_sample_probe`.
    - Tier A: derive semseg OBB and dominant-normal features for all `161,498` support/contact
      rows, including pose/orientation, signed surface gap, support area proxy, and normal
      alignment candidates.
    - Tier B: derive aligned PLY / mesh-contact features on a `1,200` row stratified probe sample,
      with non-hard-surface oversampling and scan/visible-pair caps.
    - Tier C: keep sequence/multi-view as audit / `Q_e` only, not immediate `C_e` model input.
    - Required diagnostics: feature derivability, finite numeric rate, predicate-wise variation,
      hard-surface sensitivity, HL/LH queue sensitivity, blocked-field absence, and old numeric
      gap/overlap proxy dominance.
    - Boundary: train-only plan, no candidate materialization, no learned smoke, no
      validation/test usage, no paper evidence, and no H001 modification.
    - Validation errors: `0`.
    - Selected next: `compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner`.

51. `compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner.py`,
      wrote `compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner.md`,
      and generated
      `artifacts/compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner/`.
    - Purpose: execute the train-only support/contact feature probe before any row materialization
      or learned smoke.
    - Counts: `161,498` support/contact rows, Tier A semseg OBB/normal features for all
      `161,498` rows, and Tier B aligned PLY contact-proxy features for a stratified `1,200` row
      sample across `654` scans.
    - Gate result: Tier A derivability passed, Tier A finite-value sanity passed, Tier B sample
      size passed, model-safe blocked fields were absent, and no high old-numeric proxy dominance
      was flagged.
    - Remaining risks: hard-surface dominance remains high (`0.7023`) and HL/LH queue imbalance
      remains extreme (`1,069/160,429`), so queue kind and construction/provenance fields remain
      audit-only.
    - Decision: feature result review is allowed, but candidate materialization, learned smoke,
      and paper evidence remain blocked.
    - Boundary: train-only feature probe, no validation/test usage, no H001 modification, no
      target creation, and no model training.
    - Validation errors: `0`.
    - Selected next: `compatibility_dataset_v3_support_contact_feature_probe_result_review`.

52. `compatibility_dataset_v3_support_contact_feature_probe_result_review`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v3_support_contact_feature_probe_result_review.py`,
      wrote `compatibility_dataset_v3_support_contact_feature_probe_result_review.md`, and
      generated `artifacts/compatibility_dataset_v3_support_contact_feature_probe_result_review/`.
    - Purpose: decide whether the completed support/contact mesh/pose/contact feature probe is
      strong enough for direct materialization or should first route through a target-design plan.
    - Feature gate: reviewed features are derivable, old numeric proxy dominance high-count is
      `0`, and pose-conditioned predicate contrast exists for two predicate pairs.
    - Predicate diagnosis: `lying on` vs `standing on` and `lying on` vs `supported by` are
      pose-conditioned contrast candidates; `standing on` vs `supported by` collapses under the
      current evidence and should not be used as a clean primary negative pair.
    - Remaining blockers: hard-surface dominance, HL/LH queue imbalance, exact-pair clean
      capacity `4`, and `standing on` / `supported by` superordinate overlap.
    - Decision: allow a target-design plan, but keep candidate materialization, learned smoke,
      and paper evidence blocked.
    - Boundary: train-only result review, no validation/test usage, no H001 modification, no row
      materialization, and no model training.
    - Validation errors: `0`.
    - Selected next: `compatibility_dataset_v3_support_contact_pose_conditioned_target_plan`.

53. `compatibility_dataset_v3_support_contact_pose_conditioned_target_plan`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v3_support_contact_pose_conditioned_target_plan.py`,
      wrote `compatibility_dataset_v3_support_contact_pose_conditioned_target_plan.md`, and
      generated
      `artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_target_plan/`.
    - Purpose: freeze the support/contact target design before any capacity scan, row
      materialization, or learned smoke.
    - Target contract: each anchor creates two same-`G_e` rows with different `T_e`, one for
      `lying on` and one for `standing on`.
    - Label policy: lying-like support/contact pose makes `lying on` positive and `standing on`
      negative; upright support/contact pose makes `standing on` positive and `lying on` negative.
    - `supported by` is diagnostic/superordinate only; it is not a clean primary negative for
      `standing on`.
    - Quota gate for the next scan: target `200` anchors, minimum `120`; at least `60`
      lying-like and `60` upright anchors; non-hard-surface share at least `0.30`; max single
      visible-pair share `0.12`; max single scan share `0.10`.
    - Decision: capacity scan is allowed, but candidate materialization, learned smoke, and paper
      evidence remain blocked.
    - Boundary: train-only target-design plan, no validation/test usage, no H001 modification, no
      row materialization, and no model training.
    - Validation errors: `0`.
    - Selected next: `compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan`.

54. `compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan`
    - completed on 2026-06-26.
    - added `tools/compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan.py`,
      wrote `compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan.md`, and
      generated
      `artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan/`.
    - Purpose: check whether the frozen support/contact `lying on` / `standing on` same-`G_e`
      target is feasible before writing a materialization plan.
    - Capacity: scanned `161,498` support/contact queue rows and `75,763` unique directed anchors;
      selected threshold classified `4,031` anchors.
    - Selected preview: `200` anchor groups / `400` potential rows, with `100` lying-like and
      `100` upright-support anchors.
    - Controls: selected non-hard-surface share `1.0`, max single visible-pair share `0.035`, max
      single scan share `0.03`, optional PLY point/contact feature complete rate `1.0` over the
      first `120` selected anchors.
    - Audit caveat: selected preview queue kind is all `LH`, but queue kind is audit-only and the
      target label comes from pose-conditioned predicate flips, not HL/LH.
    - Decision: allow a candidate materialization plan, but keep actual materialization, learned
      smoke, and paper evidence blocked.
    - Boundary: train-only capacity scan, no validation/test usage, no H001 modification, no row
      materialization, and no model training.
    - Validation errors: `0`.
    - Selected next:
      `compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan`.

55. `compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan`
    - completed on 2026-06-26.
    - added
      `tools/compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan.py`,
      wrote
      `compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan.md`,
      and generated
      `artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan/`.
    - Purpose: freeze exact row materialization policy before creating support/contact candidate
      rows.
    - Contract: reuse the frozen `200`-anchor capacity preview exactly; expand each anchor into
      two same-`G_e` predicate-flip rows, one `lying on` and one `standing on`.
    - Planned counts: `400` rows, `200` positives, `200` negatives, `200` `lying on` rows,
      `200` `standing on` rows, `100` lying-like anchors, and `100` upright anchors.
    - Forbidden actions: no threshold changes, no row refill, no queue-kind target labels, no
      source-score/rank compatibility labels, no validation/test rows, and no learned smoke.
    - Required next gate after materialization: schema/shortcut audit before learned smoke.
    - Decision: candidate materialization is allowed, but learned smoke and paper evidence remain
      blocked.
    - Boundary: train-only materialization plan, no validation/test usage, no H001 modification,
      no row materialization, and no model training.
    - Validation errors: `0`.
    - Selected next:
      `compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization`.

56. `compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization`
    - completed on 2026-06-26.
    - added
      `tools/compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization.py`,
      wrote
      `compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization.md`,
      and generated
      `artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization/`.
    - Purpose: expand the frozen 200-anchor support/contact capacity preview into concrete
      same-`G_e` `lying on` / `standing on` candidate rows without running learned smoke.
    - Materialized counts: `200` anchors, `400` rows, `200/200` positive/negative labels,
      `200` `lying on` rows, `200` `standing on` rows, `100/100` lying-like/upright anchors,
      and `0` hard-surface rows.
    - Evidence coverage: semseg OBB/pose/contact features are complete for `400/400` rows;
      optional aligned PLY point/contact features are complete for `240/400` rows and are
      represented through `Q_e`.
    - Schema precheck: row count, anchor count, rows per anchor, label balance, predicate counts,
      state counts, same-`G_e` pair integrity, paired-label integrity, hidden-token absence,
      and hard-surface exclusion all pass.
    - Decision: schema/shortcut audit is allowed, but learned smoke and paper evidence remain
      blocked.
    - Boundary: train-only candidate materialization, no validation/test usage, no H001
      modification, and no model training.
    - Validation errors: `0`.
    - Selected next:
      `compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit`.

57. `compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit`
    - completed on 2026-06-26.
    - added
      `tools/compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit.py`,
      wrote
      `compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit.md`,
      and generated
      `artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit/`.
    - Purpose: audit schema leakage and single-field shortcut risk before any learned smoke over
      the support/contact pose-conditioned candidate rows.
    - Counts: `400` candidate rows, `400` smoke-ready rows, `200` groups, balanced `200/200`
      labels, and balanced `200/200` `lying on` / `standing on` predicates.
    - Allowed single-feature probes: predicate, object classes, `Z_e` availability flags, `Q_e`
      flags, and every single `G_e` numeric threshold probe are all `0.500`; allowed
      high/medium-risk probes `0`.
    - Blocked raw high-risk probes: `raw_row_id`, `target_label_self`,
      `hidden_pose_state_x_predicate`, and `hidden_G_hash_x_predicate` are `1.000`, which is
      expected because they are not present in `feature_blocks`.
    - Group integrity: `200/200` groups pass two-row, one-positive/one-negative, same-`G_e`,
      and predicate-pair checks.
    - Decision: sanitized-view smoke plan is allowed, but learned smoke and paper evidence remain
      blocked.
    - Boundary: train-only schema audit, no validation/test usage, no H001 modification, no row
      materialization, and no model training.
    - Validation errors: `0`.
    - Selected next:
      `compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan`.

58. `compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan`
    - completed on 2026-06-26.
    - added
      `tools/compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan.py`,
      wrote
      `compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan.md`,
      and generated
      `artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan/`.
    - Purpose: freeze the learned-smoke input contract, model views, controls, and gates for the
      support/contact pose-conditioned target without running a learned model.
    - Input contract: next runner must read only the schema-audited `smoke_ready_view.jsonl` and
      only the `feature_blocks` root. Raw candidate rows, hidden manifests, row ids, anchor ids,
      scan ids, visible pairs, queue kinds, source predicates, hidden pose states, and geometry
      hashes remain forbidden features.
    - Counts: `400` rows, `200/200` positive/negative labels, `200` paired groups,
      `400/400` semseg-complete rows, and `240/400` optional point-complete rows.
    - Primary model: `M5b_compatibility_TG_pose_interaction`, using predicate-conditioned
      lying/upright pose interactions over `G_e_mesh_pose_contact`.
    - Required controls: source-only, semantic-only, geometry-only, no-interaction concat,
      wrong-T same-G, global shuffled-G, and within-predicate shuffled-G.
    - Decision: learned-smoke runner implementation is allowed, but learned smoke and paper
      evidence remain blocked until the runner executes and controls are reviewed.
    - Boundary: train-only smoke plan, no validation/test usage, no H001 modification, no model
      training.
    - Validation errors: `0`.
    - Selected next:
      `compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner`.

59. `compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner`
    - completed on 2026-06-26.
    - added
      `tools/compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner.py`,
      wrote
      `compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner.md`,
      and generated
      `artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner/`.
    - Purpose: execute the train-only grouped-CV learned smoke over the frozen support/contact
      smoke-ready view with source/semantic/geometry/no-interaction baselines and wrong-T /
      shuffled-G controls.
    - Result: all predefined smoke gates passed. `M5b_compatibility_TG_pose_interaction`
      achieved AUROC `1.000`, AUPRC `1.000`, and balanced accuracy `1.000`.
    - Key baselines: source-only AUROC `0.500`, semantic-only AUROC `0.382`, geometry-only AUROC
      `0.500`, no-interaction concat AUROC `0.382`.
    - Controls: wrong-T same-G AUROC `0.000`, shuffled-G global AUROC `0.525`, shuffled-G
      within-predicate AUROC `0.568`, paired compatible-minus-incompatible mean margin
      `0.915326`.
    - Interpretation: this is a clean train-only `C_e` mechanism proof for support/contact
      pose-conditioned compatibility, not yet a broad relation-reliability or paper-level result.
      Calibration/ECE should be reviewed separately because current ECE is a helper diagnostic,
      not a promotion gate.
    - Boundary: train-only grouped-CV smoke, no validation/test usage, no H001 modification, no
      paper evidence.
    - Validation errors: `0`.
    - Selected next:
      `compatibility_dataset_v3_support_contact_pose_conditioned_result_review`.

60. `compatibility_dataset_v3_support_contact_pose_conditioned_result_review`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_support_contact_pose_conditioned_result_review.py`,
      wrote
      `compatibility_dataset_v3_support_contact_pose_conditioned_result_review.md`, and
      generated
      `artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_result_review/`.
    - Purpose: decide how far the passed support/contact smoke can be claimed before adding
      another relation family or promoting anything toward paper evidence.
    - Decision: accept the support/contact result as a scoped `C_e` mechanism proof, not as broad
      relation reliability.
    - Allowed claim: predicate-independent support/contact `G_e` can become compatible or
      incompatible depending on `lying on` versus `standing on` semantic content `T_e`.
    - Blocked claims: broad relation reliability, final `p_rel` / `p_obs`, human-audited
      reliability performance, all-family 3DSSG generality, and paper-level Docker evidence.
    - Caveats: constructed target remains high severity; AUROC `1.000` is useful as a mechanism
      proof but too clean for deployable reliability; calibration is not established; paper
      evidence still requires Docker protocol promotion.
    - Boundary: train-only result review, no validation/test usage, no H001 modification, no new
      learned model, and no paper evidence.
    - Validation errors: `0`.
    - Selected next:
      `compatibility_dataset_v3_multi_family_result_synthesis_plan`.

61. `compatibility_dataset_v3_multi_family_result_synthesis_plan`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_multi_family_result_synthesis_plan.py`, wrote
      `compatibility_dataset_v3_multi_family_result_synthesis_plan.md`, and generated
      `artifacts/compatibility_dataset_v3_multi_family_result_synthesis_plan/`.
    - Purpose: synthesize the two passed scoped `C_e` results into one claim boundary and decide
      whether to add another relation family, design an independent validity target, or plan Docker
      promotion.
    - Evidence: `relative_vertical` and `support_contact_pose_conditioned` both pass the same
      mechanism pattern. `M5b` AUROC is `1.000` for both; geometry-only remains `0.500`; plain
      concat remains below `0.600`; wrong-T and shuffled-G controls degrade as expected.
    - Allowed claim: across relative-vertical and support/contact pose-conditioned relation
      families, predicate-independent `G_e` is insufficient by itself and relation compatibility
      requires `C_e = compatibility(T_e, G_e)`.
    - Route decision: freeze the two-family `C_e` mechanism claim and select independent validity
      target planning before adding attachment/proximity/horizontal families.
    - Blocked claims: broad relation reliability, final `p_rel` / `p_obs`, human-audited
      reliability performance, all-family generality, and paper-level Docker evidence.
    - Boundary: train-only synthesis plan, no validation/test usage, no H001 modification, no new
      learned model, and no paper evidence.
    - Validation errors: `0`.
    - Selected next:
      `compatibility_dataset_v3_independent_validity_target_plan`.

62. `compatibility_dataset_v3_independent_validity_target_plan`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_independent_validity_target_plan.py`, wrote
      `compatibility_dataset_v3_independent_validity_target_plan.md`, and generated
      `artifacts/compatibility_dataset_v3_independent_validity_target_plan/`.
    - Purpose: choose a target source independent from the constructed same-`G_e` compatibility
      labels before testing `C_e`, `p_obs`, or `p_rel` on relation validity.
    - Selected target: `GT_anchored_train_validity_target`.
    - Target-source decision: official train GT is selected; existing manual/no-GT labels are
      rejected for train target use; cross-source agreement is deferred; high-precision geometry
      rules are auxiliary only; `no-GT = negative` is rejected.
    - Train GT capacity snapshot: `relative_vertical` has `3662` GT rows (`higher than = 1831`,
      `lower than = 1831`); `support_contact_pose_conditioned` has `12016` GT rows
      (`standing on = 9992`, `lying on = 2024`).
    - Label policy: GT-supported compatible rows are positive; matched counterfactual or wrong-pair
      rows can be negative only when geometry contradiction and controls agree; no-GT but
      geometry-supported rows become abstain/audit, not negative.
    - Boundary: train-only target plan, no validation/test usage, no H001 modification, no new
      learned model, and no paper evidence.
    - Validation errors: `0`.
    - Selected next:
      `compatibility_dataset_v3_independent_validity_source_inventory`.

63. `compatibility_dataset_v3_independent_validity_source_inventory`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_independent_validity_source_inventory.py`, wrote
      `compatibility_dataset_v3_independent_validity_source_inventory.md`, and generated
      `artifacts/compatibility_dataset_v3_independent_validity_source_inventory/`.
    - Purpose: inventory whether official train GT anchors, Open3DSG train source evidence `Z_e`,
      geometry evidence `G_e`, and strong hard-negative candidates are joinable before
      materializing independent validity rows.
    - Input scanned: `4818996` train-side `match_rows.jsonl` rows; selected primary rows
      `741384`.
    - `relative_vertical`: `370692` rows, source `Z_e` join rate `1.0`, geometry `G_e` join rate
      `1.0`, exact-GT satisfied positives `1140`, strong negatives `19350`, no-GT
      geometry-satisfied abstain/audit rows `105242`.
    - `support_contact_pose_conditioned`: `370692` rows, source `Z_e` join rate `1.0`, geometry
      `G_e` join rate `1.0`, exact-GT satisfied positives `7564`, strong negatives `1067`,
      no-GT geometry-satisfied abstain/audit rows `83463`.
    - Decision: both primary families pass materialization-feasibility gates. No-GT rows remain
      abstain/audit candidates and are not used as negative labels.
    - Boundary: train-only source inventory, no validation/test usage, no row materialization, no
      learned model, no H001 modification, and no paper evidence.
    - Validation errors: `0`.
    - Selected next:
      `compatibility_dataset_v3_independent_validity_materialization_plan`.

64. `compatibility_dataset_v3_independent_validity_materialization_plan`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_independent_validity_materialization_plan.py`, wrote
      `compatibility_dataset_v3_independent_validity_materialization_plan.md`, and generated
      `artifacts/compatibility_dataset_v3_independent_validity_materialization_plan/`.
    - Purpose: freeze row quotas, schema, hard-negative matching, no-GT abstain handling, blocked
      fields, and post-materialization audit gates before creating GT-anchored independent
      validity rows.
    - Planned rows: `4027` total, including `3200` primary binary rows and `827` nonbinary
      abstain/audit rows.
    - Primary binary quotas: `relative_vertical` `800/800` positive/negative and
      `support_contact_pose_conditioned` `800/800` positive/negative.
    - Nonbinary quotas: `400` no-GT geometry-satisfied abstain/audit rows, `400`
      geometry-uncertain abstain rows, and `27` exact-GT geometry-unsatisfied audit-required rows.
    - Label policy: positives are exact GT matches with satisfied geometry; negatives are GT-pair
      other-predicate or same-family mismatch rows with unsatisfied geometry; no-GT rows remain
      abstain/audit only.
    - Boundary: train-only materialization plan, no validation/test usage, no row materialization,
      no learned model, no H001 modification, and no paper evidence.
    - Validation errors: `0`.
    - Selected next:
      `compatibility_dataset_v3_independent_validity_candidate_materialization`.

65. `compatibility_dataset_v3_independent_validity_candidate_materialization`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_independent_validity_candidate_materialization.py`, wrote
      `compatibility_dataset_v3_independent_validity_candidate_materialization.md`, and generated
      `artifacts/compatibility_dataset_v3_independent_validity_candidate_materialization/`.
    - Purpose: materialize the frozen GT-anchored independent validity plan into candidate rows,
      model-safe smoke view, hidden manifest, quota audit, and schema precheck artifacts.
    - Materialized rows: `4027` total, including `3200` primary binary rows and `827` nonbinary
      abstain/audit rows.
    - Primary binary labels are balanced: `1600` positive and `1600` negative.
    - Family counts: `relative_vertical = 2012`,
      `support_contact_pose_conditioned = 2015`.
    - Quota audit: all frozen quota cells passed. No-GT rows were kept as abstain/audit and were
      not used as negative labels.
    - Selection caveat: strict scan plus visible-pair caps selected `3491` rows; a deterministic
      fallback relaxed only the visible-pair cap and selected the remaining `536` rows. This keeps
      the independent target balanced but makes visible-pair shortcut auditing mandatory.
    - Boundary: train-only candidate materialization, no validation/test usage, no learned model,
      no H001 modification, and no paper evidence.
    - Validation errors: `0`.
    - Selected next:
      `compatibility_dataset_v3_independent_validity_schema_shortcut_audit`.

66. `compatibility_dataset_v3_independent_validity_schema_shortcut_audit`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_independent_validity_schema_shortcut_audit.py`, wrote
      `compatibility_dataset_v3_independent_validity_schema_shortcut_audit.md`, and generated
      `artifacts/compatibility_dataset_v3_independent_validity_schema_shortcut_audit/`.
    - Purpose: check whether the materialized independent validity target is safe to use for
      learned smoke, after removing construction-derived geometry summaries from the model view.
    - Sanitized primary view: `3200` rows with balanced `1600/1600` labels.
    - Schema result: sanitized blocked feature-path hits `0`, sanitized blocked field leakage hits
      `0`.
    - Blocked construction summary probes: `geometry_status`, `consistency_score`,
      `geometry_residual_proxy`, and `geometry_axis` each recover the target with accuracy `1.0`;
      `p_geom_valid` reaches `0.750625`. These are excluded from the sanitized view.
    - Remaining allowed-feature shortcut risk: `predicate_x_class_pair` reaches `0.976562` and
      `subject_object_class_pair` reaches `0.84`.
    - Decision: learned smoke remains blocked. The target is class-balanced and schema-sanitized,
      but still not independent enough because object-pair/predicate-object-pair strata can recover
      the label.
    - Boundary: train-only schema audit, no validation/test usage, no learned model, no H001
      modification, and no paper evidence.
    - Validation errors: `1`, intentionally recording the allowed-feature shortcut blocker rather
      than an input/schema failure.
    - Selected next:
      `compatibility_dataset_v3_independent_validity_path_decision_after_schema_shortcut_audit`.

67. `compatibility_dataset_v3_independent_validity_path_decision_after_schema_shortcut_audit`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_independent_validity_path_decision_after_schema_shortcut_audit.py`,
      wrote
      `compatibility_dataset_v3_independent_validity_path_decision_after_schema_shortcut_audit.md`,
      and generated
      `artifacts/compatibility_dataset_v3_independent_validity_path_decision_after_schema_shortcut_audit/`.
    - Purpose: decide whether the blocked independent-validity target should be repaired, frozen as
      diagnostic evidence, or promoted to learned smoke.
    - Decision: freeze the current independent-validity target as diagnostic evidence and do not run
      learned smoke from it.
    - Current-artifact repair capacity: family `3200`, predicate `2374`, subject/object class pair
      `1024`, exact predicate x class pair `150`, and exact predicate x class pair x rank band
      `146`.
    - Reason: exact `predicate_x_class_pair` is the strongest allowed shortcut, so class-pair-only
      repair is insufficient. Exact predicate-class repair inside the current artifact has too few
      balanced rows.
    - Rejected routes: learned smoke now, dropping object labels from `T_e`, current-artifact exact
      predicate-class rebalancing, class-pair-only rebalancing, using `geometry_status` /
      `p_geom_valid` as learned input, and paper reliability promotion.
    - Selected next: full-train stratum-repair capacity scan.
    - Boundary: train-only path decision, no validation/test usage, no learned model, no H001
      modification, and no paper evidence.
    - Validation errors: `0`.
    - Selected next:
      `compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan`.

68. `compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan.py`,
      wrote `compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan.md`, and
      generated
      `artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan/`.
    - Purpose: scan full train for exact `predicate_label + subject_class_label +
      object_class_label` strata containing both positive and negative independent-validity
      candidates.
    - Full-train scan: `4818996` total match rows, `741384` selected primary-family rows, and
      `29121` primary rows with `8704` positive and `20417` negative.
    - Join rates: source `Z_e` and raw geometry `G_e` are both `1.0` on primary rows.
    - Exact `predicate_x_class_pair` repair capacity: `3024` groups, `39` mixed groups, raw balanced
      capacity `2384`, and scan-capped capacity `2252`.
    - The capacity scan passes the repair gate: minimum primary rows `800`, minimum per-class rows
      `400`, minimum mixed exact strata `30`, and minimum scan-capped rows `600`.
    - Decision: independent validity is not abandoned. The previous 4027-row artifact remains
      diagnostic, but full train has enough exact semantic-stratum capacity for a repaired
      materialization attempt.
    - Boundary: train-only capacity scan, no validation/test usage, no row materialization, no
      learned model, no H001 modification, and no paper evidence.
    - Validation errors: `0`.
    - Selected next:
      `compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan`.

69. `compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan.py`,
      wrote
      `compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan.md`, and
      generated
      `artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan/`.
    - Purpose: freeze an exact semantic-stratum repaired materialization contract for the blocked
      independent-validity target.
    - Planned target: `1600` primary binary rows with `800/800` positive/negative labels.
    - Retained strata: `35` exact `predicate_label + subject_class_label + object_class_label`
      strata, with per-stratum positive/negative balance and max `125` pairs per stratum.
    - Planned family rows: `relative_vertical = 1512`,
      `support_contact_pose_conditioned = 88`.
    - Predicate rows: `higher than = 760`, `lower than = 752`, `lying on = 64`, and
      `standing on = 24`.
    - Important caveat: the repaired target is not family-balanced generality evidence.
      Support/contact exact-stratum capacity is too small, so it is retained only as a diagnostic
      slice in this target.
    - Blocked model inputs: `geometry_status`, `p_geom_valid`, `consistency_score`, residual
      summaries, target pools, `label_match_status`, hidden GT provenance, scan ids, and selection
      metadata.
    - Boundary: train-only materialization plan, no row materialization, no validation/test usage,
      no learned model, no H001 modification, and no paper evidence.
    - Validation errors: `0`; warnings: `2`.
    - Selected next:
      `compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization`.

70. `compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization.py`,
      wrote
      `compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization.md`,
      and generated
      `artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization/`.
    - Purpose: materialize train-only exact predicate/object-class balanced rows following the
      repaired quota plan.
    - Materialized target: `1600` primary rows with `800/800` positive/negative labels across `35`
      exact strata.
    - Family rows: `relative_vertical = 1512` and
      `support_contact_pose_conditioned = 88`.
    - Predicate rows: `higher than = 760`, `lower than = 752`, `lying on = 64`, and
      `standing on = 24`.
    - Strict scan-cap selection filled all quotas; scan-cap relaxation rows `0`.
    - Schema precheck passed: model-safe forbidden key hits `0`, feature-block forbidden key hits
      `0`, and stratum internal balance failures `0`.
    - Boundary: train-only candidate materialization, no validation/test usage, no learned model, no
      H001 modification, and no paper evidence.
    - Validation errors: `0`.
    - Selected next:
      `compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit`.

71. `compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit.py`,
      wrote
      `compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit.md`, and
      generated
      `artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit/`.
    - Purpose: audit the repaired target for schema leakage and residual shortcuts before learned
      smoke.
    - Rows: `1600` model-safe rows with `800/800` labels and `35` retained exact strata.
    - Critical shortcut result: `critical_high_or_medium = 0`,
      `source_confidence_high_or_medium = 0`, and `raw_geometry_high_or_medium = 0`.
    - Previous blocker repaired: `predicate_x_class_pair = 0.500000`,
      `subject_object_class_pair = 0.500000`, and `predicate_label = 0.500000`.
    - Additional low-risk source probes: `rank_band = 0.553750`, `semantic_rank = 0.549375`, and
      `semantic_score_norm = 0.525625`.
    - Schema result: sanitized blocked feature-path hits `0`, model feature blocked-key hits `0`.
      Hidden construction fields remain predictive, but they are not model inputs.
    - Boundary: train-only schema/shortcut audit, no validation/test usage, no learned model, no
      H001 modification, and no paper evidence.
    - Validation errors: `0`.
    - Selected next:
      `compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan`.

72. `compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan.py`,
      wrote
      `compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan.md`,
      and generated
      `artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan/`.
    - Purpose: freeze the train-internal learned-smoke input, baseline, control, and gate contract
      for the repaired sanitized view.
    - Input rows: `1600` rows with `800/800` labels, `1097` groups, `491` mixed-label groups, and
      `35` retained exact strata.
    - Planned baselines: semantic-only `T_e`, source-only `Z_e`, semantic+source `T_e+Z_e`,
      geometry-only `G_e_raw`, plain `T_e+G_e_raw` concatenation, compatibility interaction
      `T_e+G_e_raw`, and full factorized `T_e+Z_e+G_e_raw+Q_e`.
    - Planned controls: shuffled-G global, shuffled-G within predicate, wrong-predicate-family, and
      no-interaction concat.
    - Gate decision: geometry-only is a serious baseline, not a near-chance requirement. If
      geometry-only is within `0.02` AUROC of the best factorized view, the result is
      geometry-dominance diagnostic rather than factorized compatibility evidence.
    - Boundary: train-only smoke plan, no learned smoke, no validation/test usage, no H001
      modification, and no paper evidence.
    - Validation errors: `0`.
    - Selected next:
      `compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner`.

73. `compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner.py`,
      wrote
      `compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner.md`,
      and generated
      `artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner/`.
    - Purpose: run train-only grouped-CV learned smoke over the repaired sanitized view.
    - Dataset: `1600` rows, `800/800` labels, `1097` groups, `491` mixed-label groups, and
      validation errors `0`.
    - Primary result: `M6_TG_compatibility_interaction` AUROC `0.995633` and
      `M7_factorized_TZGQ` AUROC `0.995280`.
    - Shortcut baselines stayed below the frozen threshold: semantic/source max `0.568110`.
    - Geometry-only baseline was weak: `M4_geometry_only_G` AUROC `0.527064`; primary margin over
      geometry-only `0.468569`.
    - Controls passed: shuffled-G global `0.514618`, shuffled-G within predicate `0.458553`, and
      wrong-predicate control `0.026644`.
    - Boundary: train-only hypothesis smoke, no validation/test usage, no paper evidence, no H001
      modification, and no calibrated probability claim because primary-model `ECE-10` is high.
    - Selected next:
      `compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review`.

74. `compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review.py`,
      wrote
      `compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review.md`, and
      generated
      `artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review/`.
    - Purpose: review the passed train-only smoke result, lock allowed claim boundaries, and choose
      the next route.
    - Accepted claim: train-only exact-stratum repaired independent-validity evidence supports
      explicit predicate-conditioned compatibility `C_e = compatibility(T_e, G_e)` for
      discrimination/ranking.
    - Blocked claims: calibrated posterior reliability, paper-level result, held-out result, broad
      all-relation 3DSSG reliability, and support/contact independent-validity generality from this
      artifact.
    - Family scope: `relative_vertical` is primary supported (`1512` rows, slice AUROC
      `0.999990`); `support_contact_pose_conditioned` remains diagnostic (`88` rows, slice AUROC
      `0.702479`, wrong-predicate slice AUROC `0.603306`).
    - Main risk: primary `ECE-10 = 0.480112`, so no calibrated probability claim is allowed.
    - Selected next:
      `compatibility_dataset_v3_independent_validity_calibration_scope_plan`.

75. `compatibility_dataset_v3_independent_validity_calibration_scope_plan`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_independent_validity_calibration_scope_plan.py`,
      wrote
      `compatibility_dataset_v3_independent_validity_calibration_scope_plan.md`, and generated
      `artifacts/compatibility_dataset_v3_independent_validity_calibration_scope_plan/`.
    - Purpose: audit whether the high runner `ECE-10` is a real calibration blocker and select the
      next evidence route.
    - Calibration audit: the previous runner `ECE-10` is not a valid binary probability calibration
      gate by itself because it compares threshold correctness with raw positive-class score.
      Corrected metrics give `M6` probability ECE `0.046582`, `M6` Brier `0.020504`, and `M7`
      probability ECE `0.048281`.
    - Decision: calibration metric definition is repaired for future smoke runners, but calibrated
      `p_rel` / `p_obs` remains blocked because the target is train-only `C_e`, not a held-out
      reliability target.
    - Selected next: support/contact independent-validity balancing. The current artifact remains
      relative-vertical dominant (`1512 / 1600`) and support/contact has only `88` rows.

76. `compatibility_dataset_v3_independent_validity_support_contact_balancing_plan`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_independent_validity_support_contact_balancing_plan.py`,
      wrote
      `compatibility_dataset_v3_independent_validity_support_contact_balancing_plan.md`, and
      generated
      `artifacts/compatibility_dataset_v3_independent_validity_support_contact_balancing_plan/`.
    - Purpose: decide whether support/contact can become a primary GT-anchored independent-validity
      family after the exact-stratum repaired target left it as an `88`-row diagnostic slice.
    - Diagnosis: exact predicate-class balance is too strict for support/contact (`88` rows:
      `lying on = 64`, `standing on = 24`), but predicate-level scan-capped capacity is sufficient
      (`support/contact = 2134`, `lying on = 1370`, `standing on = 764`).
    - Selected route: predicate-balanced support/contact independent-validity materialization with
      `1200` target rows, `800` minimum rows, `600` rows per predicate, and `300/300`
      positive/negative balance inside each predicate.
    - Rejected route: reuse the old `400`-row pose-conditioned constructed target as main evidence;
      it remains auxiliary `C_e` mechanism evidence, not independent validity ground truth.
    - Required controls before smoke: class-pair cap, scan cap, directed-pair cap, rank-band cap,
      and schema shortcut audit with `p_geom_valid`, `geometry_status`, label provenance, and
      construction summaries blocked from model input.

77. `compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization.py`,
      wrote
      `compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization.md`,
      and generated
      `artifacts/compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization/`.
    - Purpose: materialize the selected support/contact-primary independent-validity target before
      schema shortcut audit.
    - Scanned `4,818,996` train match rows, including `370,692` support/contact-family rows and
      `8,631` primary support/contact candidate rows.
    - Materialized `1200` rows with global `600 / 600` positive/negative balance.
    - Predicate balance: `lying on = 300/300`, `standing on = 300/300`.
    - Cap audit passed: max scan share `0.0108`, directed-pair share `0.0017`, class-pair share
      `0.0167`, rank-band share `0.4017`.
    - Schema precheck passed: zero forbidden construction-key hits in `model_safe_view` and feature
      blocks; `p_geom_valid`, `geometry_status`, label provenance, and construction summaries remain
      hidden-only.
    - Selected next: schema shortcut audit before any learned smoke.

78. `compatibility_dataset_v3_independent_validity_support_contact_balancing_schema_shortcut_audit`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_independent_validity_support_contact_balancing_schema_shortcut_audit.py`,
      wrote
      `compatibility_dataset_v3_independent_validity_support_contact_balancing_schema_shortcut_audit.md`,
      and generated
      `artifacts/compatibility_dataset_v3_independent_validity_support_contact_balancing_schema_shortcut_audit/`.
    - Purpose: audit the support/contact-primary `1200`-row model-safe view before any learned
      smoke after exact predicate-class balance was relaxed.
    - Schema leakage checks passed: sanitized blocked feature path hits `0` and model feature
      blocked key hits `0`.
    - Candidate balance remained intact: `600/600` positive/negative globally and `300/300` inside
      both `lying on` and `standing on`.
    - Learned smoke is blocked by critical allowed semantic shortcut probes:
      `subject_class_label` accuracy `0.804167`, `object_class_label` accuracy `0.785000`,
      `subject_object_class_pair` accuracy `0.920000`, and `predicate_x_class_pair` accuracy
      `0.975833`.
    - Source-confidence probes and raw-geometry single-field probes did not trigger medium/high
      risk warnings, so the current blocker is object-class composition rather than `Z_e` or raw
      `G_e` alone.
    - Selected next:
      `compatibility_dataset_v3_independent_validity_support_contact_balancing_path_decision_after_schema_shortcut_audit`.

79. `compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_capacity_scan`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_capacity_scan.py`,
      wrote
      `compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_capacity_scan.md`,
      and generated
      `artifacts/compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_capacity_scan/`.
    - Purpose: test the first-choice support/contact repair, namely stronger class-pair and
      within-class contrast after object-class shortcut risk blocked learned smoke.
    - Full train scan: `4,818,996` rows scanned, `370,692` support/contact-family rows, and
      `8,631` primary support/contact candidate rows.
    - Predicate availability: `lying on` positive/negative `1,643/685`; `standing on`
      positive/negative `5,921/382`.
    - Relaxed `subject_class + object_class` contrast has `50` mixed groups and `426` scan-capped
      balanced rows, so a small diagnostic is possible.
    - Strict `predicate + subject_class + object_class` contrast has only `13` mixed groups and
      `88` scan-capped balanced rows; by predicate, `lying on = 64` and `standing on = 24`.
    - Decision: strict support/contact class-pair repair is blocked for main learned smoke; relaxed
      class-pair repair can only be diagnostic because it does not remove the full
      `predicate_x_class_pair` shortcut.
    - Selected next:
      `compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_after_capacity_scan`.

80. `compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_after_capacity_scan`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_after_capacity_scan.py`,
      wrote
      `compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_after_capacity_scan.md`,
      and generated
      `artifacts/compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_after_capacity_scan/`.
    - Selected path:
      `freeze_support_contact_independent_validity_as_diagnostic_select_scope_synthesis`.
    - Rejected strict support/contact predicate-class repair as a main target because
      `predicate_x_class_pair` scan-capped capacity is only `88` rows, with `lying on = 64` and
      `standing on = 24`.
    - Deferred relaxed class-pair diagnostic because it has `426` rows but does not control the full
      `predicate_x_class_pair` shortcut.
    - Deferred object-class-masked diagnostic because it removes part of deployable `T_e`.
    - Boundary: no learned smoke, no row materialization, no validation/test usage, no calibrated
      `p_rel` / `p_obs`, no paper-level evidence, and no H001 modification.
    - Selected next:
      `compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze`.

81. `compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze`
    - completed on 2026-06-27.
    - added
      `tools/compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze.py`,
      wrote
      `compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze.md`,
      and generated
      `artifacts/compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze/`.
    - Purpose: synthesize H002 scope after freezing support/contact independent-validity as
      diagnostic-only.
    - Current allowed claim: train-only predicate-conditioned compatibility `C_e` evidence.
      Semantic/source evidence and predicate-independent geometry are insufficient alone, while
      `C_e = compatibility(T_e, G_e)` separates valid and invalid candidates on the exact-stratum
      repaired target.
    - Main evidence remains relative-vertical dominant: `M6_TG_compatibility_interaction` AUROC
      `0.9956328125`, geometry-only `0.5270640625`, source-only `0.56811015625`, and
      wrong-predicate `0.02664375`.
    - Support/contact scope: pose-conditioned support/contact is scoped constructed `C_e`
      mechanism evidence; support/contact independent-validity is diagnostic-only frozen because
      strict predicate-class capacity is `88`.
    - Calibration scope: corrected train-only probability ECE is `0.04658165053413088` and Brier is
      `0.020503824238432555`, but calibrated `p_rel/p_obs` remains blocked because the target is
      not held-out relation reliability.
    - Selected next:
      `compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis`.

Immediate next:

```text
compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis
```
