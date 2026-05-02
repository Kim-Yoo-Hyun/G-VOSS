# Evidence Export

Created at: `2026-04-30T03:09:39.248032+00:00`
Scan id: `f62fd5fd-9a3f-2f44-883a-1e5cf819608e`
Geometry source: `semseg_obb_v0`
Rule version: `h001-rules-v0`

## Validation

- Passed: `True`
- Errors: `0`
- Warnings: `3`

## Counts

- `objects_3dssg`: `60`
- `objects_semseg`: `60`
- `relation_tuples`: `772`
- `unique_relation_endpoint_ids`: `57`
- `missing_object_joins`: `0`
- `missing_semseg_joins`: `0`
- `invalid_obb_objects`: `0`
- `edges_exported`: `772`
- `ply_vertices`: `72017`
- `ply_faces`: `99823`
- `seg_indices`: `72017`

## Predicate Families

- `attachment_deferred`: `19`
- `proximity`: `68`
- `relative_horizontal`: `342`
- `relative_vertical`: `48`
- `size_comparison_deferred`: `14`
- `support_contact`: `32`
- `unsupported_first_pass`: `249`

## Top Predicates

- `same object type`: `236`
- `left`: `121`
- `right`: `121`
- `close by`: `68`
- `behind`: `50`
- `front`: `50`
- `higher than`: `24`
- `lower than`: `24`
- `standing on`: `21`
- `lying on`: `11`
- `attached to`: `10`
- `hanging on`: `9`

## Geometry Availability

- `true`: `772`

## Next Action

Review `edges.jsonl`, then run the `h001-rules-v0` verifier application.

This is Phase A output only; it is not prediction-level H001 evidence.
