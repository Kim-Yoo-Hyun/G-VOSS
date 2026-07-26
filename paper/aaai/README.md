# RelCompat3D AAAI-27 Manuscript

Last updated: 2026-07-27 KST

This directory contains the active AAAI-27 source, an optional two-figure teaser
variant, and the canonical review PDFs. Superseded manuscript snapshots, the
AAAI-26 style, and historical inspection notes live under
`archive/paper/aaai_snapshots/`.

## Active Layout

| Path | Role |
| --- | --- |
| `main.tex`, `preamble.tex`, `sec/{0_abstract,1_introduction,2_related_work,3_method,4_experiments,5_discussion_limitations,6_conclusion}.tex` | active anonymous main-paper source in manuscript order |
| `main_teaser.tex` | optional variant that shares `main.tex` and adds the source-backed demotion before the method overview |
| `supplement.tex`, `sec/supplement.tex` | active method details and supplementary experiments, including matched-estimator, score-mapping, simple-baseline, routing, construct-dependence, point/mesh, uncertainty, and provenance evidence |
| `sec/old.tex` | inactive material retained outside the main and supplement builds |
| `reproducibility_checklist_main.tex`, `reproducibility_checklist.tex` | standalone checklist source |
| `aaai2027.sty`, `aaai2027.bst` | active AAAI-27 style |
| `official/` | preserved official anonymous and checklist templates |
| `Dockerfile.tex` | pinned paper-build environment |
| `main_aaai27.pdf` | canonical main-paper review PDF |
| `main_teaser_aaai27.pdf` | selected two-figure teaser upload layout; canonical review PDF |
| `supplement_aaai27.pdf` | canonical technical-supplement PDF |
| `reproducibility_checklist_aaai27.pdf` | canonical checklist PDF |

The default LaTeX outputs `main.pdf`, `main_teaser.pdf`, `supplement.pdf`, and
`reproducibility_checklist_main.pdf` are disposable build products and are not
canonical versions.

## Main-Paper Structure

The active manuscript uses six top-level sections:

1. Introduction
2. Related Work
3. Method, with Problem Formulation, Compatibility Estimation, and Family-Aware Re-Ranking
4. Experiments, with Data and Splits, Baselines and Training, Results, Ablations, and Qualitative Analysis
5. Discussion and Limitations
6. Conclusion

Problem formulation is part of Method; Experimental Setup and results share the
Experiments section. Result-specific interpretation stays next to the tables,
while claim scope, family heterogeneity, construct validity, and single-dataset limits
are consolidated in Discussion and Limitations.

## Verified Outputs

- `main_aaai27.pdf`: 9 US-Letter pages; technical content ends on page 7 and
  references begin in the remaining page-7 column; SHA256
  `5b9d917a61fc9045f46aa477750590f40c621157068ae74dec1ccc5e8e7f113b`.
- `main_teaser_aaai27.pdf`: 9 US-Letter pages with the source-backed full-width
  demotion on page 2 and method overview on page 3; technical content ends on
  page 7 and pages 8--9 contain references
  only; SHA256
  `ac0313df7248da518488f0f39ab7d6cce42d1ac2cc6d5f234fc2aee4631e588c`.
- `supplement_aaai27.pdf`: 18 US-Letter pages; SHA256
  `c56ee4b1a9c335e5d41ac88e9543a9ef4fa65f70fc0e4c6b3026b4b3d31da3fe`.
- `reproducibility_checklist_aaai27.pdf`: 2 US-Letter pages; SHA256
  `a346d55325dc63f7e9324cd0dc34dbcc0e72abc6ad3836f730d39c370477e212`.

The main canonical PDFs were not changed during the 2026-07-27 supplement
revision. The supplement canonical PDF was regenerated after reorganizing the
source into main-aligned Method and Experiments sections and adding the frozen
P0 score-mapping, simple-baseline, routing, and construct-dependence evidence.
The checklist canonical PDF was regenerated from the official AAAI-27
questions with compact status-only answers. Earlier smoke builds of the
consolidated source produced
9-page `main.pdf` and 10-page `main_teaser.pdf`.
The current teaser source already produced 10 pages before consolidation, and
pre/post-consolidation PDF text is identical; the extra page is therefore a
pre-existing transcript/layout issue rather than a consequence of merging the
section files. The fresh main and teaser logs also retain one pre-existing
4.43-pt overfull table row. Reconcile those two layout differences before the
next canonical release regeneration.

