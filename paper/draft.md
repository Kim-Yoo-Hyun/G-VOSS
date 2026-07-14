# RelCompat3D / H001 First-Pass Manuscript Draft

Last updated: 2026-07-13 KST

Status: `planning_draft_superseded_by_current_aaai_family_main_source`

This is a first-pass manuscript prose draft derived from `paper/outline.md`.
It is not camera-ready text. The purpose is to make the paper-body logic
readable end to end before final caption compression or final
bibliography/build verification. The first ICCV-style LaTeX source conversion
now lives under `archive/paper/iccv/`.

Current paper-facing title is `Beyond Semantic Confidence: Relation-Algebra-
Constrained Geometric Compatibility for 3D Scene Graph Relations`; the method name is
`RelCompat3D`. The active manuscript source is
`paper/aaai/`. This draft is a planning prose copy only; final submission text,
tables, captions, and current metrics should be checked against `paper/aaai/`,
`paper/preview.md`, `paper/progress.md`, and `summary.md`. Framework-first
override, 2026-07-13: the relation-algebra-constrained product is the main
method and evaluated rank-average is a scale-robust RelCompat3D instantiation;
neither is universally dominant. The active AAAI source contains the authoritative SGFN
source comparison, family decomposition, and human-validity boundary. Older
single-main-score wording below is preserved only as superseded planning prose.

Factorization override, 2026-07-10: the active manuscript defines `T_e` as
predicate/family semantics, raw `G_e` as predicate-independent same-pair
geometry, `Z_e` as source confidence, and
`C_e=sigmoid(h_a(Phi(T_e,G_e)))`, enforcing `Z_e notin C_e` before final
`S_e=F(Z_e,C_e)` fusion. It is a bounded score for a constructed
GT-positive/counterfactual target, not a physical-validity probability. Older
body text that calls `p_geom_valid`-only “geometry-only” is
superseded: it is calibrator-only/no-`Z`. The historical main table has no true
`G_e`-only row; the completed strict factor audit now supplies that diagnostic
and the exact counterfactual controls.

Related Work citation placeholders have been replaced with BibTeX-style keys.
The 2026-05-23 literature pass keeps recent open-world/VLM graph and
RelWitness citations in the final draft with separated roles: direct novelty
threat, spatial-relation boundary, VLM/incremental trend, open-world/RAG
boundary, and downstream grounding motivation.
Current key map:

| shorthand | BibTeX-style key |
| --- | --- |
| 3DSSG | `wald2020learning3dssg` |
| SGGpoint | `zhang2021sggpoint` |
| SMKA | `feng2023smka` |
| VL-SAT | `wang2023vlsat` |
| SGRec3D | `koch2024sgrec3d` |
| Open3DSG | `koch2024open3dsg` |
| CCL-3DSGG | `chen2024ccl3dsgg` |
| FROSS | `hou2025fross` |
| OpenFunGraph | `zhang2025openfungraph` |
| OctreeGraph | `wang2025octreegraph` |
| FirePlace | `huang2025fireplace` |
| GREAT | `shao2025great` |
| SGAligner | `sarkar2023sgaligner` |
| SG-PGM | `xie2024sgpgm` |
| ZING-3D | `saxena2025zing3d` |
| Open-World 3DSG-RAG | `yu2025openworld3dsg` |
| View-on-Graph | `liu2026viewongraph` |
| VIZOR | `madhavaram2026vizor` |
| RelWitness | `nguyen2026relwitness` |

## Title

Beyond Semantic Confidence: Relation-Algebra-Constrained Geometric
Compatibility for 3D Scene Graph Relations

## Abstract

