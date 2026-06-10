# Survey 0609: Semantic-Geometry Consistency Representation for 3D Scene Graphs

- Date checked: 2026-06-09 KST
- Work scope: new H001-adjacent branch only. Existing H001 hypothesis, experiment, and paper files were not modified.
- Working root: `literature/survey_0609/`
- Full 100-paper inventory: `meta/selected_papers.md`
- PDF/cache manifest: `meta/download_manifest.json`
- Code inventory: `meta/code_inventory.md`

## 0. Search And Download Record

Facts:

- The requested "Google Scholar 100-paper" pass was approximated with primary-source collection because Google Scholar has no official public API and automated scraping is commonly blocked by CAPTCHA/rate limiting.
- Semantic Scholar Graph API returned HTTP `429 Too Many Requests` during this run. This is an API quota/rate-limit response, usually from unauthenticated or shared-IP usage; it is not a paper-access or copyright issue.
- Primary sources used instead: existing `literature/` seed papers, arXiv API, OpenAlex API, CVF Open Access, PMLR, RSS proceedings, NeurIPS pages, official project pages, and official GitHub repositories.
- Selected papers: 100.
- Local PDFs: 100/100 downloaded under `papers/`.
- Official code URLs found: 20.
- GitHub repositories cloned: 19/20 under `repos/`.
- Failed code access: `SMKA` lists `https://github.com/HHrEtvP/SMKA`, but GitHub access failed with terminal prompts disabled. Existing local metadata also recorded this repository as inaccessible.

Distribution:

| Year | Count |
| --- | ---: |
| 2026 | 24 |
| 2025 | 35 |
| 2024 | 20 |
| 2023 | 13 |
| 2022 | 3 |
| 2021 | 2 |
| 2020 | 2 |
| 2019 | 1 |

Role distribution:

| Role | Count |
| --- | ---: |
| Core 3DSG / representation | 30 |
| Open-vocabulary 3DSG / grounding | 25 |
| LLM/VLM 3D reasoning | 15 |
| Semantic-geometry consistency / representation | 11 |
| Robotics / embodied graph | 11 |
| Functional / affordance graph | 3 |
| Edge-specific 3DSG representation | 2 |
| 3DGS / neural scene graph | 2 |
| Spatial-knowledge 3DSG | 1 |

Claim boundary:

- This is a screened survey, not a full-paper-card intake for all 100 papers.
- Existing read papers keep their previous detailed notes in `literature/<paper-folder>/`.
- New papers are screened for relationship to the new idea: representing and testing whether high semantic relation scores are geometrically valid in 3D.

## 1. Working Research Question

User idea:

> In 3D Scene Graphs, use both semantic and geometry signals at the representation level to study semantic-geometry consistency: if a semantic score is high, does the relation actually hold geometrically?

Refined question:

> Can a 3DSG relation edge represent semantic plausibility and geometric validity as separable, calibrated quantities, so that semantically plausible but physically inconsistent relations can be detected, re-ranked, abstained from, or repaired?

This is close to the current H001 claim but the emphasis shifts from only an evaluation/re-ranking layer to a representation question:

- Current H001: calibrated geometry-consistency evaluation/re-ranking for existing relation-source outputs.
- New branch: relation-edge representation where semantic confidence, geometry evidence, uncertainty, and provenance are explicit and trainable/evaluable.

## 2. Relationship Map Across Papers

### 2.1 Foundation: 3DSG as semantic plus 3D structure

Key papers:

- `3D Scene Graph: A Structure for Unified Semantics, 3D Space, and Camera` (ICCV 2019)
- `Learning 3D Semantic Scene Graphs from 3D Indoor Reconstructions` (CVPR 2020)
- `SceneGraphFusion` (arXiv 2021)
- `Hydra` (RSS 2022)

Facts:

- These papers define 3DSG as a structured graph over objects, places, rooms, cameras, and relations.
- Geometry is already part of the representation, so novelty cannot be "combine semantics and geometry."

Inference:

- The gap is not representation existence. The gap is relation-edge accountability: does the edge store enough evidence to distinguish semantic plausibility from geometric validity?

### 2.2 Edge modeling and closed-set relation prediction

Key papers:

- `SGGpoint` (CVPR 2021)
- `SMKA` (CVPR 2023)
- `VL-SAT` (CVPR 2023 Highlight)
- `SGFormer` (arXiv 2023)
- `Lang3DSG` (arXiv 2023)
- `3D-VLAP` (arXiv / TMM 2024)

Facts:

- `SGGpoint` makes relation edges first-class learned objects through EdgeGCN-style reasoning.
- `SMKA` brings support hierarchy, spatial knowledge, and symbolic knowledge into point-cloud relation prediction.
- `VL-SAT` uses visual-linguistic semantic supervision to improve relation prediction, especially for long-tail/ambiguous relations.

Inference:

- These papers make "edge-aware" or "semantic plus geometry features" insufficient as a contribution.
- A defensible branch should ask whether the learned edge representation is calibrated to physical consistency, not only whether it improves predicate recall.

### 2.3 Open-vocabulary 3DSG and queryable graph systems

Key papers:

- `Open3DSG` (CVPR 2024)
- `CCL-3DSGG` (CVPR 2024)
- `ConceptGraphs` (ICRA 2024)
- `OVSG` (CoRL 2023)
- `HOV-SG` (RSS 2024)
- `OpenGraph` (RA-L 2024)
- `Open-Vocabulary Octree-Graph` (ICCV 2025)
- `ZING-3D` (arXiv 2025)
- `VIZOR` (WACV 2026)

Facts:

- Recent systems increasingly use CLIP/VLM/LLM features for queryable objects, open-set relations, and downstream task grounding.
- Several graph representations store geometry-like edge attributes such as distance, vectors, hierarchy, or coarse spatial relation.

Inference:

- Open-vocabulary relation prediction amplifies the semantic-confidence problem: a relation phrase can be plausible in language but invalid in the actual scan geometry.
- This supports a semantic/geometry decoupling representation rather than another open-vocabulary generator.

### 2.4 Direct semantic-geometry consistency and novelty threats

Key papers:

- `RelWitness` (arXiv 2026)
- `FirePlace` (CVPR 2025)
- `RieMind` (arXiv 2026)
- `3D-VCD` (CVPR 2026 accepted / arXiv)
- `SG-PGM` (arXiv 2024)
- `GREAT` (CVPR 2025)
- `ToLL` (arXiv 2026)
- `Statistical Confidence Rescoring for Robust 3D Scene Graph Generation from Multi-View Images` (arXiv 2025)

Facts:

- `RelWitness` is the closest novelty threat: it explicitly introduces visual-geometric relation witnesses and calibrated witness quality for open-vocabulary 3DSG.
- `FirePlace` and `RieMind` show that LLM semantic/common-sense reasoning benefits from explicit 3D geometric refinement or tools.
- `3D-VCD` shows hallucination mitigation through scene-graph perturbation / contrastive decoding.
- `SG-PGM` and `GREAT` show semantic-geometric fusion in downstream alignment and affordance grounding.

Inference:

- The new branch cannot claim first use of geometry verification, witnesses, semantic-geometric fusion, or calibration in isolation.
- The stronger claim is representation-level separation and evaluation of semantic confidence versus geometry validity across relation sources, with explicit controls.

### 2.5 LLM/VLM graph reasoning and downstream task use

Key papers:

- `SayPlan` (CoRL 2023 Oral)
- `SG-Nav` (NeurIPS 2024)
- `3DGraphLLM` (ICCV 2025)
- `3D-Mem` (CVPR 2025)
- `3D-GRAND` (CVPR 2025)
- `SCOUT/SymSearch` (arXiv 2026)
- `SceneGraphGrounder` (arXiv 2026)
- `View-on-Graph` (AAAI 2026)
- `GraphEQA`, `GraphPad`, `EmbodiedRAG`

Facts:

- 3DSG is increasingly used as an interface for LLM/VLM planning, navigation, visual grounding, QA, and embodied reasoning.
- These systems often evaluate task success, grounding accuracy, or hallucination, but do not always isolate relation-level semantic error versus geometry violation.

Inference:

- Downstream use gives motivation for why relation consistency matters.
- It should not become the main branch immediately unless the relation-level representation is already validated.

### 2.6 Functional, affordance, articulation, and dynamic graphs

Key papers:

- `OpenFunGraph` (CVPR 2025 Highlight)
- `FunGraph` (arXiv 2025)
- `FunFact` (arXiv 2026)
- `ArtiSG` (arXiv 2025)
- `Pandora` (arXiv 2026)
- `DovSG` (T-RO/arXiv 2024)
- `FROSS` (ICCV 2025)
- `LOST-3DSG`, `DGSG-Mind`, `OGScene3D`

Facts:

- Functional and articulated relations expand beyond simple spatial predicates.
- Dynamic and online systems require graph updates and temporal consistency.

Inference:

- These are good future extensions, but they broaden the problem too much for the first representation branch.
- For H001 continuity, begin with geometry-checkable relation families and only later add functional/attachment/articulation.

## 3. Code Investigation Summary

