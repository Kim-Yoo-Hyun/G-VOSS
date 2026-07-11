# H001 Main-Score Provenance

Frozen at UTC: `2026-07-10T06:18:51.186058+00:00`

| date | event | evidence |
| --- | --- | --- |
| 2026-05-06 | `family_calibrator_artifact_created` | model.json created_at and source_split=train_dev_calib |
| 2026-06-23T20:12:53+09:00 | `family_calibrator_first_committed` | commit `45dc45f857f8160edc3080b6fbcb77785d4dd73d` |
| 2026-06-23 | `full_validation_source_metrics_generated` | both metrics_k_sweep/metrics.json created_at fields |
| 2026-06-24T14:09:45+09:00 | `family_condition_reframed_from_control_to_method_candidate` | commit `d8a07fa91641407daf6d6778dca658e3bc4794af`; H001_v2 11_family_conditional_risk_result.md introduced after source results |
| 2026-06-25T09:38:00+09:00 | `family_conditional_risk_promoted_to_paper_main_score` | commit `d4999aaa6485814b0a05267304ad5e8efda46fb6`; paper/TODO/result wording explicitly promoted the condition |
| 2026-07-10 | `independent_physical_validity_audit_protocol_frozen` | physical_validity_audit/frozen_v1 manifest; labels initially empty |

## Claim boundary

- Fact: calibrator fitting preceded source metric generation and used train/dev calibration rows.
- Fact: paper-main selection followed observation of source metric results.
- Consequence: current VL-SAT/Open3DSG main-score comparisons are retrospective, not confirmatory.
- Prospective evidence: the frozen independent human audit can confirm physical-validity reduction once independent labels are complete.
- Still unresolved: a fresh exact-label source-metric confirmatory target requires a user choice.