3D Scene Graphs represent objects and relations in a form useful for spatial
reasoning, but relation predictions can remain unreliable even when predicted
predicates appear semantically plausible. We study a relation-level failure
mode: semantic relation confidence is not necessarily calibrated to the 3D
geometry of the same object pair, so a predictor can rank physically
inconsistent relations highly. To expose and reduce this failure, we introduce
a calibrated geometry-consistency evaluation and re-ranking framework for
geometry-checkable relation families. The framework standardizes prediction
rows across relation sources, preserves subject-object identity, joins explicit
3D evidence, estimates calibrated geometry-validity risk, and reports a main
family-conditional score with pooled and rule-verified variants under a
recall-violation protocol. On the full official validation split, RelCompat3D
re-ranking improves VL-SAT R@50/R@100 from 0.9272/0.9635 to 0.9288/0.9683
while reducing Violation@100 from 0.0476 to 0.0333. On the Open3DSG
full-validation recovery branch, the same family-conditional score improves
R@100 from 0.5161 to 0.6047 while reducing Violation@100 from 0.1242 to
0.0341. GT positive/counterfactual checks separate valid and invalid geometry
with AUROC/AUPRC of 0.9772/0.9729, and controls rule out geometry-only,
distance-only, shuffled-geometry, and wrong-pair explanations. These
results support a scoped relation-reliability claim for measured
geometry-checkable 3D Scene Graph relations, not a broad open-vocabulary graph
generation claim.

## 1. Introduction

3D Scene Graphs turn reconstructed scenes into structured object-relation
representations that can support spatial reasoning, embodied AI, scene
alignment, visual grounding, and downstream decision making
\cite{wald2020learning3dssg,sarkar2023sgaligner,xie2024sgpgm,liu2026viewongraph}.
For these uses, relation prediction must be reliable in the physical scene,
not only plausible at the category or language level. A graph edge such as
`standing on`, `next to`, or `higher than` is useful only if it describes the
actual subject-object pair in 3D.

We study a failure mode in which semantic relation predictors rank plausible
relation labels that are geometrically inconsistent for the actual object
pair. A relation can sound plausible for two object categories while being
contradicted by their contact evidence, distance, or vertical arrangement in
the reconstructed scene. This mismatch matters more as 3D Scene Graphs become
interfaces for language-facing, open-vocabulary, and embodied systems
\cite{koch2024open3dsg,hou2025fross,zhang2025openfungraph,wang2025octreegraph,saxena2025zing3d,yu2025openworld3dsg,madhavaram2026vizor}.

The failure is not simply that existing 3DSSG methods ignore geometry. Prior
work already uses edge features, point-cloud structure, spatial knowledge,
multimodal semantics, and geometric fusion
\cite{zhang2021sggpoint,feng2023smka,wang2023vlsat,koch2024sgrec3d,chen2024ccl3dsgg}.
The gap is more specific: semantic relation confidence is not necessarily a
calibrated estimate of relation-level physical consistency. A high relation
score can behave as a semantic plausibility score without indicating whether
the same subject-object pair satisfies the relation in 3D.

This motivates a calibrated geometry-consistency evaluation and re-ranking
framework. The framework treats an existing predictor as a relation source,
standardizes its outputs into identity-preserving prediction rows, joins
object-pair geometry evidence by subject and object instance identifiers,
estimates `p_geom_valid`, and evaluates relation rankings with both exact-label
recall and geometric violation. This design is necessary because hard physical
rules and probabilistic reliability scores answer different questions:
rule-verified variants diagnose strict consistency, while calibrated variants
expose a usable recall-violation operating point. Figure 1 summarizes this
failure-mechanism-to-framework path.

We evaluate the framework on geometry-checkable relation families:
`support_contact`, `proximity`, and `relative_vertical`. VL-SAT is the primary
reproduced closed-set relation source, and Open3DSG is used as measured
second-source evidence within the same H001-family scope
\cite{wang2023vlsat,koch2024open3dsg}. Controls test whether the effect can be
explained by geometry-only ranking, a generic distance heuristic, shuffled
geometry, or wrong-pair geometry. GT-positive and counterfactual checks test
the geometry-validity signal independently from prediction re-ranking, while
qualitative failure analysis shows how semantic plausibility diverges from
physical consistency.

Our contributions are threefold:

1. We identify and formalize a relation-level reliability failure in 3D Scene
   Graph prediction: semantic relation confidence can rank plausible predicates
   that are physically inconsistent because it is not calibrated to
   object-pair geometry.
2. We introduce a calibrated geometry-consistency evaluation and re-ranking
   framework that standardizes prediction rows, joins identity-preserving 3D
   evidence, and ranks by a family-conditional calibrated geometry-risk score
   while retaining pooled and rule-verified variants as ablation/diagnostic
   conditions.
3. We define a recall-violation evaluation protocol for geometry-checkable
   relation families, including exact-label `R@K`, `Violation@K`,
   GT-positive/counterfactual verifier evaluation, and geometry identity
   controls.

