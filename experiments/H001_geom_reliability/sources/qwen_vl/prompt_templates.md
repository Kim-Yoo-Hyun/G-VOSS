# Qwen-VL Prompt Templates

These prompts are contract templates. They are frozen before held-out metric inspection.

## `semantic_only_v1`

```text
You are given one or more image crops from the same indoor 3D scene.
The subject object is: {subject_label} (id {subject_id}).
The object object is: {object_label} (id {object_id}).
Pair crops may mark the subject with a red box and the object with a blue box. Use these boxes only to identify the target pair.

Use only the visual evidence and object labels. Do not assume hidden 3D geometry.
Choose relations only from this allowed list: {candidate_predicates}.

Return strict JSON with this schema:
{
  "answer_is_visible": true or false,
  "predictions": [
    {"predicate": "<allowed predicate>", "confidence": 0.0-1.0, "rationale_short": "<brief reason>"}
  ]
}
If no relation is visually supported, return an empty predictions list.
```

## `geometry_aware_diagnostic_v1`

```text
Diagnostic-only prompt. You are given image crops and a frozen 3D geometry summary.
Subject: {subject_label} (id {subject_id}); Object: {object_label} (id {object_id}).
Allowed predicates: {candidate_predicates}.
Geometry summary: {geometry_summary}

Return strict JSON with predicted predicates and a short note about whether the geometry summary supports or contradicts the visual relation.
This prompt is not used for the main semantic-only condition.
```
