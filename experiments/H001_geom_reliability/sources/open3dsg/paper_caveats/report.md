# Open3DSG Paper Caveats

Status: `open3dsg_paper_caveats_ready`
Created at: `2026-05-19T03:57:42.145011+00:00`

## Purpose

This artifact freezes the paper-facing caveat wording for Open3DSG Table 6 and failure-analysis discussion.
It does not change metrics, taxonomy, checkpoint selection, or denominator policy.

## Fixed Wording

### `table_note_short`

Open3DSG results use a Docker-reproduced averaged-BLIP variant selected by train-dev val/loss before H001 held-out inspection. They are reported on the Open3DSG-covered H001 eval scope after preprocessed-ready filtering, with exact-label recall over 2,545 in-scope GT relations.

### `scope_caveat`

Open3DSG training uses an explicit preprocessed-ready split: 1158/1178 train scans, 3744/3852 train subgraphs, and 79704/81190 train relations. The train-dev validation split is also filtered to 156/160 subgraphs. H001 evaluation uses the covered loadable Open3DSG scope with 377/388 contexts/features and reports `validation_missing_preprocessed:11` as an explicit caveat.

### `variant_caveat`

The Open3DSG checkpoint is an explicitly labeled averaged-BLIP variant, not the exact non-averaged BLIP projector route. The selected checkpoint is `epoch=13-step=13104.ckpt`, chosen by train-dev `val/loss` 0.3288108110 at step 13103 before H001 held-out metric, failure, or visual inspection.

### `denominator_caveat`

Open3DSG recall is exact predicate-label matched. Family grouping is used for reliability/violation reporting only. The reported H001-family denominator is 2,545 GT rows: support_contact 1,199, proximity 1,128, and relative_vertical 218; 4,960 other-family GT rows are outside the H001 metric claim.

### `residual_calibration_caveat`

The calibrated `p_geom_valid` score is not a hard validity label. Qualitative inspection found 10/36 sampled rule-violated cases with `p_geom_valid > 0.9`, so probabilistic, rule-verified, and family-specific variants must be reported separately.

### `non_claim`

These Open3DSG results support measured H001-family relation-reliability evidence, not broad open-vocabulary 3DSSG generation improvement and not arbitrary-baseline generality.

## Coverage Facts

### Train Filter

- train scans: `1158/1178`
- train subgraphs: `3744/3852`
- train relations: `79704/81190`
- removed subgraphs/relations: `108/1486`
- recoverability: `not_recoverable_by_simple_retry_filter_missing_subgraphs`

### Train-Dev Validation Filter

- validation scans: `30/30`
- validation subgraphs: `156/160`
- validation relations: `3696/3749`
- recoverability: `not_recoverable_by_simple_retry_filter_missing_subgraphs`

### H001 Eval Coverage

- selected scans / identity contexts / directed pairs: `127` / `388` / `25916`
- complete feature ids: `377`
- missing preprocessed contexts: `11`
- raw dump rows: `19162`
- adapter prediction rows: `496600`
- adapter filtered raw rows outside H001 object context: `62`

### Metric Denominator

- GT rows: `7505`
- in-scope GT denominator: `2545`
- target family counts: `{'proximity': 1128, 'relative_vertical': 218, 'support_contact': 1199}`
- excluded GT rows: `4960`

### Residual Calibration Risk

- inspected cases: `36`
- demoted by geometry-aware reranking: `23`
- promoted or retained: `13`
- rule-violated with p_geom_valid > 0.9: `10`

## Validation

- no validation errors

## Claim Boundary

Paper-facing wording artifact only. It fixes how to report Open3DSG scope/variant/calibration caveats; it does not change metrics, taxonomy, checkpoint selection, or denominator policy.
