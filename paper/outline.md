# RelCompat3D / H001 Paper Outline

Framework-first override, 2026-07-14: RelCompat3D is a geometric-compatibility
framework. The structured product
(`family_conditional_risk`) and evaluated rank-average are two soft fusion
instantiations; pooled calibration is an ablation, RRF a strong comparator, and
hard filtering a diagnostic. Any older wording below that calls the product the
unique or universally dominant main method is superseded. The SGFN comparison
shows that both soft instantiations satisfy the K=100 joint Recall--Violation
criterion, with explicit `support_contact` and human-validity limitations.

Factorization override, 2026-07-10: `T_e` is predicate/family semantics,
`G_e` raw predicate-independent same-pair geometry, `Z_e` source confidence,
and `C_e=sigmoid(h_a(Phi(T_e,G_e)))`, with `Z_e notin C_e` and
`S_e=F(Z_e,C_e)`. The score targets constructed GT-positive/counterfactual
ordering and is not a physical-validity probability. Any older “geometry-only” label for the
`p_geom_valid`-only row means calibrator-only/no-`Z`, not true `G_e`-only.
The strict train-only factor/counterfactual package is complete. Exact
wrong-$T$/pair, close-by swap, and vertical inverse controls support the
selected family model, while failed pooled-interaction structural controls
block a generic interaction claim. The SGFN gate remains unchanged.

Current manuscript override, 2026-07-12: the submission follows the sequence
observed failure -> structural cause -> factor-isolation necessity -> method ->
results -> limitations. Figure 1 is the actual-failure-to-framework overview;
Figure 2 is the three-source K=`{5,10,20,50,100}` trajectory; Figure 3 contains
two corrections and one residual top-10 failure. K=100 is primary; all other K
values are reported without additional protocol labels. A 69-parameter source-supervised nonlinear
rescorer is stronger at low K and blocks formula-optimality claims. Codex proxy
results are excluded from the submission and live only in `paper/paper_nonsub/`.

Table override, 2026-07-14: Table 1 jointly reports Recall and verifier-derived
Violation for K=`{5,10,20,50,100}` across Source score, the RelCompat3D
product, rank-average, RRF, and pooled product. Table 2 reports the six frozen
K=50/100 controls: wrong predicate, wrong pair, shuffled geometry, label-fixed
endpoint swap, distance-only, and compatibility-only. Hard filtering is a
construction diagnostic in the artifacts, not a primary comparator row. Any
older three-table or separate Recall/Violation plan below is superseded.

Structure/title override, 2026-07-14: the active title is `Beyond Semantic
Confidence: Relation-Algebra-Constrained Geometric Compatibility for 3D Scene
Graph Relations`, and the method name is `RelCompat3D`. The active source has six
top-level sections: Introduction; Related Work; Method (including Problem
Setup); Experiments (including setup and results); Discussion and Limitations;
and Conclusion. Older independent Problem Formulation, Experimental Setup, and
Results and Discussion headings below are superseded planning history.

Last updated: 2026-07-14 KST

This outline turns `paper/preview.md` into a paper-writing skeleton. It is not the final manuscript. It fixes the section logic, evidence placement, reviewer-defense responsibilities, title candidates, and contribution statements before drafting the abstract and manuscript sections.

Status: `planning_outline_superseded_by_current_aaai_family_main_source`

The authoritative current manuscript state is `paper/aaai/`, `paper/preview.md`,
and `paper/progress.md`. The outline below preserves older planning rationale
and historical sensitivity wording; do not use its body metrics as final
submission values without checking the current AAAI source, `metrics_k_sweep/`
artifacts, and the 2026-06-25 family-main scoring decision.

## Drafting Constraints

Fact:

- Candidate: `CAND-001 / H001_geometry-grounded-verification`.
- Paper-facing name: `Beyond Semantic Confidence: Relation-Algebra-Constrained Geometric Compatibility for 3D Scene Graph Relations`.
- Method framing: predictor-agnostic geometric compatibility and joint reliability evaluation.
- Main evidence sources: VL-SAT full official validation and Open3DSG
  full-validation `recovery_relaxed_views_min2/`.
- RelCompat3D main method: source score times relation-algebra-constrained
  compatibility; rank-average is a fixed scale-robust instantiation, with no
  universal formula-dominance claim.
- Pooled calibrated ablation: `probabilistic_recalibrated =
  semantic_score * p_geom_valid`.
- Calibrator-only/no-`Z` control: `p_geom_valid` without semantic score; the
  separate strict factor audit now supplies true `G`-only.
- Main relation families: `support_contact`, `proximity`, `relative_vertical`.
- Paper-result experiments must remain Docker reproducible.

Inference:

- The paper should be scoped as a relation-reliability paper for geometry-checkable 3DSSG relation families.
- The paper should not be framed as broad open-vocabulary 3DSSG SOTA.
- The core novelty is the failure-mechanism-to-method link: semantic plausibility is not calibrated to relation-level physical consistency, so a calibrated geometry-consistency reliability layer is needed.

Non-claims:

- Do not claim arbitrary-baseline generality.
- Do not claim full open-vocabulary 3DSSG generation improvement.
- Do not claim exact non-averaged Open3DSG reproduction.
- Do not describe the reduced visual sanity check as a large-scale or strictly blinded human audit.

## Working Claim

Current allowed claim:

```text
For geometry-checkable 3D scene graph relation families, calibrated geometry-consistency scoring exposes semantically plausible but physically inconsistent relation predictions and can reduce geometric violations while preserving measurable recall tradeoffs across VL-SAT and Open3DSG.
```

Claim boundary:

- `VL-SAT` supports the primary closed-set relation-reliability result.
- Open3DSG supports the main open-vocabulary relation-source case study within
  the measured families.
- Qwen-VL full official validation downstream is complete as third-source modern VLM extension evidence, but remains outside the main claim unless explicitly promoted.

## Title Candidates

Recommended primary title:

```text
Beyond Semantic Confidence: Relation-Algebra-Constrained Geometric Compatibility for 3D Scene Graph Relations
```

Why this is preferred:

- It foregrounds the method name, calibration, geometric consistency,
  reliability, and relation prediction.
- It does not overclaim broad open-vocabulary 3DSSG generation improvement.
- It matches the current evidence: measured relation-family reliability across `VL-SAT` and Open3DSG.

Alternative title candidates:

1. `Measuring and Reducing Geometric Inconsistency in 3D Scene Graph Relations`
2. `Geometry-Consistent Reliability for 3D Scene Graph Relation Prediction`
3. `From Semantic Plausibility to Physical Consistency in 3D Scene Graph Relations`
4. `Calibrated Physical Consistency for 3D Scene Graph Relation Prediction`
5. `Reliability-Aware 3D Scene Graph Relations via Calibrated Geometry Consistency`
6. `Calibrated Geometry Re-Ranking for Relation Reliability in 3D Scene Graphs`
7. `When Plausible Relations Violate Space: Calibrated Geometry Consistency for 3D Scene Graphs`
8. `Evaluating Geometry-Consistent Reliability in 3D Scene Graph Relations`

Avoided title patterns:

- `Open-Vocabulary 3D Scene Graph Generation with Geometry`
- `A General Geometry Verifier for 3D Scene Graphs`
- `Improving 3D Scene Graph Prediction with Geometry`
- `State-of-the-Art Open-Vocabulary 3D Scene Graph Relations`

Reason:

- These overstate generation, baseline generality, or SOTA scope, and make the work look like a generic module or verifier script.

## Contribution Statements

Recommended contribution wording:

1. Failure mechanism:
   We identify and formalize a relation-level reliability failure in 3D Scene Graph prediction: semantic relation confidence can rank plausible predicates that are physically inconsistent because it is not calibrated to object-pair geometry.

2. Method framework:
   We introduce a calibrated geometry-consistency evaluation and re-ranking framework that standardizes prediction rows across relation sources, joins identity-preserving 3D geometry evidence, and ranks by a family-conditional calibrated geometry-risk score while retaining pooled and rule-verified variants as ablation/diagnostic conditions.

3. Evaluation protocol:
   We define a recall-violation evaluation protocol for geometry-checkable relation families, including exact-label `R@K`, `Violation@K`, GT-positive/counterfactual verifier evaluation, and nontriviality controls such as geometry-only, distance-only, shuffled-geometry, and wrong-pair geometry variants.

Empirical result, not a separate contribution bullet:

- Cross-source `VL-SAT` and Open3DSG results, plus failure analysis, should be presented as the evidence validating the three contributions. They should appear in Results and Failure Analysis, not as a fourth contribution.

Compact version for paper introduction:

```text
Our contributions are: (i) a failure formulation for semantically plausible but geometrically inconsistent 3D scene graph relations; (ii) a calibrated geometry-consistency evaluation and re-ranking framework with explicit operating points; and (iii) a recall-violation evaluation protocol with GT-based verifier checks and geometry identity controls. We validate these contributions with Docker-reproducible cross-source evidence on VL-SAT and Open3DSG, including failure analysis and residual calibration-risk disclosure.
```

Non-contribution wording to avoid:

- "We add geometry to 3DSSG."
- "We build a verifier script."
- "We improve open-vocabulary 3DSSG."
- "We provide a baseline-agnostic relation predictor."
- "We solve physical consistency for all 3D relations."

## Paper Skeleton

### Title

Status: draft title candidates fixed. Use the recommended primary title unless a later paper draft reveals a stronger scoped phrase.

Role:

- Signal relation reliability, geometry consistency, and 3D scene graphs.
- Avoid claiming broad open-vocabulary generation improvement.

Recommended title:

```text
Calibrating Geometric Consistency for Reliable 3D Scene Graph Relations
```

### Abstract

Status: draft skeleton fixed; refine after the Introduction logic is expanded.

Required logic:

1. Problem: semantic 3D relation predictors can produce plausible but physically inconsistent edges.
2. Cause: semantic confidence is not calibrated to relation-level 3D geometry.
3. Contributions: failure mechanism, calibrated framework, and recall-violation protocol.
4. Method: calibrated geometry-consistency evaluation and re-ranking framework.
5. Evidence: `VL-SAT` metrics, controls, GT-based verifier evaluation, and Open3DSG second-source results.
6. Boundary: measured geometry-checkable relation families, not broad open-vocabulary 3DSSG SOTA.