We validate these contributions with Docker-reproducible evidence on VL-SAT
and Open3DSG, including nontriviality controls, second-source metrics, and
failure analysis. The claim is intentionally scoped: H001 measures and improves
relation reliability for geometry-checkable 3DSSG families. It does not claim
general open-vocabulary 3D Scene Graph generation improvement, arbitrary-source
generality, or guaranteed physical correctness.

## 2. Related Work

### 2.1 3D Scene Graph Relation Prediction

3D Scene Graphs represent indoor scenes as structured collections of objects
and relations, enabling downstream spatial reasoning beyond isolated object
recognition. Early 3DSSG work established the 3RScan/3DSSG setting and made
predicate recall a standard way to evaluate relation prediction in reconstructed
3D scenes \cite{wald2020learning3dssg}. Subsequent relation-prediction
methods model relation edges more explicitly, using edge-oriented graph
reasoning, point-cloud features, multimodal cues, and spatial knowledge to
improve closed-set predicate prediction
\cite{zhang2021sggpoint,feng2023smka,wang2023vlsat,koch2024sgrec3d}.

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
relations
\cite{koch2024open3dsg,chen2024ccl3dsgg,hou2025fross,zhang2025openfungraph,wang2025octreegraph}.
This line is important because relation labels increasingly come from
visual-language priors or open-vocabulary semantic sources rather than only
from fixed closed-set classifiers. It also raises the reliability requirement:
when relation edges are used as language-facing scene representations,
plausible text labels must still refer to object pairs that satisfy the
corresponding spatial relation in the scene.

Very recent systems broaden this setting further. ZING-3D uses VLM reasoning
for zero-shot incremental 3D scene graphs with depth grounding and
distance-bearing edges \cite{saxena2025zing3d}; VIZOR constructs
viewpoint-invariant zero-shot scene graphs with object-centric spatial
relations \cite{madhavaram2026vizor}; and Open-World 3DSG-RAG connects
open-world graph construction to retrieval-augmented reasoning across
downstream tasks \cite{yu2025openworld3dsg}. We cite these papers as trend and
boundary evidence, not as direct H001 baselines.

Recent graph-mediated grounding work also uses scene graphs as an explicit
interface for VLM reasoning over 3D spatial information
\cite{liu2026viewongraph}. We treat this as downstream motivation rather than
as a direct baseline: H001 evaluates the reliability of relation rows before
they are reused by grounding, retrieval, or planning systems.

H001 is not positioned as a broad open-vocabulary 3D scene graph generation
method. We use VL-SAT as the primary reproduced relation source and Open3DSG as
second-source evidence within measured geometry-checkable relation families.
The claim is scoped to relation reliability for `support_contact`, `proximity`,
and `relative_vertical`, not to general open-vocabulary graph generation.
Qwen-VL remains a third semantic source / modern VLM extension unless it
receives the same Docker, denominator, metric, bootstrap, and audit treatment
as the main evidence.

### 2.3 Geometry-Aware Relation Reasoning And Semantic-Geometric Fusion

A broad set of 3D reasoning methods already uses geometry: edge features,
support/contact patterns, affordance geometry, metric distance, topology, and
semantic-geometric fusion
\cite{zhang2021sggpoint,feng2023smka,huang2025fireplace,shao2025great,xie2024sgpgm}.
Scene
graph alignment and registration methods further demonstrate that graph
structure and geometric consistency matter when scene graphs are reused for
matching, alignment, and downstream geometric tasks \cite{sarkar2023sgaligner,xie2024sgpgm}.

Very recent arXiv work on RelWitness makes the overlap sharper by introducing
visual-geometric relation witnesses, calibrated witness quality, and
witness-consistent decoding for open-vocabulary 3D scene graph generation under
incomplete relation supervision \cite{nguyen2026relwitness}.
This motivates a narrow distinction for H001. We do not claim novelty from the
existence of visual-geometric relation evidence or calibrated relation evidence
alone. In the checked version, RelWitness reports simulated planning values, so
we treat it as near-concurrent related work rather than a quantitative baseline.
H001 studies a different contract: a calibrated reliability layer over existing
relation-source outputs. The same prediction row is joined to object-pair
geometry, assigned a calibrated geometry-validity score, and evaluated through
recall/violation operating points and controls.

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
For this reason, the paper reports the main family-conditional score alongside
pooled and rule-verified variants.

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
violation jointly. Figure 1 presents these requirements as a pipeline from
relation-source outputs to calibrated operating points.

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

