# H003 TODO

Last updated: 2026-06-18 KST

## Now

- [ ] Freeze H003 row schema: semantic fields, compact geometry fields, source score/rank, label provenance, corruption provenance, and split id.
- [ ] Define label policy: confirmed positive, weak positive, generated negative, audit negative, unknown.
- [ ] Define negative sampling policy: wrong-pair, swap, shuffled geometry, predicate-family flip, vertical inversion, and support/contact removal.
- [ ] Define shortcut controls: semantic-only, geometry-only, same-class/different-geometry, same-geometry/different-predicate, same-rank-band.
- [ ] Decide first source scope: use existing source summaries only, or build a small read-only row export from existing artifacts without changing H001 outputs.

## Next

- [ ] Draft `04_dataset_contract.md` after row schema and source scope are fixed.
- [ ] Draft `05_smoke_protocol.md` with split policy, baselines, metrics, and pass/fail thresholds.
- [ ] Decide whether the first prototype is binary classifier, two-tower embedding, or binary + margin ranking hybrid.
- [ ] Decide whether H003 should reuse H002 RGA terminology or keep a separate embedding terminology.

## Guardrails

- [ ] Do not modify H001/GeoCalib experiment, paper, result, or release files.
- [ ] Do not create an `experiments/` root for H003 until the hypothesis promotion gate passes.
- [ ] Do not treat missing GT annotations as negatives by default.
- [ ] Do not report learned-model gains without explicit-rule, semantic-only, and geometry-only baselines.

## Completed

- [x] Created H003 hypothesis branch under `hypothesis/CAND-001/H003_Embedding/`.
- [x] Captured initial semantic-geometry consistency embedding idea, risks, method contract, and hypothesis-stage TODOs.

