# H001 Paper Preview

Last updated: 2026-07-15 KST

This file is the current manuscript handoff for H001. Historical experiment
chronology belongs in the experiment reports and archive, not here.

## Current Paper

- Title: `Beyond Semantic Confidence: Relation-Algebra-Constrained Geometric
  Compatibility for 3D Scene Graph Relations`
- Method name: `RelCompat3D`
- Venue workspace: `paper/aaai/`
- Scope: `proximity`, `relative_vertical`, and `support_contact` relations on
  one shared 3DSSG/3RScan target.
- Evidence: VL-SAT, Open3DSG, and SGFN relation predictors evaluated at
  K=`{5,10,20,50,100}`. K=50 is a descriptive mid-curve reference rather than
  a separately registered endpoint; all K values remain in the main table.

The paper uses six top-level sections: Introduction, Related Work, Method,
Experiments, Discussion and Limitations, and Conclusion. Problem Setup is
inside Method; setup and results are grouped under Experiments. The narrative
order is failure, structural cause, factor isolation, method, evidence, and
then limitations.

## Method and Claim

Each candidate is factorized into predicate/family semantics `T_e`, raw
predicate-independent same-pair geometry `G_e`, source confidence `Z_e`, and a
bounded compatibility score
`C_e=sigmoid(h_a(Phi(T_e,G_e)))`. Neither source score nor predictor identity
is an input to `C_e`. The score targets constructed positive/counterfactual
ordering; it is not a probability of physical validity.

Linked positive--counterfactual pairs train the compatibility model, and exact
relation-algebra projection enforces close-by swap invariance and vertical
inverse equivariance. The primary decision rule is a family-slot applicability
route:

- proximity and vertical candidates are ordered by `Z_e C_e` within the source
  family slots;
- support/contact candidates retain their source ordering;
- the source-ranked family-slot sequence is preserved at every K.

This route preserves support/contact selections and global family composition
exactly while applying compatibility only where the frozen algebraic controls
are valid. The unrestricted product is an ablation, not the primary method.

Allowed claim:

> RelCompat3D assesses geometric compatibility for fixed relation predictions
> with a fitted layer whose inputs exclude predictor identity and source
> score. It separates source confidence from predicate--geometry compatibility and
> improves the aggregate Recall--verifier-Violation operating point across
> three predictors on a shared 3DSSG target.

Blocked claims include universal formula superiority, best-rescorer
performance, cross-dataset generalization, independent human physical
validity, and solved support/contact compatibility.

## K=50 Reference Results

| Source | Source R/V | Routed RelCompat3D R/V | Unrestricted product R/V |
| --- | ---: | ---: | ---: |
| VL-SAT | .9272/.0268 | .9277/.0197 | .9293/.0203 |
| Open3DSG public/full target | .4043/.1387 | .4418/.0342 | .4655/.0265 |
| SGFN | .7402/.0385 | .7450/.0263 | .7706/.0256 |

At K=50, routed scan-cluster intervals show lower verifier Violation for all
three predictors, positive Recall changes for Open3DSG and SGFN, and no
detectable Recall change for near-ceiling VL-SAT. Across K=10--50, every routed
Recall point estimate is preserved or improved and every V point estimate is
lower. The analysis resamples 157 scans and carries all contexts of each
sampled scan; paired context resampling preserves the same direction as a
sensitivity. K=5 and K=100 remain in the main table as boundary conditions.

The supplement additionally reports the method without target-specific
refitting on ReplicaSSG/FROSS:
paired joint gains at K=10 and K=50, with K=100 saturation caused by heavily
quantized source scores. This is a transfer stress test, not established
dataset-level generalization.

Open3DSG is evaluated on the official 548-context/3,972-GT universe; contexts
without public-pipeline candidates are retained as empty candidate sets.
Coverage variants are reported only as supplement sensitivities.

## Strong Comparisons and Controls

- Rank-average and RRF are fixed rank-fusion comparators.
- Pooled product tests whether family conditioning is necessary.
- Hard filtering is a zero-violation diagnostic that may return fewer than K.
- Wrong-predicate, wrong-pair, shuffled-geometry, endpoint-swap,
  distance-only, and compatibility-only controls are reported at K=50/100.
- A frozen train-only, source-score-excluded nonlinear model receives the same
  constructed supervision and uses the same family-slot route. It does not
  jointly dominate the product: at Open3DSG K=100 it improves Recall by
  `.0297` while increasing Violation by `.0047`.
- A separate SGFN-specific exact-label nonlinear rescorer is a stronger-label
  comparator, not a supervision-matched replacement.

These comparisons support the factorized framework and falsification contract,
not a uniquely optimal fusion equation.

## Construct-Validity Audit Boundary

The 488-item Codex proxy reference and all required visual adjudications are
complete. Reviewers A, B, and C checked every completed row and recorded
`confirm` with zero revisions at `2026-07-14T22:49:11+09:00`. The validated
result is therefore a **reviewer-verified LLM annotation reference**. It is not
three independent blank-sheet human annotations and does not convert
verifier-derived V into Human V@K. It remains excluded from the active
submission and is documented only in `paper/paper_nonsub/`.

Independent human construct validation remains optional: two independent
first-pass annotators must label the blank 488-item queue, followed by a third
blinded adjudicator for mandatory disagreements/low-confidence/ambiguous rows.

## Canonical Files

- research state: `summary.md`
- task board: `TODO.md`
- paper rules: `docs/paper.md`
- recovery/run commands: `docs/reproducibility.md`
- experiment entry: `experiments/H001_geom_reliability/README.md`
- primary routing: `experiments/H001_geom_reliability/support_contact_routing_v1/`
- matched nonlinear comparison:
  `experiments/H001_geom_reliability/supervision_matched_nonlinear_v1/`
- Open3DSG route sensitivity:
  `experiments/H001_geom_reliability/open3dsg_official_route_v1/`
- routed public/full ablations:
  `experiments/H001_geom_reliability/structured_ablation_v1/routed_public_full_evaluation/`
- compact results: `results/h001_geom_reliability/report.md`
- manuscript and canonical PDFs: `paper/aaai/`
- previous verified anonymous upload bundle (stale after current revision):
  `release/h001_aaai27_openreview_20260714_233534/`
- reviewer-verified LLM analysis: `paper/paper_nonsub/`

The only remaining submission-side decisions are author/OpenReview metadata,
the public code license and post-acceptance artifact URL, and whether to run a
separate independent-human alignment study.
