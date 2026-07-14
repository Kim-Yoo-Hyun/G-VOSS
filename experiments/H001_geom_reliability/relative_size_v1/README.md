# Relative-Size Extension

Status: Docker evaluation complete on 2026-07-13 and promoted as a bounded
secondary scope extension. The active paper uses one main-text scope sentence
and the full supplement result; it does not use this family as core learned-
method evidence.

## Frozen Contract

- family: `relative_size` with `bigger than` / `smaller than`;
- firewall: 1,061 train / 117 internal-dev / 157 official final-validation
  scans, with pairwise overlap zero;
- compatibility input: predicate sign `T`, source-independent point geometry
  `G`, and signed `T x G` interactions;
- forbidden compatibility inputs: source score, source rank, object class, and
  any final-validation label;
- main point evidence: alternating vertex subset A with p05--p95 robust
  extents;
- independent verifier: disjoint vertex subset B with p02--p98 extents;
- annotation OBB: fixed-rule baseline only, never an input to learned `C_e`;
- controls: wrong predicate, endpoint swap plus inverse predicate, common-scale
  invariance, wrong pair, shuffled geometry, point-rule only, and OBB-rule only;
- evaluation: VL-SAT, Open3DSG, and SGFN at K = `{5,10,20,50,100}`, with
  K=100 primary and 1,000 shared 548-context paired bootstrap resamples.

The accepted inverse-equivariant model and score were locked before official
final-validation evaluation:

- model SHA-256: `bfb6068307b9743a0f852a1082e4fa40c50ef15094601f930f1e431cbdade015`;
- score-definition SHA-256:
  `d63bd805b0866118f0bb0fb510913b68270e543fe1923ed9b67d47496e0fb0c7`;
- lock-file SHA-256:
  `473dd5b723dd90f47f44491b7e7d13ff96a3d3bc779153803a13df2aa36d8585`.

## Fit And Controls

The train-only fit contains 3,244 rows; internal-dev contains 376 diagnostic
rows. Internal-dev AUROC is `0.99740`. Wrong-predicate accuracy is reflected by
a `0.96809` correct-over-inverse win rate. Endpoint-swap inverse-equivariance
and common-scale invariance have maximum absolute numerical error
`2.22e-16`. All frozen controls pass.

## Official Validation Result

The size-family exact-label denominator is 170. Adding it to the existing
3,972-row denominator gives a four-family denominator of 4,142 over all 548
contexts. At K=100:

| source | size dR | size dV (95% CI) | four-family dR (95% CI) | four-family dV (95% CI) |
| --- | ---: | ---: | ---: | ---: |
| VL-SAT | `0.0000` | `-0.10253` `[-0.10635,-0.09878]` | `+0.00483` `[+0.00198,+0.00803]` | `-0.02393` `[-0.02610,-0.02185]` |
| Open3DSG | `0.0000` | `-0.12735` `[-0.13826,-0.11673]` | `+0.06977` `[+0.04777,+0.09346]` | `-0.10402` `[-0.10900,-0.09973]` |
| SGFN | `0.0000` | `-0.05925` `[-0.06157,-0.05720]` | `+0.02559` `[+0.01987,+0.03174]` | `-0.03590` `[-0.03808,-0.03362]` |

The learned product therefore passes the frozen within-family and global
four-family K=100 gate for every source. Its size-family Recall is also
preserved or improved at every evaluated lower K.

Rank-average is not a second universally passing four-family instantiation: it
fails the global Recall guard on VL-SAT and narrowly fails the strict CI rule
on SGFN. Do not extend the existing two-instantiation claim to the four-family
setting.

## Interpretation Boundary

The extension passes a framework-scope gate, not a formula-superiority gate.
The learned product does not strictly lower Violation more than the fixed
point-rule baseline: learned-minus-point-rule V at K=100 is `+0.00318` for
VL-SAT, `+0.00005` for Open3DSG, and `+0.00367` for SGFN. It beats the OBB rule
for Open3DSG and SGFN, while the VL-SAT difference is unresolved.

Construct circularity is reduced but not eliminated. The model and verifier
use disjoint point subsets and different robust extent estimators, so they do
not reuse an exact rule. However, both still measure the same segmented point
cloud. On 170 final-validation GT rows, the independent verifier reports 162
satisfied, 2 violated, 2 uncertain, and 4 unsupported; its binary agreement is
`1.0` with both the point rule and annotation-OBB rule. This makes
`relative_size` a useful, geometry-identifiable scope extension, but also a
rule-easy family. Do not claim learned compatibility, fusion, or construct
validity superiority from this experiment.

## Artifacts And Reproduction

- protocol: `protocol.json`;
- fit/model diagnostics: `fit/`;
- pre-evaluation lock: `lock.json`;
- metrics, paired CIs, family composition, construct audit: `evaluation/`;
- implementation: `src/geocalib/run_relative_size_extension.py`;
- Docker services: `relative_size_freeze`, `relative_size_fit`,
  `relative_size_lock`, and `relative_size_evaluate` in
  `configs/h001/compose.yaml`.

Run the four Docker services in that order. Existing nonempty outputs are
guarded; a scientific rerun should use a new output root rather than overwrite
the locked artifact.
