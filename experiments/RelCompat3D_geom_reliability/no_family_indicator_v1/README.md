# Active No-Family-Indicator Refit

Status: `promoted_active_method`

This is the active RelCompat3D model. It removes the constant family
one-hot from each family-specific linear head. The family identifier still
selects the head, its training-only normalization statistics, its supported
transformations, and its re-ranking scope. No other feature, row, target,
optimizer setting, fusion rule, or evaluation definition may change.

The fit stage read only the 1,061-scan training split and the 117-scan
internal-development split. Internal development was used only as a sanity
diagnostic and did not select a model or restore the removed feature. The fit
stage wrote the model and score-definition lock before any official-validation
file was opened.

The model was promoted on 2026-07-20 after all official-validation,
matched-comparator, control, interval, surface-audit, runtime, paper, and PDF
checks completed. `active_paper_lock.json` is the preserved pre-promotion
snapshot; the current promotion pointer is
`experiments/RelCompat3D_geom_reliability/active_method.json`.

## Frozen Result

- The three family-specific heads contain 66 parameters rather than 69:
  proximity `21`, relative vertical `22`, and support/contact `23`.
- The removed inputs are exactly `family:proximity`,
  `family:relative_vertical`, and `family:support_contact`; the family label
  still selects the head, transformations, and re-ranking scope. Pooled factor
  models are unchanged because family indicators are not constant in a pooled
  head.
- Training retains 60,208 rows; internal development retains 6,246 rows; the
  1,061/117/157 scan firewall is unchanged and the fit reads zero official
  validation rows.
- Internal-development sanity at K=100 changes Source to the candidate from
  Recall `0.98828` to `0.99011` and Violation `0.05743` to `0.03149`.
  The linked-pair positive win rate is `0.99261`, and projected proximity and
  vertical transformation error is exactly zero.
- Official evaluation retains all 548 contexts, the 3,972 exact-label
  denominator, all three predictors, and K=`{5,10,20,50,100}`. Relative to the
  historical 69-parameter predecessor, the largest absolute change over the
  main family-aware result grid is `0.076` percentage points for Recall and
  `0.004` percentage points for Violation.

At K=50, active Recall/Violation percentages are:

| Predictor | Source | RelCompat3D | Change |
| --- | ---: | ---: | ---: |
| VL-SAT | 92.72 / 2.68 | 92.77 / 1.97 | +0.05 / -0.70 |
| Open3DSG | 40.43 / 13.87 | 44.18 / 3.42 | +3.75 / -10.45 |
| SGFN | 74.02 / 3.85 | 74.50 / 2.63 | +0.48 / -1.22 |

The complete old-to-new all-K comparison is preserved in
`candidate_paper/comparison.md`; matched
MLP, rank-average, RRF, all-family product, controls, uncertainty, surface
audit, feature-removal analysis, counterfactual sensitivity, and shared
scan-cluster intervals are in `candidate_paper/` and `evaluation/`. Direct
Linear removals of the linked pairwise term and transformation averaging are
in `evaluation/component_removals/`.

## Locks and Release

- protocol SHA256:
  `011b460c0a5706559d3a5bd6da5f94719417f81bb4d68a9a5b9447fcbd0c41c6`
- structured model SHA256:
  `f53a8bdcf1d8dc37d3935fccfbaf9d3c435ddd057848b0ee5e343ddca3ea0194`
- strict model SHA256:
  `0dcdfd137214ca35074f9215227694c0a72fd4f450905ab39b8b18d66fd5c2f2`
- score contract SHA256:
  `a92e3fb99c897bc2ad791b6004c47560da5b603f21f6056c50f156f10373f9f0`
- pre-promotion review bundle: `release_candidate/`
- deterministic release archive: `release_candidate.tar.zst`, SHA256
  `9156745e154c5d39d6c6c19d323f3fe3961c8d51f5d02709850465b161823f14`
- promoted anonymous OpenReview bundle:
  `release/relcompat3d_aaai27_openreview_20260727_073328/`; the selected `main.pdf`
  is the teaser layout and its outer/inner checksum checks pass.

All 12 official-validation evaluation manifests are complete. The active paper
source, figures, tables, supplement, and runtime report now read from this
root. A separate zero-refit ReplicaSSG/FROSS evaluation is stored in
`evaluation/external_transfer/`; because that target had been observed during
earlier development, its manifest intentionally classifies it as a transfer
stress test rather than an untouched confirmation. The historical 69-parameter
model and its outputs remain available only for provenance and old-to-new
comparison.

One downstream launch stopped before evaluation because the routed-ablation
runner compared JSON object serialization order rather than the frozen set of
condition names. The check was corrected to compare exact membership; no
condition, model, row, score, or protocol value changed. The resumed Docker run
completed with exit `0`. Logs are
`logs/relcompat3d_no_family_indicator_downstream_20260720_051946.log` and
`logs/relcompat3d_no_family_indicator_downstream_resume_20260720_052859.log`.

## Commands

From the repository root:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm no_family_indicator_fit
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm no_family_indicator_freeze_initial
scripts/run_no_family_indicator_v1.sh initial
scripts/run_no_family_indicator_v1.sh downstream
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm no_family_indicator_runtime
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm relcompat3d_component_removals
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm no_family_indicator_external_transfer
```

## Owners

- `protocol.json`: immutable pre-fit contract.
- `fit/`: strict and structured models, internal-development diagnostics,
  score contract, model lock, and manifest.
- `protocols/`: post-fit, pre-evaluation protocols containing the locked model
  hashes.
- `evaluation/`: official-validation metrics, controls, and intervals.
- `candidate_paper/`: preserved pre-promotion comparison and generated source
  fragments.
- `release_candidate/`: verified pre-promotion review bundle.
- `evaluation/runtime/`: active CPU cost and parameter-count measurement.
- `evaluation/external_transfer/`: previously observed ReplicaSSG/FROSS target,
  rerun without target-specific fitting using the active model.