Abstract skeleton:

```text
3D Scene Graphs represent objects and relations in a form useful for spatial reasoning, but relation prediction can remain unreliable even when predicted predicates appear semantically plausible.
We identify a relation-level failure mode: semantic relation confidence is not necessarily calibrated to object-pair geometry, so predictors can rank physically inconsistent relations highly.
To study this failure, we introduce a calibrated geometry-consistency evaluation and re-ranking framework for geometry-checkable relation families, standardizing prediction rows, joining identity-preserving 3D geometry evidence, and re-ranking with a family-conditional calibrated geometry-risk score while retaining pooled and rule-verified variants as ablation/diagnostic conditions.
We further define a recall-violation evaluation protocol with exact-label R@K, Violation@K, GT-positive/counterfactual verifier checks, and geometry identity controls.
On VL-SAT, the family-conditional score improves R@50/R@100 while reducing Violation@100 relative to semantic-only ranking; controls show that the effect is not explained by geometry-only ranking, distance-only heuristics, shuffled geometry, or wrong-pair geometry.
On Open3DSG, the full-validation recovery branch provides open-vocabulary relation-source evidence that geometry-consistency can reduce violations under explicit recall tradeoffs, while failure analysis exposes residual calibration risk.
These results support a scoped relation-reliability claim for geometry-checkable 3DSSG families, not a broad open-vocabulary 3D Scene Graph generation claim.
```

Shorter abstract skeleton:

```text
Semantic 3D Scene Graph relation predictors can produce plausible relation labels that violate object-pair geometry. We formalize this as a relation-level reliability failure and introduce a calibrated geometry-consistency evaluation and re-ranking framework for geometry-checkable relation families. The framework standardizes prediction rows, joins identity-preserving 3D evidence, and ranks by a family-conditional calibrated geometry-risk score under a recall-violation protocol, with pooled and rule-verified variants retained as ablation/diagnostic conditions. Experiments on VL-SAT and Open3DSG show that calibrated geometry-consistency reduces geometric violations under measurable recall tradeoffs, with controls ruling out geometry-only, distance-only, shuffled-geometry, and wrong-pair explanations. Failure analysis further reveals residual overconfidence in probabilistic geometry scores. The claim is scoped to measured geometry-checkable 3DSSG relations rather than broad open-vocabulary graph generation.
```

Numbers to insert only if the target venue expects quantitative abstract evidence:

- `VL-SAT` full-validation main `family_conditional_risk` R@50/R@100 `0.9288/0.9683` vs `semantic_only` `0.9272/0.9635`; Violation@100 `0.0333` vs `0.0476`.
- `VL-SAT` full-validation pooled `probabilistic_recalibrated` R@50/R@100 `0.9305/0.9688`; Violation@100 `0.0404`.
- Open3DSG full-validation 548/548 recovery: `family_conditional_risk` R@50/R@100 `0.4658/0.6047` and Violation@50/@100 `0.0286/0.0341` vs `semantic_only` `0.4096/0.5161` and `0.1386/0.1242`.
- GT verifier: `p_geom_valid` AUROC/AUPRC `0.9772/0.9729`.

Abstract wording constraints:

- Do not say "we improve open-vocabulary 3DSSG generation."
- Do not say "we propose a verifier script."
- Do not call Qwen-VL evidence part of the main abstract.
- Mention Open3DSG as measured H001-family second-source evidence, not as a full official Open3DSG SOTA comparison.

### 1. Introduction

Main job:

- Establish why relation reliability matters in 3D Scene Graphs.
- Define the specific failure mode: semantic plausibility can diverge from physical consistency.
- Explain why this is not solved by adding geometry as a generic feature.
- State the scoped claim and the relation families.

Evidence to cite internally:

- `VL-SAT` semantic-only violations.
- Open3DSG semantic-only violations.
- Qualitative failure cases where geometry-aware reranking demotes inconsistent predictions.

Reviewer defense:

- Make clear that the paper is not claiming general SOTA generation.
- Avoid motivation-only novelty. Tie the observed failure to the need for calibrated geometry-consistency evaluation and re-ranking.

Paragraph-level logic:

1. 3D Scene Graph relation reliability problem:
   Open by stating that 3D Scene Graphs are useful because they turn 3D perception into object-relation structures for spatial reasoning, robotics, and downstream decision making. The reliability bottleneck is not only object recognition, but whether predicted relations are physically consistent in 3D.

2. Concrete failure mode:
   Define the failure as a mismatch between semantic plausibility and physical consistency. A predictor can assign high semantic confidence to a relation label that sounds plausible for the object categories but violates the actual object-pair geometry in the scene.

3. Why the failure occurs:
   Explain that semantic relation confidence is not necessarily calibrated to relation-level geometry. This is stronger than saying "existing methods do not use geometry"; the key claim is that relation scores are not evaluated as calibrated physical-consistency signals with explicit recall-violation tradeoffs.

4. Why the method form is necessary:
   Motivate calibrated geometry-consistency evaluation and re-ranking from the failure cause. The method must standardize prediction rows, preserve object-pair identity, join 3D evidence, estimate `p_geom_valid`, and report multiple operating points because hard physical validity and probabilistic confidence are not the same.

5. Evidence preview:
   Preview that Open3DSG is the main open-vocabulary relation-source case study and `VL-SAT` is the controlled reproduced anchor. Mention controls at a high level: geometry-only and distance-only heuristics are insufficient; shuffled/wrong-pair geometry tests object-pair identity; GT/counterfactual checks support the verifier signal.

6. Contributions and scope:
   End the Introduction by listing the three contributions and the empirical validation sentence. The scope must be explicit: measured geometry-checkable families (`support_contact`, `proximity`, `relative_vertical`), not broad open-vocabulary 3DSSG generation or arbitrary-baseline generality.

Draft paragraph skeleton:

```text
3D Scene Graphs provide a structured representation of objects and relations that can support spatial reasoning, robotics, and downstream scene understanding. For such uses, relation prediction must be reliable in the physical scene, not merely plausible at the category or language level.

We study a failure mode in which semantic relation predictors rank plausible relation labels that are geometrically inconsistent for the actual object pair. For example, a relation can be plausible for two object categories but contradicted by their contact, distance, or vertical arrangement in the reconstructed 3D scene.

This failure is not simply a lack of geometry features. Rather, semantic relation confidence is not necessarily calibrated to relation-level physical consistency. A relation score can therefore behave as a semantic plausibility score without providing a calibrated estimate of whether the relation is geometrically valid.

This motivates a calibrated geometry-consistency evaluation and re-ranking framework. The framework standardizes prediction rows across relation sources, preserves object-pair identity, joins 3D geometry evidence, and ranks by a family-conditional calibrated geometry-risk score while retaining pooled and rule-verified variants under a recall-violation protocol.

We evaluate the framework on geometry-checkable relation families using Open3DSG as the main open-vocabulary relation-source case study and VL-SAT as a controlled reproduced anchor. Controls test whether the effect can be explained by geometry-only ranking, distance-only heuristics, shuffled geometry, or wrong-pair geometry, while GT-positive and counterfactual checks evaluate the verifier signal.

Our contributions are: (i) a failure formulation for semantically plausible but geometrically inconsistent 3D scene graph relations; (ii) a calibrated geometry-consistency evaluation and re-ranking framework with explicit operating points; and (iii) a recall-violation evaluation protocol with GT-based verifier checks and geometry identity controls. We validate these contributions with Docker-reproducible cross-source evidence on VL-SAT and Open3DSG, including failure analysis and residual calibration-risk disclosure.
```

Do not write:

- "Existing methods ignore geometry."
- "We add a geometry module."
- "We improve open-vocabulary 3DSSG."
- "Our verifier guarantees physical correctness."
- "The method is baseline-agnostic."

Must include before the end of Introduction:

- relation families: `support_contact`, `proximity`, `relative_vertical`
- claim boundary: measured geometry-checkable relation reliability
- empirical validation role of `VL-SAT` and Open3DSG
- Qwen-VL omitted from the main Introduction evidence unless later promoted with full metrics

### 2. Related Work

Main job:

- Position against 3DSSG prediction, open-vocabulary 3DSSG, geometry-aware relation modeling, and scene graph reliability/calibration.
- Explain why existing methods are not directly measuring relation-level physical consistency.

Subsections:

- 2.1 3D Scene Graph relation prediction.
- 2.2 Open-vocabulary 3D Scene Graphs and VLM-based scene understanding.
- 2.3 Geometry-aware constraints and spatial relation reasoning.
- 2.4 Reliability, calibration, and post-hoc evaluation in structured prediction.

Reviewer defense:

- Do not say existing work ignores geometry entirely.
- Say the gap is relation-level calibrated consistency and recall-violation tradeoff accounting.

Paper-body positioning map:

| subsection | papers to cite | what to say | H001 contrast |
| --- | --- | --- | --- |
| 3D Scene Graph relation prediction | 3DSSG, SGGpoint, SMKA, VL-SAT, SGRec3D | These works establish 3DSSG/3RScan relation prediction, edge-oriented reasoning, multimodal/spatial knowledge, and standard predicate recall evaluation. | H001 does not replace these predictors; it evaluates and re-ranks their relation rows by calibrated relation-level geometry consistency. |
| Open-vocabulary 3D Scene Graphs | Open3DSG, CCL-3DSGG, Open-Vocabulary Functional 3D Scene Graphs, FROSS, Open-Vocabulary Octree-Graph | Recent work expands 3DSG toward open-vocabulary objects, predicates, online generation, functional relations, and compact graph representations. | H001 does not claim broad open-vocabulary generation; it asks whether predicted relation edges are physically reliable for geometry-checkable families. |
| Geometry-aware relation reasoning | SGGpoint, SMKA, FirePlace, GREAT, SG-PGM | Geometry, edge features, support hierarchy, affordance geometry, and semantic-geometric fusion are already important in 3D reasoning. | The missing piece is not "geometry exists", but calibrated relation-level consistency with identity-preserving geometry joins and recall-violation reporting. |
| 3D scene graphs for downstream reasoning | SGAligner, SG-PGM, OVSG, ConceptGraphs, HOV-SG, SayPlan, SG-Nav, 3DGraphLLM, 3D-Mem | Scene graphs are used for alignment, registration, navigation, object search, planning, and 3D-LLM reasoning. | These motivate why relation reliability matters downstream, but they are not direct baselines for H001 unless a separate downstream experiment is added. |
| Reliability and calibration | calibration / post-hoc structured prediction literature to be selected later | Reliability requires reporting confidence, failure modes, and operating points rather than only top-K label recall. | H001 instantiates this idea for geometry-checkable 3DSSG relations through `p_geom_valid`, rule-verified diagnostics, controls, and violation metrics. |