Full static inventory is in `meta/code_inventory.md`. Important findings:

| Code group | Repositories | Useful for this branch | Limitation |
| --- | --- | --- | --- |
| Closed-set 3DSG edge models | `SGGpoint`, `VL-SAT` | Edge feature extraction, relation scores, 3DSSG-compatible baselines | Mostly predicts labels; no explicit validity channel |
| Open-vocabulary relation sources | `Open3DSG`, `OpenFunGraph`, `FROSS` | Open-set relation proposals and source adapters | Relation confidence is not guaranteed to be geometry-calibrated |
| Queryable/open-vocab maps | `ConceptGraphs`, `OVSG`, `HOV-SG`, `OpenGraph`, `Octree-Graph` | Node/edge graph construction, object retrieval, distance/vector fields | Often downstream/map focused, not relation-level consistency benchmark |
| Upstream open-vocab perception | `OpenScene`, `OpenMask3D`, `LangSplat` | Object features, masks, language fields | Node/object level, not enough for edge validity |
| Robotics graph infrastructure | `Hydra`, `DovSG`, `SG-Nav`, `3D-Mem` | Hierarchy, online graph updates, downstream task motivation | Adds simulator/planning complexity |
| Graph-to-LLM interfaces | `3DGraphLLM`, `Beyond Bare Queries` | Graph serialization/embedding, relation use in language tasks | Does not directly solve semantic-score/geometric-validity decoupling |

Implementation inference:

- The most reusable code for an H001-compatible branch is still `VL-SAT` and `Open3DSG` as relation sources, plus the existing H001 geometry join artifacts.
- `Octree-Graph`, `OVSG`, `HOV-SG`, and `OpenGraph` are representation references because they expose hierarchy, distance, vectors, and queryable graph structure.
- `RelWitness` is methodologically close but no official code was found in this run; it should be treated as a required related-work boundary, not as an executable baseline yet.

## 4. What The Literature Implies For The New Idea

Facts:

- 3DSG already encodes semantic and spatial structure.
- Open-vocabulary and VLM-based 3DSG methods are now common.
- Several recent papers expose geometry, witness, distance, or task-grounding evidence.
- Current H001 already has Docker-generated source outputs for `VL-SAT` and `Open3DSG`, geometry joins, violation metrics, controls, and bootstrap evidence.

Paper-claim implication:

- Weak claim: "We combine semantic and geometry in 3DSG."
- Stronger claim: "We show that relation semantic confidence and geometric validity are different variables, quantify their mismatch, and learn/evaluate relation-edge representations that make the mismatch observable and actionable."

Reviewer-defense implication:

- Must show high semantic score but invalid geometry cases.
- Must show geometry-only or hard-rule filtering is not enough.
- Must report recall/coverage cost and denominator caveats.
- Must include wrong-pair/shuffled-geometry and family-specific controls.
- Must compare at least two relation sources if making a source-agnostic claim.

## 5. Seven Method Proposals

### Method 1. Dual-Channel Relation Edge Representation

Core idea:

- Represent every candidate edge as:
  `edge = (subject, object, predicate_text, semantic_score, geometry_evidence, p_geom_valid, uncertainty, provenance)`.
- Keep `semantic_score` and `p_geom_valid` separate rather than collapsing them into a single relation confidence.

Integration with H001:

- Directly compatible with current H001 rows from `VL-SAT` and `Open3DSG`.
- Existing geometry join can supply distance, vertical order, contact/support evidence, overlap, relation family, and verifier decision.

Evaluation:

- `Recall@K`, `Violation@K`, `ECE/Brier` for `p_geom_valid`, high-semantic invalid rate, and abstention coverage.

Novelty risk:

- Must cite `Octree-Graph`, `Open3DSG`, `RelWitness`, and `SGGpoint`.
- Novelty is not the edge tuple itself; it is the explicit semantic-validity separation and calibrated evaluation.

Verdict:

- Best first branch. Minimal implementation risk and most aligned with current H001.

### Method 2. Semantic-Geometry Consistency Embedding

Core idea:

- Learn an embedding where valid `(predicate, subject geometry, object geometry, pair geometry)` tuples are close and counterfactual invalid tuples are far.
- Use positive GT relations and generated negatives such as wrong-pair, swapped-subject/object, shuffled-geometry, and predicate-family counterfactuals.

Integration with H001:

- Use current H001 exact-label GT positives and GT-derived negatives.
- Start with `support_contact`, `proximity`, `relative_vertical`; optionally add `attachment_deferred` only after separate user confirmation.

Evaluation:

- AUROC/AUPRC for valid vs invalid, retrieval of valid edge among semantic candidates, robustness to wrong-pair controls, and calibration transfer from `VL-SAT` to `Open3DSG`.

Novelty risk:

- Similar in spirit to contrastive and visual-linguistic pretraining papers, but focused on relation-level semantic-geometry consistency rather than object/node semantics.

Verdict:

- Strongest representation-method candidate if there is time to train a small model.

### Method 3. Score Decomposition: Semantic Prior Plus Geometry Residual

Core idea:

- Model relation confidence as:
  `logit(edge_valid) = f_sem(predicate, labels, source_score) + f_geom(3D evidence) + f_interaction(predicate, geometry)`.
- The paper studies where `f_sem` is high but `f_geom` contradicts it.

Integration with H001:

- Use current semantic-only scores as `f_sem` inputs and existing verifier/calibrator features as `f_geom`.
- Train/calibrate on train/train-dev, report validation-only metrics.

Evaluation:

- Semantic-only vs geometry-only vs decomposed model.
- Per-family calibration curves.
- High-semantic/low-geometry quadrant analysis.

Novelty risk:

- Could look like a simple calibrated reranker unless the decomposition is analyzed and used as representation evidence.

Verdict:

- Good low-risk upgrade from current H001 re-ranking.

### Method 4. Graph-Level Consistency Energy

Core idea:

- Move from independent edge scoring to graph-level consistency.
- Penalize mutually inconsistent edges, for example conflicting support direction, impossible vertical cycles, incompatible contact/proximity states, or duplicate contradictory predicates over the same object pair.

Integration with H001:

- Start after Method 1 or Method 3 because it needs reliable edge-level scores.
- Use H001 prediction rows as candidates, then optimize a small graph energy or factor graph over each subgraph.

Evaluation:

- Edge-level `Violation@K`, graph-level contradiction count, recall loss, and qualitative failure taxonomy.

Novelty risk:

- Related to factor-graph reasoning, Hydra-style spatial structure, and `FunFact`.
- Keep scope to relation consistency rather than full robot planning.

Verdict:

- Good second-stage method. Too broad as the first branch.

### Method 5. Counterfactual Consistency Benchmark

Core idea:

- Build a benchmark protocol that intentionally decouples semantic plausibility from geometry:
  wrong pair, shuffled geometry, swapped subject/object, perturbed object height, removed contact, and relation-family label flip.

Integration with H001:

- Current H001 controls already include wrong-pair/shuffled-style ideas; formalize them as a representation benchmark.
- Use the same `VL-SAT` and `Open3DSG` source outputs.

Evaluation:

- Counterfactual sensitivity, false-valid rate under geometry corruption, and semantic-score invariance under geometry-breaking perturbations.

Novelty risk:

- Benchmark-only contribution needs method evidence or a very strong diagnostic result.

Verdict:

- Essential as an evaluation component, not enough alone as the main method.

### Method 6. Evidence-Retrieval Relation Verifier

Core idea:

- For each semantic relation proposal, retrieve geometry evidence and optionally visual witness views, then score whether the evidence supports the relation.
- The relation edge stores evidence provenance, not only a scalar score.

Integration with H001:

- Existing H001 geometry evidence can be the first evidence source.
- Qwen-VL or image crops can be a later third-source extension, but should remain non-main until Docker inference and validation finish.

Evaluation:

- Evidence availability, evidence sufficiency, invalid high-semantic relation demotion, and human-auditable examples.

Novelty risk:

- `RelWitness` is very close. This branch must emphasize arbitrary relation-source reliability, denominator transparency, and existing-source re-ranking rather than claiming first witness evidence.

Verdict:

- Valuable, but only after careful Related Work positioning.

### Method 7. Uncertainty-Gated Graph Interface For LLM/Robot Tasks

Core idea:

- Expose relation edges to an LLM/planner only when semantic and geometry channels agree; otherwise abstain, ask for more evidence, or mark the edge as uncertain.

Integration with H001:

- Use the edge representation from Method 1 as input.
- Evaluate offline first on graph QA/grounding/target-selection tasks, not full navigation.

Evaluation:

- Invalid answer rate, hallucinated relation use, abstention rate, task accuracy, and relation-violation breakdown.

Novelty risk:

- Overlaps with `SayPlan`, `SG-Nav`, `3DGraphLLM`, `RieMind`, `3D-VCD`, and `3D-Mem`.
- Keep as downstream validation, not main contribution.

Verdict:

- Good future extension after the relation representation is validated.

## 6. Recommended Branch Plan

Recommended main direction:

> Semantic-Geometry Consistency Edge Representation for 3D Scene Graphs.

Minimal first prototype:

1. Use existing H001 `VL-SAT` and `Open3DSG` relation-source outputs.
2. Define the dual-channel edge schema from Method 1.
3. Add Method 3 score decomposition as the first trainable/calibrated model.
4. Use Method 5 controls as the benchmark protocol.
5. Report both edge-level metrics and quadrant analysis:
   - high semantic / high geometry
   - high semantic / low geometry
   - low semantic / high geometry
   - low semantic / low geometry

Do not start with:

- A new open-vocabulary 3DSG generator.
- Full robot navigation/planning.
- Functional or articulated relations as the main scope.
- Qwen-VL as main evidence before full Docker validation.

Best paper claim if successful:

> Relation confidence in open-vocabulary 3DSG is not a single quantity: semantic plausibility and geometric validity can disagree. A dual-channel, calibrated relation-edge representation exposes this disagreement and improves reliability under source-transfer and counterfactual geometry controls.

## 7. Orthogonal Persona Review

### Persona A: 3DSSG / Computer Vision Method Reviewer

Review stance:

- This reviewer cares about novelty against `SGGpoint`, `VL-SAT`, `Open3DSG`, `CCL-3DSGG`, `FROSS`, `VIZOR`, and especially `RelWitness`.

Assessment:

- Integration possible: yes.
- Main concern: the idea can look like "yet another geometry verifier" unless the representation question is central.
- Required evidence:
  - Two relation sources, not only `VL-SAT`.
  - Counterfactual geometry controls.
  - Per-family analysis.
  - Recall/violation tradeoff.
  - Clear difference from `RelWitness`: existing-source reliability and semantic/geometry score separation, not first witness evidence.

Verdict:

- Acceptable branch if framed as calibrated relation-edge representation and reliability diagnosis. Weak if framed as adding geometry to 3DSG.

### Persona B: ML Representation / Calibration Reviewer

Review stance:

- This reviewer cares about whether the semantic and geometry channels are statistically meaningful, calibrated, and not tuned on validation.

Assessment:

- Integration possible: yes, because H001 already has GT positives, GT-derived negatives, source scores, geometry features, and bootstrap machinery.
- Main concern: hand-designed features and thresholds can appear post hoc.
- Required evidence:
  - Train/train-dev-only fitting.
  - Calibration curves, Brier/NLL/ECE, AUROC/AUPRC.
  - Wrong-pair and shuffled-geometry controls.
  - Source-transfer test: fit on one source or train-dev, evaluate on both `VL-SAT` and `Open3DSG`.
  - Ablation: semantic-only, geometry-only, dual-channel, and interaction/decomposition.

Verdict:

- Strong integration path. Method 2 or Method 3 can make the branch more than a rule-based verifier.

### Persona C: Robotics / Embodied AI Reviewer

Review stance:

- This reviewer cares about whether reliable relation edges matter for downstream tasks, not only benchmark tables.

Assessment:

- Integration possible: yes, but downstream should be secondary.
- Main concern: if the branch jumps to navigation/search/planning, simulator/perception complexity will dominate the thesis.
- Required evidence:
  - Keep offline relation reliability as the main claim.
  - Add only a small downstream sanity check after relation metrics are stable.
  - Report abstention/uncertainty behavior, because robots should not act on high-semantic but geometry-invalid edges.
  - Use graph QA/grounding/target-selection before ObjectNav or full manipulation.

Verdict:

- Good long-term value, but the first paper should not become a robotics system paper.

## 8. Final Feasibility Judgment

Facts:

- The literature now contains many open-vocabulary and LLM/VLM 3D graph systems.
- Direct prior art already covers edge modeling, spatial knowledge, visual-linguistic training, open-vocabulary graph generation, geometry witnesses, functional relations, and LLM geometry tools.
- Current H001 artifacts already provide a rare advantage: two relation sources, geometry joins, violation metrics, calibration artifacts, controls, and denominator-transparent reports.

Inference:

- The idea is viable if it is treated as a representation and calibration problem:
  semantic confidence is not equivalent to geometric validity.
- The most defensible new branch is not a new 3DSG generator, but a relation-edge representation that exposes, calibrates, and evaluates semantic-geometry disagreement.
- The strongest initial method is Method 1 plus Method 3 plus Method 5:
  dual-channel representation, score decomposition, and counterfactual consistency benchmark.

Recommended next file if this branch is promoted:

- `hypothesis/CAND-001/H001_geometry-grounded-verification/semantic_geometry_representation_0609.md`

Do not promote to main H001 paper claim yet:

- This survey is branch exploration.
- Any claim expansion should wait for an explicit user decision and Docker-reproducible evidence.

