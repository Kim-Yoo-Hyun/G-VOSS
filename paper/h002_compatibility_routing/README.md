# H002 Paper Workspace

Last updated: 2026-07-11 KST

Standalone paper workspace for:

**Semantic-Geometry Compatibility Learning for Reliable 3D Scene Graph Relations**

The canonical source is `aaai2027/`. H001 manuscript files under
`paper/aaai/` are separate and must not be edited from this workspace.

## Current Claim

The paper proposes relation-aware evidence routing and validates the
predicate-geometry compatibility route on 3DSSG validation predictions from
VL-SAT and Open3DSG.

- main: higher/lower and bigger/smaller
- caveated: left/right
- geometry-only control: close by
- failure analysis: front/behind and support/contact

The paper does not claim official hidden-test, SOTA, all-relation reliability,
support/contact solved, learned G_e improvement, or calibrated p_obs/p_rel.

The current package is complete for this scoped claim: main manuscript 7 pages,
supplement 3 pages, and checklist 2 pages. No broader paper claim is opened by
this build.

## Files

- `aaai2027/`: canonical AAAI source, bibliography, supplement, checklist, figures, and tables
- `risk.md`: active reviewer-risk register

Earlier draft/outline/table duplicates, the venue-agnostic manuscript scaffold,
and the broad unvalidated framework PNG were removed.

## Evidence

- claim contract: `hypothesis/CAND-001/H002_factorized-relation-confidence/paper_claim_core.md`
- experiment root: `experiments/H002_compatibility_routing/`
- main table: `experiments/H002_compatibility_routing/main_validation_table_refresh/latest/`
- paper assets: `experiments/H002_compatibility_routing/paper_strengthening_assets/latest/`

Runtime stage-local `next_todo` values are provenance. Current work is governed
by `TODO.md`, not by old artifact fields.