### 4.4 Family-Conditional Calibrated Risk Re-Ranking

The main RelCompat3D score uses a frozen relation-family-conditioned calibrator:

```text
p_geom_valid_family_i = C_family(phi(g_i)),
```

where `phi(g_i)` is the geometry feature vector and `C_family` is the calibrator
for the mapped relation family. The pooled calibrator

```text
p_geom_valid_i = C_pooled(phi(g_i))
```

is retained as an ablation. Both calibrators are trained on train-dev
calibration positives and counterfactual negatives. The predicate-family map,
hard-rule thresholds, counterfactual construction, and calibrator files are
fixed before held-out source-result reporting.

We use geometry validity as a calibrated risk term rather than as a hard
accept/reject gate:

```text
R_geom_i = -log p_geom_valid_family_i
U_lambda(i) = log score_sem_i - lambda * R_geom_i
score_geocalib_i = score_sem_i * p_geom_valid_family_i.
```

The reported RelCompat3D score fixes `lambda = 1`. This preserves the source
semantic ranking signal while continuously penalizing calibrated geometric
inconsistency. We do not tune `lambda` on held-out source results; pooled and
hard-rule variants are reported separately as ablation/diagnostic conditions.

We report four main operating points. `semantic_only` ranks by the source
semantic score and serves as the reproduced source baseline.
`family_conditional_risk` is the main RelCompat3D score. It ranks by the product
of semantic confidence and family-conditioned calibrated geometry validity.
`probabilistic_recalibrated` ranks by semantic confidence times pooled
`p_geom_valid` and is the pooled calibrated-risk ablation.
`rule_verified_point_subtype` removes hard violations before ranking and is
reported as a zero-violation diagnostic.

### 4.5 Controls

The control conditions test whether the result can be explained by simpler
signals. Geometry-only ranking uses `p_geom_valid` without semantic score and
is therefore distinct from pooled calibrated reranking. Distance-only ranking
tests whether a generic spatial heuristic explains the result. Shuffled-geometry
and wrong-pair-geometry controls test whether relation-level object-pair
identity is necessary. If these controls perform worse than the calibrated
setting, the result supports the framework design rather than a generic "add
geometry" explanation.

## 5. Experimental Setup

This section fixes the experimental scope before reporting results, because
RelCompat3D's claim depends on denominator transparency as much as on metric
values. The paper-facing scope is the full official validation split: 157
scans, 548 contexts, 36,808 directed object pairs, 957,008 VL-SAT prediction
rows, 11,254 ground-truth rows, and 3,972 in-scope GT relation instances across
the measured geometry-checkable families.

Open3DSG provides the main open-vocabulary relation-source case study within
the same measured-family metric scope. The selected checkpoint is the official
non-averaged BLIP route `epoch=13-step=13104.ckpt`, chosen by train-dev
validation loss before held-out source-result inspection. The paper-facing
Open3DSG route is the full-validation `recovery_relaxed_views_min2/` branch,
which reaches 548/548 contexts by using `OPEN3DSG_MIN_VISIBLE_OBJECTS=2` plus
relaxed view regeneration for two scans. The 533/548 covered branch and the
historical 377/388 versus R2 388/388 branches remain sensitivity evidence.

All paper-body experiment results are generated through Docker under
`experiments/H001_geom_reliability/`. The paper reports exact-label `R@50` and
`R@100`, `Violation@50` and `Violation@100`, the fixed low-K grid
K = `{5,10,20,50,100}`, GT-positive/counterfactual verifier evaluation,
nontriviality controls, Open3DSG source metrics, and qualitative failure
analysis. Host-only outputs are not promoted to paper evidence.

## 6. Results And Discussion

The central question is whether calibrated geometry consistency reduces
physically inconsistent relation predictions without collapsing recall. Figure
2 visualizes the recall-violation tradeoff, and the main table reports VL-SAT
and Open3DSG on the full-validation K grid. On VL-SAT, the main
`family_conditional_risk` score improves R@50/R@100 from 0.9272/0.9635 to
0.9288/0.9683 while reducing Violation@100 from 0.0476 to 0.0333. The pooled
`probabilistic_recalibrated` ablation reaches 0.9305/0.9688 but leaves a
higher Violation@100 of 0.0404, so it is a recall-favoring ablation rather
than the main score.

