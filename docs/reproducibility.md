# RelCompat3D Reproducibility and Recovery

Last updated: 2026-07-27 KST.

This document is the authoritative entry point for RelCompat3D reruns, artifact
handoff, cleanup, and recovery. Read it before moving, deleting, uploading, or
restoring any RelCompat3D artifact.

## 1. Current Submission Snapshot

The public repository is a compact evidence-and-code package. It contains:

- the manuscript, supplement, checklist, bibliography, and figure sources;
- the focused RelCompat3D Dockerfile and Compose configuration;
- the Python allowlist shipped in the last verified code-and-data supplement,
  plus the point/mesh audit entry point and its active calibration dependency;
- active protocols, model locks, compact metrics, intervals, controls, and
  audit summaries;
- a compact result index and execution runbooks.

It intentionally excludes:

- raw prediction and verifier JSONL rows;
- 3RScan/3DSSG data, point clouds, meshes, and RGB-D frames;
- Open3DSG, VL-SAT, SGFN, FROSS, or Qwen checkpoints and source repositories;
- feature caches and model caches;
- raw point/mesh audit measurements;
- historical H002, literature, and hypothesis work;
- old release bundles and runtime logs.

A GitHub-only checkout can inspect and validate the compact evidence. It cannot
rerun source inference, fitting, or raw geometry audits without the external
inputs described below.

The active public namespace is `RelCompat3D` for names and
`relcompat3d` for lowercase machine identifiers. Ignored recovery snapshots
retain their frozen legacy layouts; restore data into the canonical public
paths below instead of rewriting a preserved snapshot in place.

## 2. Canonical Public Paths

| Role | Path |
| --- | --- |
| selected manuscript PDF | paper/aaai/main_teaser_aaai27.pdf |
| selected manuscript source | paper/aaai/main_teaser.tex |
| supplement source | paper/aaai/supplement.tex |
| checklist source | paper/aaai/reproducibility_checklist_main.tex |
| active method pointer | experiments/RelCompat3D_geom_reliability/active_method.json |
| active protocol/model root | experiments/RelCompat3D_geom_reliability/no_family_indicator_v1/ |
| factor-isolation lock | experiments/RelCompat3D_geom_reliability/factor_isolation_protocol/ |
| split firewall | experiments/RelCompat3D_geom_reliability/train_only_reestablishment_v1/ |
| score robustness and simple baselines | experiments/RelCompat3D_geom_reliability/score_robustness_v1/ |
| routing constraint controls | experiments/RelCompat3D_geom_reliability/routing_controls_v1/ |
| construct-dependence package | experiments/RelCompat3D_geom_reliability/construct_dependence_v1/ |
| component diagnostics | experiments/RelCompat3D_geom_reliability/component_diagnostics_v1/ |
| five-seed robustness | experiments/RelCompat3D_geom_reliability/seed_robustness_v1/ |
| row-level paper reproduction | experiments/RelCompat3D_geom_reliability/row_reproduction_v1/ |
| candidate-pool Recall oracles | experiments/RelCompat3D_geom_reliability/candidate_oracle_v1/ |
| result index | results/relcompat3d_geom_reliability/manifest.json |
| result summary | results/relcompat3d_geom_reliability/report.md |
| Dockerfile | configs/relcompat3d/Dockerfile |
| Compose file | configs/relcompat3d/compose.structured.yaml |
| wrapper | scripts/run_no_family_indicator_v1.sh |
| full command map | experiments/RelCompat3D_geom_reliability/commands.md |

The current source builds to nine US-Letter pages. Technical content ends and
the references begin on page 7; the references continue on pages 8--9. The
prior Table 2 horizontal overflow is resolved. One 36.77646 pt first-page
vertical overfull remains. A current candidate release may be generated for
verification, but it is not upload-ready until that warning and the
submission-system disclosure checks are resolved.

The current supplement builds to 19 US-Letter pages. Its canonical SHA-256 is
`505361303b01c46a3cba01f7ae9e7e7c708a39ac1fa8d5e7e1ea6698b095ff5f`;
the final log has no unresolved reference or overfull-box warning.

## 3. Active Method Integrity

The promoted root is:

experiments/RelCompat3D_geom_reliability/no_family_indicator_v1/

