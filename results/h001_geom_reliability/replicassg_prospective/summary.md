# ReplicaSSG / FROSS prospective confirmation

Status: `dataset_level_prospective_evaluation_ready`; all 24 provenance and
firewall validations pass. The target is the 11-scene official ReplicaSSG test
split, and the untouched semantic source is the official VisualGenome-trained
FROSS RT-DETR-EGTR release. ReplicaSSG validation scenes were not used.

The pre-registered dataset-level K=100 framework gate fails. This result must
not be used to claim dataset-level transfer of the joint recall/violation gate.

| method | Recall@100 | delta Recall (paired 95% CI) | V@100 | delta V (paired 95% CI) | primary gate |
| --- | ---: | --- | ---: | --- | --- |
| semantic only | 0.36047 | -- | 0.19674 | -- | reference |
| calibrated family product | 0.36047 | 0.00000 [0.00000, 0.00000] | 0.19674 | 0.00000 [0.00000, 0.00000] | fail: no strict V gain |
| rank-average family | 0.33140 | -0.02907 [-0.07407, 0.01333] | 0.03839 | -0.15835 [-0.19292, -0.12190] | fail: recall guardrail |
| RRF, c=60 | 0.33140 | -0.02907 [-0.05786, -0.00510] | 0.05950 | -0.13724 [-0.16820, -0.10452] | diagnostic |

All four factor products (`M_T`, true `M_G`, `M_add`, and `M_int`) also match
semantic-only exactly at K=100. No condition is promoted from this target.

The product has positive lower-K evidence, but K was frozen with 100 as the
primary endpoint and the complete grid must remain visible:

| K | semantic R / V | product R / V | product delta R (paired 95% CI) | product delta V (paired 95% CI) |
| ---: | ---: | ---: | --- | --- |
| 5 | 0.04651 / 0.07273 | 0.06395 / 0.01818 | +0.01744 [-0.02857, 0.07627] | -0.05455 [-0.14545, 0.00000] |
| 10 | 0.07558 / 0.08182 | 0.13953 / 0.03636 | +0.06395 [0.00543, 0.13044] | -0.04545 [-0.09091, 0.00000] |
| 20 | 0.14535 / 0.11818 | 0.21512 / 0.03182 | +0.06977 [-0.00781, 0.17244] | -0.08636 [-0.15455, -0.02727] |
| 50 | 0.25581 / 0.13100 | 0.31395 / 0.09225 | +0.05814 [0.02255, 0.09723] | -0.03875 [-0.07493, -0.01292] |
| 100 | 0.36047 / 0.19674 | 0.36047 / 0.19674 | 0.00000 [0.00000, 0.00000] | 0.00000 [0.00000, 0.00000] |

Family analysis explains the rank-average tradeoff. At within-family K=100,
rank-average changes proximity R/V from `0.41830/0.05382` to
`0.43137/0.03875`, and relative-vertical R/V from `0.21053/0.40377` to
`0.21053/0.10317`. In the actual global top-100 composition, however, it loses
five proximity GT hits while retaining all four recovered vertical hits. The
large violation reduction therefore does not satisfy the frozen aggregate
recall guardrail.

Controls remain limitations rather than promotion evidence. The family model's
vertical inverse-equivariance error is small (`0.00049` mean), and its exact-GT
correct-minus-wrong-pair compatibility is positive (`+0.41370`, scene-bootstrap
95% CI `[+0.25892,+0.53936]`). However, close-by endpoint-swap error is nonzero
(`0.01908` mean), and the wrong-T control has only five exact-GT candidate rows
across two scenes with a CI crossing zero. Support/contact was correctly not
run because ReplicaSSG `on`/`against` are not exact mappings to H001 subtypes.

The official exact-label denominator is 172 (`near`: 153, `above`: 9,
`under`: 10). The adapter emits 4,290 candidates from 1,430 matched directed
FROSS edges, and geometry preserves 4,290/4,290 rows. Bootstrap uses the same
1,000 scene resamples for all methods, seed `20260711`.

The first valid scene shard exposed an execution-only stdin attachment issue:
Docker consumed the scan loop input and triggered an early merge. The frozen
runner was not changed; `scripts/no_stdin_bin/docker` redirects only Docker
stdin, all shards are revalidated before reuse, and the failed logs are
preserved. This operational erratum does not change frames, source settings,
scores, mappings, or evaluation.

Authoritative full output remains under
`experiments/H001_geom_reliability/sources/replicassg/evaluation/`; this compact
artifact preserves every frozen method/K result and the source/protocol hash
chain in `summary.json`.