Draft related-work contrast paragraph:

```text
Prior 3D scene graph work has already shown that semantic relation prediction benefits from 3D geometry, edge features, multimodal knowledge, and open-vocabulary visual-language features. Our claim is therefore not that existing 3DSSG methods ignore geometry. Instead, we focus on a reliability gap that remains after relation scores are produced: semantic confidence is not necessarily a calibrated estimate of relation-level physical consistency for the same object pair. This motivates a post-prediction reliability layer that preserves object-pair identity, joins explicit 3D evidence, estimates calibrated geometric validity, and reports recall and violation jointly.
```

Positioning constraints:

- Cite `VL-SAT` and Open3DSG as reproduced relation sources, not as defeated strawmen.
- Cite SGAligner/SG-PGM as downstream motivation and semantic-geometric fusion context, not as direct relation-prediction baselines.
- Cite OpenFunGraph/FROSS/Octree-Graph as broader open-vocabulary/functionality/online directions, not as evidence that H001 solves those tasks.
- If calibration literature is added later, keep it methodological and do not imply H001 is a general calibration theory paper.

### 3. Problem Formulation

Main job:

- Define prediction rows, object pairs, predicate candidates, and geometry evidence.
- Define target families: `support_contact`, `proximity`, `relative_vertical`.
- Define `R@K`, `Violation@K`, recall retention, and in-scope denominator.
- Define exact-label recall and family-level reliability reporting.

Evidence/artifacts:

- `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/02_method.md`
- `results/h001_geom_reliability/manifest.lock.json`
- `results/h001_geom_reliability/tables/table1_main_prediction.md`
- `experiments/H001_geom_reliability/sources/open3dsg/metric_scope/report.md`

Reviewer defense:

- Make the denominator explicit before results.
- Separate exact predicate recall from family-level violation reporting.
- State excluded relation families clearly.

Formal problem skeleton:

Let a scene graph source produce candidate relation rows:

```text
r_i = (s_i, o_i, p_i, a_i, y_i, score_sem_i)
```

where `s_i` and `o_i` are subject/object instance identifiers, `p_i` is a predicate label, `a_i` is the predicate family, `y_i` stores source metadata such as scan/subgraph identifiers, and `score_sem_i` is the source semantic relation confidence.

For each row, H001 joins identity-preserving geometry evidence:

```text
g_i = G(scan_i, subgraph_i, s_i, o_i)
```

where `g_i` may include OBB features, point/local evidence, distance/contact/vertical relations, and missing-evidence reason codes.

The verifier produces:

```text
v_i in {satisfied, uncertain, violated}
p_geom_valid_i = P(v_i != violated | g_i, a_i)
```

The paper evaluates only geometry-checkable families:

```text
A = {support_contact, proximity, relative_vertical}
```

Rows outside `A` are preserved in prediction exports but excluded from the H001 violation claim.

Metric definitions to write in the paper:

- `R@K`: exact predicate-label recall over the fixed in-scope GT denominator.
- `Violation@K`: fraction of top-K in-scope predicted rows whose joined geometry is judged `violated`.
- Recall retention: `R@K(method) / R@K(semantic_only)`.
- Violation reduction: `Violation@K(semantic_only) - Violation@K(method)`, reported together with recall.

Denominator wording:

```text
All recall values are exact predicate-label recall over the fixed H001 in-scope denominator. Family grouping is used to define geometry-checkable reliability scope and violation analysis, not to relax predicate-label matching.
```

### 4. Method

Main job:

- Present the calibrated geometry-consistency evaluation/re-ranking framework.
- Explain relation-family-specific geometry checks.
- Explain `p_geom_valid`, hard rule verification, family-conditional calibration, and re-ranking variants.

Subsections:

- 4.1 Relation-row standardization across prediction sources.
- 4.2 Geometry evidence extraction and relation-family checks.
- 4.3 Calibrated `p_geom_valid` scoring.
- 4.4 Re-ranking and operating points.
- 4.5 Controls: geometry-only, distance-only, shuffled geometry, wrong-pair geometry.

Reviewer defense:

- Avoid "verifier script" wording.
- Emphasize calibration, operating points, and identity-preserving joins.
- Explain why hard rules and probabilistic scores are reported separately.

Method formalization:

1. Relation-row standardization:
   Convert each source output into the same row contract:

   ```text
   (scan_id, subgraph_id, subject_id, object_id, predicate, family, score_sem, source)
   ```

   This is the unit of comparison across `VL-SAT`, Open3DSG, controls, and future optional sources.

2. Identity-preserving geometry join:
   Join geometry by `(scan_id, subgraph_id, subject_id, object_id)` rather than by category names or unordered pair statistics. This prevents geometry evidence from drifting across instances and supports shuffled/wrong-pair controls.

3. Family-specific geometry checks:

   | family | evidence type | hard decision intuition |
   | --- | --- | --- |
   | `support_contact` | point/local contact, vertical support, OBB overlap, support subtype | violated when support/contact is contradicted by geometry evidence |
   | `proximity` | object distance, pair scale, OBB/point distance | violated when predicted nearness is inconsistent with pair distance |
   | `relative_vertical` | vertical ordering, centroid/extent relation | violated when predicted vertical relation contradicts object height ordering |

4. Calibrated geometry validity:

   ```text
   p_geom_valid_i = C_a(phi(g_i))
   ```

   where `phi(g_i)` is the geometry feature vector and `C_a` is either the pooled or family-specific frozen calibrator trained on `train_dev_calib` positives and counterfactual negatives.

5. Re-ranking operating points:

   ```text
   score_geocalib_i = score_sem_i * p_geom_valid_family_i
   score_pooled_i = score_sem_i * p_geom_valid_i
   ```

   Main reported variants:

   | variant | ranking/filter rule | role |
   | --- | --- | --- |
   | `semantic_only` | rank by `score_sem` | reproduced source baseline |
   | `family_conditional_risk` | rank by `score_sem * p_geom_valid_family` | RelCompat3D main score |
   | `probabilistic_recalibrated` | rank by `score_sem * p_geom_valid` | pooled calibrated-risk ablation |
   | `rule_verified_point_subtype` | remove hard `violated` rows before ranking | zero-violation diagnostic |

6. Nontriviality controls:

   | control | what it breaks/tests |
   | --- | --- |
   | geometry-only | tests whether semantic confidence is still necessary |
   | distance-only | tests whether a simple distance heuristic explains the result |
   | shuffled geometry | breaks instance identity while preserving parts of the geometry distribution |
   | wrong-pair geometry | tests whether object-pair-specific geometry is necessary |

Algorithm skeleton:

```text
Input: relation predictions P, scene geometry G, calibrator C, family map F
Output: ranked relation rows with semantic score, geometry evidence, p_geom_valid, and verifier status

1. Standardize P into identity-preserving relation rows.
2. For each row, map predicate to a geometry-checkable family when possible.
3. Join object-pair geometry evidence by scan/subgraph/subject/object ids.
4. Run family-specific geometry checks and assign satisfied/uncertain/violated status.
5. Estimate p_geom_valid with the frozen pooled and family-specific calibrators.
6. Produce rankings: semantic-only, main family-conditional RelCompat3D, pooled calibrated ablation, and rule-verified diagnostic.
7. Evaluate exact-label R@K and Violation@K on the fixed in-scope denominator.
```

Method wording rule:

- Write "calibrated geometry-consistency evaluation and re-ranking framework."
- Do not write "geometry verifier post-processing script."

### 5. Experimental Setup

Main job:

- Describe datasets, prediction sources, splits, Docker reproduction, and evaluation protocol.
- Keep the title as `Experimental Setup`; explain fixed scope, denominator,
  filtered splits, and Docker-result boundaries in the section body rather than
  in the heading.

Subsections:

- 5.1 H001 fixed held-out scope.
- 5.2 `VL-SAT` reproduced closed-set source.
- 5.3 Open3DSG reproduced second-source variant.
- 5.4 Metrics and controls.
- 5.5 Reproducibility and locked artifacts.

Evidence/artifacts:

- `docs/reproducibility.md`
- `results/h001_geom_reliability/report.md`
- `experiments/H001_geom_reliability/commands.md`
- `experiments/H001_geom_reliability/sources/open3dsg/paper_caveats/report.md`

Open3DSG caveats that must be in this section:

- Full official validation scope: 157 scans / 548 contexts / 3,972 H001-family GT rows.
- Selected official non-avg Open3DSG checkpoint `epoch=13-step=13104.ckpt`, chosen by train-dev `val/loss`.
- Filtered train split: 3,744/3,852 subgraphs.
- Train-dev validation split: 156/160 subgraphs.
- Open3DSG main table branch: `recovery_relaxed_views_min2/`, 548/548 contexts, with `OPEN3DSG_MIN_VISIBLE_OBJECTS=2` and relaxed view regeneration for two scans.
- The original 533/548 full-validation covered branch remains sensitivity / unmodified-source-route evidence.
- Historical 127-scan Open3DSG numbers belong only in appendix/sensitivity: old 377/388 comparison row versus R2 388/388 representative historical branch.
- Exact-label full-validation H001-family denominator: 3,972.

### 6. Main Results

Main job:

- Show that calibrated geometry-consistency reduces violations while preserving measurable recall tradeoffs.

Tables:

- AAAI Table 1: fixed H001 evaluation scope and denominator.
- AAAI Table 2: main source results, with Open3DSG first as the main
  open-vocabulary case study and `VL-SAT` second as the controlled reproduced
  anchor.
- AAAI Table 3: controls and diagnostics for geometry-only, distance-only,
  shuffled-geometry, and wrong-pair explanations.
- Source-specific claim boundary / non-claims, GT-based verifier evaluation,
  structured audit, visual sanity check, and detailed family rows are summarized
  in prose unless an appendix is added.

