# ReplicaSSG Transfer Stress Test and Development Diagnostic

Last updated: 2026-07-15 KST

This source root owns H001's cross-dataset transfer stress test on the official
ReplicaSSG test split. The original run was executed under a frozen protocol,
but its observed result is now used for method diagnosis and development.
Accordingly, the paper does not describe the target as untouched, prospective,
or single-shot confirmation.

The initial run uses the 11 official ReplicaSSG test scenes and the official
FROSS Visual-Genome-trained RT-DETR-EGTR source with predicted 2D scene graphs
and ground-truth camera poses. It did not use ReplicaSSG validation scenes. The
later `development_v2/` route explicitly performs test-specific fusion
development and records that fact in its protocol and output manifests.

Only exact pre-existing H001 predicate semantics are mapped:

- `near` -> `close by` (`proximity`)
- `above` -> `higher than` (`relative_vertical`)
- `under` -> `lower than` (`relative_vertical`)

`on`, `against`, and the other ReplicaSSG predicates are excluded rather than
post-hoc mapped to H001 support/contact subtypes. The protocol, exact
denominator, score family, K grid, paired-scene bootstrap, and gates are frozen
under `prospective_protocol/frozen_v1/` before source prediction.

The official renderer emits roughly 39,600 frames over the 11 test scenes.
Execution is therefore scene-wise: render one complete official trajectory,
run the unchanged frozen FROSS source, validate and hash its one-scene shard,
then remove only that regenerated RGB-D sequence and its scene-local extracted
texture copy before continuing. The final source pickle is a deterministic
ordered merge of all 11 preserved shards; this changes storage scheduling, not
frames, source settings, or evaluation.

The first valid `apartment_1` shard exposed an execution-only stdin issue:
`docker compose run` consumed the scan loop's standard input, so the locked
runner attempted the final merge after one scene. The failed attempts are
preserved in `logs/h001_replicassg_fross_stream_v{4,5,6}_20260711.log` (exit
1). Resume keeps the hash-locked runner unchanged and prepends
`scripts/no_stdin_bin/` to `PATH`; its three-line `docker` shim redirects only
Docker's stdin to `/dev/null`. It does not read or change frames, predictions,
methods, mappings, thresholds, or evaluation logic. Every existing shard is
still schema/scene validated before reuse.

The official weight archive is locked before engine export/inference at
SHA-256 `03dc86a1a0f40321a2caa0e35ec2739f458837365455017b5a830a0f5349467c`.
The adapter, geometry scorer, evaluator, shard merger, streaming runner,
compose file, and both Dockerfiles are hash-locked in the protocol manifest.

Paper evidence requires Docker execution for protocol freeze, source staging,
inference, adapter export, geometry scoring, metrics/bootstrap, and final
provenance audit. Runtime Replica meshes, rendered frames, weights, TensorRT
engines, and large row-level outputs remain ignored local artifacts.

## Result

All 11 official test scenes completed and merged into a source prediction with
SHA-256 `0c229242ba6f18653330d9f71b5182227b69790664e8e11a551bae4a26e05a27`.
The adapter produces 4,290 candidates, geometry preserves every row, and the
exact-label GT denominator is 172. All 24 final provenance/firewall validations
are true.

The frozen K=100 framework gate fails. `family_product` is identical to
`semantic_only` at R/V `0.36047/0.19674`, so its strict violation-improvement
gate fails. `rank_average_family` reaches R/V `0.33140/0.03839`; dV is
`-0.15835` with paired CI `[-0.19292,-0.12190]`, but dR is `-0.02907` with CI
`[-0.07407,+0.01333]`, violating the recall guardrail. The product improves
the tradeoff at K=20 and K=50, but those remain secondary diagnostics because
K=100 was frozen as primary.

Compact tracked evidence is under
`results/h001_geom_reliability/replicassg_prospective/`. The directory name is
a preserved historical artifact identifier; the current scientific role is a
transfer stress test and development diagnostic. Large ignored runtime output
was removed after compact-result verification. The original result remains a
valid transfer diagnostic; it is not an unbiased estimate of a newly developed
method's dataset-level generalization.

## Development v2

`development_v2/protocol.json` fixes a post-result development grid for:

- within-context quantile normalization of source and compatibility scores;
- bounded monotone penalties
  `percentile(Z) - alpha * max(0, tau - C)`;
- a percentile-compatibility variant robust to compatibility scale;
- an exact bounded-displacement decoder that limits absolute source-rank movement;
- leave-one-scene-out selection diagnostics plus an all-scene deployment
  configuration.

The Docker service is `replicassg_development_v2`. Runtime regeneration is
owned by `scripts/run_replicassg_development_v2_pipeline.sh`; output is written
under `development_v2/evaluation/`.

Development v2 completed on a regenerated 4,293-candidate execution, versus
4,290 candidates in the historical run. All compared methods use the same new
candidate set. The all-scene selection reaches R/V@100 `.35465/.03935`, while
the LOSO estimate reaches `.31977/.03839` and fails the Recall guardrail. The
selected rule's 548-context cross-source evaluation is under
`development_v2/cross_source_evaluation/` and passes its denominator checks,
but does not improve the established product consistently enough for promotion.
These outputs are supplement-only development evidence.

## Locked Final-Method Evaluation v1

`final_method_transfer_v1/protocol.json` freezes a separate evaluation of the
current final RelCompat3D model and family-slot rule on the regenerated
4,293-row ReplicaSSG/FROSS artifact. It uses zero ReplicaSSG fit rows and zero
target-specific hyperparameters. Because this test split was inspected during
the earlier runs above, its classification is a cross-dataset benchmark
evaluation on a previously observed target, not prospective confirmation.

Docker command:

```bash
env UID=$(id -u) GID=$(id -g) docker compose \
  -f configs/h001/compose.structured.yaml run --rm external_dataset_transfer
```

The primary routed product improves R/V at K=10 and K=50, but at K=100 changes
R/V only from `.35465/.19674` to `.35465/.19578`. Its dV scene-bootstrap CI is
`[-.00288,.00000]`, so the strict primary gate fails. The frozen route-aware
rank-average diagnostic preserves family composition and reaches
`.38372/.04223`; dR is `+.02907` `[-.00476,.06714]` and dV is `-.15451`
`[-.19182,-.11015]` under the same fixed numerical rule.

The decomposition shows that 86.28% zero source scores make raw products
degenerate, while global rank fusion loses Recall through cross-family
displacement. It also finds a .44186 candidate-recall ceiling, substantial
feature shift, and much stronger compatibility alignment with the external
verifier (AUC .9453) than with exact labels (AUC .6674). All 20 manifest
validations pass. The full per-scene, family, feature, rank, and selection
diagnostics are in `final_method_transfer_v1/evaluation/summary.json`.