On Open3DSG, `semantic_only` has R@50/R@100 of 0.4096/0.5161 and
Violation@50/@100 of 0.1386/0.1242. The main `family_conditional_risk` score
improves recall to 0.4658/0.6047 and reduces violations to 0.0286/0.0341. The
pooled ablation improves R@100 to 0.5723 but leaves Violation@100 at 0.0811.
The `rule_verified_point_subtype` setting achieves zero measured violations and
is treated as a diagnostic rather than the default method because hard
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
prediction re-ranking. GT-positive rows remain nonviolated at a rate of 0.9965,
while GT-derived counterfactual negatives are nonsatisfied at a rate of 0.9673.
The calibrated `p_geom_valid` score separates these groups with AUROC/AUPRC of
0.9772/0.9729 and Brier score 0.0543. This supports the use of `p_geom_valid`
as a reliability signal while still leaving room for residual calibration risk.

Table 4 reports audit and visual sanity checks as supporting evidence rather
than as the primary metric result. The structured audit covers 250 rows and
reaches quality-issue precision of 0.8933, while the reduced 50-row visual
spot-check reaches a target-bucket quality-issue rate of 0.9333 with
contradiction rate 0.0333. We use these checks to support failure-mechanism
interpretation and to detect annotation or verifier issues, not as a
large-scale independent human audit.

The Open3DSG result is source-output reliability evidence rather than a broad
open-vocabulary SOTA claim. Under the measured family scope, Open3DSG
`semantic_only` ranking reaches R@50/R@100 of 0.4096/0.5161 with
Violation@50/@100 of 0.1386/0.1242. The pooled
`probabilistic_recalibrated` ablation reduces violations to 0.0606/0.0811 while
shifting recall to 0.3975/0.5723. The rule-verified setting again gives a
zero-violation diagnostic, and the main `family_conditional_risk` score reaches
R@50/R@100 of 0.4658/0.6047 with Violation@50/@100 of 0.0286/0.0341. These
results support a cross-source relation-reliability claim within measured
families, with the selected non-averaged checkpoint, filtered-split,
full-validation recovery policy, exact-label denominator, and
residual-calibration caveats kept explicit.

The qualitative failure analysis explains why the metric changes occur and
provides candidate source rows for Figure 3. Open3DSG failure rows produce
57,736 real analysis rows with zero validation errors, and the inspected
36-case qualitative queue shows that 23 cases are demoted by geometry-aware
re-ranking. Figure 3 uses geometry-backed panels from this queue to show
family-structured failures: proximity failures often involve distance
contradictions, relative-vertical failures involve vertical-order
contradictions, and support/contact failures expose float-gap or support-plane
contradictions. This supports the failure mechanism: a relation can be
semantically plausible from object categories but physically inconsistent for
the actual object pair.

The same qualitative analysis also exposes a limitation. Eight of the 36 sampled
rule-violated cases still have `p_geom_valid > 0.9`. This means the calibrated
score should not be interpreted as a hard validity label. It also justifies why
the paper reports the main family-conditional score alongside pooled and
rule-verified variants rather than collapsing them into a single
"geometry-corrected" output.

## 7. Limitations

The current study is intentionally scoped to geometry-checkable relation
families. Relations whose correctness depends primarily on functional, social,
affordance, or language-pragmatic context are outside the H001 metric claim.
The evaluation also uses closed-set/GT-object relation rows and exact
predicate-label recall, so the results should be read as relation-reliability
evidence rather than full open-vocabulary scene graph generation performance.

The Open3DSG experiment uses a selected official non-averaged checkpoint with
explicit filtering and recovery-policy caveats. The checkpoint is selected by
train-dev validation loss before held-out inspection, the training and
validation splits are filtered to preprocessed-ready subgraphs, and the
paper-facing branch uses `recovery_relaxed_views_min2/` to cover 548/548
validation contexts. These choices do not invalidate the scoped reliability
result, but they prevent broad Open3DSG leaderboard or open-vocabulary SOTA
claims.

The visual and qualitative evidence should also be read with the correct scope.
The reduced visual sanity check and Open3DSG qualitative case inspection are
reviewer-defense and failure-mechanism evidence, not large-scale independent
human audits. They help identify failure modes and residual calibration risk,
but the quantitative claim remains tied to the fixed metric denominator and
Docker-generated tables.

