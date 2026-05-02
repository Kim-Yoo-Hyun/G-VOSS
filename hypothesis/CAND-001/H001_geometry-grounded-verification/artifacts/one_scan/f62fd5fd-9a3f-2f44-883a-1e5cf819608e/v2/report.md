# Verifier v2 Report

Created at: `2026-04-30T11:14:56.791799+00:00`
Scan id: `f62fd5fd-9a3f-2f44-883a-1e5cf819608e`

## Role

`h001-verifier-v2` is a subtype-aware support/contact smoke-test verifier.
It is not benchmark evidence.

## Summary

| Metric | Value |
| --- | ---: |
| all edges | 772 |
| support/contact edges | 32 |
| review count | 1 |
| visually plausible v2 violations | 0 |

## Support Status

| Status | Count |
| --- | ---: |
| `satisfied` | 31 |
| `uncertain` | 1 |

## Subtypes

| Subtype | Count |
| --- | ---: |
| `geometry_quality_uncertain` | 1 |
| `legged_floor_support` | 15 |
| `rigid_object_on_furniture` | 5 |
| `soft_support_contact` | 11 |

## Transitions

| Transition | Count |
| --- | ---: |
| `v1_satisfied_to_v2_satisfied` | 19 |
| `v1_uncertain_to_v2_satisfied` | 1 |
| `v1_violated_to_v2_satisfied` | 11 |
| `v1_violated_to_v2_uncertain` | 1 |

## Interpretation

Inference:

v2 should be judged by whether it reduces visually plausible false violations while preserving inspectable support/contact evidence.

## Validation

- passed: `True`
- errors: `0`
- warnings: `1`