experiments/RelCompat3D_geom_reliability/active_method.json records these hashes:

| Lock | SHA256 |
| --- | --- |
| protocol | 011b460c0a5706559d3a5bd6da5f94719417f81bb4d68a9a5b9447fcbd0c41c6 |
| structured Linear model | f53a8bdcf1d8dc37d3935fccfbaf9d3c435ddd057848b0ee5e343ddca3ea0194 |
| strict model | 0dcdfd137214ca35074f9215227694c0a72fd4f450905ab39b8b18d66fd5c2f2 |
| source-score contract | a92e3fb99c897bc2ad791b6004c47560da5b603f21f6056c50f156f10373f9f0 |
| MLP model | ccf4107c06d95161df8ecb1948b37f781025407d7b3596ddd6886394a2976c3e |
| MLP control summary | 6eb64771c9483102b47b167ff0bde6e81425daa6fbaca885a1eb9d02f870951d |
| MLP point/mesh summary | 3fc9e42b7554b4df4be620ad8d89ca22d99e652d835f141755cd662b1c90fa01 |

Verify them with:

~~~bash
root=experiments/RelCompat3D_geom_reliability/no_family_indicator_v1
sha256sum \
  "$root/protocol.json" \
  "$root/fit/structured_models.json" \
  "$root/fit/strict_models.json" \
  "$root/fit/score_contract.json" \
  "$root/evaluation/nonlinear/models.json" \
  "$root/evaluation/mlp_ablation/summary.json" \
  "$root/evaluation/mlp_surface_audit/summary.json"
~~~

## 4. Compact Evidence Map

| Evidence | Directory |
| --- | --- |
| main variants and matched comparators | no_family_indicator_v1/evaluation/routed_comparators/ |
| all-family comparison | no_family_indicator_v1/evaluation/structured_main/ |
| Linear controls | no_family_indicator_v1/evaluation/routed_ablation/ |
| MLP controls | no_family_indicator_v1/evaluation/mlp_ablation/ |
| paired scan-level intervals | no_family_indicator_v1/evaluation/scan_cluster/ |
| Linear point/mesh audit | no_family_indicator_v1/evaluation/surface_audit/ |
| MLP point/mesh audit | no_family_indicator_v1/evaluation/mlp_surface_audit/ |
| feature-removal analysis | no_family_indicator_v1/evaluation/held_out_primitive/ |
| counterfactual sensitivity | no_family_indicator_v1/evaluation/counterfactual_sensitivity/ |
| direct component removals | no_family_indicator_v1/evaluation/component_removals/ |
| Open3DSG route sensitivity | no_family_indicator_v1/evaluation/open3dsg_route/ |
| support/contact preservation | no_family_indicator_v1/evaluation/support_routing/ |
| CPU timing | no_family_indicator_v1/evaluation/runtime/ |
| transfer stress test | no_family_indicator_v1/evaluation/external_transfer/ |
| score mapping and closest simple baselines | score_robustness_v1/evaluation/ |
| matched routing constraint controls | routing_controls_v1/evaluation/ |
| construct-dependence evidence package | construct_dependence_v1/evaluation/ |
| matched component diagnostics | component_diagnostics_v1/evaluation/ |
| five-seed fitting robustness | seed_robustness_v1/evaluation/ |
| regenerated Tables 1--3 and Figure 3 data | row_reproduction_v1/evaluation/ |
| candidate-pool coverage and Recall upper bounds | candidate_oracle_v1/evaluation/ |

All paths above are relative to experiments/RelCompat3D_geom_reliability/.

## 5. Reproduction Tiers

### Tier A: GitHub-only validation

Available without external data:

- parse JSON protocols and manifests;
- validate the Docker Compose file;
- compile the Python source;
- inspect stored metrics, controls, intervals, and audit summaries;
- inspect regenerated Tables 1--3, Figure 3 data, and the 291-cell comparison;
- inspect candidate-pool coverage and three Recall-oracle summaries;
- verify model and protocol hashes;
- build the paper if the TeX image is available.

### Tier B: Metric regeneration

Requires the frozen row-level prediction, geometry, ground-truth, and verifier
inputs referenced by the protocol files. These rows are excluded from Git
because they are large and source-derived.