Finally, `p_geom_valid` is a calibrated reliability score, not a proof of
physical correctness. Residual high-confidence but rule-violated cases motivate
future work on attachment-style physical relations such as attached, hanging,
or connected objects before broader functional predicates. Such an upgrade
would require additional surface/contact/gravity evidence and a separate
validation contract. Larger visual audits, modern VLM relation sources, and
downstream tasks remain natural follow-up settings where relation reliability
can be tested through planning, navigation, alignment, or embodied reasoning.

## 8. Conclusion

This paper studies a scoped reliability failure in 3D Scene Graph relation
prediction: semantic relation confidence can rank plausible predicates that are
physically inconsistent for the same object pair. We address this failure with
a calibrated geometry-consistency evaluation and re-ranking framework that
standardizes relation rows, preserves subject-object identity, joins explicit
3D evidence, estimates calibrated geometry risk, and reports recall and
geometric violation together.

Across VL-SAT and the Docker-reproduced Open3DSG full-validation recovery
branch, the results show that family-conditional geometry-consistency
re-ranking can reduce violations under measurable recall tradeoffs. The
GT-positive/counterfactual verifier checks, geometry identity controls, and
qualitative failure analysis support the central claim: the useful contribution
is not merely adding geometry, but making relation-level physical consistency
calibrated, identity-preserving, and reportable. The remaining limitations
point to the next stage: attachment-style physical
relations as the nearest family upgrade, modern VLM relation sources, and
downstream tests where reliable relation edges directly affect embodied
reasoning.

## Draft TODO

- Run an ICCV-style compression pass after the table/figure layout is placed in
  a manuscript source; prioritize Results/Table 6 wording and Related Work.
- Convert the current Markdown draft into a section-by-section manuscript
  source only after the paper-body prose is stable.
- Use the geometry-backed Figure 3 panel as the preferred draft; keep scene
  crop rendering only as optional final polish if a deterministic path is added.
- Keep Table 6/Open3DSG caveats visible until the paper-body logic is stable.

## Draft Budget Review

Reviewed on: 2026-05-23 KST

ICCV-style content status:

- Manuscript prose from Title through Conclusion is about 3,507 words before
  final compression and before LaTeX/table/figure layout.
- Front matter is about 707 words excluding title: 201-word Abstract and
  506-word Introduction.
- The current draft is content-complete enough for a layout/conversion pass,
  but still needs compression after figures/tables are placed.

Main-paper table recommendation:

| table | placement | reason |
| --- | --- | --- |
| Table 1 | main | Primary VL-SAT operating-point evidence. |
| Table 2 | main, compact | Nontriviality controls defend against geometry-only, distance-only, shuffled, and wrong-pair explanations. |
| Table 3 | main if compact; otherwise appendix with one-sentence main summary | Independent GT-positive/counterfactual support for `p_geom_valid`. |
| Table 4 | appendix | Audit/sanity evidence is supportive, not the primary metric claim. |
| Table 5 | prose or appendix | Claim-boundary accounting should be visible, but the full table can move if page budget is tight. |
| Table 6 | main | Open3DSG second-source evidence and caveats are required for the cross-source claim. |
| Appendix A1 | appendix | Calibrator/threshold provenance and Open3DSG caveat consistency defend against post-hoc tuning and denominator attacks. |

Figure placement recommendation:

- Figure 1 main: failure mechanism and framework.
- Figure 2 main: recall-violation tradeoff.
- Figure 3 main if space permits; otherwise main-text small panel plus appendix
  enlarged version. Do not remove all qualitative geometry evidence.

## Draft Review

Status: `passed_claim_scope_figures_citation_keys_section_title_intro_body_gap_budget_reviewed`

Reviewed on: 2026-05-23 KST

Review result:

| item | status | decision |
| --- | --- | --- |
| Claim scope | pass | The draft stays within measured geometry-checkable relation reliability and does not claim broad open-vocabulary 3DSSG generation improvement. |
| Title/Abstract/Introduction | filled and reviewed | The draft now includes a scoped title, quantitative abstract, and Introduction that links failure mechanism to method necessity before Related Work. Current front matter is about 701 words excluding title, with a 201-word abstract and 500-word Introduction, which is acceptable for an ICCV-style content draft before final compression. |
| Paper-body gap review | patched | Added Figure 1-3 callouts, Table 4 audit/sanity prose, and a Conclusion section before LaTeX/template conversion. |
| Method framing | pass | The method is described as a calibrated geometry-consistency evaluation and re-ranking framework, not as a standalone verifier script. |
| Open3DSG caveats | pass | The selected non-averaged checkpoint, filtered train/dev split, full-validation recovery policy, 533/548 sensitivity branch, exact-label denominator, and residual calibration risk remain explicit. |
| Appendix provenance | pass | `paper/appendix.md` records calibrator/threshold provenance, Open3DSG caveat consistency, Figure 3 optionality, and Qwen-VL third-source boundary. |
| Qwen-VL boundary | pass | Qwen-VL remains third-source extension evidence and is not used as a main metric result before full-source promotion. |
| Citation keys | scaffolded | Related Work placeholders have been replaced with BibTeX-style keys; `paper/references.bib` contains draft entries for all inserted keys. Final ICCV-style build still needs verification once a manuscript source exists. |
| Evidence links | patched | Results prose now points to Table 1, Table 2, Table 3, Table 5, and Table 6. |
| Figure readiness | generated and verified | Draft SVGs are generated under `paper/generated/figures/`; Figure 3 also has a geometry-backed point-cloud panel upgrade with validation passed. |
| Section structure | locked | Keep Section 5 as a short standalone `Experimental Setup` section. Do not merge it into Results because denominator, filtered-split, covered-scope, and Docker-result boundaries are part of the reviewer defense. |
| Section title | standardized | Top-tier CV/CVPR/ICCV-style papers typically use section labels such as `Experiments`, `Experimental Setup`, `Evaluation Setup`, `Datasets`, `Evaluation Metrics`, and `Implementation Details`. H001 therefore keeps scope/denominator caveats in the text but uses the standard heading `Experimental Setup`. |
| Budget/table placement | reviewed | Manuscript prose is about 3,507 words from Title through Conclusion before compression. Recommended main tables are Table 1, compact Table 2, compact Table 3 if space allows, and Table 6; Table 4 and full Table 5 should move to appendix/prose if page budget is tight. |

Evidence map:

| draft claim | evidence source |
| --- | --- |
| VL-SAT recall/violation operating points | `results/h001_geom_reliability/tables/table1_main_prediction.md` |
| Geometry-only, distance-only, shuffled, wrong-pair controls | `results/h001_geom_reliability/tables/table2_controls.md` |
| GT-positive/counterfactual verifier support | `results/h001_geom_reliability/tables/table3_gt_verifier.md` |
| Claim boundary and non-claims | `results/h001_geom_reliability/tables/table5_claim_boundary.md` |
| Open3DSG second-source metrics | `results/h001_geom_reliability/tables/table6_cross_source_status.md` and `experiments/H001_geom_reliability/sources/open3dsg/metrics/metrics.json` |
| Open3DSG caveat wording | `experiments/H001_geom_reliability/sources/open3dsg/paper_caveats/report.md` |
| Failure mechanism and residual calibration risk | `experiments/H001_geom_reliability/sources/open3dsg/failure_cases/inspection.md` and `paper/generated/figures/figure3_geometry_report.md` |
| Docker reproducibility and artifact portability | `docs/reproducibility.md` |

Figure source-lock decision:

- Figure 1 is a method/framework diagram sourced from Sections 3-4,
  `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/02_method.md`, and
  `results/h001_geom_reliability/manifest.lock.json`.
- Figure 2 is a two-panel `R@100` / `Violation@100` tradeoff plot using Table 1
  for VL-SAT and Open3DSG `metrics.json` with paper caveats.
- Figure 3 uses traceable Open3DSG qualitative rows and the preferred
  geometry-backed point-cloud panel upgrade
  `open3dsg_case_001`, `open3dsg_case_005`, `open3dsg_case_010`, and
  `open3dsg_case_007`.
- The authoritative source-lock file is `paper/figures.md`.
- Generated draft SVGs are `paper/generated/figures/figure1_framework.svg`,
  `paper/generated/figures/figure2_tradeoff.svg`,
  `paper/generated/figures/figure3_failure_cases.svg`, and the preferred
  `paper/generated/figures/figure3_geometry_panels.svg`.