All four canonical files have zero Type 3 and CID/Identity-H fonts. The current
18-page supplement has no unresolved references or LaTeX/overfull warnings.
It includes matched Linear/MLP component diagnostics and five predeclared
fitting executions without changing the active method.
The Introduction grounds its geometric-mismatch motivation in direct witness
and constraint-refinement work and cites the foundational 3D Scene Graph paper.
Related Work uses three thematic subsections; every prose paragraph ends by
stating the shared premise and the distinction relative to RelCompat3D.
Related Work and Experimental Setup cite both the original 3RScan/RIO dataset
and the 3DSSG annotations. Method and Experimental Setup repeat citations at
the first local occurrence of named predictors/datasets, and the RRF baseline
cites its original publication; the Abstract remains citation-free.
The active manuscript uses the promoted `no_family_indicator_v1` framework.
`RelCompat3D-Linear` uses `T_i=p_i`; the family label selects the head and
procedure without entering the head feature vector, and its stored/primary
parameter counts are 66/43. `RelCompat3D-MLP` is a shared 69-parameter compact
nonlinear estimator whose family indicator is not constant. Both exclude the
source relation score and predictor identity and share the training/ranking
contract.
The ordered-pair and exact relation-candidate identities are distinguished in
Method, while the exact Recall, verifier-derived Violation, uncertainty, and
coverage definitions are consolidated under Experimental Setup.
Method also records each predictor's native score contract, the two implemented
predicate-signed height interactions, family-specific counterfactual
construction, shared loss constants, deterministic tie handling, and the
absence of predictor-specific normalization or refitting. The formal group-
averaging statement and proof are in the supplement.
The reported evaluation scope comprises support/contact, proximity, and
vertical-order relations, whereas the re-ranking scope comprises only
proximity and vertical order. The main rule defines the support/contact list
directly as the corresponding source-ranking subsequence. The manuscript also
states that counterfactual construction and the primary verifier share some
OBB-derived measurements and treats Violation@K as verifier-derived rather
than independent physical-validity ground truth.
The active overview and teaser assets are generated from locked ordered-pair
geometry and numeric summaries. `render_user_reference_figures.py` preserves
the user-supplied compositions while redrawing point projections, labels,
lines, modules, and relation graphs as SVG vectors. The dense neutral scene
marks are traced from the supplied compositions rather than embedded as raster
layers. The final PDF assets contain no raster images or PDF font objects. At
their manuscript widths, their minimum effective label sizes are 9.20 pt and
9.13 pt, minimum strokes are 0.60 pt and 0.60 pt, and all colored text has at
least 6.53:1 contrast on white. Figure 2
uses the final transformation-consistent notation $C^{\mathrm{tr}}(T,G)$.

The current main paper excludes Codex-derived validity results. Its narrative
is failure-first. Figure 1 presents a qualitative demotion, Figure 2 presents
the compatibility and family-aware re-ranking pipeline, and Figure 3 presents
the percentage-scale three-predictor \(K\) trajectories for Source,
`RelCompat3D-Linear`, and `RelCompat3D-MLP`. The three-case
pair--evidence--outcome grid is
supplemental. Figures use Helvetica-compatible TeX Gyre Heros source text,
white backgrounds, and restrained colorblind-safe accents. Table 1 appears
before its quantitative interpretation and jointly reports percentage
Recall/Violation at all five \(K\) values. In the selected teaser layout, the
one-column matched-control Table 2 and compact \(K=50\) point- and mesh-based
audit Table 3
appear side by side at the top of page 7. Table 3 reports Source,
RelCompat3D-Linear, paired change, and measured/decidable coverage; MLP and
all-\(K\) point/mesh/agreement audits are in the supplement. Product (all
families) is retained in Table 1 as a scope comparison, and
Open3DSG uses the public/full-target route. K=50 is an intermediate reported
value in the prose, not a separately registered or visually selected
endpoint; K=5 and K=100 remain visible in
the complete curve. The supplement reports the
ReplicaSSG/FROSS stress test across all five K values. The completed Codex proxy reference,
mandatory adjudication, and verifier comparison exist
only in `paper/paper_nonsub/` and must not enter the submission bundle unless a
later explicit reporting decision follows external verification.

The selected teaser manuscript places the one-column, source-backed demotion on
the first page: the violated `desk higher than ceiling` relation moves from
rank 6 to 425. The full-width method overview is Figure 2, and aggregate
results remain in Table 1 and Figure 3. To keep the seven-page body limit
without reducing fonts, both main variants place the three-case qualitative
grid in the supplement. The current source retains the first-page vertical
overfull for the final layout pass, following the user's explicit decision to
keep Figure 1 on the first page.

