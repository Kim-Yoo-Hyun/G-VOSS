# H001 First-Pass Manuscript Draft

Last updated: 2026-05-21 KST

Status: `first_pass_reviewed_source_lock_next`

This is a first-pass manuscript prose draft derived from `paper/outline.md`.
It is not camera-ready text. The purpose is to make the paper-body logic
readable end to end before figure generation, caption compression, or final
bibliography formatting.

Citation placeholders such as `[3DSSG]`, `[VL-SAT]`, and `[Open3DSG]` should be
replaced with final BibTeX keys later. Current placeholders are
`[3DSSG]`, `[SGGpoint]`, `[SMKA]`, `[VL-SAT]`, `[SGRec3D]`, `[Open3DSG]`,
`[CCL-3DSGG]`, `[FROSS]`, `[OpenFunGraph]`, `[OctreeGraph]`, `[FirePlace]`,
`[GREAT]`, `[SGAligner]`, and `[SG-PGM]`.

## 2. Related Work

### 2.1 3D Scene Graph Relation Prediction

3D Scene Graphs represent indoor scenes as structured collections of objects
and relations, enabling downstream spatial reasoning beyond isolated object
recognition. Early 3DSSG work established the 3RScan/3DSSG setting and made
predicate recall a standard way to evaluate relation prediction in reconstructed
3D scenes [3DSSG]. Subsequent relation-prediction methods model relation edges
more explicitly, using edge-oriented graph reasoning, point-cloud features,
multimodal cues, and spatial knowledge to improve closed-set predicate
prediction [SGGpoint, SMKA, VL-SAT, SGRec3D].

These works show that 3D geometry is already important for relation prediction.
Our work does not claim that existing 3DSSG methods ignore geometry. Instead,
we focus on a reliability gap that remains after a relation predictor has
produced scored predicate candidates: a high semantic relation score is not
necessarily a calibrated estimate that the relation is physically consistent
for the same object pair in 3D. H001 therefore treats existing predictors as
relation sources and studies whether their ranked relation rows can be
evaluated and re-ranked by calibrated geometry consistency.

### 2.2 Open-Vocabulary 3D Scene Graphs And VLM-Based Scene Understanding

Recent work extends 3D scene graphs toward open-vocabulary objects, open-set
relations, VLM-derived features, online graph generation, and functional
relations [Open3DSG, CCL-3DSGG, FROSS, OpenFunGraph, OctreeGraph]. This line is
important because relation labels increasingly come from visual-language priors
or open-vocabulary semantic sources rather than only from fixed closed-set
classifiers. It also raises the reliability requirement: when relation edges are
used as language-facing scene representations, plausible text labels must still
refer to object pairs that satisfy the corresponding spatial relation in the
scene.

H001 is not positioned as a broad open-vocabulary 3D scene graph generation
method. We use VL-SAT as the primary reproduced relation source and Open3DSG as
second-source evidence within measured geometry-checkable relation families.
The claim is scoped to relation reliability for `support_contact`, `proximity`,
and `relative_vertical`, not to general open-vocabulary graph generation.
Qwen-VL remains an optional modern semantic-source extension unless it receives
the same Docker, denominator, metric, and audit treatment as the main evidence.

### 2.3 Geometry-Aware Relation Reasoning And Semantic-Geometric Fusion

A broad set of 3D reasoning methods already uses geometry: edge features,
support/contact patterns, affordance geometry, metric distance, topology, and
semantic-geometric fusion [SGGpoint, SMKA, FirePlace, GREAT, SG-PGM]. Scene
graph alignment and registration methods further demonstrate that graph
structure and geometric consistency matter when scene graphs are reused for
matching, alignment, and downstream geometric tasks [SGAligner, SG-PGM].

The gap addressed here is more specific. We ask whether relation-level
geometric evidence is identity-preserving, calibrated, and reported jointly
with recall. A generic geometry feature or distance prior is not enough: the
geometry evidence must be joined to the correct subject-object instance pair,
mapped to the correct relation family, and evaluated as a reliability signal
with explicit operating points. This is why H001 includes geometry-only,
distance-only, shuffled-geometry, and wrong-pair controls.

