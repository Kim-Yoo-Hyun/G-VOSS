# H001 Reproducibility and Recovery

Last updated: 2026-07-22 KST.

This document is the authoritative entry point for H001 reruns, artifact
handoff, cleanup, and recovery. Read it before moving, deleting, uploading, or
restoring any H001 artifact.

## 1. Current Submission Snapshot

The public repository is a compact evidence-and-code package. It contains:

- the manuscript, supplement, checklist, bibliography, and figure sources;
- the focused H001 Dockerfile and Compose configuration;
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

## 2. Canonical Public Paths

| Role | Path |
| --- | --- |
| selected manuscript PDF | paper/aaai/main_teaser_aaai27.pdf |
| selected manuscript source | paper/aaai/main_teaser.tex |
| supplement source | paper/aaai/supplement.tex |
| checklist source | paper/aaai/reproducibility_checklist_main.tex |
| active method pointer | experiments/H001_geom_reliability/active_method.json |
| active protocol/model root | experiments/H001_geom_reliability/no_family_indicator_v1/ |
| factor-isolation lock | experiments/H001_geom_reliability/factor_isolation_protocol/ |
| split firewall | experiments/H001_geom_reliability/train_only_reestablishment_v1/ |
| result index | results/h001_geom_reliability/manifest.json |
| result summary | results/h001_geom_reliability/report.md |
| Dockerfile | configs/h001/Dockerfile |
| Compose file | configs/h001/compose.structured.yaml |
| wrapper | scripts/run_no_family_indicator_v1.sh |
| full command map | experiments/H001_geom_reliability/commands.md |

The selected stored PDF is nine US-Letter pages. A fresh build from the current
consolidated manuscript source is ten pages and reports one 4.43 pt overfull
box. Do not regenerate a final upload bundle until that layout debt is fixed.

## 3. Active Method Integrity

The promoted root is:

experiments/H001_geom_reliability/no_family_indicator_v1/

experiments/H001_geom_reliability/active_method.json records these hashes:

| Lock | SHA256 |
| --- | --- |
| protocol | f75918d4257468c794f4d9f55dc0ba18b8177f5b01f1811fecf12f0b3d426cd6 |
| structured Linear model | 08cd309bbacead29dd9f76cd3845e3625de72423e45c242e33114ca686e2c01c |
| strict model | 5b6423d0825395990b00663fc0004799268d87c9480493895d01d1c3ef9c3218 |
| source-score contract | 8da781cb793717c6ef6b69de2a737ee8a5dc96b7b52d9d08e73d831177bbbd89 |
| MLP model | ccf4107c06d95161df8ecb1948b37f781025407d7b3596ddd6886394a2976c3e |
| MLP control summary | 83e85bbb9c940644ece4d0322db6ea2f7c98dccfbd11a62ff1efbf47295484ce |
| MLP point/mesh summary | c77c94024fe9de09afbe9ad418f97945a114087cb0199a00079b77df83c3bd55 |

Verify them with:

~~~bash
root=experiments/H001_geom_reliability/no_family_indicator_v1
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
| Open3DSG route sensitivity | no_family_indicator_v1/evaluation/open3dsg_route/ |
| support/contact preservation | no_family_indicator_v1/evaluation/support_routing/ |
| CPU timing | no_family_indicator_v1/evaluation/runtime/ |
| transfer stress test | no_family_indicator_v1/evaluation/external_transfer/ |

All paths above are relative to experiments/H001_geom_reliability/.

## 5. Reproduction Tiers

### Tier A: GitHub-only validation

Available without external data:

- parse JSON protocols and manifests;
- validate the Docker Compose file;
- compile the Python source;
- inspect stored metrics, controls, intervals, and audit summaries;
- verify model and protocol hashes;
- build the paper if the TeX image is available.

### Tier B: Metric regeneration

Requires the frozen row-level prediction, geometry, ground-truth, and verifier
inputs referenced by the protocol files. These rows are excluded from Git
because they are large and source-derived.

Tier B can regenerate ranking metrics, paired intervals, controls, and runtime
summaries without rerunning the original relation predictors.

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
experiments/H001_geom_reliability/sources/. Those rows are preserved only in
the ignored local snapshot and verified external release history. They must be
restored to the declared paths or the protocol paths must be remapped in a new,
explicitly frozen reproduction contract.

Never commit datasets, source checkpoints, feature caches, or row-level JSONL.

## 7. Docker Validation and Execution

Validate the public Compose file:

~~~bash
docker compose -f configs/h001/compose.structured.yaml config --quiet
docker compose -f configs/h001/compose.structured.yaml config --services
~~~

Build and fit:

~~~bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml build no_family_indicator_fit

env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm no_family_indicator_fit

env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm no_family_indicator_freeze_initial
~~~

Run the coordinated phases:

~~~bash
scripts/run_no_family_indicator_v1.sh initial
scripts/run_no_family_indicator_v1.sh downstream
~~~

Additional services are documented in configs/h001/README.md and
experiments/H001_geom_reliability/commands.md.

The wrapper skips complete outputs and refuses to overwrite a nonempty,
incomplete output directory.

## 8. Paper Build

The protected manuscript image is h001-aaai27-tex:20260712.

~~~bash
docker build -f paper/aaai/Dockerfile.tex \
  -t h001-aaai27-tex:20260712 paper/aaai

docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD:/workspace" -w /workspace/paper/aaai \
  h001-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main_teaser.tex

docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD:/workspace" -w /workspace/paper/aaai \
  h001-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error supplement.tex
~~~

After building, verify page size, page count, fonts, unresolved references,
anonymous metadata, and overfull warnings.

## 9. Last Verified Release Baseline

The ignored local bundle is:

release/h001_aaai27_openreview_20260720_084307/

Its code_and_data_supplement.zip supplied the active src/config/script/experiment
allowlist used for this cleanup. Before later manuscript consolidation it
passed:

- ZIP integrity;
- internal MANIFEST.sha256 verification;
- anonymous path and metadata checks;
- JSON and Compose parsing;
- extracted-source Docker builds;
- canonical PDF and font checks.

It is a recovery and comparison baseline. Because the current manuscript source
has changed, it must not be uploaded as though it were a newly regenerated
release.

## 10. Local Archive

All non-submission material is physically preserved under:

archive/local/pre_submission_20260722/

The directory is ignored by Git. It contains approximately 23GB, including:

- previous_archive/: the earlier H001 archive, historical results/scripts,
  hypothesis records, cached files, and superseded venue material;
- repository_roots/: moved literature, hypothesis, and H002 experiment trees;
- src/: source files excluded from the verified submission allowlist;
- configs/: optional and historical Docker configurations.

Only archive/README.md belongs to the public repository.

The former active H001 pre-cleanup snapshot is nested under:

archive/local/pre_submission_20260722/previous_archive/experiments/
H001_geom_reliability/pre_submission_20260722/

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
