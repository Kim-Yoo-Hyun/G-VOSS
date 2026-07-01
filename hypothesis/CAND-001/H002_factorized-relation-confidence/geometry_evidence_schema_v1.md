# H002 Geometry Evidence Schema V1

Date: 2026-06-25 KST

## Purpose

이 문서는 `G_e`와 `Q_e`의 입력 경계를 정의한다. `G_e`는 predicate-independent
geometry evidence이고, `Q_e`는 evidence quality / observability다.

```text
G_e = what geometry exists between the two objects
Q_e = whether the geometry evidence is sufficient to decide
```

Predicate-specific relation validity는 `G_e` 단독이 아니라 `C_e = compatibility(T_e, G_e)`에서
판단한다.

## Global Geometry Evidence `G_e`

모든 relation family에 공통으로 만들 수 있는 geometry-only fields다.

### Object Geometry

- subject/object OBB center
- subject/object OBB size
- subject/object volume
- subject/object height
- subject/object footprint area
- subject/object point count
- subject/object mesh surface area, if available

### Pair Geometry

- center distance
- minimum boundary distance
- XY distance
- vertical center difference `delta_z`
- subject bottom to object top gap
- object bottom to subject top gap
- 3D bbox overlap ratio
- projected XY overlap ratio
- footprint overlap area
- containment ratio, subject in object
- containment ratio, object in subject
- nearest surface gap, if mesh/point surface is available
- contact candidate count or contact area proxy
- normal agreement near candidate contact, if normals exist

### Generic Context Geometry

- floor proximity for subject/object
- wall proximity for subject/object
- vertical support candidate flag from geometry only
- extreme overlap/artifact flag
- scale-normalized distance
- pair direction vector in scene/world frame
- pair direction vector in object-pair normalized frame

Blocked from `G_e`:

- predicate label or text
- relation family
- source score/rank/source id
- official GT label
- audit accept/reject label
- target construction key

## Evidence Quality `Q_e`

`Q_e`는 relation true/false를 직접 판단하지 않고 `p_obs`를 통해 abstain/selective decision을
조절한다.

Fields:

- subject point count
- object point count
- pair/union point count
- subject/object mesh exists
- mesh completeness proxy
- normal availability
- same-frame subject-object visibility
- individual subject/object crop availability
- multi-view count
- sequence frame count
- occlusion risk proxy
- low coverage flag
- missing geometry flag
- unsupported family flag
- evidence conflict flag
- asset tier: geometry-only, individual-view-plus-mesh, same-frame-visible

## Relation-Family Compatibility Views

아래 fields는 `G_e`의 원천 feature다. 어떤 feature가 중요한지는 `T_e`와 만나는
compatibility head에서 결정한다.

### Proximity: `close by`

Relevant `G_e` fields:

- minimum boundary distance
- center distance
- scale-normalized distance
- XY distance
- footprint gap
- object size ratio

Compatibility intuition:

```text
close by requires small distance relative to object scale and scene context.
```

### Relative Vertical: `higher than`, `lower than`

Relevant `G_e` fields:

- `delta_z`
- top/bottom vertical margin
- vertical ordering confidence
- projected XY overlap as context
- object height ratio

Compatibility intuition:

```text
higher/lower depends on vertical order, not source score.
```

### Support / Contact: `standing on`, `lying on`, `supported by`

Relevant `G_e` fields:

- subject bottom to object top gap
- projected XY overlap
- footprint overlap area
- contact area proxy
- normal alignment near contact
- subject/object floor proximity
- support-surface flatness proxy, if available

Compatibility intuition:

```text
support/contact requires vertical order, near-contact, and support surface overlap.
```

### Attachment: `attached to`, `hanging on`, `connected to`

Relevant `G_e` fields:

- nearest surface gap
- projected overlap
- relative vertical anchor position
- contact boundary proxy
- normal alignment
- floor support confound
- wall/vertical surface proximity
- pair direction and relative height

Relevant `Q_e` fields:

- same-frame visibility
- mesh completeness
- crop availability
- evidence tier

Compatibility intuition:

```text
attachment often needs geometry plus observability; pure OBB evidence can be insufficient.
```

`connected to` remains diagnostic unless a specific physical connection schema is defined.

### Relative Horizontal: `left`, `right`, `front`, `behind`

Deferred family.

Relevant `G_e` fields:

- horizontal offset in scene frame
- pair direction vector
- reference frame availability
- camera/view frame direction, if used

Relevant `Q_e` fields:

- reference-frame ambiguity
- view-frame availability

Compatibility intuition:

```text
horizontal relations are frame-dependent, so observability/reference frame must be explicit.
```

### Containment: `inside`, `surrounding`

Deferred family.

Relevant `G_e` fields:

- containment ratio
- volume overlap
- boundary violation distance
- object size ratio

Compatibility intuition:

```text
containment requires asymmetric inclusion, not just proximity.
```

## H001 `p_geom_valid` Role

H001 `p_geom_valid` is retained as:

1. geometry-only baseline;
2. rule-derived teacher for auxiliary supervision;
3. calibration reference for relation-family score sanity;
4. ablation input in a separately named condition.

It is not:

- the final relation reliability;
- an input to `C_e` in the main learned-compatibility condition;
- a substitute for `G_e` vector/token evidence;
- a negative label for no-GT rows.

## Normalization

Geometry fields should be normalized without using predicate/source labels.

Recommended normalization:

- distances normalized by object scale and scene scale;
- vertical margins normalized by object height;
- overlap fields clipped to `[0, 1]`;
- missing numeric values represented by mask plus neutral fill value;
- per-source score normalization kept outside `G_e` in `Z_e`.

## Schema Output Contract

Each candidate row should expose:

```text
geometry_features: dict
geometry_feature_mask: dict
observability_features: dict
observability_mask: dict
p_geom_valid_baseline: optional float
geometry_status_baseline: optional string
```

The baseline fields are allowed for evaluation, teacher supervision, and ablation. They must be
excluded from the main `G_e` input unless the experiment is explicitly named as a baseline/teacher
condition.

## Current Follow-Up

```text
counterfactual_protocol_v1 = completed
prototype_dataset_contract_v1 = completed
smoke_baseline_plan_v1 = completed
prototype_dataset_materialization_v1 = completed
smoke_baseline_runner_v1 = completed
learned_smoke_runner_v1 = completed
attachment_numeric_geometry_materialization_v1 = completed
attachment_numeric_geometry_smoke_v1 = completed
next = attachment_smoke_path_decision_v1
```

The attachment smoke showed that attachment `T_e + G_e` compatibility is stronger than source-only,
geometry-only, and predicate/family shortcut probes, but hidden construction probes remain high.
The next step should decide whether attachment joins the combined H002 prototype now or first needs
stricter shortcut controls / target repair.