### 2.4 Reliability And Calibration For Structured Relation Outputs

Standard relation prediction metrics such as R@K measure whether the correct
predicate appears among top-ranked predictions, but they do not directly ask
whether the predicted relation is physically valid in the reconstructed 3D
scene. For relation edges that support downstream reasoning, this is a
reliability problem: the score attached to a relation should not only indicate
semantic plausibility, but also reflect whether the relation is consistent with
object-pair geometry.

H001 instantiates this reliability view for geometry-checkable 3DSSG relation
families. The framework standardizes prediction rows, joins 3D geometry
evidence for the same object pair, estimates a calibrated probability
`p_geom_valid`, and reports recall and violation together. This makes the
tradeoff explicit: a method that removes all violations by pruning nearly all
relations is not useful, and a method that preserves recall while leaving
physically inconsistent relations highly ranked is not reliable.

## 3. Problem Formulation

Let a relation source produce a set of candidate relation rows for a 3D scene.
Each row is written as

```text
r_i = (scan_i, subgraph_i, s_i, o_i, p_i, a_i, score_sem_i),
```

where `s_i` and `o_i` are subject and object instance identifiers, `p_i` is the
predicate label, `a_i` is the mapped predicate family, and `score_sem_i` is the
source semantic confidence. The tuple `(scan_i, subgraph_i, s_i, o_i)` is the
identity key used to preserve the object pair across prediction, geometry, and
ground-truth joins.

For each prediction row, we join object-pair geometry evidence

```text
g_i = G(scan_i, subgraph_i, s_i, o_i).
```

The evidence can include OBB features, point/local contact evidence, distance,
vertical ordering, support/contact subtype information, and missing-evidence
reason codes. H001 evaluates only geometry-checkable relation families:

```text
A = {support_contact, proximity, relative_vertical}.
```

Rows outside these families are preserved in exports but excluded from the H001
violation claim. This prevents the method from pretending that all semantic
relations are reducible to geometry rules.

The geometry verifier assigns a row-level status

```text
v_i in {satisfied, uncertain, violated}
```

and the calibrator estimates

```text
p_geom_valid_i = P(v_i != violated | g_i, a_i).
```

The score is a calibrated reliability signal, not a hard proof of correctness.
For this reason, the paper reports probabilistic, rule-verified, and
family-specific operating points separately.

The main recall metric is exact predicate-label `R@K` over the fixed in-scope
ground-truth denominator. Family grouping defines the geometry-checkable
reliability scope and violation analysis; it does not relax predicate-label
matching. `Violation@K` is the fraction of top-K in-scope predicted rows whose
joined geometry is judged `violated`. We report recall retention and violation
reduction together so that violation reduction cannot be interpreted without its
recall tradeoff. This denominator and metric scope correspond to the locked
scope reported in Tables 1 and 5, with Open3DSG-specific coverage reported in
Table 6.

## 4. Method

H001 is a calibrated geometry-consistency evaluation and re-ranking framework
for 3D scene graph relation predictions. It is not a replacement relation
predictor and not a standalone verifier script. The framework is built around
four design requirements: preserve relation-row identity, join explicit
object-pair geometry, calibrate geometry validity, and evaluate recall and
violation jointly.

### 4.1 Relation-Row Standardization

Different relation sources expose predictions in different formats. We convert
each source output into a shared row contract:

```text
(scan_id, subgraph_id, subject_id, object_id, predicate, family, score_sem, source).
```

This row is the unit of comparison across VL-SAT, Open3DSG, controls, and
future optional sources. The standardized row keeps the semantic score from the
source model but adds the fields needed for identity-preserving geometry joins
and denominator-stable evaluation.

### 4.2 Identity-Preserving Geometry Join

Geometry is joined by `(scan_id, subgraph_id, subject_id, object_id)`, not by
category names or unordered object-pair statistics. This matters because the
same predicate can be plausible for many object categories while being false
for a particular instance pair. The wrong-pair and shuffled-geometry controls
directly test this design choice by breaking or perturbing object-pair identity
while preserving parts of the geometry distribution.

