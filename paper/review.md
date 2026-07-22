# RelCompat3D Reviewer Assessment

Last updated: 2026-07-22 KST

이 문서는 selected main PDF에 대한 reviewer-level assessment와 consensus만
소유한다. Exact attack, evidence boundary, mitigation, blocked wording, and
submission gates are not repeated here; they are owned by `paper/risk.md`.

## Review Target

- Main artifact: `paper/aaai/main_teaser_aaai27.pdf`
- Layout: 9 pages, seven technical pages, Figures 1--3 and Tables 1--3.
- Scientific scope: fixed relation candidates; proximity/vertical-order
  family-aware re-ranking; support/contact source-order preservation.
- Evaluation scope: VL-SAT, Open3DSG, and SGFN on one shared 3DSSG target.
- Proposed estimators: RelCompat3D-Linear and RelCompat3D-MLP.

The freshly consolidated source has a separate 10-page/4.43-pt-overfull layout
debt. That issue is tracked as R7 in `paper/risk.md` and does not change the
scientific assessment below.

## Overall Assessment

Current range: **borderline to weak accept**.

The paper's strongest aspect is the direct connection between an observed
failure and the method contract: a source relation score is not treated as an
explicit estimate of compatibility with the corresponding ordered-pair
geometry. RelCompat3D separates those factors, learns compatibility with
linked counterfactuals, imposes the applicable relation transformations, and
uses matched family-aware comparisons.

The acceptance ceiling is not presentation volume or missing baselines. It is
the combination of construct dependence and one shared dataset target. These
limits are disclosed and partially stress-tested, but not eliminated. The
correct submission route is therefore a scoped reliability-method paper, not a
broad 3D scene graph SOTA or physical-validity claim.

## Reviewer Score Summary

| perspective | score | confidence | central judgment |
| --- | ---: | ---: | --- |
| Method and novelty | 5/10 | 4/5 | principled framework, moderate novelty ceiling |
| Experimental validity | 5/10 | 5/5 | unusually careful controls, residual construct/scope limits |
| Writing and reproducibility | 6/10 | 4/5 | clear narrative and strong artifacts, final layout pass pending |
| Consensus | 5--6/10 | high | defensible borderline/weak-accept submission |

## Reviewer A — Method and Novelty

### Verdict

The contribution is more than a generic score multiplier because the input
separation, ordered-pair identity, counterfactual training, transformation
averaging, and family-preserving output rule form one falsifiable reliability
contract. The individual components—small classifiers, product scoring, and
finite transformation averaging—are not independently high-novelty.

### What works

- The failure mechanism determines the method form rather than serving as a
  generic motivation.
- Compatibility excludes source relation score and predictor identity.
- Linear and nonlinear estimators test whether the effect depends on one model
  capacity.
- Transformation consistency is exact at inference for the defined proximity
  and vertical transformations.
- Family-aware re-ranking acknowledges the support/contact evidence boundary
  instead of applying the model indiscriminately.
- Closest generator-internal geometry methods are distinguished from fixed
  output reliability assessment.

### What may still trigger rejection

- A reviewer may reduce the method to engineered geometric features and
  post-processing.
- Product scoring and group averaging are standard operations.
- The transformation set and re-ranking scope cover only two relation families.
- Strong alternatives occupy different Pareto points, preventing a simple
  method-dominance claim.

The exact response and allowed novelty statement are owned by R4 and R5 in
`paper/risk.md`.

### Representative comment

> The paper is strongest when framed as a structured reliability contract for
> fixed predictions. Its novelty should rest on the coupling of factor
> separation, counterfactual compatibility learning, exact relation
> transformations, and family-scoped re-ranking—not on the product score.

## Reviewer B — Experimental Validity

### Verdict

The experimental design is strong for a re-ranking paper: it exposes all five
$K$ values, reports exact-match Recall with verifier-derived Violation, matches
the ranking procedure across comparators, and includes targeted falsification
controls. The remaining concern is whether the measured improvement transfers
beyond related geometric constructs and the shared 3DSSG target.

