# H002 Reviewer Risk Register

Last updated: 2026-07-11 KST

## 1. Claim-Experiment Gap

**Risk:** relation-aware framework wording exceeds comparison-route evidence.

**Rule:** state that the framework is proposed and its compatibility route is
validated. Do not claim all relation families are solved.

## 2. Geometry-Rule Interpretation

**Risk:** H002 looks like post-hoc geometry filtering.

**Defense:** raw \(C_e=f_C(T_e,G_e)\) excludes \(Z_e\); compare semantic-only,
geometry-only, plain concatenation, wrong-predicate, shuffled-geometry, and
wrong-pair controls.

## 3. Arbitrary Product

**Risk:** \(S_2=\widetilde Z_e\widetilde C_e\) looks heuristic.

**Defense:** present the parameter-free \(\lambda=1\) risk-aware log utility and
product-of-experts interpretation. Do not tune \(\lambda\) on validation.

## 4. Target-Metric Coupling

**Risk:** comparison targets and Violation use related signed geometry.

**Defense:** keep Recall@K as semantic utility, report independent controls and
family/source slices, and avoid general reliability wording.

## 5. Validation-Only Evidence

**Risk:** results are confused with official hidden-test or leaderboard results.

**Rule:** write “official 3DSSG validation split” and “custom Violation@K.”
Open3DSG is an open-vocabulary source, while quantitative Recall uses the
closed-vocabulary 3DSSG mapping.

## 6. Lateral Generality

**Risk:** left/right is presented as universal success.

**Rule:** report the Open3DSG gains and VL-SAT Recall tradeoff. Front/behind
remains a reference-frame/depth failure.

## 7. Support/Contact Circularity

**Risk:** the support/contact proxy is used as independent reliability evidence.

**Rule:** retain the 35/347 imbalance, 0.908 majority baseline, and 1.0/1.0
geometry-rule recovery in limitations. No solved-route wording or metric rerun.

## 8. Discarded Extensions

Learned G_e and p_obs/p_rel are not promoted. They may appear only as failed
diagnostics or future work, not as implemented main modules.

## 9. Normalization

The main score uses frozen label-free per-source normalization for \(Z_e\) and
per-source-family normalization for raw \(C_e\). Report raw/rank sensitivity
and do not claim normalization invariance.

## Submission Boundary

Allowed: scoped validation-level compatibility reranking with explicit route
boundaries.

Blocked: hidden-test, SOTA, leaderboard, all-family solved, support/contact
solved, calibrated selective reliability, or learned-geometry improvement.