### 4.3 Family-Specific Geometry Checks

H001 uses relation-family-specific checks for `support_contact`, `proximity`,
and `relative_vertical`. For support/contact, the evidence includes point/local
contact, vertical support, OBB overlap, and support subtypes. For proximity, the
evidence includes object distance and pair scale. For relative vertical
relations, the evidence includes centroid and extent ordering along the vertical
axis. The verifier returns `violated` only when the evidence is strong enough;
otherwise ambiguous or weak geometry can be marked `uncertain`.

### 4.4 Calibrated Geometry Validity And Re-Ranking

The probabilistic operating point uses a frozen calibrator:

```text
p_geom_valid_i = C_a(phi(g_i)),
```

where `phi(g_i)` is the geometry feature vector and `C_a` is either the pooled
or family-specific calibrator trained on `train_dev_calib` positives and
counterfactual negatives. The main probabilistic re-ranking score is

```text
score_prob_i = score_sem_i * p_geom_valid_i.
```

We report four main operating points. `semantic_only` ranks by the source
semantic score and serves as the reproduced source baseline.
`probabilistic_recalibrated` ranks by the product of semantic confidence and
calibrated geometry validity. `rule_verified_point_subtype` removes hard
violations before ranking and is reported as a zero-violation diagnostic.
`family_specific_p_geom_valid` uses family-specific calibration and provides a
stricter violation-first operating point.

### 4.5 Controls

The control conditions test whether the result can be explained by simpler
signals. Geometry-only ranking tests whether semantic confidence remains
necessary. Distance-only ranking tests whether a generic spatial heuristic
explains the result. Shuffled-geometry and wrong-pair-geometry controls test
whether relation-level object-pair identity is necessary. If these controls
perform worse than the calibrated setting, the result supports the framework
design rather than a generic "add geometry" explanation.

## 5. Experimental Setup

The primary source is the reproduced VL-SAT closed-set relation prediction
setting on the fixed H001 held-out scope. The scope contains 127 scans, 388
subgraphs, 25,916 directed pairs, 673,816 prediction rows, 7,505 ground-truth
rows, and 2,545 in-scope GT relation instances across the measured
geometry-checkable families. These counts are the fixed denominator for the
VL-SAT result in Table 1 and the claim-boundary accounting in Table 5.

Open3DSG provides second-source evidence within the same H001-family metric
scope. The Open3DSG result is reported as a Docker-reproduced averaged-BLIP
variant. The selected checkpoint is `epoch=13-step=13104.ckpt`, chosen by
train-dev validation loss before H001 held-out inspection. The Open3DSG runtime
uses a filtered preprocessed-ready train split of 3,744/3,852 subgraphs, a
train-dev validation split of 156/160 subgraphs, and an H001 covered loadable
evaluation scope of 377/388 contexts with `validation_missing_preprocessed:11`
reported as a caveat. These caveats must remain visible in Table 6 and in the
main text wherever Open3DSG is used as second-source evidence.

All paper-body experiment results are generated through Docker under
`experiments/H001_geom_reliability/`. The paper reports exact-label `R@50` and
`R@100`, `Violation@50` and `Violation@100`, GT-positive/counterfactual
verifier evaluation, nontriviality controls, Open3DSG second-source metrics,
and qualitative failure analysis. Host-only outputs are not promoted to paper
evidence.

## 6. Results And Discussion

The central question is whether calibrated geometry consistency reduces
physically inconsistent relation predictions without collapsing recall. On
VL-SAT, Table 1 shows that the reproduced `semantic_only` ranking reaches R@50/R@100 of
0.9599/0.9894 with Violation@50/@100 of 0.0247/0.0469. The main
`probabilistic_recalibrated` setting improves R@50/R@100 to 0.9642/0.9921 and
reduces Violation@100 to 0.0391. This supports the intended recall-first use
case: calibrated geometry validity can reduce violations while preserving, and
slightly improving, exact-label recall.