Main Table 1 includes `RelCompat3D-Linear` and `RelCompat3D-MLP` as two proposed
compatibility estimators under the same framework. RankAvg and RRF are matched
fusion baselines; pooled product is a supplemental family-conditioning
ablation. Main Table 2 reports their matched K=50 controls, while the supplement
reports the complete K=100 controls and nine
train-only counterfactual-policy refits. Their default reproduces the main
model, and maximum absolute changes are `.0020/.0011` R/V at K=50 and
`.0035/.0020` at K=100. Paired scan-level cluster intervals are given for every
reported K. A separate CPU table reports the compatibility/re-ranking layer
from preloaded rows and explicitly excludes source inference, reconstruction,
geometry joining, file parsing, metrics, and bootstrap.

The Point- and Mesh-Based Consistency Audit remeasures proximity and
vertical-order relations from point vertices and area-weighted mesh samples
without OBB inputs or primary verifier labels. Its alternative Violation
measure is not directly comparable to primary Violation. Its compact \(K=50\)
Linear agreement table is in the main paper. The MLP audit, all \(K\) values,
separate point/mesh estimates, coverage, thresholds, intervals,
and synthetic interventions are in the supplement. This reduces exact-rule
overlap but is not independent physical-validity ground truth.

## Build

From the repository root:

```bash
docker build -f paper/aaai/Dockerfile.tex -t relcompat3d-aaai27-tex:20260712 paper/aaai
docker run --rm --entrypoint bash --user "$(id -u):$(id -g)" \
  -v "$PWD":/workspace -w /workspace relcompat3d-geom-reliability:latest -lc \
  'python paper/scripts/render_user_reference_figures.py &&
   python paper/scripts/generate_draft_figures.py'
docker run --rm --entrypoint bash --user "$(id -u):$(id -g)" \
  -v "$PWD":/workspace -w /workspace relcompat3d-aaai27-tex:20260712 -lc \
  'for stem in figure2_tradeoff; do
     rsvg-convert --width 2400 --keep-aspect-ratio \
       --output paper/generated/figures/${stem}.png \
       paper/generated/figures/${stem}.svg;
   done'
# Convert the two native-vector user-composition redraws to outlined PDF 1.5.
docker run --rm --user "$(id -u):$(id -g)" \
  -v "$PWD":/workspace -w /workspace relcompat3d-aaai27-tex:20260712 sh -lc \
  'for stem in teaser_demotion_reference framework_user_reference; do
     rsvg-convert --format pdf \
       --output paper/generated/figures/${stem}.raw.pdf \
       paper/generated/figures/${stem}.svg;
   done'
for stem in teaser_demotion_reference framework_user_reference; do
  gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite \
    -dCompatibilityLevel=1.5 -dNoOutputFonts \
    -sOutputFile=paper/generated/figures/${stem}.pdf \
    paper/generated/figures/${stem}.raw.pdf
  rm paper/generated/figures/${stem}.raw.pdf
done
docker run --rm -v "$PWD/paper:/work" -w /work/aaai \
  relcompat3d-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
docker run --rm -v "$PWD/paper:/work" -w /work/aaai \
  relcompat3d-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error main_teaser.tex
docker run --rm -v "$PWD/paper:/work" -w /work/aaai \
  relcompat3d-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error supplement.tex
docker run --rm -v "$PWD/paper:/work" -w /work/aaai \
  relcompat3d-aaai27-tex:20260712 \
  latexmk -pdf -interaction=nonstopmode -halt-on-error \
  reproducibility_checklist_main.tex
```

After verification, copy the default outputs to the four versioned canonical
filenames above, then remove LaTeX intermediates. Do not retain multiple PDFs
with identical hashes in this directory.

## Submission Bundle

The upload bundle must contain one selected main-paper PDF (default or teaser),
the supplement, the checklist, and a
focused anonymous code/data ZIP generated from `no_family_indicator_v1/`,
its strict split/model/score locks, the compact final
ReplicaSSG protocol/evaluation summary, the feature-removal analysis,
active figure sources, and current manuscript source. Historical Codex-proxy, ReplicaSSG development branches,
Qwen-VL, and superseded manuscript material are excluded from this bundle.
The latest verified pre-table-layout upload bundle is
`release/relcompat3d_aaai27_openreview_20260720_084307/`. It selects the teaser layout
and includes the promoted `no_family_indicator_v1` source, locks, and compact
results, but it must be regenerated before upload to include the current
table-layout PDF revision. The default PDF remains a layout comparison.

AAAI-27 policy lock: at most 7 technical pages and 9 total pages; content after
the technical limit is references only. The checklist is uploaded separately. Supplementary
material is optional, anonymous, and not required reading.