Tier B can regenerate ranking metrics, paired intervals, controls, runtime
summaries, the paper tables and trade-off figure data, and candidate-pool
oracles without rerunning the original relation predictors.

The row exporter creates a smaller pseudonymized bundle containing only the
fields needed for paper-level regeneration. Original scan, context, and
instance identifiers are replaced by keyed hashes; raw geometry and object
categories are omitted. Public redistribution of this derived bundle is held
until the authors confirm the 3RScan/3DSSG terms or obtain data-owner
permission. The exporter and deterministic join remain the fallback from
licensed Tier-B inputs.

### Tier C: Full source reproduction

Requires official datasets, source repositories, checkpoints, and model/feature
caches. It covers Open3DSG, VL-SAT, and SGFN source inference and geometry-row
generation before Tier B.

Tier C is not carried by the anonymous GitHub repository.

## 6. External Data Requirements

The protocol files retain the original repository-relative mount contracts.
Important external roots include:

- local_dataset/3RScan/
- local_dataset/3DSSG/
- local_dataset/3DSSG_subset/
- Open3DSG checkpoint, image-feature, and source-runtime payloads;
- VL-SAT and SceneGraphFusion source checkpoints and exports;
- ReplicaSSG/FROSS rows for the transfer stress test.

The primary active protocols also reference row-level files formerly under
experiments/RelCompat3D_geom_reliability/sources/. Those rows are preserved only in
the ignored local snapshot and verified external release history. They must be
restored to the declared paths or the protocol paths must be remapped in a new,
explicitly frozen reproduction contract.

Never commit datasets, source checkpoints, feature caches, or row-level JSONL.

## 7. Docker Validation and Execution

Validate the public Compose file:

~~~bash
docker compose -f configs/relcompat3d/compose.structured.yaml config --quiet
docker compose -f configs/relcompat3d/compose.structured.yaml config --services
~~~

Build and fit:

~~~bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml build no_family_indicator_fit

env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm no_family_indicator_fit

env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm no_family_indicator_freeze_initial
~~~

Run the coordinated phases:

~~~bash
scripts/run_no_family_indicator_v1.sh initial
scripts/run_no_family_indicator_v1.sh downstream
~~~

Additional services are documented in configs/relcompat3d/README.md and
experiments/RelCompat3D_geom_reliability/commands.md.

The P0 score-robustness and closest-simple-baseline analysis uses the same
hash-locked Tier-B rows as the active routed comparator:

~~~bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_score_robustness
~~~

Its local protocol references the ignored pre-submission archive in place to
avoid duplicating roughly 10 GB. For another machine, restore files with the
same hashes to the protocol paths or freeze an explicit path-remapping
protocol. The compact outputs are inspectable without those row files.
The completed evaluation manifest has SHA-256
`57780a58173759b03f784549c2ea0213c9cfdbd5c633863ff7dbd977f8dd3548`;
its own output-hash map verifies every compact CSV, JSON, and Markdown result.

The P0 routing-constraint control and construct-dependence package use the same
hash-locked evidence boundary:

~~~bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_routing_constraints

env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_construct_dependence
~~~

The routing manifest SHA-256 is
`f3e3e5dbda813d60a2a47307a876ab2bd1bfdf693085d0e7689bfe64c43a7bca`.
The construct-dependence manifest SHA-256 is
`caf38e8ab74e0ae76c1f23ffaa6e53c10de4b4fbcf7db6bc6f15dc6da600d426`.
These analyses do not update `active_method.json` or select a replacement
method from final-validation results.

The matched component and training-seed diagnostics use the same locked rows,
active model contract, and official evaluation universe:

~~~bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_component_diagnostics

env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_seed_robustness
~~~

The component manifest SHA-256 is
`107c83993359b0681d77cc4c808696bb23e97c8f9c708a6feec140815bfaa917`.
The five-seed manifest SHA-256 is
`2bcc816f3307ab22fe93002d2db0db930b7a0088aacda54315b5aba1c78d09fe`.
Both manifests verify the 1,061/117/157 split, 60,208 training rows, 6,246
development rows, 3,972 evaluation ground-truth relations, family-sequence
preservation, support/contact preservation, and exact reproduction of the
active models and main point estimates. The active MLP seed was fixed before
the five-seed analysis and was not reselected.