The stricter `family_specific_p_geom_valid` setting reaches R@50/R@100 of
0.9619/0.9914 and Violation@50/@100 of 0.0204/0.0310. This provides a stronger
violation-first operating point. The `rule_verified_point_subtype` setting
achieves zero measured violations while keeping R@50/R@100 at 0.9587/0.9890,
but we treat it as a diagnostic rather than the default method because hard
filtering exposes one end of the reliability-recall tradeoff.

Table 2 reports the nontriviality controls. They show that the effect is not explained by geometry
alone or by a generic distance prior. Geometry-only ranking falls to R@50/R@100
of 0.2028/0.5049 and has higher violations than the main calibrated setting.
Distance-only ranking also underperforms, reaching R@50/R@100 of 0.3835/0.5642.
Shuffled geometry and wrong-pair geometry preserve more of the source signal but
still degrade both recall and violation behavior relative to calibrated
identity-preserving joins. These controls support the design requirement that
geometry evidence must be joined to the correct object pair and calibrated as a
relation-level reliability signal.

Table 3 tests the geometry signal independently from
prediction re-ranking. GT-positive rows remain nonviolated at a rate of 0.9972,
while GT-derived counterfactual negatives are nonsatisfied at a rate of 0.9694.
The calibrated `p_geom_valid` score separates these groups with AUROC/AUPRC of
0.9779/0.9737 and Brier score 0.0538. This supports the use of `p_geom_valid`
as a reliability signal while still leaving room for residual calibration risk.

Table 6 reports Open3DSG as second-source evidence rather than a broad open-vocabulary
SOTA claim. Under the measured H001-family scope, Open3DSG `semantic_only`
ranking reaches R@50/R@100 of 0.3945/0.4963 with Violation@50/@100 of
0.1326/0.1195. The `probabilistic_recalibrated` setting reduces violations to
0.0575/0.0803 while shifting recall to 0.3843/0.5580. The rule-verified setting
again gives a zero-violation diagnostic, and the family-specific setting reaches
R@50/R@100 of 0.4530/0.5984 with Violation@50/@100 of 0.0228/0.0311. These
results support a cross-source relation-reliability claim within measured H001
families, with the averaged-BLIP, filtered-split, covered-scope, exact-label
denominator, and residual-calibration caveats kept explicit.

The qualitative failure analysis explains why the metric changes occur and
provides candidate source rows for Figure 3.
Open3DSG failure rows produce 57,736 real analysis rows with zero validation
errors, and the inspected 36-case qualitative queue shows that 23 cases are
demoted by geometry-aware re-ranking. The cases are family-structured:
proximity failures often involve distance contradictions, relative-vertical
failures involve vertical-order contradictions, and support/contact failures
expose float-gap or support-plane contradictions. This supports the failure
mechanism: a relation can be semantically plausible from object categories but
physically inconsistent for the actual object pair.

The same qualitative analysis also exposes a limitation. Ten of the 36 sampled
rule-violated cases still have `p_geom_valid > 0.9`. This means the calibrated
score should not be interpreted as a hard validity label. It also justifies why
the paper reports probabilistic, rule-verified, and family-specific variants
separately rather than collapsing them into a single "geometry-corrected"
output.

## 7. Limitations

The current study is intentionally scoped to geometry-checkable relation
families. Relations whose correctness depends primarily on functional, social,
affordance, or language-pragmatic context are outside the H001 metric claim.
The evaluation also uses closed-set/GT-object relation rows and exact
predicate-label recall, so the results should be read as relation-reliability
evidence rather than full open-vocabulary scene graph generation performance.

The Open3DSG experiment is a reproduced averaged-BLIP variant with explicit
filtering and coverage caveats. The checkpoint is selected by train-dev
validation loss before H001 held-out inspection, the training and validation
splits are filtered to preprocessed-ready subgraphs, and H001 evaluation covers
the loadable Open3DSG scope. These choices do not invalidate the scoped
reliability result, but they prevent claims of exact non-averaged Open3DSG
reproduction or broad open-vocabulary SOTA.

