# H002 Train RGA Audit

Last updated: 2026-06-12

## Purpose

`22_train_rga_rows.md`에서 만든 train `RGA-HL/RGA-LH` queue를 바로 claim으로
사용하지 않고, 수동/시각 audit을 위한 compact seed로 줄인다. 목표는 `RGA-LH`가
정말 semantic underconfidence나 annotation coverage signal인지, 아니면 dense relation
or geometry-trivial noise인지 구분할 준비를 하는 것이다.

This stage does not perform manual visual judgment yet.

## Input Artifacts

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/train_hl_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/train_lh_queue.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/train_rga_summary.json
```

Queue counts:

| Queue | Condition | Rows |
| --- | --- | ---: |
| `HL` | high semantic, geometry unsatisfied | 47 |
| `LH` | low semantic, geometry satisfied | 11,588 |

## Tool

Added:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/tools/train_rga_audit.py
```

Command:

```bash
python3 hypothesis/CAND-001/H002_factorized-relation-confidence/tools/train_rga_audit.py
```

Status:

```text
status: ready
```

Output artifacts:

```text
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/audit/train_rga_audit_summary.json
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/audit/audit_seed.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/audit/hl_seed.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/audit/lh_seed.jsonl
hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/train_rga_seed/open3dsg_train_pilot/rga/audit/report.md
```

## Seed Policy

HL은 47행뿐이라 전부 audit seed에 포함했다. LH는 11,588행이므로 아래 정책으로 줄였다.

| Source | Seed Rows |
| --- | ---: |
| all HL rows | 47 |
| LH exact non-proximity high-underconfidence | 20 |
| LH exact proximity high-underconfidence | 10 |
| LH family-match high-underconfidence | 20 |
| LH pair-other support/vertical | 20 |
| LH no-GT support/vertical | 20 |
| LH no-GT proximity dense-check | 10 |
| LH stratified fill | 70 |
| total | 217 |

The seed file includes null manual fields:

```text
object_pair_valid
predicate_visually_plausible
geometry_witness_correct
gt_annotation_missing_or_sparse
ontology_or_granularity_issue
segmentation_or_instance_issue
final_audit_label
notes
```

## Stratification Result

LH label mix:

| Label Status | Proximity | Relative Vertical | Support Contact | Total |
| --- | ---: | ---: | ---: | ---: |
| `exact_match` | 358 | 16 | 266 | 640 |
| `family_match` | 0 | 0 | 506 | 506 |
| `pair_has_other_predicate` | 884 | 457 | 1,116 | 2,457 |
| `no_gt_for_pair` | 3,070 | 2,273 | 2,642 | 7,985 |
| total | 4,312 | 2,746 | 4,530 | 11,588 |

HL label mix:

| Label Status | Relative Vertical | Support Contact | Total |
| --- | ---: | ---: | ---: |
| `pair_has_other_predicate` | 6 | 3 | 9 |
| `no_gt_for_pair` | 12 | 26 | 38 |
| total | 18 | 29 | 47 |

Preliminary read:

| Item | Value |
| --- | ---: |
| LH exact/family-positive rows | 1,146 |
| LH exact/family-positive share | 9.89% |
| LH no-GT rows | 7,985 |
| LH no-GT share | 68.91% |
| LH no-GT proximity rows | 3,070 |
| LH no-GT proximity share among no-GT | 38.45% |
| HL exact/family-positive rows | 0 |

Interpretation:

- `RGA-LH` has a real exact/family-positive subset. This supports keeping the
  bidirectional mismatch hypothesis alive.
- Most `RGA-LH` rows are still no-GT or same-pair-other-predicate rows. These can
  be annotation sparsity, ontology mismatch, multiple valid relations, or false
  positives.
- `proximity` contributes many no-GT LH rows, so dense spatial relation noise is
  a serious risk.
- HL has no exact/family-positive rows in this train pilot queue. Its current
  role is overconfidence/no-GT/pair-other audit, not proof that correct labels are
  often geometry-contradicted.

## Factorized Reliability Explanation

User question:

```text
P(edge reliability | semantic evidence, label evidence, geometry evidence,
coverage, uncertainty)
```

Yes, this posterior combines edge-level information about the same candidate
relation. But it should not be treated as a blind concatenation of every field
followed by one classifier. The safer formulation is a factorized posterior over
a latent edge reliability variable.

Let:

```text
R_e = whether relation edge e is reliable enough to keep/use/promote
S_e = semantic evidence
L_e = label or audit evidence
G_e = geometry evidence
C_e = coverage evidence
U_e = uncertainty evidence
```

Then the factorized form is:

```text
P(R_e = 1 | S_e, L_e, G_e, C_e, U_e)
  ∝ ψ_sem(R_e, S_e)
    ψ_label(R_e, L_e)
    ψ_geom(R_e, G_e)
    ψ_cov(R_e, C_e)
    ψ_unc(R_e, U_e)
```

A practical trainable version is:

```text
logit P(R_e = 1)
  = β0
  + f_sem(S_e)
  + f_label(L_e)
  + f_geom(G_e)
  + f_cov(C_e)
  + f_unc(U_e)
  + f_interact(S_e, G_e, C_e)
```

This is different from simple `semantic_score * p_geom_valid` because it keeps
the evidence roles separate.

### Evidence Blocks

`semantic evidence`:

```text
source relation score
semantic rank in subgraph
predicate rank for object pair
source model id
predicate label/family
```

Role:

- says how much the relation source believes the edge.
- captures semantic plausibility and source confidence.

`label evidence`:

```text
exact_match
family_match
pair_has_other_predicate
no_gt_for_pair
manual audit label, if available
```

Role:

- used for train/evaluation calibration and audit supervision.
- should not be used as an input at deployment unless GT or human audit labels
  are actually available.
- in unlabeled inference, this block is absent, predicted, or replaced by weak
  supervision.

`geometry evidence`:

```text
geometry_status in {satisfied, unsatisfied, uncertain, unsupported, missing}
p_geom_valid
consistency_score
relation-specific residual features
reason_codes
```

Role:

- says whether observed 3D evidence supports the predicate.
- `p_geom_valid` is geometry-only calibrated validity evidence.
- deterministic `geometry_status` is still needed because `p_geom_valid` alone
  can hide uncertainty and coverage issues.

`coverage evidence`:

```text
family supported or unsupported
geometry available
point evidence available
object endpoint geometry available
verification policy/source
```

Role:

- prevents unsupported/missing rows from being treated as negative geometry.
- tells the posterior when to abstain instead of overconfidently accept/reject.

`uncertainty evidence`:

```text
uncertain geometry status
ambiguous residuals
low observation support
semantic rank margin or score ambiguity
conflicting label/geometry states
```

Role:

- reduces overconfident decisions.
- can route the edge to audit instead of keep/delete.

## How Evidence Should Combine

### 1. Semantic-only baseline

```text
P(R_e = 1) = calib_semantic(score_or_rank)
```

This tests whether source confidence alone explains reliability.

### 2. Geometry-only baseline

```text
P(R_e = 1) = p_geom_valid
```

This tests whether geometry alone explains reliability. It cannot distinguish
semantic underconfidence from dense geometry candidates.

### 3. Semantic + geometry baseline

```text
logit P(R_e = 1)
  = β0 + β_s logit(p_sem) + β_g logit(p_geom_valid)
```

or a product/reranking form:

```text
score = semantic_score * p_geom_valid
```

This is close to the earlier H001-style combination.

### 4. Factorized reliability posterior

```text
logit P(R_e = 1)
  = β0
  + β_s f_sem(rank, score, source)
  + β_g f_geom(status, p_geom_valid, residuals)
  + β_l f_label(match_or_audit_state)
  + β_c f_coverage(available, unsupported, missing)
  + β_u f_uncertainty(uncertain, conflict)
  + β_sg f_interaction(semantic_geometry_disagreement)
```

Key behavior:

- high semantic + unsatisfied geometry should reduce reliability or trigger
  audit.
- low semantic + satisfied geometry should not automatically promote the edge;
  it should become an underconfidence or annotation-coverage candidate.
- exact/family label evidence can teach the model which mismatch cases are
  reliable, but only in train/audit contexts.
- unsupported geometry should not be scored as invalid; coverage should cause
  abstention or lower confidence.
- uncertainty should be preserved as uncertainty, not silently folded into valid
  or invalid.

## Current Boundary

Established:

- Train HL/LH queues are stratified.
- A compact audit seed exists.
- The factorized reliability posterior has a clear evidence decomposition.

Not established:

- Manual visual/mesh audit labels.
- Factor weights or calibrated posterior.
- Whether LH no-GT rows are mostly missed relations or geometry-trivial noise.
- Paper-level held-out evidence.

## Next TODO

Next document:

```text
24_train_manual_audit.md
```

Required next work:

- fill a subset of `audit_seed.jsonl` manual fields.
- separate `true_underconfidence`, `annotation_sparsity`, `ontology_mismatch`,
  `object_pair_error`, `geometry_artifact`, and `dense_relation_noise`.
- only after this, define a train-only factorized reliability baseline contract.
