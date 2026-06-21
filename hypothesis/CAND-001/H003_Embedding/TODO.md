# H003 TODO

Last updated: 2026-06-20 KST

## Now

- [ ] Create `06_source_inventory.md`: exact read-only source path whitelist, allowed deployable fields, target fields, ignored hidden/proxy fields, and planned H003 artifact output root.
- [ ] Decide the first concrete source export: Open3DSG-derived CAND-001 train rows only, or a paired Open3DSG/VL-SAT source-transfer smoke.
- [ ] Decide whether to implement a schema/leakage validator before row export.
- [ ] Decide whether the first smoke artifact can stay under `hypothesis/CAND-001/H003_Embedding/artifacts/` or should wait until a Docker prototype gate.

## Next

- [ ] Draft the read-only row export manifest once `06_source_inventory.md` is fixed.
- [ ] Implement a no-training schema validator if the user approves moving from hypothesis docs to prototype tooling.
- [ ] Run Stage A dataset sanity before any learned model.

## Guardrails

- [x] Do not modify H001/GeoCalib experiment, paper, result, or release files.
- [x] Do not create an `experiments/` root for H003 until the hypothesis promotion gate passes.
- [x] Do not treat missing GT annotations as negatives by default.
- [x] Do not report learned-model gains without explicit-rule, semantic-only, and geometry-only baselines.

## Completed

- [x] Created H003 hypothesis branch under `hypothesis/CAND-001/H003_Embedding/`.
- [x] Captured initial semantic-geometry consistency embedding idea, risks, method contract, and hypothesis-stage TODOs.
- [x] Fixed H003 framing as `M1 schema + M5 counterfactual benchmark + M3 posterior first + M2 embedding second + M9 future extension`.
- [x] Froze H003 row schema, label policy, negative sampling policy, shortcut controls, split policy, and first source-scope boundary in `04_dataset_contract.md`.
- [x] Drafted `05_smoke_protocol.md` with dataset sanity checks, baselines, M3/M2 order, metrics, and smoke pass/fail gates.
- [x] Selected M3 factorized posterior as the first prototype target and M2 embedding as the second-stage method.
- [x] Decided H003 should use separate embedding/posterior terminology and treat H002 `RGA` as prior-branch context only.
