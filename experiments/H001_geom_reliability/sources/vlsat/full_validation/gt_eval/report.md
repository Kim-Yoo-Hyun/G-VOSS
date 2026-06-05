# GT-Based Verifier Evaluation

- Date: `2026-05-06`
- Status: `ready`
- Output root: `experiments/H001_geom_reliability/sources/vlsat/full_validation/gt_eval`

## Purpose

Reduce the burden on qualitative audit by adding GT-positive consistency and GT-derived counterfactual negative checks.

## Counts

| Item | Count |
| --- | ---: |
| GT positives | 3972 |
| counterfactual negatives | 3972 |
| total rows | 7944 |

## Main Summary

| Split | Rows | Satisfied | Uncertain | Violated | Mean p_geom_valid |
| --- | ---: | ---: | ---: | ---: | ---: |
| GT positive | 3972 | 0.8578 | 0.1387 | 0.0035 | 0.8668 |
| GT-derived negative | 3972 | 0.0327 | 0.6692 | 0.2981 | 0.1260 |

## p_geom_valid Discrimination

| Rows | Brier | AUROC valid | AUPRC valid |
| ---: | ---: | ---: | ---: |
| 7944 | 0.0543 | 0.9772 | 0.9729 |

## Family Breakdown

| Family | Positive rows | Positive nonviolated | Negative rows | Negative nonsatisfied | Family AUROC |
| --- | ---: | ---: | ---: | ---: | ---: |
| `proximity` | 1766 | 1.0000 | 1766 | 1.0000 | 0.9976 |
| `relative_vertical` | 390 | 0.9949 | 390 | 0.9949 | 0.8960 |
| `support_contact` | 1816 | 0.9934 | 1816 | 0.9295 | 0.9924 |

## Interpretation

Fact:

- This evaluation uses held-out GT positives and deterministic GT-derived counterfactual negatives.
- It does not replace the 50-row blinded visual spot-check.

Inference:

- If positive nonviolated rate and p_geom_valid discrimination are high, qualitative audit can be used as a small sanity check rather than the main evidence.
- Any high GT-positive violated rate should be interpreted as label noise, geometry incompleteness, or verifier over-strictness that needs qualitative review.