Result interpretation:

- `VL-SAT` `probabilistic_recalibrated` improves R@50/R@100 and lowers violations relative to semantic-only.
- `rule_verified_point_subtype` gives a zero-violation diagnostic, not the default main setting.
- Controls show the effect is not explained by geometry-only ranking, simple distance, shuffled geometry, or wrong-pair geometry.
- Open3DSG supports the same reliability direction within measured H001 families, with stronger caveats.

Reviewer defense:

- Always report recall and violation together.
- Do not present violation reduction without recall tradeoff.
- Do not hide Open3DSG caveats in table footnotes only.

Results prose skeleton:

```text
The main question is whether geometry-consistency scoring reduces physically inconsistent relation predictions without collapsing recall. On VL-SAT, the main family-conditional score improves exact-label recall while reducing violations relative to semantic-only ranking. The pooled calibrated score is reported as a recall-favoring ablation, and the hard rule-verified variant is reported as a diagnostic zero-violation point rather than the default method because it exposes the upper end of the reliability-recall tradeoff.
```

Control prose skeleton:

```text
The control conditions show that the effect is not explained by geometry alone or by a generic distance prior. Geometry-only and distance-only rankings underperform the semantic source, while shuffled and wrong-pair geometry degrade the reliability signal. This supports the design requirement that geometry evidence must be joined to the correct object pair and calibrated as a relation-level reliability signal.
```

Open3DSG prose skeleton:

```text
Open3DSG provides second-source evidence rather than a broad open-vocabulary SOTA claim. Under the measured H001-family scope, geometry-consistency variants again reduce violations under explicit recall tradeoffs. The main result is reported on the full-validation 548/548 recovery branch with selected-checkpoint, filtered-split, recovery-policy, exact-denominator, and residual-calibration caveats stated in the experimental setup and table notes. Historical 127-scan old 377/388 versus R2 388/388 belongs in appendix/sensitivity only.
```

### 7. Failure Analysis

Main job:

- Explain when semantic plausibility and physical consistency diverge.
- Show where geometry-aware reranking helps.
- Expose residual calibration risk.

Evidence:

- Open3DSG real failure-analysis rows: 57,736 rows, 0 validation errors.
- Qualitative inspection: 36 cases.
- 23/36 selected cases demoted by geometry-aware reranking.
- 10/36 sampled rule-violated cases still have `p_geom_valid > 0.9`.

Reviewer defense:

- Report residual calibration risk as a limitation and design insight.
- Use it to justify reporting the main family-conditional score alongside pooled and rule-verified variants.
- Do not claim the calibrated score is a hard validity label.

Failure-analysis prose skeleton:

```text
The qualitative cases support the failure mechanism: some relation predictions remain semantically plausible from object categories but are contradicted by contact, distance, or vertical arrangement in the reconstructed scene. Geometry-aware reranking demotes many such cases, which explains the reduction in Violation@K. At the same time, residual high-confidence but rule-violated cases show that p_geom_valid should not be interpreted as a hard validity label. This is why the paper reports the main family-conditional score alongside pooled and rule-verified variants.
```

### 8. Limitations

Required limitations:

- Scope limited to geometry-checkable relation families.
- Current claim is closed-set/GT-object and measured-family reliability evidence.
- Open3DSG main result uses the selected official non-avg checkpoint on the full-validation 548/548 recovery-policy branch with filtered train/dev provenance.
- The original 533/548 full-validation covered branch and historical old 377/388 versus R2 388/388 comparison are sensitivity evidence, not main table rows.
- Reduced visual sanity check is not a large-scale independent audit.
- Qwen-VL is optional and not metric evidence yet.

Reviewer defense:

- Limitations should be explicit enough that they cannot be framed as hidden denominator manipulation.
- State why these limitations do not invalidate the scoped reliability claim.

Limitation prose skeleton:

```text
The current study is intentionally scoped to geometry-checkable relation families. Relations whose correctness depends primarily on functional, social, affordance, or language-pragmatic context are outside the H001 metric claim. The evaluation also uses closed-set/GT-object relation rows and exact predicate-label recall, so the results should be read as relation-reliability evidence rather than full open-vocabulary scene graph generation performance.
```

```text
The Open3DSG main experiment uses a selected official non-avg checkpoint on the full-validation 548/548 recovery-policy branch with explicit filtered-split, recovery-policy, and sensitivity caveats. The checkpoint is selected by train-dev validation loss before validation source-result reporting. The original 533/548 full-validation covered branch and the historical old 377/388 versus R2 388/388 comparison remain sensitivity evidence. These choices do not invalidate the scoped reliability result, but they prevent claims of broad open-vocabulary SOTA or unmodified Open3DSG preprocess reproduction.
```

```text
Finally, p_geom_valid is a calibrated reliability score, not a proof of physical correctness. The residual calibration-risk cases motivate reporting hard rule-verified and family-conditional risk variants alongside the probabilistic setting, and motivate future work on broader predicate families, stronger visual audit, and modern VLM relation sources.
```

### 9. Conclusion

Main job:

- Restate the failure-mechanism contribution.
- Restate calibrated geometry-consistency as the method contribution.
- Summarize evidence across `VL-SAT` and Open3DSG.
- Point to future work: `attachment_deferred` as the next physical-relation
  upgrade, modern VLM sources, functional/robotics relations, and
  online/embodied settings.
- Do not jump directly from H001 to broad function reasoning. If the paper
  expands, use the completed G0 scope/schema audit, G1 extractor contract, G1b
  evidence-only dry run, G1c point/surface validation, G2 conservative verifier
  policy, G3 calibration/counterfactual route, G4 GT policy smoke, G4b
  error/visual sanity planning, G4c strict-only calibration-filter freeze, and
  G5a pooled strict calibration fit, G5b bounded source scoring preflight, and
  G5c full-source protocol freeze for
  `attached to` / `hanging on` / `connected to`; next freeze the full-source
  scoring/metric protocol before adding any small function reasoning case
  study.

## Figure Plan

Figure 1:

- Failure mechanism and framework overview.
- Show semantic-only ranking, geometry evidence, calibrated consistency score, and re-ranked output.

Figure 2:

- Reliability-recall tradeoff across semantic-only, main family-conditional RelCompat3D, pooled calibrated ablation, and rule-verified diagnostic points.
- Show why recall and violation must be reported together.

Figure 3:

- Qualitative failure taxonomy.
- Show examples where semantic plausibility and physical consistency diverge.
- Include residual calibration-risk examples.

Source:

- `results/h001_geom_reliability/figures/figure_specs.md`
- `experiments/H001_geom_reliability/sources/open3dsg/failure_cases/inspection.md`

## Figure Asset Plan

Status: `content_plan_ready_assets_to_generate_later`

Figure 1: framework overview

- Panel A: semantic relation source emits object-pair predicate scores.
- Panel B: relation-row standardization preserves `(scan_id, subgraph_id, subject_id, object_id)`.
- Panel C: identity-preserving geometry join attaches OBB, point/local, contact, distance, and vertical evidence.
- Panel D: family-specific verifier and calibrator produce `status` and `p_geom_valid`.
- Panel E: semantic-only and geometry-aware ranked lists are compared under `R@K` and `Violation@K`.
- Source inputs: `02_method.md`, `manifest.lock.json`, `figure_specs.md`.
- Generation mode: diagram/manual figure; no new metric computation needed.

Figure 2: reliability-recall tradeoff

- Plot/table-panel candidates:
  - x-axis: `R@100` or recall retention.
  - y-axis: `Violation@100`.
  - points: `semantic_only`, `probabilistic_recalibrated`, `rule_verified_point_subtype`, `family_conditional_risk`.
  - optional separate markers for `VL-SAT` and Open3DSG.
- Source inputs:
  - `results/h001_geom_reliability/tables/table1_main_prediction.json`
  - `results/h001_geom_reliability/tables/table6_cross_source_status.json`
- Reviewer role: prevents "violation reduction is only pruning" by showing recall and violation together.

Figure 3: qualitative failure taxonomy

- Panel groups:
  - semantic plausibility but support/contact contradiction.
  - semantic plausibility but proximity contradiction.
  - semantic plausibility but vertical-order contradiction.
  - residual high-`p_geom_valid` rule-violated case.
- Source inputs:
  - `experiments/H001_geom_reliability/sources/open3dsg/failure_cases/inspection.md`
  - `experiments/H001_geom_reliability/sources/open3dsg/failure_rows/`
  - optional visual assets only if already reproducible from local data.
- Reviewer role: supports failure mechanism and discloses residual calibration risk.

Do not generate new visual claims unless source rows, scan/object ids, and geometry evidence are traceable.

## Manuscript-Ready Figure Captions

Figure 1 caption draft:

```text
Overview of calibrated geometry-consistency evaluation and re-ranking. A relation source first produces semantic predicate scores for object pairs. We standardize these predictions into identity-preserving relation rows, join 3D geometry evidence for the same object pair, estimate relation-family-specific geometric validity scores, and report the main family-conditional RelCompat3D score with pooled and rule-verified variants. This framing treats geometry consistency as a calibrated reliability layer, not as a replacement relation predictor.
```

Reviewer-defense role:

- Defends against "this is only a verifier script" by showing a framework with row standardization, identity preservation, geometry evidence, calibration, and operating points.
- Keeps the method scoped as reliability evaluation/re-ranking rather than broad 3DSSG generation.

Figure 2 caption draft:

```text
Recall-violation tradeoff across semantic-only and geometry-consistency
operating points on the H001 held-out relation scope. The family-conditional
risk condition is the RelCompat3D main score, the pooled calibrated condition is
an ablation, and the rule-verified condition provides a zero-violation
diagnostic with a recall tradeoff. This figure should be read as a reliability
tradeoff, not as a standalone SOTA leaderboard.
```

Reviewer-defense role:

- Defends against "violation reduction only comes from pruning recall" by showing recall and violation jointly.
- Clarifies why main family-conditional, pooled, and rule-verified variants are reported separately.

Figure 3 caption draft:

```text
Geometry-backed qualitative failure patterns where semantic plausibility diverges from physical consistency. The selected Open3DSG cases use the same locked inspection rows and preprocessed object point clouds to illustrate relations that are plausible from object semantics but contradicted by contact, proximity, or vertical arrangement in 3D. Geometry-aware re-ranking demotes many such cases, while residual high-confidence but rule-violated examples reveal calibration risk and motivate separate reporting of probabilistic and rule-verified outputs.
```

Reviewer-defense role:

- Defends the failure-mechanism claim with traceable qualitative cases.
- Prevents overclaiming by explicitly showing residual calibration risk.
- Should not be described as a representative large-scale visual audit.

Korean caption notes:

- Figure 1은 method가 "script"가 아니라 calibrated reliability framework임을 보여주는 그림이다.
- Figure 2는 recall과 violation을 동시에 보여줘 pruning-only 공격을 방어하는 그림이다.
- Figure 3은 semantic plausibility와 physical consistency mismatch를 보여주되, residual calibration risk도 숨기지 않는 그림이다.

## Table Plan

| table | purpose | source artifact |
| --- | --- | --- |
| AAAI Table 1 | Fixed H001 evaluation scope and denominator | `paper/aaai/sec/5_experiments.tex`, `results/h001_geom_reliability/tables/table5_claim_boundary.md` |
| AAAI Table 2 | Main source results: Open3DSG first, `VL-SAT` controlled anchor second | `paper/aaai/sec/6_results.tex`, `results/h001_geom_reliability/tables/table6_cross_source_status.md`, `results/h001_geom_reliability/tables/table1_main_prediction.md` |
| AAAI Table 3 | Controls and diagnostics for geometry-only, distance-only, shuffled-geometry, and wrong-pair alternatives | `paper/aaai/sec/6_results.tex`, `results/h001_geom_reliability/tables/table2_controls.md` |
| Prose evidence | Source-specific claim boundary / non-claims, GT verifier, structured audit, visual sanity check, and family details | `paper/aaai/sec/5_experiments.tex`, `paper/aaai/sec/7_limitations.tex`, `results/h001_geom_reliability/tables/table5_claim_boundary.md`, `table3_gt_verifier.md`, `table4_audit.md` |

## Table And Appendix Placement

Status: `draft_placement_ready`

Recommended main-paper tables:

| table | placement | reason |
| --- | --- | --- |
| Table 1 | main | fixed H001 denominator and source outputs |
| Table 2 | main | Open3DSG-first source results with VL-SAT as controlled anchor |
| Table 3 | main | controls and diagnostics that rule out simpler explanations |

Recommended appendix tables:

| table | placement | reason |
| --- | --- | --- |
| Calibrator / threshold provenance | appendix | shows family mapping, rule thresholds, counterfactual construction, calibrator artifacts, and held-out use were fixed before source-result reporting |
| Source-specific claim boundary | prose or appendix | keeps blocked extensions and non-claims visible without consuming a main table |
| Audit / visual sanity detail | appendix with short main-text summary | structured audit and 50-row visual sanity check are reviewer-defense evidence, not the primary metric result |
| Detailed family-conditional risk rows | appendix | useful for transparency without crowding main result |
| Full Open3DSG caveat/coverage accounting | appendix with main-text caveat summary | keeps denominator/filter details traceable |
| Qwen-VL runtime smoke, if run | appendix/future-work only | not main metric evidence unless promoted with full Docker metric/audit treatment |

Space-risk fallback:

- Keep controls, GT verifier, audit, and visual sanity checks as prose evidence unless an appendix is added.
- Do not remove Open3DSG caveats from manuscript Table 2; move details to appendix only if the main text still states the variant, covered scope, denominator, and residual calibration risk.
- The current provenance appendix owner is `paper/appendix.md`; update it before changing calibration, thresholds, Open3DSG caveat wording, Figure 3 final-polish status, or Qwen-VL boundary.

## Next Drafting Tasks

1. Continue only final caption/prose polish unless a new layout issue appears.
2. Current visual/layout inspection confirms the Open3DSG-first 9-page build has no missing citations, undefined refs, or overfull hbox warnings.
3. Use the generated geometry-backed Figure 3 panel as the preferred draft; keep rendered scene crops only as optional final polish if deterministic rendering is added.
4. Keep Qwen-VL as optional appendix/future-work material unless it is promoted with full Docker metric, denominator, and audit treatment.

## Korean Outline

이 섹션은 위 outline을 한국어로 병기한 작성 지침이다. 영어 논문 초안은 위 구조를 따르되, 실제 논리 점검은 이 한국어 버전으로도 확인한다.

### 작성 제약

사실:

- 후보 주제는 `CAND-001 / H001_geometry-grounded-verification`이다.
- 방법 기여는 calibrated geometry-consistency evaluation and re-ranking framework로 쓴다.
- 핵심 실험 소스는 `VL-SAT`와 Open3DSG다.
- 핵심 relation family는 `support_contact`, `proximity`, `relative_vertical`이다.
- 논문 본문용 실험 결과는 Docker로 재현 가능해야 한다.

추론:

- 이 논문은 geometry-checkable 3DSSG relation family에 대한 relation reliability 논문으로 좁혀야 한다.
- broad open-vocabulary 3DSSG SOTA 논문으로 쓰면 안 된다.
- novelty는 "geometry를 추가했다"가 아니라, semantic plausibility가 relation-level physical consistency와 calibration되어 있지 않다는 실패 원인과 그 원인 때문에 calibrated geometry-consistency reliability layer가 필요하다는 연결에 있다.

비주장:

- arbitrary-baseline generality를 주장하지 않는다.
- full open-vocabulary 3DSSG generation improvement를 주장하지 않는다.
- exact non-averaged Open3DSG reproduction을 주장하지 않는다.
- reduced visual sanity check를 large-scale 또는 strictly blinded human audit로 표현하지 않는다.

### 현재 허용 Claim

허용되는 현재 claim:

```text
Geometry-checkable 3D scene graph relation family에서 calibrated geometry-consistency scoring은 semantically plausible하지만 physically inconsistent한 relation prediction을 드러내고, VL-SAT와 Open3DSG에서 recall tradeoff를 측정하면서 geometric violation을 줄일 수 있다.
```

claim boundary:

- `VL-SAT`는 primary closed-set relation-reliability 결과를 뒷받침한다.
- Open3DSG는 측정된 H001 family 내부에서 second-source evidence를 제공한다.
- Qwen-VL은 full Docker metric, bootstrap, audit treatment를 받기 전까지 third-source modern VLM extension evidence로만 둔다.

### Title Candidates

추천 primary title:

```text
Calibrating Geometric Consistency for Reliable 3D Scene Graph Relations
```

이 제목을 우선 추천하는 이유:

- calibration, geometric consistency, reliability, relation prediction이 모두 드러난다.
- broad open-vocabulary 3DSSG generation improvement를 과장하지 않는다.
- 현재 evidence인 `VL-SAT` + Open3DSG의 measured relation-family reliability claim과 맞다.

대안 title candidates:

1. `Measuring and Reducing Geometric Inconsistency in 3D Scene Graph Relations`
2. `Geometry-Consistent Reliability for 3D Scene Graph Relation Prediction`
3. `From Semantic Plausibility to Physical Consistency in 3D Scene Graph Relations`
4. `Calibrated Physical Consistency for 3D Scene Graph Relation Prediction`
5. `Reliability-Aware 3D Scene Graph Relations via Calibrated Geometry Consistency`
6. `Calibrated Geometry Re-Ranking for Relation Reliability in 3D Scene Graphs`
7. `When Plausible Relations Violate Space: Calibrated Geometry Consistency for 3D Scene Graphs`
8. `Evaluating Geometry-Consistent Reliability in 3D Scene Graph Relations`

피해야 할 title pattern:

- `Open-Vocabulary 3D Scene Graph Generation with Geometry`
- `A General Geometry Verifier for 3D Scene Graphs`
- `Improving 3D Scene Graph Prediction with Geometry`
- `State-of-the-Art Open-Vocabulary 3D Scene Graph Relations`

이유:

- generation, baseline generality, SOTA scope를 과장하거나 generic verifier/script처럼 보이게 만든다.

### Contribution Statements

추천 contribution wording:

1. Failure mechanism:
   3D Scene Graph prediction에서 relation-level reliability failure를 식별하고 formalize한다. Semantic relation confidence는 object-pair geometry와 calibration되어 있지 않기 때문에, 그럴듯하지만 물리적으로 일관되지 않은 predicate를 높게 rank할 수 있다.

2. Method framework:
   calibrated geometry-consistency evaluation and re-ranking framework를 제안한다. 이 framework는 prediction row를 source 간 표준화하고, identity-preserving 3D geometry evidence를 join하며, main `family_conditional_risk`, pooled calibrated ablation, rule-verified diagnostic을 분리해 보고한다.

3. Evaluation protocol:
   geometry-checkable relation family를 위한 recall-violation evaluation protocol을 정의한다. 여기에는 exact-label `R@K`, `Violation@K`, GT-positive/counterfactual verifier evaluation, geometry-only / distance-only / shuffled-geometry / wrong-pair geometry control이 포함된다.

별도 contribution bullet이 아니라 실험 결과로 둘 항목:

- `VL-SAT`와 Open3DSG cross-source result 및 failure analysis는 위 세 contribution을 검증하는 empirical evidence로 Results와 Failure Analysis에서 보여준다. 네 번째 contribution으로 쓰지 않는다.

논문 Introduction용 compact version:

```text
Our contributions are: (i) a failure formulation for semantically plausible but geometrically inconsistent 3D scene graph relations; (ii) a calibrated geometry-consistency evaluation and re-ranking framework with explicit operating points; and (iii) a recall-violation evaluation protocol with GT-based verifier checks and geometry identity controls. We validate these contributions with Docker-reproducible cross-source evidence on VL-SAT and Open3DSG, including failure analysis and residual calibration-risk disclosure.
```

피해야 할 contribution wording:

- "geometry를 3DSSG에 추가했다."
- "verifier script를 만들었다."
- "open-vocabulary 3DSSG를 개선했다."
- "baseline-agnostic relation predictor를 제공한다."
- "모든 3D relation의 physical consistency를 해결한다."

### 제목

상태: draft title candidates를 고정했다. 이후 논문 초안에서 더 나은 scoped phrase가 나오지 않으면 추천 primary title을 사용한다.

역할:

- relation reliability, geometry consistency, 3D scene graph가 드러나야 한다.
- broad open-vocabulary generation improvement처럼 보이면 안 된다.

추천 title:

```text
Calibrating Geometric Consistency for Reliable 3D Scene Graph Relations
```

### 초록

상태: draft skeleton을 고정했다. Introduction logic을 확장한 뒤 문장 순서와 수치를 다듬는다.

필수 논리:

1. 문제: semantic 3D relation predictor는 그럴듯하지만 물리적으로 일관되지 않은 edge를 만들 수 있다.
2. 원인: semantic confidence가 relation-level 3D geometry와 calibration되어 있지 않다.
3. 기여: failure mechanism, calibrated framework, recall-violation protocol.
4. 방법: calibrated geometry-consistency evaluation and re-ranking framework.
5. 근거: `VL-SAT` metric, controls, GT-based verifier evaluation, Open3DSG second-source result.
6. 경계: measured geometry-checkable relation family에 대한 결과이며, broad open-vocabulary 3DSSG SOTA가 아니다.

초록 skeleton:

```text
3D Scene Graph는 spatial reasoning에 유용한 object-relation 구조를 제공하지만, relation prediction은 predicate가 semantic하게 그럴듯해 보여도 물리적으로 일관되지 않을 수 있다.
본 연구는 semantic relation confidence가 object-pair geometry와 반드시 calibration되어 있지 않기 때문에 physically inconsistent relation이 높은 순위에 놓일 수 있다는 relation-level failure mode를 정의한다.
이를 검증하기 위해 geometry-checkable relation family를 대상으로 calibrated geometry-consistency evaluation and re-ranking framework를 제안한다.
이 framework는 prediction row를 표준화하고, identity-preserving 3D geometry evidence를 join하며, main `family_conditional_risk`, pooled calibrated ablation, rule-verified diagnostic을 분리해 보고한다.
또한 exact-label `R@K`, `Violation@K`, GT-positive/counterfactual verifier check, geometry identity control을 포함하는 recall-violation evaluation protocol을 정의한다.
`VL-SAT` 실험에서는 calibrated setting이 semantic-only ranking 대비 recall을 유지하거나 개선하면서 violation을 줄이며, controls는 이 효과가 geometry-only ranking, distance-only heuristic, shuffled geometry, wrong-pair geometry로 설명되지 않음을 보인다.
Open3DSG 결과는 measured H001-family scope에서 second-source evidence를 제공하고, failure analysis는 probabilistic geometry score의 residual overconfidence를 드러낸다.
따라서 본 연구의 claim은 broad open-vocabulary 3DSSG generation improvement가 아니라, geometry-checkable relation family에 대한 scoped relation-reliability claim이다.
```

짧은 초록 skeleton:

```text
Semantic 3D Scene Graph relation predictor는 그럴듯하지만 object-pair geometry와 충돌하는 relation을 생성할 수 있다. 본 연구는 이를 relation-level reliability failure로 formalize하고, geometry-checkable relation family를 위한 calibrated geometry-consistency evaluation and re-ranking framework를 제안한다. 이 framework는 identity-preserving 3D evidence를 join하고 main `family_conditional_risk`, pooled calibrated ablation, rule-verified diagnostic을 recall-violation protocol로 평가한다. `VL-SAT`와 Open3DSG 실험은 calibrated geometry-consistency가 measurable recall tradeoff 아래 geometric violation을 줄일 수 있음을 보이고, controls와 failure analysis는 geometry signal의 nontriviality와 residual calibration risk를 함께 드러낸다. 본 claim은 measured geometry-checkable 3DSSG relation reliability에 한정된다.
```

초록에 수치를 넣을 때만 사용할 후보:

- `VL-SAT` full-validation main `family_conditional_risk` R@50/R@100 `0.9288/0.9683` vs `semantic_only` `0.9272/0.9635`; Violation@100 `0.0333` vs `0.0476`.
- `VL-SAT` full-validation pooled `probabilistic_recalibrated` R@50/R@100 `0.9305/0.9688`; Violation@100 `0.0404`.
- Open3DSG full-validation recovery main `family_conditional_risk` R@50/R@100 `0.4658/0.6047` and Violation@50/@100 `0.0286/0.0341` vs `semantic_only` `0.4096/0.5161` and `0.1386/0.1242`.
- GT verifier: `p_geom_valid` AUROC/AUPRC `0.9772/0.9729`.

### 1. Introduction

주요 역할:

- 3D Scene Graph에서 relation reliability가 왜 중요한지 설명한다.
- semantic plausibility와 physical consistency가 어긋나는 구체적 failure mode를 정의한다.
- 단순히 geometry feature를 추가하는 문제가 아니라 relation-level consistency calibration 문제임을 설명한다.
- 논문의 scoped claim과 target relation family를 제시한다.

내부 근거:

- `VL-SAT` semantic-only violation.
- Open3DSG semantic-only violation.
- geometry-aware reranking이 inconsistent prediction을 demote한 qualitative failure case.

reviewer 방어:

- general SOTA generation paper가 아님을 분명히 한다.
- motivation-only novelty를 피한다.
- 관찰된 failure가 왜 calibrated geometry-consistency evaluation/re-ranking을 필요로 하는지 연결한다.

문단별 논리:

1. 3D Scene Graph relation reliability 문제:
   3D Scene Graph는 3D perception 결과를 object-relation 구조로 바꿔 spatial reasoning, robotics, downstream decision making에 유용하게 만든다. 하지만 여기서 병목은 object recognition만이 아니라, 예측된 relation이 실제 3D scene에서 물리적으로 일관적인지다.

2. 구체적 failure mode:
   semantic plausibility와 physical consistency가 어긋나는 failure를 정의한다. Predictor는 object category 관점에서는 그럴듯한 relation label에 높은 semantic confidence를 줄 수 있지만, 실제 object-pair geometry는 그 relation을 부정할 수 있다.

3. failure의 원인:
   이 문제는 단순히 "geometry feature가 없다"가 아니다. 핵심은 semantic relation confidence가 relation-level geometry와 calibration되어 있지 않다는 점이다. Relation score는 semantic plausibility score처럼 동작하지만, 그 relation이 geometrically valid한지에 대한 calibrated estimate가 아닐 수 있다.

4. 왜 이런 method 형태가 필요한가:
   failure 원인 때문에 calibrated geometry-consistency evaluation and re-ranking framework가 필요하다고 연결한다. 이 framework는 prediction row를 표준화하고, object-pair identity를 보존하며, 3D geometry evidence를 join하고, main `family_conditional_risk`, pooled calibrated ablation, rule-verified diagnostic을 recall-violation protocol로 보고해야 한다.

5. evidence preview:
   `VL-SAT`는 primary reproduced source, Open3DSG는 measured H001-family second-source evidence로 제시한다. Controls는 geometry-only ranking, distance-only heuristic, shuffled geometry, wrong-pair geometry로 효과가 설명되지 않는지 확인한다. GT-positive/counterfactual check는 verifier signal의 근거로 사용한다.

6. contribution과 scope:
   Introduction 마지막에는 3개 contribution을 제시하고, cross-source/failure analysis는 empirical validation으로 분리한다. Scope는 반드시 `support_contact`, `proximity`, `relative_vertical`의 measured geometry-checkable families이며, broad open-vocabulary 3DSSG generation이나 arbitrary-baseline generality가 아님을 명시한다.

문단 skeleton:

```text
3D Scene Graph는 object와 relation을 구조화해 spatial reasoning, robotics, downstream scene understanding을 지원할 수 있다. 이러한 활용에서 relation prediction은 category나 language 수준에서 그럴듯한 것을 넘어서, 실제 3D scene에서 물리적으로 신뢰할 수 있어야 한다.

본 연구는 semantic relation predictor가 실제 object pair에는 geometrically inconsistent한 relation label을 높게 rank할 수 있는 failure mode를 다룬다. 예를 들어 두 object category에는 그럴듯한 relation이라도, reconstructed 3D scene에서 contact, distance, vertical arrangement가 그 relation과 충돌할 수 있다.

이 failure는 단순한 geometry feature 부재가 아니다. 핵심은 semantic relation confidence가 relation-level physical consistency와 반드시 calibration되어 있지 않다는 점이다. 따라서 relation score는 semantic plausibility는 나타내지만, 해당 relation이 geometrically valid한지에 대한 calibrated estimate는 아닐 수 있다.

이 원인은 calibrated geometry-consistency evaluation and re-ranking framework를 필요로 한다. 이 framework는 relation source 간 prediction row를 표준화하고, object-pair identity를 보존하며, 3D geometry evidence를 join하고, main `family_conditional_risk`, pooled calibrated ablation, rule-verified diagnostic을 recall-violation protocol 아래 보고한다.

우리는 `VL-SAT`를 primary reproduced source로, Open3DSG를 measured H001-family second-source evidence로 사용해 framework를 평가한다. Geometry-only ranking, distance-only heuristic, shuffled geometry, wrong-pair geometry control은 효과의 nontriviality를 검증하고, GT-positive/counterfactual check는 verifier signal을 평가한다.

본 연구의 contribution은 세 가지다: (i) semantically plausible하지만 geometrically inconsistent한 3D scene graph relation에 대한 failure formulation, (ii) explicit operating point를 갖는 calibrated geometry-consistency evaluation and re-ranking framework, (iii) GT-based verifier check와 geometry identity control을 포함하는 recall-violation evaluation protocol. `VL-SAT`와 Open3DSG의 Docker-reproducible evidence 및 failure analysis는 이 세 contribution을 검증하는 empirical validation으로 사용한다.
```

쓰면 안 되는 표현:

- "기존 방법은 geometry를 무시한다."
- "geometry module을 추가했다."
- "open-vocabulary 3DSSG를 개선했다."
- "verifier가 physical correctness를 보장한다."
- "baseline-agnostic method다."

Introduction 끝나기 전 반드시 포함할 내용:

- relation families: `support_contact`, `proximity`, `relative_vertical`
- claim boundary: measured geometry-checkable relation reliability
- `VL-SAT`와 Open3DSG의 empirical validation 역할
- Qwen-VL은 full metric으로 승격하기 전까지 Introduction main evidence에서 제외

### 2. Related Work

주요 역할:

- 3DSSG prediction, open-vocabulary 3DSSG, geometry-aware relation modeling, scene graph reliability/calibration과의 관계를 정리한다.
- 기존 방법이 geometry를 전혀 쓰지 않는다고 말하지 않는다.
- gap은 relation-level calibrated consistency와 recall-violation tradeoff accounting이라고 정리한다.

하위 섹션:

- 2.1 3D Scene Graph relation prediction.
- 2.2 Open-vocabulary 3D Scene Graphs and VLM-based scene understanding.
- 2.3 Geometry-aware constraints and spatial relation reasoning.
- 2.4 Reliability, calibration, and post-hoc evaluation in structured prediction.

reviewer 방어:

- 기존 연구를 과소평가하지 않는다.
- "기존 연구는 geometry가 없다"가 아니라 "relation-level physical consistency를 calibrated reliability signal로 측정하고 recall tradeoff와 함께 보고하지 않는다"로 쓴다.

### 3. Problem Formulation

주요 역할:

- prediction row, object pair, predicate candidate, geometry evidence를 정의한다.
- target family인 `support_contact`, `proximity`, `relative_vertical`를 정의한다.
- `R@K`, `Violation@K`, recall retention, in-scope denominator를 정의한다.
- exact-label recall과 family-level reliability reporting을 분리한다.

근거 파일:

- `archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/02_method.md`
- `results/h001_geom_reliability/manifest.lock.json`
- `results/h001_geom_reliability/tables/table1_main_prediction.md`
- `experiments/H001_geom_reliability/sources/open3dsg/metric_scope/report.md`

reviewer 방어:

- 결과를 보여주기 전에 denominator를 명시한다.
- exact predicate recall과 family-level violation reporting을 혼동하지 않는다.
- excluded relation family를 분명히 적는다.

### 4. Method

주요 역할:

- calibrated geometry-consistency evaluation/re-ranking framework를 제시한다.
- relation-family-specific geometry check를 설명한다.
- `p_geom_valid`, hard rule verification, family-conditional calibration, re-ranking variant를 설명한다.

하위 섹션:

- 4.1 Relation-row standardization across prediction sources.
- 4.2 Geometry evidence extraction and relation-family checks.
- 4.3 Calibrated `p_geom_valid` scoring.
- 4.4 Re-ranking and operating points.
- 4.5 Controls: geometry-only, distance-only, shuffled geometry, wrong-pair geometry.

reviewer 방어:

- "verifier script"라는 표현을 피한다.
- calibration, operating point, identity-preserving join을 강조한다.
- hard rule과 probabilistic score를 왜 분리해서 보고하는지 설명한다.

### 5. Experimental Setup

주요 역할:

- dataset, prediction source, split, Docker reproduction, evaluation protocol을 설명한다.
- 제목은 `Experimental Setup`으로 유지하고, fixed scope, denominator,
  filtered split, Docker-result boundary는 제목이 아니라 본문에서 명시한다.

하위 섹션:

- 5.1 H001 fixed held-out scope.
- 5.2 `VL-SAT` reproduced closed-set source.
- 5.3 Open3DSG reproduced second-source variant.
- 5.4 Metrics and controls.
- 5.5 Reproducibility and locked artifacts.

근거 파일:

- `docs/reproducibility.md`
- `results/h001_geom_reliability/report.md`
- `experiments/H001_geom_reliability/commands.md`
- `experiments/H001_geom_reliability/sources/open3dsg/paper_caveats/report.md`

이 섹션에 반드시 들어갈 Open3DSG caveat:

- full official validation scope: 157 scans / 548 contexts / 3,972 H001-family GT rows.
- selected official non-avg Open3DSG checkpoint `epoch=13-step=13104.ckpt`, train-dev `val/loss`로 선택.
- filtered train split: 3,744/3,852 subgraphs.
- train-dev validation split: 156/160 subgraphs.
- Open3DSG main table branch: `recovery_relaxed_views_min2/`, 548/548 contexts, `OPEN3DSG_MIN_VISIBLE_OBJECTS=2`, relaxed two-scan view regeneration.
- original 533/548 full-validation covered branch는 sensitivity / unmodified-source-route evidence로만 사용.
- historical 127-scan Open3DSG는 appendix/sensitivity에서만 old 377/388 comparison row와 R2 388/388 representative branch로 비교.
- exact-label full-validation H001-family denominator: 3,972.

### 6. Main Results

주요 역할:

- calibrated geometry-consistency가 violation을 줄이면서 recall tradeoff를 측정 가능하게 만든다는 점을 보인다.

사용할 표:

- AAAI Table 1: fixed H001 evaluation scope and denominator.
- AAAI Table 2: main source results. Open3DSG를 main open-vocabulary case
  study로 먼저 제시하고 `VL-SAT`를 controlled reproduced anchor로 둔다.
- AAAI Table 3: controls and diagnostics. Geometry-only, distance-only,
  shuffled geometry, wrong-pair geometry 설명을 분리한다.
- Source-specific claim boundary / non-claims, GT-based verifier evaluation,
  structured audit, visual sanity check, detailed family row는 appendix가
  추가되기 전까지 prose-backed reviewer-defense evidence로 압축한다.

결과 해석:

- `VL-SAT`의 `probabilistic_recalibrated`는 semantic-only 대비 R@50/R@100을 높이고 violation을 낮춘다.
- `rule_verified_point_subtype`는 zero-violation diagnostic이며 default main setting은 아니다.
- controls는 결과가 geometry-only ranking, simple distance, shuffled geometry, wrong-pair geometry로 설명되지 않음을 보인다.
- Open3DSG는 더 강한 caveat이 있지만, 측정된 H001 family 안에서 같은 reliability 방향을 지지한다.

reviewer 방어:

- recall과 violation을 항상 같이 보고한다.
- violation reduction만 단독으로 강조하지 않는다.
- Open3DSG caveat을 table footnote에만 숨기지 않는다.

### 7. Failure Analysis

주요 역할:

- semantic plausibility와 physical consistency가 언제 어긋나는지 설명한다.
- geometry-aware reranking이 도움이 되는 케이스를 보여준다.
- residual calibration risk를 드러낸다.

근거:

- Open3DSG real failure-analysis rows: 57,736 rows, validation errors 0.
- qualitative inspection: 36 cases.
- 23/36 selected cases는 geometry-aware reranking으로 demote됨.
- 10/36 sampled rule-violated cases는 여전히 `p_geom_valid > 0.9`.

reviewer 방어:

- residual calibration risk를 limitation과 design insight로 보고한다.
- main family-conditional score, pooled ablation, rule-verified diagnostic을 분리해서 보고해야 하는 이유로 사용한다.
- calibrated score를 hard validity label이라고 주장하지 않는다.

### 8. Limitations

필수 limitation:

- scope는 geometry-checkable relation family로 제한된다.
- 현재 claim은 closed-set/GT-object와 measured-family reliability evidence다.
- Open3DSG main result는 selected official non-avg checkpoint와 full-validation 548/548 recovery-policy branch를 사용한다.
- original 533/548 full-validation covered branch와 historical old 377/388 versus R2 388/388 comparison은 sensitivity evidence로만 사용한다.
- reduced visual sanity check는 large-scale independent audit가 아니다.
- Qwen-VL은 optional이며 아직 metric evidence가 아니다.

reviewer 방어:

- limitation을 충분히 명시해서 hidden denominator manipulation처럼 보이지 않게 한다.
- 이 limitation들이 scoped reliability claim을 무효화하지 않는 이유를 설명한다.

### 9. Conclusion

주요 역할:

- failure-mechanism contribution을 다시 요약한다.
- calibrated geometry-consistency를 method contribution으로 다시 정리한다.
- `VL-SAT`와 Open3DSG evidence를 요약한다.
- future work로는 broader predicates를 일반적으로 말하기보다
  `attachment_deferred`를 다음 physical-relation upgrade로 먼저 제시한다.
  G0 scope/schema audit, G1 extractor contract, G1b evidence-only dry run,
  G1c point/surface validation, G2 conservative verifier policy design, G3
  calibration/counterfactual route, G4 GT policy smoke, G4b error/visual
  sanity planning, G4c strict-only calibration filter freeze, G5a pooled strict
  calibration fit, G5b bounded source scoring preflight, G5c full-source
  protocol freeze는 완료되었고, 다음은 optional G5d full-source scoring plus
  metrics/controls다.
  function reasoning은 attachment reliability가 검증된 뒤의 secondary pilot로 둔다.

### Figure Plan

Figure 1:

- failure mechanism과 framework overview.
- semantic-only ranking, geometry evidence, calibrated consistency score, re-ranked output을 보여준다.

Figure 2:

- reliability-recall tradeoff.
- semantic-only, main family-conditional RelCompat3D, pooled calibrated ablation, rule-verified diagnostic을 비교한다.

Figure 3:

- qualitative failure taxonomy.
- semantic plausibility와 physical consistency가 어긋나는 사례를 보여준다.
- residual calibration-risk example을 포함한다.

근거:

- `results/h001_geom_reliability/figures/figure_specs.md`
- `experiments/H001_geom_reliability/sources/open3dsg/failure_cases/inspection.md`

### Table Plan

| table | 목적 | source artifact |
| --- | --- | --- |
| AAAI Table 1 | Fixed H001 evaluation scope and denominator | `paper/aaai/sec/5_experiments.tex`, `results/h001_geom_reliability/tables/table5_claim_boundary.md` |
| AAAI Table 2 | Main source results: Open3DSG first, `VL-SAT` controlled anchor second | `paper/aaai/sec/6_results.tex`, `results/h001_geom_reliability/tables/table6_cross_source_status.md`, `results/h001_geom_reliability/tables/table1_main_prediction.md` |
| AAAI Table 3 | Controls and diagnostics for geometry-only, distance-only, shuffled-geometry, and wrong-pair alternatives | `paper/aaai/sec/6_results.tex`, `results/h001_geom_reliability/tables/table2_controls.md` |
| Prose evidence | Source-specific claim boundary / non-claims, GT verifier, structured audit, visual sanity check, and family details | `paper/aaai/sec/5_experiments.tex`, `paper/aaai/sec/7_limitations.tex`, `results/h001_geom_reliability/tables/table5_claim_boundary.md`, `table3_gt_verifier.md`, `table4_audit.md` |

