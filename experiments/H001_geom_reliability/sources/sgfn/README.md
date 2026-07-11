# SGFN Confirmatory Source

Last updated: 2026-07-10 KST

Source id: `sgfn_official_full_l160`.

This is the fresh exact-label confirmatory source selected before SGFN
inference. Target history is preserved under
`../../confirmatory_evaluation/sgfn_target_v1/`, `sgfn_target_v2/`, and
`sgfn_target_v3/`:

- v1 selected SGFN/full_l160 but mistakenly named the l20 checkpoint and the
  zero-overlap source validation list.
- v2 corrected the split identity before inference: the frozen 548 H001
  contexts use the 157 scans exactly equal to official SGFN `test_scans.txt`.
- v3 is the user-authorized pre-inference checkpoint-URL erratum. It freezes
  the official `SGFN_full_l160.zip` before correct-checkpoint download and
  prohibits further target/score/K/family/coverage changes.

## Current State

- Correct checkpoint audit: passed, object/relation classifier heads 160/26.
- Runtime staging: 157/157 scan directories and official source commit locked.
- Preprocessing: ready, 157 scans / 4,480 nodes / 27,712 source relationship
  rows; point-only filter index retains every generated 3D node.
- Inference smoke: passed on one full directed graph with strict checkpoint
  load, 160/26 vocab, RGB alignment, and 5,112 directed edges.
- Full inference: complete, exit 0; 157 scans / 4,480 nodes / 160,526 directed
  edges / 4,173,676 relation scores. Log and exit file are
  `logs/h001_sgfn_inference_20260710_163351.log` and
  `logs/h001_sgfn_inference_20260710_163351.exit`.
- Adapter: ready, 548/548 contexts, 36,808/36,808 nonself directed pairs, and
  957,008 prediction rows. The frozen 3,972-row H001 GT denominator is retained;
  11 self-`supported by` rows have no model edge and no edge is synthesized.
- Geometry join: ready with 957,008/957,008 preserved verification rows and two
  recorded nonfatal invalid-OBB warnings.
- Confirmatory metrics: ready, 1,000 paired subgraph resamples, seed 20260710.
  Final audit status is `confirmatory_primary_gate_passed`.

## Confirmatory Result

At frozen primary K=100, `semantic_only` has Recall 0.92346 (3668/3972,
95% CI [0.90365,0.94205]) and verifier V 0.06297 (3451/54800, 95% CI
[0.05973,0.06633]). `family_conditional_risk` has Recall 0.94159 (3740/3972,
95% CI [0.92269,0.95877]) and verifier V 0.03808 (2087/54800, 95% CI
[0.03560,0.04069]). Paired dR is +0.01813, 95% CI [+0.01341,+0.02325]; paired
verifier dV is -0.02489, 95% CI [-0.02699,-0.02290]. Both frozen aggregate
gates pass.

The result is not family-uniform: `support_contact` verifier dV is +0.00450,
95% CI [+0.00370,+0.00532], `proximity` is unchanged, and
`relative_vertical` verifier dV is -0.08470, 95% CI [-0.08837,-0.08105]. Fixed
rank-average fusion also passes the recall/lower-V gate against the locked main
score: R@100 0.94763 and verifier V@100 0.02772, with dR +0.00604, 95% CI
[-0.00217,+0.01446], and dV -0.01036, 95% CI [-0.01179,-0.00905]. Therefore
this run confirms exact-label aggregate Recall for the frozen SGFN target, but
does not establish unique main-score dominance or independent human validity.

## Compatibility Boundary

The official model and checkpoint are unchanged. Runtime-only compatibility
adapters are explicit:

- non-network `wandb` import stub because logging is disabled;
- `pytictoc` timer stub;
- PyG 1.x private edge-collector replacement using the identical target/source
  tensor gather and the source `message()` implementation;
- source-equivalent OBJ-texture nearest-vertex RGB alignment implemented with
  SciPy `cKDTree` because `knn_cuda` is unavailable;
- `max_num_edge=-1` so the frozen contract exports every source-available
  directed edge rather than the source loader's 512-edge cap.

These changes do not fit, tune, or substitute model weights or scores.

## Docker Order

```bash
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_checkpoint_audit_v3
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_runtime_stage
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_preprocess
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_preprocess_finalize
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_inference_smoke
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_inference
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_adapter_export
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_geometry_join
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_confirmatory_metrics
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_confirmatory_audit
```

Canonical final artifacts are `adapter/coverage_audit.json`,
`confirmatory_metrics/summary.md`, and `confirmatory_metrics/decision.json`.
Report SGFN with the frozen denominator, verifier-V limitation,
`support_contact` regression, and rank-average challenge together.