The pseudonymized row export, paper regeneration, and candidate-pool oracle
use the same frozen candidate universe:

~~~bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_export_rows

env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_reproduce_rows

env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/relcompat3d/compose.structured.yaml run --rm \
  relcompat3d_candidate_oracle
~~~

The completed exporter contains 601,140 candidates and 3,972 ground-truth
rows. The reproducer checks 291 canonical paper cells with maximum absolute
error zero at tolerance \(10^{-12}\). Its manifest SHA-256 is
`21ead0d178af66109c2f90707b0560f4e4f1d6f4308486b08955eb6b687f7104`.
The candidate-oracle manifest SHA-256 is
`a7aee28622c84a21aa61c92a6e288f08b58a3e33d69b42118c296cfa2d20a563`.

The wrapper skips complete outputs and refuses to overwrite a nonempty,
incomplete output directory.

## 8. Paper Build

The protected manuscript image is relcompat3d-aaai27-tex:20260712.

~~~bash
docker build -f paper/aaai/Dockerfile.tex \
  -t relcompat3d-aaai27-tex:20260712 paper/aaai

docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD:/workspace" -w /workspace/paper/aaai \
  relcompat3d-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main_teaser.tex

docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD:/workspace" -w /workspace/paper/aaai \
  relcompat3d-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error supplement.tex
~~~

After building, verify page size, page count, fonts, unresolved references,
anonymous metadata, and overfull warnings.

## 9. Current Release Candidate

The current ignored local candidate bundle is:

release/relcompat3d_aaai27_openreview_20260726_214500/

It is regenerated from the current main, supplement, checklist, active figure
assets, method locks, source allowlist, and compact results. Build it after
fresh Docker compilation with:

~~~bash
python scripts/build_release_bundle.py \
  --build-root /tmp/relcompat3d_release_build \
  --timestamp 20260726_214500
~~~

The release verification covers:

- ZIP integrity;
- internal MANIFEST.sha256 verification;
- anonymous path and metadata checks;
- JSON and Compose parsing;
- extracted-source Python and manuscript builds;
- exact outer-file hashes;
- PDF page size, page allocation, fonts, links, and LaTeX warnings.

The release is the latest synchronized candidate, not a final upload artifact:
the main PDF still has the first-page vertical overfull recorded above.

## 10. Local Archive

All non-submission material is physically preserved under:

archive/local/pre_submission_20260722/

The directory is ignored by Git. It contains approximately 23GB, including:

- previous_archive/: the earlier RelCompat3D archive, historical results/scripts,
  hypothesis records, cached files, and superseded venue material;
- repository_roots/: moved literature, hypothesis, and H002 experiment trees;
- src/: source files excluded from the verified submission allowlist;
- configs/: optional and historical Docker configurations.

Only archive/README.md belongs to the public repository.

The former active RelCompat3D pre-cleanup snapshot is nested under:

archive/local/pre_submission_20260722/previous_archive/experiments/
RelCompat3D_geom_reliability/pre_submission_20260722/

## 11. Cleanup and Restore Safety

Before deleting or moving any external payload:

1. identify whether the goal is paper inspection, Tier B metric regeneration,
   or Tier C full reproduction;
2. verify the external copy by checksum, file count, and expected layout;
3. record the decision in TODO.md and this runbook;
4. restore only the smallest required subtree;
5. rerun protocol, model, and output integrity checks.

The 2026-07-22 cleanup moved material within the same filesystem; it did not
delete H002, literature, hypothesis, historical code/configs/results, or prior
archives. Unnecessary historical tracked logs were deleted as requested.
Twelve selected verification logs remain locally under ignored logs/.

## 12. GitHub Publication

The current worktree is organized for a compact public snapshot, but deletion
from the current tree does not remove old blobs from Git history. To avoid
publishing historical datasets, PDFs, or large artifacts, create the public
submission from a fresh repository or an explicitly cleaned history after
reviewing the diff.

Verify prospective public files:

~~~bash
git ls-files --cached --others --exclude-standard |
while IFS= read -r p; do
  test -f "$p" || continue
  size=$(stat -c %s "$p")
  test "$size" -le 10485760 || printf '%s %s\n' "$size" "$p"
done
~~~

No commit, push, history rewrite, or remote publication is implied by the local
cleanup.