## Manuscript-Ready Table Captions

AAAI Table 1 caption draft:

```text
Fixed H001 evaluation scope. The paper claim is limited to the measured geometry-checkable families and the listed source outputs. Recall is exact predicate-label recall over the in-scope GT denominator; family grouping is used for reliability and violation reporting, not for relaxing predicate matches.
```

Reviewer-defense role:

- Locks the denominator before results.
- Prevents reviewer confusion between fixed H001 scope, source-specific loadability, and exact-label recall.

AAAI Table 2 caption draft:

```text
Main source results for the measured H001-family reliability claim. Open3DSG is reported first as the main open-vocabulary case study after Docker checkpoint reproduction, identity-preserving raw dump, prediction export, geometry join, and metric evaluation; VL-SAT is reported second as a controlled reproduced anchor. The table uses the full official 3,972-row denominator and the fixed K={5,10,20,50,100} grid. Open3DSG caveats must retain selected-checkpoint, filtered train/dev, recovery-policy, exact-label denominator, 533/548 sensitivity, appendix historical 377/388 versus R2 388/388 sensitivity, and residual calibration-risk wording.
```

Reviewer-defense role:

- Defends against "closed-set-only" by making Open3DSG the main open-vocabulary case study.
- Defends against denominator/caveat attacks by placing Open3DSG limitations directly in the caption.
- Prevents broad open-vocabulary generation claims.

AAAI Table 3 caption draft:

```text
Controls and diagnostics for the geometry-consistency signal. Geometry-only and distance-only variants test whether simple geometric heuristics explain the result, while shuffled-geometry and wrong-pair-geometry variants break object-pair identity while preserving parts of the geometry distribution. The degradation under these controls supports the need for identity-preserving relation-level geometry rather than generic spatial priors.
```

Reviewer-defense role:

- Defends against "this is just distance" or "geometry alone explains the result."
- Supports the novelty rule by linking the failure cause to object-pair geometry consistency.

Prose claim-boundary note draft:

```text
Source-specific claim boundary for H001. Open3DSG is the main open-vocabulary relation-source case study, VL-SAT is a controlled reproduced anchor, and Qwen-VL remains a third semantic source / modern VLM extension unless promoted with the same denominator, Docker, metric, bootstrap, and audit treatment. FROSS remains blocked as a full-family source. Broad open-vocabulary 3DSSG improvement is not claimed from the current evidence.
```

Reviewer-defense role:

- Makes non-claims explicit.
- Prevents the paper from drifting from scoped reliability evidence to baseline-agnostic or broad open-vocabulary claims.

Prose evidence caption/note draft for GT verifier:

```text
GT-based verifier evaluation using matched GT-positive relations and counterfactual negatives. GT positives should remain nonviolated, counterfactual negatives should not be satisfied, and p_geom_valid should separate the two groups. This evidence evaluates the geometry-consistency score itself before using it for prediction re-ranking.
```

Reviewer-defense role:

- Defends against "rules were chosen after looking at test predictions."
- Shows that `p_geom_valid` has independent GT/counterfactual support.

Prose evidence caption/note draft for audit:

```text
Structured audit and reduced visual sanity check for geometry-consistency decisions. The structured audit measures invalid-only and broader quality-issue precision, while the 50-row visual spot-check tests target-bucket quality and contradiction rates. These results are used as sanity and reviewer-defense evidence, not as a large-scale or strictly blinded human audit.
```

Reviewer-defense role:

- Provides qualitative sanity evidence while keeping provenance limitations visible.
- Prevents overclaiming the visual check as a large independent audit.

Korean caption notes:

- AAAI Table 1은 denominator/scope를 잠근다.
- AAAI Table 2는 Open3DSG-first main source result이며 Open3DSG caveat을 caption에 직접 넣어야 한다.
- AAAI Table 3은 controls and diagnostics 표이며 geometry-only/distance-only/identity-breaking 대안을 분리한다.
- Claim boundary와 non-claim은 main table이 아니라 Experimental Setup, Limitations, and Results prose에서 명시한다.
- Calibrator / threshold provenance는 `paper/appendix.md`가 소유한다. Family mapping, rule threshold, counterfactual construction, calibrator artifact, held-out 사용 여부가 바뀌면 먼저 이 파일을 갱신한다.
- Controls, GT verifier, audit는 본문 prose evidence로 남기되 appendix가 생기면 상세 표로 옮길 수 있다.

## Claim-Consistency Review

Status: `passed_claim_review_content_inventory_next`

Reviewed scope:

- Title candidates
- Contribution statements
- Abstract skeleton
- Introduction logic
- Figure 1-3 captions
- Table 1-6 captions

Review result:

| item | status | decision |
| --- | --- | --- |
| Title | pass | The recommended title claims relation reliability through calibrated geometric consistency, not broad open-vocabulary generation SOTA. |
| Contributions | pass | The paper has three contribution bullets: failure mechanism, calibrated framework, and recall-violation evaluation protocol. Cross-source results and failure analysis remain empirical validation. |
| Abstract | pass | The abstract states a scoped reliability claim for geometry-checkable relation families and explicitly excludes broad open-vocabulary 3D Scene Graph generation. |
| Introduction | pass | The logic ties the observed failure cause to method necessity: semantic relation confidence is not calibrated to relation-level physical consistency. |
| Figure captions | pass | Figures frame the method as a reliability layer, show recall-violation tradeoffs, and disclose residual calibration risk. |
| Table captions | pass | AAAI Table 1 fixes denominator/scope, Table 2 reports Open3DSG-first source results with caveats, and Table 3 reports controls/diagnostics. Claim boundary, GT verifier, and audit evidence are summarized in prose unless an appendix is added. |

Allowed manuscript claim:

```text
For geometry-checkable 3D scene graph relation families, calibrated geometry-consistency scoring exposes semantically plausible but physically inconsistent relation predictions and can reduce geometric violations while preserving measurable recall tradeoffs across VL-SAT and Open3DSG.
```

Do not drift into these claims:

- H001 improves broad open-vocabulary 3D Scene Graph generation.
- H001 is a baseline-agnostic relation predictor.
- The method is just a verifier script.
- Qwen-VL is part of the main metric evidence before full-source promotion.
- Open3DSG is reproduced as an exact non-averaged BLIP official route.
- Reduced visual sanity checks are large-scale blinded human audits.

Korean review note:

- 현재 abstract, Introduction, table caption, figure caption은 모두 scoped relation-reliability claim과 일치한다.
- AAAI Table 2는 caveat을 숨기지 않는 점이 중요하다. Table 3는 controls/diagnostics 방어 역할을 유지한다.
- Qwen-VL은 third semantic source / modern VLM extension으로만 두며, full-source Docker metric, bootstrap, audit가 끝나기 전에는 본문 main evidence로 승격하지 않는다.

## Paper Content Coverage Checklist

Status: `content_blocks_secured_draft_figures_layout_reviewed_aaai_defense_passed`

Purpose:

- Before polishing captions or camera-ready wording, confirm that every paper-body claim has corresponding evidence, table/figure placement, limitation wording, and reviewer defense.

Content already secured:

| paper content | evidence status | source |
| --- | --- | --- |
| Problem and failure mechanism | secured | `paper/outline.md`, `docs/paper.md`, qualitative failure inspection |
| Three contribution structure | secured | failure mechanism, calibrated framework, recall-violation protocol |
| `VL-SAT` controlled-anchor result | secured | AAAI Table 2 plus Table 3 controls, GT verifier, and audit evidence |
| Nontriviality controls | secured | geometry-only, distance-only, shuffled-geometry, wrong-pair controls |
| GT-based verifier evaluation | secured | GT-positive/counterfactual metrics |
| Open3DSG main open-vocabulary case study | secured with caveats | AAAI Table 2, Open3DSG metrics, raw-dump provenance, failure rows |
| Failure analysis | secured as qualitative/reviewer-defense evidence | 57,736 rows and 36 inspected cases |
| Reproducibility | secured | Docker experiment root, `docs/reproducibility.md`, locked manifests, AAAI checklist after references |
| Claim boundary | secured | `docs/paper.md`, Experimental Setup / Limitations prose, Open3DSG caveat wording |
| Qwen-VL optional extension boundary | secured as optional/non-metric | contract/cache ready, no main metric claim |

Content blocks secured in this outline pass:

| content block | status | next use |
| --- | --- | --- |
| Related-work positioning map | secured | Convert section-level bullets into Related Work prose with citations. |
| Method formalization | secured | Convert notation, operating points, and algorithm skeleton into Problem/Method sections. |
| Figure asset plan | secured | Generate figures later from locked sources; no new claims without traceable rows. |
| Table placement and appendix split | secured | Use AAAI Tables 1-3 in main paper; keep calibrator/threshold provenance, controls, GT verifier, audit details, family details, and Qwen as prose/appendix candidates. |
| Limitation paragraphs | secured | Convert caveat paragraphs into Limitations/Discussion prose. |
| Reviewer-attack response text | secured | Convert control, Open3DSG, and failure-analysis skeletons into Results/Discussion prose. |
| Optional Qwen-VL decision | scoped | Keep as appendix/future-work only unless promoted with full Docker metric/audit treatment. |
| AAAI reproducibility checklist | inserted | Revisit `partial/no` answers after final artifact/code-release packaging. |
| AAAI reviewer-defense pass | secured | Main text directly answers hand-coded verifier, geometry-only/distance, recall-tradeoff, Open3DSG recovery-policy provenance, family-selection, and AAAI-relevance attacks. |

Priority:

1. Optional final caption/prose polish: keep Open3DSG main without overclaiming broad open-vocabulary generation.
2. Keep only optional final Figure 3 scene-crop polish if deterministic rendering is added; the geometry-backed panel is already generated.
3. Polish captions further only if needed; do not hide Open3DSG caveats.

### 다음 Drafting Task

1. 필요하면 final caption/prose polish만 진행한다. Open3DSG-first layout은 이미 반영되었고, broad open-vocabulary generation claim으로 과장하지 않는 것이 핵심이다.
2. Figure 3은 현재 geometry-backed point-cloud panel을 preferred draft로 사용한다. Scene crop은 같은 locked case ID를 보존하는 deterministic rendering path가 추가될 때만 final polish로 고려한다.
