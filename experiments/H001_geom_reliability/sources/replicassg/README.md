# ReplicaSSG Prospective Evaluation

This source root owns H001's dataset-level prospective evaluation on the
official ReplicaSSG test split. It is separate from all 3RScan/3DSSG targets;
whether it confirms the frozen claim is determined only by the pre-registered
gate.

The frozen target uses the 11 official ReplicaSSG test scenes and the official
FROSS Visual-Genome-trained RT-DETR-EGTR source with predicted 2D scene graphs
and ground-truth camera poses. ReplicaSSG validation scenes are not used for
method, mapping, threshold, or score selection.

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
`results/h001_geom_reliability/replicassg_prospective/`. Full ignored runtime
output remains under this source root. This result is valid untouched
dataset/source prospective evidence, but it is negative evidence for the
pre-registered joint-gate claim.