### What works

- All proposed and matched methods use the same candidate universe.
- Recall and Violation are reported together, ruling out a simple filtering
  explanation.
- Wrong-predicate, wrong-pair, shuffled-geometry, endpoint-swap,
  distance-only, and compatibility-only controls probe distinct mechanisms.
- Paired scan-level intervals respect dependence among contexts from one scan.
- Feature-removal and counterfactual sensitivity analyses test literal rule
  copying and protocol fragility.
- The point/mesh audit removes OBB inputs and primary verifier labels and
  reproduces the direction of change under an alternative measurement.

### What may still trigger rejection

- Compatibility construction and primary Violation share geometric primitives.
- The alternative audit shares reconstructed geometry and ontology and is not
  independent ground truth.
- Three predictors do not constitute three dataset tests.
- Support/contact is evaluated but intentionally unchanged.
- Public Open3DSG candidate coverage requires careful denominator wording.

Exact facts and defenses are owned by R1, R2, R3, and R6 in
`paper/risk.md`.

### Representative comment

> The matched controls and scan-level intervals are convincing, but the paper
> should remain explicit that it measures verifier-derived reliability across
> predictors on one target rather than independent physical correctness or
> dataset generalization.

## Reviewer C — Writing, Figures, and Reproducibility

### Verdict

The selected teaser has a coherent visual sequence: Figure 1 motivates the
failure, Figure 2 explains the mechanism, and Figure 3 summarizes the
Recall--Violation trajectories. The six-section structure is conventional and
the main tables are self-contained. Reproducibility evidence is stronger than
typical for a compact post-processing method.

### What works

- Abstract/Introduction follow problem → cause → method → scoped result.
- Related Work distinguishes generator design, geometric evidence, and
  reliability/calibration.
- Method can be followed without treating the figure as the only definition.
- Table 1 exposes all $K$ values; Tables 2 and 3 isolate controls and the
  alternative audit.
- The technical supplement contains construction rules, proofs, sensitivities,
  uncertainty, runtime, and provenance.
- Docker source, checksums, and the standalone checklist are available.

### Remaining revision pressure

- First-read explanations of counterfactuals, transformation averaging, and
  family-aware list selection must remain plain enough for a non-specialist.
- Main prose should interpret patterns rather than repeat dense tables.
- Scientific limits should be stated once in Discussion rather than repeated as
  defensive prose throughout the paper.
- The consolidated source must be brought back to the selected 9-page layout
  and its overfull row fixed before upload.

Detailed layout/release action is owned by R7 in `paper/risk.md`.

### Representative comment

> The manuscript is organized and reproducible. The final pass should focus on
> preserving the clear failure–mechanism–evidence flow while reconciling the
> selected PDF with the consolidated source.

## Consensus

### Accepted contribution summary

1. A concrete ordered-pair geometric mismatch not captured by exact-match
   retrieval alone.
2. Source-score-excluded predicate--geometry compatibility with linked
   counterfactual supervision.
3. Exact consistency under the defined proximity and vertical transformations.
4. Family-aware re-ranking with matched strong comparisons.
5. Joint Recall--Violation evidence, targeted controls, and an alternative
   point/mesh audit.

### Main rejection paths

- presenting product scoring or transformation averaging alone as the novelty;
- implying independent physical-validity validation;
- treating three predictors as cross-dataset generalization;
- implying that support/contact is improved;
- uploading a source-built PDF that violates the page limit or contains the
  unresolved overfull row.

### Current recommendation

> Proceed with `main_teaser_aaai27.pdf` as the selected main layout. Preserve
> the scoped reliability claim, resolve R7 before final upload, regenerate the
> anonymous bundle, and do not add experiments unless they close a named risk
> or intentionally broaden the claim.

## Next Review Gate

Repeat the final review only after:

1. the consolidated source reproduces a compliant selected teaser PDF;
2. all canonical hashes and release manifests are refreshed;
3. title, abstract, TL;DR, author metadata, and anonymity checks are frozen.