The visual and qualitative evidence should also be read with the correct scope.
The reduced visual sanity check and Open3DSG qualitative case inspection are
reviewer-defense and failure-mechanism evidence, not large-scale independent
human audits. They help identify failure modes and residual calibration risk,
but the quantitative claim remains tied to the fixed metric denominator and
Docker-generated tables.

Finally, `p_geom_valid` is a calibrated reliability score, not a proof of
physical correctness. Residual high-confidence but rule-violated cases motivate
future work on broader predicate families, stronger calibration, larger visual
audits, modern VLM relation sources, and downstream tasks where relation
reliability can be tested through planning, navigation, alignment, or embodied
reasoning.

## Draft TODO

- Replace citation placeholders with final BibTeX keys.
- Decide whether Section 5 should remain in this draft or be merged into a
  shorter Experimental Setup section after venue page limits are known.
- Source-lock Figure 1-3 before drawing: Figure 1 from the method contract,
  Figure 2 from Table 1 plus optional Table 6 cross-source overlay, and Figure 3
  from traceable qualitative case rows.
- Keep Table 6/Open3DSG caveats visible until the paper-body logic is stable.

## Draft Review

Status: `passed_claim_scope_with_source_lock_followup`

Reviewed on: 2026-05-21 KST

Review result:

| item | status | decision |
| --- | --- | --- |
| Claim scope | pass | The draft stays within measured geometry-checkable relation reliability and does not claim broad open-vocabulary 3DSSG generation improvement. |
| Method framing | pass | The method is described as a calibrated geometry-consistency evaluation and re-ranking framework, not as a standalone verifier script. |
| Open3DSG caveats | pass | The averaged-BLIP variant, filtered train/dev split, covered loadable scope, `validation_missing_preprocessed:11`, exact-label denominator, and residual calibration risk remain explicit. |
| Qwen-VL boundary | pass | Qwen-VL remains optional extension evidence and is not used as a main metric result. |
| Citation placeholders | needs follow-up | Related Work still uses placeholder citation keys and needs final BibTeX replacement. |
| Evidence links | patched | Results prose now points to Table 1, Table 2, Table 3, Table 5, and Table 6. |
| Figure readiness | source-lock needed | Figure claims are ready conceptually, but source rows/assets must be fixed before drawing final figures. |

Evidence map:

| draft claim | evidence source |
| --- | --- |
| VL-SAT recall/violation operating points | `experiments/H001_geom_reliability/tables/table1_main_prediction.md` |
| Geometry-only, distance-only, shuffled, wrong-pair controls | `experiments/H001_geom_reliability/tables/table2_controls.md` |
| GT-positive/counterfactual verifier support | `experiments/H001_geom_reliability/tables/table3_gt_verifier.md` |
| Claim boundary and non-claims | `experiments/H001_geom_reliability/tables/table5_claim_boundary.md` |
| Open3DSG second-source metrics | `experiments/H001_geom_reliability/tables/table6_cross_source_status.md` and `experiments/H001_geom_reliability/sources/open3dsg/metrics/metrics.json` |
| Open3DSG caveat wording | `experiments/H001_geom_reliability/sources/open3dsg/paper_caveats/report.md` |
| Failure mechanism and residual calibration risk | `experiments/H001_geom_reliability/sources/open3dsg/failure_cases/inspection.md` |
| Docker reproducibility and artifact portability | `docs/reproducibility.md` |

Figure source-lock decision before drawing:

- Figure 1 should be a method/framework diagram sourced from Sections 3-4,
  `hypothesis/CAND-001/H001_geometry-grounded-verification/02_method.md`, and
  `experiments/H001_geom_reliability/manifest.lock.json`.
- Figure 2 should be a recall-violation tradeoff plot. The safest first version
  uses Table 1 only; a cross-source variant can add Table 6 if the caption keeps
  Open3DSG caveats visible.
- Figure 3 should use traceable qualitative rows from
  `experiments/H001_geom_reliability/sources/open3dsg/failure_cases/inspection.md`;
  if VL-SAT visual spot-check examples are mixed in, the caption must separate
  visual sanity evidence from Open3DSG deterministic qualitative inspection.
